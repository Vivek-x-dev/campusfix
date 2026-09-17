"""Users stub."""
from fastapi import APIRouter
router = APIRouter()


@router.get("/users/me")
async def me():
    return {"role": "admin", "name": "CampusFix Demo"}
