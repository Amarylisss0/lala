import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask and SQLAlchemy
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///bookjournal.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database with app
db.init_app(app)

# Create database tables
with app.app_context():
    # Import models here to avoid circular imports
    import models  # noqa: F401
    db.create_all()

# Configure Google Books API key
app.config["GOOGLE_BOOKS_API_KEY"] = os.environ.get("GOOGLE_BOOKS_API_KEY", "")

# Configure cache settings for API requests
app.config["CACHE_TIMEOUT"] = 3600  # 1 hour cache timeout
