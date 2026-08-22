from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import create_tables
from app.database.orm import initialize_orm
from app.routes.analytics import router as analytics_router
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.chatbot import router as chatbot_router
from app.routes.dashboard import router as dashboard_router
from app.routes.database import router as database_router
from app.routes.forecast import router as forecast_router
from app.routes.ml import router as ml_router
from app.routes.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_tables()
        initialize_orm()
    except Exception:
        # Keep development running if DB needs initialization
        pass
    yield


app = FastAPI(title="InsightForge AI Predictive Manufacturing API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(database_router, prefix="/api")
app.include_router(ml_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/")
def home():
    return {"message": "InsightForge AI is running"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "project": "AI_Predictive_Manufacturing_Dashboard",
        "version": "1.0.0"
    }

