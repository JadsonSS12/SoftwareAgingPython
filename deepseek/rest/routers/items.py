# routers/items.py
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from datetime import datetime
import uuid

from schemas import ItemCreate, ItemUpdate, ItemResponse, PaginatedResponse
from dependencies import get_current_user, common_deps
from exceptions import NotFoundException
from logging_config import logger

router = APIRouter(prefix="/items", tags=["items"])


# In-memory storage for demonstration
# In production, use a database like PostgreSQL, MySQL, or MongoDB
items_db = {}


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=common_deps,
    summary="Create a new item",
    response_description="The created item"
)
async def create_item(
    item: ItemCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new item in the system."""
    try:
        item_id = str(uuid.uuid4())
        now = datetime.now()
        
        db_item = {
            "id": item_id,
            **item.dict(),
            "created_at": now,
            "updated_at": now
        }
        
        items_db[item_id] = db_item
        
        logger.info("Item created", item_id=item_id, user_id=current_user["id"])
        
        return ItemResponse(**db_item)
    except Exception as e:
        logger.error("Failed to create item", error=str(e))
        raise


@router.get(
    "",
    response_model=PaginatedResponse,
    dependencies=common_deps,
    summary="List all items",
    response_description="Paginated list of items"
)
async def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name and description")
):
    """Retrieve a paginated list of items with optional filtering."""
    try:
        # Filter items
        filtered_items = list(items_db.values())
        
        if status:
            filtered_items = [item for item in filtered_items if item["status"] == status]
        
        if search:
            search_lower = search.lower()
            filtered_items = [
                item for item in filtered_items
                if search_lower in item["name"].lower() or 
                (item["description"] and search_lower in item["description"].lower())
            ]
        
        # Paginate
        total = len(filtered_items)
        pages = (total + size - 1) // size
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        
        paginated_items = filtered_items[start_idx:end_idx]
        
        logger.info("Items listed", page=page, size=size, total=total)
        
        return PaginatedResponse(
            items=[ItemResponse(**item) for item in paginated_items],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        logger.error("Failed to list items", error=str(e))
        raise


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    dependencies=common_deps,
    summary="Get item by ID",
    response_description="The requested item"
)
async def get_item(
    item_id: str = Path(..., description="The ID of the item to retrieve")
):
    """Retrieve a specific item by its ID."""
    try:
        if item_id not in items_db:
            raise NotFoundException(f"Item with ID {item_id} not found")
        
        return ItemResponse(**items_db[item_id])
    except NotFoundException:
        raise
    except Exception as e:
        logger.error("Failed to get item", item_id=item_id, error=str(e))
        raise


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    dependencies=common_deps,
    summary="Update an item",
    response_description="The updated item"
)
async def update_item(
    item_update: ItemUpdate,
    item_id: str = Path(..., description="The ID of the item to update"),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing item."""
    try:
        if item_id not in items_db:
            raise NotFoundException(f"Item with ID {item_id} not found")
        
        current_item = items_db[item_id]
        
        # Update only provided fields
        update_data = item_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            current_item[field] = value
        
        current_item["updated_at"] = datetime.now()
        
        logger.info("Item updated", item_id=item_id, user_id=current_user["id"])
        
        return ItemResponse(**current_item)
    except NotFoundException:
        raise
    except Exception as e:
        logger.error("Failed to update item", item_id=item_id, error=str(e))
        raise


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=common_deps,
    summary="Delete an item"
)
async def delete_item(
    item_id: str = Path(..., description="The ID of the item to delete"),
    current_user: dict = Depends(get_current_user)
):
    """Delete an item from the system."""
    try:
        if item_id not in items_db:
            raise NotFoundException(f"Item with ID {item_id} not found")
        
        del items_db[item_id]
        
        logger.info("Item deleted", item_id=item_id, user_id=current_user["id"])
    except NotFoundException:
        raise
    except Exception as e:
        logger.error("Failed to delete item", item_id=item_id, error=str(e))
        raise