from flask import render_template, request, jsonify, redirect, url_for, session, flash, g
from app import app, db
from models import User, Book, UserBook
from telegram_auth import validate_telegram_data
from api import search_google_books, get_book_details
from recommendation import get_recommendations
from datetime import datetime
import logging

# Before request handler to check user authentication
@app.before_request
def load_user():
    """Load user before each request if user is authenticated"""
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

# Home page
@app.route('/')
def index():
    """Render home page"""
    return render_template('index.html')

# Telegram authentication
@app.route('/auth', methods=['POST'])
def auth():
    """Authenticate user via Telegram"""
    try:
        auth_data = request.json
        if validate_telegram_data(auth_data):
            # Get or create user
            telegram_id = auth_data.get('id')
            user = User.query.filter_by(telegram_id=str(telegram_id)).first()
            
            if not user:
                # Create new user
                user = User(
                    telegram_id=str(telegram_id),
                    first_name=auth_data.get('first_name', ''),
                    last_name=auth_data.get('last_name', ''),
                    username=auth_data.get('username', ''),
                    photo_url=auth_data.get('photo_url', ''),
                    auth_date=datetime.fromtimestamp(int(auth_data.get('auth_date', 0))),
                    last_login=datetime.utcnow()
                )
                db.session.add(user)
            else:
                # Update existing user
                user.last_login = datetime.utcnow()
                if auth_data.get('first_name'):
                    user.first_name = auth_data.get('first_name')
                if auth_data.get('last_name'):
                    user.last_name = auth_data.get('last_name')
                if auth_data.get('username'):
                    user.username = auth_data.get('username')
                if auth_data.get('photo_url'):
                    user.photo_url = auth_data.get('photo_url')
            
            db.session.commit()
            
            # Set user in session
            session['user_id'] = user.id
            return jsonify({'success': True, 'redirect': url_for('library')})
        else:
            return jsonify({'success': False, 'error': 'Invalid authentication data'}), 403
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Logout
@app.route('/logout')
def logout():
    """Log out user"""
    session.pop('user_id', None)
    return redirect(url_for('index'))

# User profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile page"""
    if not g.user:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Get preferences from form
            preferences = {
                'favorite_genres': request.form.getlist('favorite_genres'),
                'reading_pace': request.form.get('reading_pace'),
                'preferred_languages': request.form.getlist('preferred_languages')
            }
            
            # Update user preferences
            g.user.set_preferences(preferences)
            db.session.commit()
            flash('Профиль успешно обновлен', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении профиля: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('profile.html', user=g.user)

# Library
@app.route('/library')
def library():
    """User library page"""
    if not g.user:
        return redirect(url_for('index'))
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    sort_by = request.args.get('sort_by', 'updated_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Build query
    query = UserBook.query.filter_by(user_id=g.user.id).join(Book)
    
    # Apply status filter
    if status != 'all':
        query = query.filter(UserBook.status == status)
    
    # Apply sorting
    if sort_by == 'title':
        if sort_order == 'asc':
            query = query.order_by(Book.title.asc())
        else:
            query = query.order_by(Book.title.desc())
    elif sort_by == 'author':
        if sort_order == 'asc':
            query = query.order_by(Book.author.asc())
        else:
            query = query.order_by(Book.author.desc())
    elif sort_by == 'rating':
        if sort_order == 'asc':
            query = query.order_by(UserBook.rating.asc())
        else:
            query = query.order_by(UserBook.rating.desc())
    else:  # default: updated_at
        if sort_order == 'asc':
            query = query.order_by(UserBook.updated_at.asc())
        else:
            query = query.order_by(UserBook.updated_at.desc())
    
    # Execute query
    user_books = query.all()
    
    return render_template('library.html', 
                          user_books=user_books, 
                          status=status, 
                          sort_by=sort_by, 
                          sort_order=sort_order)

# Book detail
@app.route('/book/<int:user_book_id>')
def book_detail(user_book_id):
    """Book detail page"""
    if not g.user:
        return redirect(url_for('index'))
    
    user_book = UserBook.query.filter_by(id=user_book_id, user_id=g.user.id).first_or_404()
    return render_template('book_detail.html', user_book=user_book)

# Add book
@app.route('/add-book', methods=['GET', 'POST'])
def add_book():
    """Add book page"""
    if not g.user:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Check if adding from Google Books or manual entry
            google_books_id = request.form.get('google_books_id')
            
            if google_books_id:
                # Get book from Google Books API
                book_details = get_book_details(google_books_id)
                
                # Check if book already exists in database
                book = Book.query.filter_by(google_books_id=google_books_id).first()
                
                if not book:
                    # Create new book
                    book = Book(
                        title=book_details.get('title', 'Неизвестная книга'),
                        author=book_details.get('authors', ['Неизвестный автор'])[0] if book_details.get('authors') else 'Неизвестный автор',
                        isbn=book_details.get('industryIdentifiers', [{}])[0].get('identifier', '') if book_details.get('industryIdentifiers') else '',
                        google_books_id=google_books_id,
                        description=book_details.get('description', ''),
                        categories=','.join(book_details.get('categories', [])),
                        cover_url=book_details.get('imageLinks', {}).get('thumbnail', '') if book_details.get('imageLinks') else '',
                        page_count=book_details.get('pageCount'),
                        published_date=book_details.get('publishedDate', ''),
                        publisher=book_details.get('publisher', ''),
                        language=book_details.get('language', '')
                    )
                    db.session.add(book)
                    db.session.flush()  # Get book.id without committing transaction
            else:
                # Manual book entry
                book = Book(
                    title=request.form.get('title', 'Неизвестная книга'),
                    author=request.form.get('author', 'Неизвестный автор'),
                    isbn=request.form.get('isbn', ''),
                    description=request.form.get('description', ''),
                    categories=request.form.get('categories', ''),
                    cover_url=request.form.get('cover_url', ''),
                    page_count=int(request.form.get('page_count', 0)) if request.form.get('page_count') else None,
                    published_date=request.form.get('published_date', ''),
                    publisher=request.form.get('publisher', ''),
                    language=request.form.get('language', '')
                )
                db.session.add(book)
                db.session.flush()  # Get book.id without committing transaction
            
            # Check if user already has this book
            existing_user_book = UserBook.query.filter_by(user_id=g.user.id, book_id=book.id).first()
            
            if existing_user_book:
                flash('Эта книга уже есть в вашей библиотеке', 'warning')
                return redirect(url_for('book_detail', user_book_id=existing_user_book.id))
            
            # Create user book association
            user_book = UserBook(
                user_id=g.user.id,
                book_id=book.id,
                status=request.form.get('status', 'to_read'),
                rating=float(request.form.get('rating')) if request.form.get('rating') else None,
                review=request.form.get('review', ''),
                notes=request.form.get('notes', '')
            )
            
            # Add start/end dates if provided
            if request.form.get('start_date'):
                user_book.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            if request.form.get('end_date'):
                user_book.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            
            db.session.add(user_book)
            db.session.commit()
            
            flash('Книга успешно добавлена в вашу библиотеку', 'success')
            return redirect(url_for('book_detail', user_book_id=user_book.id))
            
        except Exception as e:
            flash(f'Ошибка при добавлении книги: {str(e)}', 'danger')
            db.session.rollback()
            logging.error(f"Error adding book: {str(e)}")
    
    # For GET request or form errors
    return render_template('add_book.html')

# Edit book
@app.route('/book/<int:user_book_id>/edit', methods=['GET', 'POST'])
def edit_book(user_book_id):
    """Edit book page"""
    if not g.user:
        return redirect(url_for('index'))
    
    user_book = UserBook.query.filter_by(id=user_book_id, user_id=g.user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update user book details
            user_book.status = request.form.get('status', user_book.status)
            user_book.rating = float(request.form.get('rating')) if request.form.get('rating') else None
            user_book.review = request.form.get('review', '')
            user_book.notes = request.form.get('notes', '')
            
            # Update dates if provided
            if request.form.get('start_date'):
                user_book.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            else:
                user_book.start_date = None
                
            if request.form.get('end_date'):
                user_book.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            else:
                user_book.end_date = None
            
            # Update book details
            book = user_book.book
            book.title = request.form.get('title', book.title)
            book.author = request.form.get('author', book.author)
            book.isbn = request.form.get('isbn', book.isbn)
            book.description = request.form.get('description', book.description)
            book.categories = request.form.get('categories', book.categories)
            book.page_count = int(request.form.get('page_count', 0)) if request.form.get('page_count') else None
            book.published_date = request.form.get('published_date', book.published_date)
            book.publisher = request.form.get('publisher', book.publisher)
            book.language = request.form.get('language', book.language)
            
            # Only update cover_url if provided
            if request.form.get('cover_url'):
                book.cover_url = request.form.get('cover_url')
            
            db.session.commit()
            flash('Книга успешно обновлена', 'success')
            return redirect(url_for('book_detail', user_book_id=user_book.id))
            
        except Exception as e:
            flash(f'Ошибка при обновлении книги: {str(e)}', 'danger')
            db.session.rollback()
            logging.error(f"Error updating book: {str(e)}")
    
    # For GET request or form errors
    return render_template('add_book.html', user_book=user_book, mode='edit')

# Delete book
@app.route('/book/<int:user_book_id>/delete', methods=['POST'])
def delete_book(user_book_id):
    """Delete book from user library"""
    if not g.user:
        return redirect(url_for('index'))
    
    user_book = UserBook.query.filter_by(id=user_book_id, user_id=g.user.id).first_or_404()
    
    try:
        db.session.delete(user_book)
        db.session.commit()
        flash('Книга удалена из вашей библиотеки', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении книги: {str(e)}', 'danger')
        db.session.rollback()
        logging.error(f"Error deleting book: {str(e)}")
    
    return redirect(url_for('library'))

# Search books
@app.route('/search')
def search():
    """Search books page"""
    if not g.user:
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    source = request.args.get('source', 'google')  # 'google' or 'internal'
    
    results = []
    if query:
        if source == 'google':
            # Search in Google Books API
            results = search_google_books(query)
        else:
            # Search in internal database
            term = f"%{query}%"
            results = Book.query.filter(
                (Book.title.ilike(term)) | 
                (Book.author.ilike(term)) | 
                (Book.categories.ilike(term))
            ).all()
    
    return render_template('search.html', 
                          query=query, 
                          source=source, 
                          results=results)

# Recommendations
@app.route('/recommendations')
def recommendations():
    """Book recommendations page"""
    if not g.user:
        return redirect(url_for('index'))
    
    # Get recommended books
    user_books = UserBook.query.filter_by(user_id=g.user.id).all()
    recommended_books = get_recommendations(g.user, user_books)
    
    return render_template('recommendations.html', 
                          recommendations=recommended_books)

# API endpoints
@app.route('/api/search', methods=['GET'])
def api_search():
    """API endpoint for book search"""
    if not g.user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '')
    source = request.args.get('source', 'google')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        if source == 'google':
            results = search_google_books(query)
            return jsonify({'results': results})
        else:
            term = f"%{query}%"
            books = Book.query.filter(
                (Book.title.ilike(term)) | 
                (Book.author.ilike(term)) | 
                (Book.categories.ilike(term))
            ).all()
            results = [
                {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'cover_url': book.cover_url,
                    'categories': book.get_categories_list(),
                    'published_date': book.published_date
                } for book in books
            ]
            return jsonify({'results': results})
    except Exception as e:
        logging.error(f"Search API error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/book/<book_id>', methods=['GET'])
def api_book_details(book_id):
    """API endpoint to get book details"""
    if not g.user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    source = request.args.get('source', 'internal')
    
    try:
        if source == 'google':
            book_details = get_book_details(book_id)
            return jsonify(book_details)
        else:
            book = Book.query.get_or_404(book_id)
            result = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'google_books_id': book.google_books_id,
                'description': book.description,
                'categories': book.get_categories_list(),
                'cover_url': book.cover_url,
                'page_count': book.page_count,
                'published_date': book.published_date,
                'publisher': book.publisher,
                'language': book.language
            }
            return jsonify(result)
    except Exception as e:
        logging.error(f"Book details API error: {str(e)}")
        return jsonify({'error': str(e)}), 500
