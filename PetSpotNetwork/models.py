from app import db
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

class User(db.Model):
    """User model representing a Telegram user"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(64), unique=True, nullable=False)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128))
    username = Column(String(128))
    photo_url = Column(String(512))
    auth_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    preferences = Column(Text, default="{}")  # JSON string storing reading preferences
    
    # Relationships
    books = relationship("UserBook", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username or self.first_name}>"
    
    def get_preferences(self):
        """Get user preferences as a dictionary"""
        try:
            return json.loads(self.preferences)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_preferences(self, preferences_dict):
        """Set user preferences from a dictionary"""
        self.preferences = json.dumps(preferences_dict)

class Book(db.Model):
    """Book model representing a book in the system"""
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    author = Column(String(256))
    isbn = Column(String(32), unique=True)
    google_books_id = Column(String(64), unique=True)
    description = Column(Text)
    categories = Column(String(512))  # Comma-separated categories/genres
    cover_url = Column(String(512))
    page_count = Column(Integer)
    published_date = Column(String(32))
    publisher = Column(String(256))
    language = Column(String(16))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_books = relationship("UserBook", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book {self.title} by {self.author}>"
    
    def get_categories_list(self):
        """Get categories as a list"""
        if not self.categories:
            return []
        return [category.strip() for category in self.categories.split(",")]

class UserBook(db.Model):
    """Association model between User and Book with user-specific attributes"""
    __tablename__ = "user_books"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    status = Column(String(32), default="to_read")  # to_read, reading, completed, abandoned
    rating = Column(Float)  # User rating, e.g., 1-5
    review = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="books")
    book = relationship("Book", back_populates="user_books")
    
    def __repr__(self):
        return f"<UserBook {self.user_id}:{self.book_id} - {self.status}>"
    
    @property
    def reading_status_display(self):
        """Get formatted reading status"""
        status_map = {
            "to_read": "Хочу прочитать",
            "reading": "Читаю",
            "completed": "Прочитано",
            "abandoned": "Заброшено"
        }
        return status_map.get(self.status, self.status)
