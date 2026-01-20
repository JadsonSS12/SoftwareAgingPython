from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Production Robust Server")

# Data model for validation
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

class UserMessage(BaseModel):
    user: str
    message: str

db_messages = []

@app.get("/")
async def read_root():
    return {"status": "online", "message": "Robust Python Server"}

@app.post("/messages/")
async def send_message(msg: UserMessage):
    db_messages.append(msg.dict())
    return {"status": "sent", "user": msg.user}

@app.get("/messages/", response_model=List[UserMessage])
async def get_messages():
    return db_messages

@app.post("/items/")
async def create_item(item: Item):
    # Business logic here
    return {"item_name": item.name, "item_id": 1}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}