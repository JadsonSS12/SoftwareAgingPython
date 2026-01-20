from fastapi import APIRouter, HTTPException
from .models import Item

router = APIRouter()

# Mock Database
db = {
    1: {"id": 1, "name": "Laptop", "price": 999.99}
}

@router.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]

@router.post("/items/", status_code=201)
async def create_item(item: Item):
    if item.id in db:
        raise HTTPException(status_code=400, detail="Item already exists")
    db[item.id] = item.dict()
    return {"message": "Item created successfully"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}