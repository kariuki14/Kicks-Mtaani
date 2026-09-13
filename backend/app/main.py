from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app import routes

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kicks Mtaani API")

# CORS — allows your frontend (GitHub Pages) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kariuki14.github.io", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images as static files
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

# Register routes
app.include_router(routes.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Kicks Mtaani API is running 🔥"}