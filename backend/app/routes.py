import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.auth import verify_api_key

router = APIRouter()

# ─── GET ALL PRODUCTS (public) ──────────────────────────────────
@router.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

# ─── GET SINGLE PRODUCT (public) ────────────────────────────────
@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ─── ADD NEW PRODUCT (protected) ────────────────────────────────
@router.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# ─── UPDATE PRODUCT (protected) ─────────────────────────────────
@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, updates: ProductUpdate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product

# ─── DELETE PRODUCT (protected) ─────────────────────────────────
@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": f"{product.name} deleted successfully"}

# ─── UPLOAD PRODUCT IMAGE (protected) ───────────────────────────
@router.post("/products/{product_id}/upload-image")
def upload_image(product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    upload_dir = "app/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{product_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    product.image_url = f"/uploads/{product_id}_{file.filename}"
    db.commit()
    db.refresh(product)
    return {"message": "Image uploaded", "image_url": product.image_url}