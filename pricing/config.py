import yaml
from pathlib import Path

try:
    from pydantic_settings import BaseSettings
except ImportError:  # Backward compatibility if pydantic<2.0
    from pydantic import BaseSettings

class Settings(BaseSettings):
    google_api_key: str = ""
    class Config:
        env_file = ".env"

SETTINGS = Settings()

def load_prices():
    path = Path(__file__).parent.parent / "config" / "prices.yaml"
    return yaml.safe_load(path.read_text())

PRICES = load_prices()
