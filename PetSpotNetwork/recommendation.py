from models import Book, UserBook
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

def get_book_features(book):
    """
    Extract features from a book to use for similarity calculation
    
    Args:
        book: Book object
    
    Returns:
        str: Space-separated string of book features
    """
    features = []
    # Add title words
    if book.title:
        features.append(book.title.lower())
    
    # Add author
    if book.author:
        features.append(book.author.lower())
    
    # Add categories/genres
    if book.categories:
        categories = [cat.strip().lower() for cat in book.categories.split(',')]
        features.extend(categories)
    
    # Add description words (limited to prevent overwhelming other features)
    if book.description:
        # Take first 100 words of description
        desc_words = book.description.lower().split()[:100]
        features.extend(desc_words)
    
    return ' '.join(features)

def get_recommendations(user, user_books, max_recommendations=10):
    """
    Get book recommendations for user based on their library
    
    Args:
        user: User object
        user_books: List of UserBook objects
        max_recommendations: Maximum number of recommendations to return
    
    Returns:
        list: List of recommended Book objects
    """
    try:
        # Get user's read books
        read_books = [ub.book for ub in user_books if ub.status == 'completed']
        
        # If user has no completed books, use all books in their library
        if not read_books:
            read_books = [ub.book for ub in user_books]
            
        # If user still has no books, cannot make recommendations
        if not read_books:
            logging.warning(f"No books found for user {user.id} to make recommendations")
            return []
        
        # Get all books from database that aren't in user's library
        user_book_ids = [ub.book_id for ub in user_books]
        candidate_books = Book.query.filter(Book.id.notin_(user_book_ids)).all()
        
        if not candidate_books:
            logging.warning("No candidate books found for recommendations")
            return []
        
        # Extract text features from books
        all_books = read_books + candidate_books
        book_features = [get_book_features(book) for book in all_books]
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(book_features)
        
        # Calculate similarity between user's books and candidate books
        num_user_books = len(read_books)
        user_book_vectors = tfidf_matrix[:num_user_books]
        candidate_book_vectors = tfidf_matrix[num_user_books:]
        
        # Compute similarity
        similarity_scores = cosine_similarity(candidate_book_vectors, user_book_vectors)
        
        # For each candidate book, get its average similarity to user's books
        avg_similarity = np.mean(similarity_scores, axis=1)
        
        # Get top recommendations
        top_indices = np.argsort(avg_similarity)[::-1][:max_recommendations]
        
        # Return recommended books
        recommendations = [candidate_books[i] for i in top_indices]
        return recommendations
        
    except Exception as e:
        logging.error(f"Error generating recommendations: {str(e)}")
        return []
