import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from the modular engines
from data_engine.router import router as data_router
from option_engine.router import router as option_router
from sector_engine.router import router as sector_router
from sentiment_engine.router import router as sentiment_router
from support_engine.router import router as support_router

app = FastAPI(
    title="Bazaar Mood API",
    description="Restored production backend API entrypoint for Bazaar Mood.",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5180"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular engine routers
app.include_router(data_router)
app.include_router(option_router)
app.include_router(sector_router)
app.include_router(sentiment_router)
app.include_router(support_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
