from fastapi import APIRouter
router = APIRouter()

@router.get("/api/health")
def health_status():
    return{"status" : "OK"}