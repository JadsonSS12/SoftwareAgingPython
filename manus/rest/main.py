from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Robust REST JSON Server")

# Data Model
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

# In-memory database for demonstration
db = [
    Item(id=1, name="Laptop", description="High-performance laptop", price=1200.0, tax=120.0),
    Item(id=2, name="Mouse", description="Wireless mouse", price=25.0, tax=2.5),
]

@app.get("/")
async def root():
    return {"message": "Welcome to the Robust REST JSON Server"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    item = next((i for i in db if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    if any(i.id == item.id for i in db):
        raise HTTPException(status_code=400, detail="Item with this ID already exists")
    db.append(item)
    return item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, updated_item: Item):
    index = next((i for i, item in enumerate(db) if item.id == item_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db[index] = updated_item
    return updated_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    index = next((i for i, item in enumerate(db) if item.id == item_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.pop(index)
    return {"message": "Item deleted successfully"}
