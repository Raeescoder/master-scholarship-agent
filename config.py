import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

class Config:
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # In-memory dynamic API key cache (can be updated via UI)
    _dynamic_gemini_key: str | None = None
    
    @classmethod
    def get_gemini_api_key(cls) -> str | None:
        if cls._dynamic_gemini_key:
            return cls._dynamic_gemini_key
        return os.getenv("GEMINI_API_KEY")

    @classmethod
    def set_gemini_api_key(cls, key: str) -> None:
        cls._dynamic_gemini_key = key.strip()
        # Also persist to .env if possible
        try:
            env_file = BASE_DIR / ".env"
            lines = []
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={key.strip()}\n")
                    updated = True
                else:
                    new_lines.append(line)
            if not updated:
                new_lines.append(f"\nGEMINI_API_KEY={key.strip()}\n")
                
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            pass

    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

config = Config()
