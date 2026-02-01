"""System Configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Global Configuration"""
    
    # API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
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
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set. Please configure it in the .env file")
        
        # Create necessary directories
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.PLAYBOOK_DIR.mkdir(exist_ok=True)
        (cls.PLAYBOOK_DIR / "history").mkdir(exist_ok=True)
        cls.CASES_DIR.mkdir(exist_ok=True)
        cls.FEEDBACK_DIR.mkdir(exist_ok=True)
        
        return True

# Auto-validate on import
Settings.validate()
