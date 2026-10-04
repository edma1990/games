"""Create database tables for a fresh installation."""

from app.database import Base, engine

# Import models before create_all so SQLAlchemy knows every table.
from app import models  # noqa: F401


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")
