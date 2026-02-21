from dataclasses import dataclass
import os
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    firebase_api_key: str = os.getenv("FIREBASE_API_KEY", "")
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")


settings = Settings()
