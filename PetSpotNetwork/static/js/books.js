// Book-related functionality

// Initialize book-related features when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Google Books search
    initGoogleBooksSearch();
    
    // Initialize book form validation
    initBookFormValidation();
    
    // Initialize book card interaction
    initBookCards();
});

// Initialize Google Books API search functionality
function initGoogleBooksSearch() {
    const googleSearchForm = document.getElementById('google-search-form');
    const searchResults = document.getElementById('search-results');
    
    if (googleSearchForm) {
        googleSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = document.getElementById('google-search-input').value.trim();
            if (!query) return;
            
            // Show loading
            showLoading();
            
            // Fetch results from API
            fetch(`/api/search?q=${encodeURIComponent(query)}&source=google`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    
                    if (data.error) {
                        showError(data.error);
                        return;
                    }
                    
                    // Display results
                    displaySearchResults(data.results);
                })
                .catch(error => {
                    hideLoading();
                    showError('Ошибка при поиске книг: ' + error.message);
                    console.error('Search error:', error);
                });
        });
    }
    
    // Handle selection of book from search results
    if (searchResults) {
        searchResults.addEventListener('click', function(e) {
            const bookCard = e.target.closest('.book-card');
            if (!bookCard) return;
            
            const bookId = bookCard.dataset.bookId;
            const source = bookCard.dataset.source || 'google';
            
            if (bookId) {
                showLoading();
                
                // Fetch book details
                fetch(`/api/book/${bookId}?source=${source}`)
                    .then(response => response.json())
                    .then(data => {
                        hideLoading();
                        
                        if (data.error) {
                            showError(data.error);
                            return;
                        }
                        
                        // Fill the form with book details
                        fillBookForm(data, source);
                    })
                    .catch(error => {
                        hideLoading();
                        showError('Ошибка при получении информации о книге: ' + error.message);
                        console.error('Book detail error:', error);
                    });
            }
        });
    }
}

// Display search results
function displaySearchResults(books) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    // Clear previous results
    searchResults.innerHTML = '';
    
    if (!books || books.length === 0) {
        searchResults.innerHTML = '<div class="alert alert-info">Книги не найдены</div>';
        return;
    }
    
    // Create book cards
    const row = document.createElement('div');
    row.className = 'row g-3';
    
    books.forEach(book => {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';
        
        col.innerHTML = `
            <div class="card book-card h-100" data-book-id="${book.id}" data-source="google">
                <div class="row g-0">
                    <div class="col-4">
                        <div class="book-cover-container">
                            ${book.cover_url ? 
                                `<img src="${book.cover_url}" class="img-fluid rounded-start book-cover" alt="${book.title}">` : 
                                `<div class="book-cover-placeholder"><i class="fas fa-book"></i></div>`
                            }
                        </div>
                    </div>
                    <div class="col-8">
                        <div class="card-body">
                            <h5 class="card-title text-truncate">${book.title}</h5>
                            <p class="card-text author text-truncate">${book.author || 'Неизвестный автор'}</p>
                            <p class="card-text categories small">
                                ${book.categories && book.categories.length > 0 ? 
                                    book.categories.slice(0, 2).join(', ') : 
                                    'Категория не указана'
                                }
                            </p>
                            <button class="btn btn-sm btn-primary select-book-btn">Выбрать</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        row.appendChild(col);
    });
    
    searchResults.appendChild(row);
}

// Fill the book form with book details
function fillBookForm(book, source) {
    // Find form elements
    const titleInput = document.getElementById('title');
    const authorInput = document.getElementById('author');
    const isbnInput = document.getElementById('isbn');
    const descriptionInput = document.getElementById('description');
    const categoriesInput = document.getElementById('categories');
    const coverUrlInput = document.getElementById('cover_url');
    const pageCountInput = document.getElementById('page_count');
    const publishedDateInput = document.getElementById('published_date');
    const publisherInput = document.getElementById('publisher');
    const languageInput = document.getElementById('language');
    
    // Hidden field for Google Books ID
    let googleBooksIdInput = document.getElementById('google_books_id');
    if (!googleBooksIdInput && source === 'google') {
        // Create the field if it doesn't exist
        googleBooksIdInput = document.createElement('input');
        googleBooksIdInput.type = 'hidden';
        googleBooksIdInput.id = 'google_books_id';
        googleBooksIdInput.name = 'google_books_id';
        document.querySelector('form').appendChild(googleBooksIdInput);
    }
    
    // Fill the form with book details
    if (titleInput) titleInput.value = book.title || '';
    if (authorInput) authorInput.value = (book.authors && book.authors.length > 0) ? book.authors[0] : (book.author || '');
    
    if (isbnInput) {
        if (book.industryIdentifiers && book.industryIdentifiers.length > 0) {
            const isbn = book.industryIdentifiers.find(id => id.type === 'ISBN_13' || id.type === 'ISBN_10');
            isbnInput.value = isbn ? isbn.identifier : '';
        } else {
            isbnInput.value = book.isbn || '';
        }
    }
    
    if (descriptionInput) descriptionInput.value = book.description || '';
    
    if (categoriesInput) {
        if (book.categories && Array.isArray(book.categories)) {
            categoriesInput.value = book.categories.join(', ');
        } else {
            categoriesInput.value = book.categories || '';
        }
    }
    
    if (coverUrlInput) {
        if (book.imageLinks && book.imageLinks.thumbnail) {
            coverUrlInput.value = book.imageLinks.thumbnail;
        } else {
            coverUrlInput.value = book.cover_url || '';
        }
    }
    
    if (pageCountInput) pageCountInput.value = book.pageCount || book.page_count || '';
    if (publishedDateInput) publishedDateInput.value = book.publishedDate || book.published_date || '';
    if (publisherInput) publisherInput.value = book.publisher || '';
    if (languageInput) languageInput.value = book.language || '';
    
    // Set Google Books ID if from Google
    if (googleBooksIdInput && source === 'google') {
        googleBooksIdInput.value = book.id || '';
    }
    
    // Show book details form and hide search
    const searchSection = document.getElementById('search-section');
    const formSection = document.getElementById('form-section');
    
    if (searchSection && formSection) {
        searchSection.classList.add('d-none');
        formSection.classList.remove('d-none');
    }
}

// Initialize book form validation
function initBookFormValidation() {
    const bookForm = document.querySelector('form.book-form');
    
    if (bookForm) {
        bookForm.addEventListener('submit', function(e) {
            // Check if title is filled
            const titleInput = document.getElementById('title');
            if (!titleInput.value.trim()) {
                e.preventDefault();
                titleInput.classList.add('is-invalid');
                
                // Scroll to the error
                titleInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }
            
            // Remove any error indications
            titleInput.classList.remove('is-invalid');
        });
    }
}

// Initialize book card interactions
function initBookCards() {
    const libraryContainer = document.getElementById('library-container');
    
    if (libraryContainer) {
        // Handle clicks on book cards
        libraryContainer.addEventListener('click', function(e) {
            const bookCard = e.target.closest('.book-card');
            if (!bookCard) return;
            
            // If the clicked element is not a button, navigate to book detail
            if (!e.target.closest('button')) {
                const bookId = bookCard.dataset.bookId;
                if (bookId) {
                    window.location.href = `/book/${bookId}`;
                }
            }
        });
    }
}

// Book status change function
function changeBookStatus(bookId, newStatus) {
    fetch(`/api/book/${bookId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            // Refresh the page to see the updated status
            window.location.reload();
        }
    })
    .catch(error => {
        showError('Ошибка при обновлении статуса: ' + error.message);
        console.error('Status update error:', error);
    });
}
