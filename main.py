import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents, db
from schemas import Product, Order

app = FastAPI(title="Ecommerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Ecommerce Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ----------------------
# Ecommerce Endpoints
# ----------------------

@app.get("/api/products")
def list_products(category: Optional[str] = None):
    """Return all products, optionally filtered by category"""
    filt = {"category": category} if category else {}
    items = get_documents("product", filt)
    # Convert ObjectId to string
    for it in items:
        it["id"] = str(it.pop("_id", ""))
    return {"items": items}


@app.post("/api/products")
def create_product(product: Product):
    """Create a new product"""
    product_id = create_document("product", product)
    return {"id": product_id}


class CartItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int
    image: Optional[str] = None


@app.post("/api/orders")
def create_order(order: Order):
    """Create an order from cart items"""
    order_id = create_document("order", order)
    return {"id": order_id, "status": "created"}


@app.post("/api/seed")
def seed_products():
    """Seed some sample products if collection is empty"""
    count = db["product"].count_documents({}) if db else 0
    if count > 0:
        return {"message": "Products already exist", "count": count}

    samples = [
        {
            "title": "Wireless Headphones",
            "description": "Noise-cancelling over-ear headphones with 30h battery.",
            "price": 129.99,
            "category": "Electronics",
            "image": "https://images.unsplash.com/photo-1518441902113-c1d70d3f49d7?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Smart Watch",
            "description": "Fitness tracking, heart-rate monitor, and GPS.",
            "price": 179.0,
            "category": "Electronics",
            "image": "https://images.unsplash.com/photo-1512149673953-1e251807ec7c?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Cotton T-Shirt",
            "description": "Premium 100% cotton tee with a relaxed fit.",
            "price": 24.5,
            "category": "Apparel",
            "image": "https://images.unsplash.com/photo-1520975922284-9c7c4be2f2d2?q=80&w=1200&auto=format&fit=crop"
        },
        {
            "title": "Coffee Maker",
            "description": "12-cup programmable coffee maker with auto shut-off.",
            "price": 59.99,
            "category": "Home",
            "image": "https://images.unsplash.com/photo-1504754524776-8f4f37790ca0?q=80&w=1200&auto=format&fit=crop"
        }
    ]
    created = 0
    for s in samples:
        create_document("product", s)
        created += 1
    return {"message": "Seeded products", "created": created}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
