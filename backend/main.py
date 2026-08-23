import os

from fastapi import FastAPI, Query, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.engine import MultimodalSearchEngine

app = FastAPI(title="Zero-Shot Search Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INDEX_PATH = os.path.join(DATA_DIR, "faiss_index.bin")
MAPPING_PATH = os.path.join(DATA_DIR, "image_paths.json")
IMAGE_DIR = os.path.join(DATA_DIR, "images")

app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

engine = None

@app.on_event("startup")
def startup_event():
    global engine
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f"Index not found at {INDEX_PATH}")
    engine = MultimodalSearchEngine(INDEX_PATH, MAPPING_PATH, IMAGE_DIR)

@app.get("/api/search")
def search_images(request: Request, q: str = Query(..., min_length=1), top_k: int = Query(6, ge=1, le=20)):
    if not engine:
        raise HTTPException(status_code=500, detail="Search engine not initialized")
    
    results = engine.search(query=q, top_k=top_k)
    
    base_url = str(request.base_url).rstrip('/')
    for res in results:
        res["url"] = f"{base_url}/images/{res['filename']}"
        
    return {"query": q, "count": len(results), "results": results}

@app.post("/api/search-by-image")
async def search_by_image(request: Request, file: UploadFile = File(...), top_k: int = Query(6, ge=1, le=20)):
    if not engine:
        raise HTTPException(status_code=500, detail="Search engine not initialized")

    contents = await file.read()
    results = engine.search_by_image(image_bytes=contents, top_k=top_k)
    
    base_url = str(request.base_url).rstrip('/')
    for res in results:
        res["url"] = f"{base_url}/images/{res['filename']}"
        
    return {"mode": "image-search", "count": len(results), "results": results}