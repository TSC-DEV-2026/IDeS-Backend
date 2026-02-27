import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="Identidade e Santidade API",
    version="0.1.0",
)

# CORS (frontend)
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.routes.user import router as user_router
from app.routes.event import router as event_router

app.include_router(user_router, prefix="/user", tags=["Usuário"])
app.include_router(event_router, prefix="/event", tags=["Eventos"])

@app.get("/")
def root():
    return {"status": "ok", "app": "Identidade e Santidade API"}