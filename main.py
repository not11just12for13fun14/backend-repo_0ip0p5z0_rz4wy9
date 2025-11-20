import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents
from schemas import Product

app = FastAPI(title="Extravagant Pet Shop API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Extravagant Pet Shop Backend is live!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# API models
class ProductCreate(BaseModel):
    title: str
    price: float
    category: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    animal: Optional[str] = None
    colors: Optional[List[str]] = []
    rating: Optional[float] = 4.5
    tags: Optional[List[str]] = []
    in_stock: bool = True

@app.get("/api/products")
def list_products(animal: Optional[str] = None, q: Optional[str] = None):
    """List products, optionally filter by animal type or search query."""
    filter_dict = {}
    if animal:
        filter_dict["animal"] = animal
    if q:
        # Simple contains search on title/description
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    try:
        items = get_documents("product", filter_dict, limit=100)
        # Convert ObjectId to str for frontend safety
        for it in items:
            it["_id"] = str(it.get("_id"))
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products", status_code=201)
def create_product(payload: ProductCreate):
    try:
        # Validate with Product schema to ensure consistency
        prod = Product(**payload.model_dump())
        new_id = create_document("product", prod)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/seed")
def seed_products():
    """Seed a handful of extravagant, colorful pet products if collection is empty."""
    try:
        existing = get_documents("product", {}, limit=1)
        if existing:
            return {"status": "skipped", "message": "Products already exist"}

        demo_products = [
            {
                "title": "Neon Glow Collar",
                "price": 29.99,
                "category": "Accessories",
                "description": "Rechargeable LED collar with rave-mode for night walks.",
                "image_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?q=80&w=1200&auto=format&fit=crop",
                "animal": "dogs",
                "colors": ["neon-pink", "electric-blue", "lime"],
                "rating": 4.7,
                "tags": ["neon", "glow", "night"],
                "in_stock": True,
            },
            {
                "title": "Catnip Disco Ball",
                "price": 18.5,
                "category": "Toys",
                "description": "Sparkly orb that scatters rainbow reflections across the room.",
                "image_url": "https://images.unsplash.com/photo-1543852786-1cf6624b9987?q=80&w=1200&auto=format&fit=crop",
                "animal": "cats",
                "colors": ["holographic", "silver"],
                "rating": 4.6,
                "tags": ["disco", "sparkle"],
                "in_stock": True,
            },
            {
                "title": "Tropical Reef Palace",
                "price": 89.0,
                "category": "Aquarium",
                "description": "A vibrant coral-themed habitat with neon accents.",
                "image_url": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=1200&auto=format&fit=crop",
                "animal": "fish",
                "colors": ["coral", "aqua", "purple"],
                "rating": 4.8,
                "tags": ["reef", "aquatic", "premium"],
                "in_stock": True,
            },
            {
                "title": "Feather Carnival Wand",
                "price": 12.99,
                "category": "Toys",
                "description": "Rainbow plume teaser for cats with bells and glitter ribbon.",
                "image_url": "https://images.unsplash.com/photo-1592194996308-7b43878e84a6?q=80&w=1200&auto=format&fit=crop",
                "animal": "cats",
                "colors": ["rainbow", "gold"],
                "rating": 4.4,
                "tags": ["play", "rainbow"],
                "in_stock": True,
            },
            {
                "title": "Birdie Neon Gym",
                "price": 54.0,
                "category": "Cages",
                "description": "Modular perch system with colorful beads and swings.",
                "image_url": "https://images.unsplash.com/photo-1535850836387-0f9dfce30846?q=80&w=1200&auto=format&fit=crop",
                "animal": "birds",
                "colors": ["neon-orange", "teal"],
                "rating": 4.5,
                "tags": ["gym", "beads"],
                "in_stock": True,
            },
        ]

        inserted = 0
        for d in demo_products:
            prod = Product(**d)
            create_document("product", prod)
            inserted += 1

        return {"status": "ok", "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
