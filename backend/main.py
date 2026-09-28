import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.database.db import init_db, get_db_connection, create_item, get_item_by_id
from backend.api import auth, items, matching, claims, community, profile, notifications, admin

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for all local and deployed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(items.router, prefix=settings.API_PREFIX)
app.include_router(matching.router, prefix=settings.API_PREFIX)
app.include_router(claims.router, prefix=settings.API_PREFIX)
app.include_router(community.router, prefix=settings.API_PREFIX)
app.include_router(profile.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)

# Create and mount static directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.on_event("startup")
def startup_event():
    print("[Back2You] Initializing database and services...")
    init_db()
    
    # Auto-seed initial test items into database if empty
    try:
        from ml.evaluation import load_dataset
        from backend.api.items import process_item_ai_embeddings
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM users WHERE email = 'alex@campus.edu'")
        alex_row = cursor.fetchone()
        cursor.execute("SELECT id FROM users WHERE email = 'sarah@campus.edu'")
        sarah_row = cursor.fetchone()
        conn.close()

        if count == 0 and alex_row and sarah_row:
            data = load_dataset()
            alex_id = alex_row[0]
            sarah_id = sarah_row[0]
            for item in data.get("items", []):
                uid = alex_id if item["type"] == "lost" else sarah_id
                item_data = {
                    "id": item["id"],
                    "user_id": uid,
                    "type": item["type"],
                    "title": item["title"],
                    "category": item["category"],
                    "description": item["description"],
                    "brand": item.get("brand", ""),
                    "color": item.get("color", ""),
                    "distinguishing_features": item.get("distinguishing_features", ""),
                    "image_url": None,
                    "location": item["location"],
                    "event_date": item["event_date"],
                    "event_time": item["event_time"],
                    "status": "ACTIVE"
                }
                new_item = create_item(item_data)
                process_item_ai_embeddings(new_item)
            print("[Back2You] Seeded initial campus lost & found benchmark reports.")
    except Exception as e:
        print(f"[Back2You] Startup seed note: {e}")

    print("[Back2You] Platform started successfully. Ready to serve requests.")

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[Unhandled Error] {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal service error occurred. Please try again."}
    )

# Frontend SPA Fallback / HTML serving
@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Back2You API is running. Access /docs for API documentation."}

@app.get("/{page}.html")
def serve_html_page(page: str):
    page_file = FRONTEND_DIR / f"{page}.html"
    if page_file.exists():
        return FileResponse(str(page_file))
    return JSONResponse(status_code=404, content={"detail": "Page not found."})

@app.get("/css/{file_name}")
def serve_css(file_name: str):
    css_file = FRONTEND_DIR / "css" / file_name
    if css_file.exists():
        return FileResponse(str(css_file), media_type="text/css")
    return JSONResponse(status_code=404, content={"detail": "CSS not found."})

@app.get("/js/{file_name}")
def serve_js(file_name: str):
    js_file = FRONTEND_DIR / "js" / file_name
    if js_file.exists():
        return FileResponse(str(js_file), media_type="application/javascript")
    return JSONResponse(status_code=404, content={"detail": "JS not found."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
