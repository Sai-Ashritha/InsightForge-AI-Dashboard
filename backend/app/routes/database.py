from fastapi import APIRouter

from app.database.db import create_tables, fetch_table

router = APIRouter()


@router.get("/db-status")
def db_status():
    try:
        result = create_tables()
        return {"status": "connected", "details": result}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/tables")
def list_tables():
    try:
        return {
            "sales": fetch_table("sales"),
            "production": fetch_table("production"),
            "inventory": fetch_table("inventory"),
            "employees": fetch_table("employees"),
            "finance": fetch_table("finance")
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
