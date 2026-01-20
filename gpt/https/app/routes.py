from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}


@router.get("/", tags=["root"])
async def root():
    return {"message": "FastAPI production server is running"}
