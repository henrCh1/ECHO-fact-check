"""System Configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

class Settings:
    """Global Configuration"""
    
    # API Configuration
    ENV_FILE = Path(__file__).parent.parent / ".env"
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    
    # Search API
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")
    GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
    
    # Project Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    PLAYBOOK_DIR = DATA_DIR / "playbook"
    CASES_DIR = DATA_DIR / "cases"
    FEEDBACK_DIR = DATA_DIR / "feedback"
    
    # Model Configuration
    # TEMPERATURE = 0.1  # Commented out to use model's default temperature
    MAX_TOKENS = 16384
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    
    @classmethod
    def validate(cls):
        """Validate filesystem configuration and ensure required directories exist."""
        # Create necessary directories
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.PLAYBOOK_DIR.mkdir(exist_ok=True)
        (cls.PLAYBOOK_DIR / "history").mkdir(exist_ok=True)
        cls.CASES_DIR.mkdir(exist_ok=True)
        cls.FEEDBACK_DIR.mkdir(exist_ok=True)
        
        return True

    @classmethod
    def has_llm_config(cls) -> bool:
        """Whether the runtime currently has enough config to call Gemini."""
        return bool(cls.GOOGLE_API_KEY and cls.GEMINI_MODEL)

    @classmethod
    def require_llm_config(cls):
        """Raise a clear error when Gemini configuration is missing."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set. Please configure it in Settings before using the system.")

    @classmethod
    def reload(cls):
        """Reload runtime settings from environment/.env."""
        load_dotenv(dotenv_path=cls.ENV_FILE, override=True)
        cls.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        cls.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        cls.SERPAPI_KEY = os.getenv("SERPAPI_KEY")
        cls.GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
        cls.GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
        cls.validate()

    @classmethod
    def update_runtime_config(cls, google_api_key: str | None = None, gemini_model: str | None = None):
        """Persist runtime config to .env and refresh in-memory settings."""
        cls.ENV_FILE.touch(exist_ok=True)

        if google_api_key is not None and google_api_key.strip():
            set_key(str(cls.ENV_FILE), "GOOGLE_API_KEY", google_api_key.strip())

        if gemini_model is not None and gemini_model.strip():
            set_key(str(cls.ENV_FILE), "GEMINI_MODEL", gemini_model.strip())

        cls.reload()

# Auto-validate on import
Settings.validate()
