import requests
import json
import logging
import os
from functools import lru_cache
from app import app

# Google Books API base URL
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

@lru_cache(maxsize=128)
def search_google_books(query, max_results=10):
    """
    Search for books using Google Books API
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        list: List of book dictionaries with basic info
    """
    api_key = app.config.get("GOOGLE_BOOKS_API_KEY", "")
    params = {
        "q": query,
        "maxResults": max_results,
        "printType": "books"
    }
    
    if api_key:
        params["key"] = api_key
    
    try:
        response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        if "items" in data:
            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                books.append({
                    "id": item.get("id"),
                    "title": volume_info.get("title", "Unknown Title"),
                    "author": volume_info.get("authors", ["Unknown Author"])[0] if volume_info.get("authors") else "Unknown Author",
                    "categories": volume_info.get("categories", []),
                    "cover_url": volume_info.get("imageLinks", {}).get("thumbnail", "") if volume_info.get("imageLinks") else "",
                    "published_date": volume_info.get("publishedDate", ""),
                    "description": volume_info.get("description", "")[:150] + "..." if volume_info.get("description", "") else ""
                })
        
        return books
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Google Books API search error: {str(e)}")
        return []

@lru_cache(maxsize=128)
def get_book_details(book_id):
    """
    Get detailed information about a book from Google Books API
    
    Args:
        book_id: Google Books volume ID
        
    Returns:
        dict: Book details or empty dict on error
    """
    api_key = app.config.get("GOOGLE_BOOKS_API_KEY", "")
    url = f"{GOOGLE_BOOKS_API_URL}/{book_id}"
    
    params = {}
    if api_key:
        params["key"] = api_key
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        volume_info = data.get("volumeInfo", {})
        
        book_details = {
            "id": data.get("id"),
            "title": volume_info.get("title", "Unknown Title"),
            "authors": volume_info.get("authors", ["Unknown Author"]),
            "publisher": volume_info.get("publisher", ""),
            "publishedDate": volume_info.get("publishedDate", ""),
            "description": volume_info.get("description", ""),
            "industryIdentifiers": volume_info.get("industryIdentifiers", []),
            "pageCount": volume_info.get("pageCount"),
            "categories": volume_info.get("categories", []),
            "language": volume_info.get("language", ""),
            "imageLinks": volume_info.get("imageLinks", {})
        }
        
        return book_details
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Google Books API details error: {str(e)}")
        return {}
