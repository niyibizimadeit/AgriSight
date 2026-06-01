"""AgriSight Backend — FastAPI application.

Run from project root:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import overview, products, analysis, predict

app = FastAPI(
    title="AgriSight API",
    description="Agricultural E-commerce Sales Analysis & Prediction System",
    version="1.0.0",
)

# CORS — allow frontend (any origin during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(overview.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(predict.router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "AgriSight API",
        "version": "1.0.0",
        "docs": "/docs",
    }
