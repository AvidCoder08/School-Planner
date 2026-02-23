from dataclasses import dataclass
import os
from dotenv import load_dotenv


load_dotenv()


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    appwrite_endpoint: str = os.getenv("APPWRITE_ENDPOINT", "")
    appwrite_project_id: str = os.getenv("APPWRITE_PROJECT_ID", "")
    appwrite_api_key: str = os.getenv("APPWRITE_API_KEY") or os.getenv("APPWRITE_FUNCTION_API_KEY", "")
    appwrite_database_id: str = os.getenv("APPWRITE_DATABASE_ID", "")

    appwrite_users_collection_id: str = os.getenv("APPWRITE_USERS_COLLECTION_ID", "users")
    appwrite_years_collection_id: str = os.getenv("APPWRITE_YEARS_COLLECTION_ID", "academic_years")
    appwrite_terms_collection_id: str = os.getenv("APPWRITE_TERMS_COLLECTION_ID", "terms")
    appwrite_subjects_collection_id: str = os.getenv("APPWRITE_SUBJECTS_COLLECTION_ID", "subjects")
    appwrite_tasks_collection_id: str = os.getenv("APPWRITE_TASKS_COLLECTION_ID", "tasks")
    appwrite_events_collection_id: str = os.getenv("APPWRITE_EVENTS_COLLECTION_ID", "events")
    appwrite_grades_collection_id: str = os.getenv("APPWRITE_GRADES_COLLECTION_ID", "grades")
    appwrite_assessments_collection_id: str = os.getenv("APPWRITE_ASSESSMENTS_COLLECTION_ID", "assessments")

    cors_allowed_origins: tuple[str, ...] = _split_csv(
        os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )
    cors_allow_origin_regex: str = os.getenv(
        "CORS_ALLOW_ORIGIN_REGEX",
        r"^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$",
    )


settings = Settings()
