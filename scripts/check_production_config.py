"""Fail fast when important production settings are missing or unsafe."""

from cryptography.fernet import Fernet

from app.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    problems = []
    if settings.app_env.lower() != "production":
        problems.append("APP_ENV must be production")
    if not settings.database_url.startswith("mysql+pymysql://"):
        problems.append("DATABASE_URL must use mysql+pymysql")
    if settings.admin_password == "change-this-before-production" or len(settings.admin_password) < 12:
        problems.append("ADMIN_PASSWORD must be a strong password of at least 12 characters")
    if len(settings.app_secret) < 32:
        problems.append("APP_SECRET must contain at least 32 characters")
    try:
        Fernet(settings.encryption_key.encode())
    except Exception:
        problems.append("ENCRYPTION_KEY must be a valid Fernet key")

    if problems:
        print("Configuration errors:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("Production configuration looks valid.")
