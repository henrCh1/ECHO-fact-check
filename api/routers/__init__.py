"""API Routers"""
from .verify import router as verify_router
from .evolution import router as evolution_router
from .settings import router as settings_router
from .playbook import router as playbook_router
from .history import router as history_router
from .warmup import router as warmup_router
from .stats import router as stats_router

__all__ = [
    "verify_router",
    "evolution_router",
    "settings_router",
    "playbook_router", 
    "history_router",
    "warmup_router",
    "stats_router"
]
