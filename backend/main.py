"""
Main entry point for Empire Conquest backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

from api import routes

app = FastAPI(
    title="Empire Conquest",
    description="OGame-inspired medieval browser strategy game API",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.app.router)

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "game": "Empire Conquest"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)