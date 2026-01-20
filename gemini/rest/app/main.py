from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as item_router

app = FastAPI(title="Production JSON Server", version="1.0.0")

# Security: Set allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes from our routes.py file
app.include_router(item_router)

