"""
ECHO Fact-Checking API

FastAPI application entry point for the ECHO fact-checking system.
Provides REST API endpoints for:
- Single and batch claim verification
- Verification history management
- Playbook/rule base management
- Warmup (custom playbook generation)
- System statistics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.routers import (
    verify_router,
    playbook_router,
    history_router,
    warmup_router,
    stats_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 ECHO Fact-Checking API starting up...")
    print(f"📁 Project root: {project_root}")
    
    # Validate configuration
    from config.settings import Settings
    Settings.validate()
    print("✅ Configuration validated")
    
    yield
    
    # Shutdown
    print("👋 ECHO Fact-Checking API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="ECHO Fact-Checking API",
    description="""
    ## ECHO - Evolving Cognitive Hierarchy for Observation
    
    An AI-powered fact-checking system with self-evolving rule base.
    
    ### Features:
    - **Single Verification**: Verify individual claims with detailed evidence and reasoning
    - **Batch Verification**: Upload CSV files for bulk verification
    - **Dual Verification Modes**: 
        - Static: Use existing rules only (faster)
        - Evolving: Trigger rule evolution after each verification (learning mode)
    - **Playbook Management**: View and manage verification rules
    - **Warmup**: Generate custom playbooks from labeled datasets
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(verify_router)
app.include_router(playbook_router)
app.include_router(history_router)
app.include_router(warmup_router)
app.include_router(stats_router)


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": "ECHO Fact-Checking API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "verify": "/api/verify",
            "batch": "/api/verify/batch",
            "playbook": "/api/playbook",
            "history": "/api/history",
            "warmup": "/api/warmup",
            "stats": "/api/stats"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
