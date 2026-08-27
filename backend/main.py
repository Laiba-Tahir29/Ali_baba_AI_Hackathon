import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.upload import router as upload_router
from .routers.analyze import router as analyze_router

# Load .env file if present in workspace root or backend dir
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip('"').strip("'")
                    if key.strip() not in os.environ and val:
                        os.environ[key.strip()] = val
    except Exception as e:
        print(f"Notice loading .env: {e}")


app = FastAPI(
    title="Cardiovascular Risk Summarizer API",
    description="FastAPI Backend for Cardiovascular Report Summarization and Risk-Flagging Assistant",
    version="1.0.0"
)

# CORS configuration for Frontend Dev server (Vite on :3000 / :5173)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(upload_router)
app.include_router(analyze_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "service": "Cardiovascular Risk Summarizer API",
        "version": "1.0.0",
        "endpoints": ["/upload", "/analyze", "/docs"]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import socket
    import sys
    import uvicorn

    port = 8000
    host = "127.0.0.1"

    # Check if port 8000 is already bound to prevent silent collision
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((host, port)) == 0:
            print(f"\n[ERROR] Port {port} is already in use by another running server instance.")
            print(f"[ACTION] Please stop the existing process on port {port} or specify another port.\n")
            sys.exit(1)

    print(f"[STARTUP] Starting FastAPI server on http://{host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
