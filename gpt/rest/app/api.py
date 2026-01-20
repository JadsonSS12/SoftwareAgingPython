from fastapi import APIRouter, HTTPException
from typing import List
from .models import Item

router = APIRouter()

# In-memory storage (replace with DB in production)
ITEMS_DB = {}

@router.get("/items", response_model=List[Item])
def list_items():
    return list(ITEMS_DB.values())

@router.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = ITEMS_DB.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/items", response_model=Item, status_code=201)
def create_item(item: Item):
    if item.id in ITEMS_DB:
        raise HTTPException(status_code=409, detail="Item already exists")
    ITEMS_DB[item.id] = item
    return item

@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if item_id not in ITEMS_DB:
        raise HTTPException(status_code=404, detail="Item not found")
    del ITEMS_DB[item_id]
