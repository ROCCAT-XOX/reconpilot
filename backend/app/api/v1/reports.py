from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def list_reports():
    raise HTTPException(
        status_code=501,
        detail="Reporting module not yet implemented",
    )


@router.post("/")
async def create_report():
    raise HTTPException(
        status_code=501,
        detail="Reporting module not yet implemented",
    )
