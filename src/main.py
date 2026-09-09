from fastapi import FastAPI
from src.routes.triage import router as triage_router

app = FastAPI()
app.include_router(triage_router)
