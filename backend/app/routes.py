import os
import shutil
import uuid
import time
import imghdr
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, User
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    verify_admin_access,
)

router = APIRouter()

# ─── Upload Directory Configuration ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── Rate limiting (simple in-memory per-IP) ─────────────────────
_rate_limits: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60       # seconds
RATE_LIMIT_MAX = 60          # requests per window


def _check_rate_limit(request: Request, max_requests: int = RATE_LIMIT_MAX) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = _rate_limits.setdefault(client_ip, [])
    # prune older timestamps
    _rate_limits[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[client_ip]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again later."
        )
    _rate_limits[client_ip].append(now)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _sanitize_filename(filename: str | None) -> str:
    """Generate a collision-resistant, path-traversal-free UUID filename."""
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    basename = os.path.basename(filename)
    _, ext = os.path.splitext(basename)
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_IMAGE_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' not allowed. Allowed: {sorted(list(ALLOWED_IMAGE_EXT))}"
        )
    return f"{uuid.uuid4().hex}{ext_lower}"


# ─── AUTHENTICATION ROUTES ───────────────────────────────────────
@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user account."""
    _check_rate_limit(request, max_requests=10)
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    # SECURITY FIX: Disabled auto-admin to prevent privilege escalation attacks
    # Admin users must be created manually via database or secure seed script
    assigned_role = "customer"  # Always assign customer role on registration

    new_user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        role=assigned_role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/auth/login", response_model=Token)
def login_user(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate with email & password to receive a JWT access token."""
    _check_rate_limit(request, max_requests=15)
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        email=user.email,
    )


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get profile details of the authenticated user."""
    return current_user


# ─── PRODUCTS (PUBLIC) ───────────────────────────────────────────
@router.get("/products", response_model=List[ProductResponse])
def get_products(
    in_stock_only: bool = False,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Fetch list of products with optional category filter."""
    query = db.query(Product)
    if in_stock_only:
        query = query.filter(Product.in_stock == True)
    if category:
        query = query.filter(Product.category == category)
    products = query.order_by(Product.id.asc()).offset(skip).limit(min(limit, 100)).all()
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Fetch single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# ─── PRODUCTS (PROTECTED - ADMIN ONLY) ───────────────────────────
@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(verify_admin_access),
):
    """Add a new product (Admin only: requires Admin API Key or Admin JWT)."""
    _check_rate_limit(request)
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updates: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(verify_admin_access),
):
    """Update a product (Admin only: requires Admin API Key or Admin JWT)."""
    _check_rate_limit(request)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(verify_admin_access),
):
    """Delete a product (Admin only: requires Admin API Key or Admin JWT)."""
    _check_rate_limit(request)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product_name = product.name
    db.delete(product)
    db.commit()
    return {"message": f"{product_name} deleted successfully"}


@router.post("/products/{product_id}/upload-image")
def upload_image(
    product_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: dict = Depends(verify_admin_access),
):
    """Upload a product image safely (Admin only)."""
    _check_rate_limit(request)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Validate Content-Type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content-type '{file.content_type}'. Allowed: {sorted(list(ALLOWED_IMAGE_TYPES))}"
        )

    # SECURITY FIX: Validate file content using magic bytes to prevent malicious file uploads
    file_bytes = file.file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Verify file is actually an image using imghdr (checks magic bytes)
    file.file.seek(0)
    detected_type = imghdr.what(None, file_bytes[:512])  # Check first 512 bytes for magic number
    if not detected_type or detected_type not in ['jpeg', 'png', 'webp', 'gif']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content is not a valid image. Detected: {detected_type or 'unknown'}"
        )
    
    file.file.seek(0)

    # Sanitize and generate safe unique filename
    safe_filename = _sanitize_filename(file.filename)
    target_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save safely to disk
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    product.image_url = f"/uploads/{safe_filename}"
    db.commit()
    db.refresh(product)

    return {
        "message": "Image uploaded successfully",
        "image_url": product.image_url,
        "product_id": product.id
    }