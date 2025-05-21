// Main app.js file for Telegram Book Journal

// Initialize the application when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Telegram Web App
    initTelegramApp();
    
    // Initialize tooltips and popovers
    initBootstrapComponents();
    
    // Add event listeners
    addEventListeners();
});

// Initialize Bootstrap components
function initBootstrapComponents() {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Add general event listeners
function addEventListeners() {
    // Handle flash message dismissal
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(message);
            bsAlert.close();
        }, 5000); // Auto-close after 5 seconds
    });
    
    // Handle main navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
        });
    });
    
    // Handle back button functionality
    const backButtons = document.querySelectorAll('.btn-back');
    backButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.history.back();
        });
    });
    
    // Initialize status filter in library
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('status', this.value);
            window.location.href = currentUrl.toString();
        });
    }
    
    // Initialize sort options in library
    const sortBySelect = document.getElementById('sort-by');
    const sortOrderSelect = document.getElementById('sort-order');
    
    if (sortBySelect && sortOrderSelect) {
        [sortBySelect, sortOrderSelect].forEach(select => {
            select.addEventListener('change', function() {
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('sort_by', sortBySelect.value);
                currentUrl.searchParams.set('sort_order', sortOrderSelect.value);
                window.location.href = currentUrl.toString();
            });
        });
    }
    
    // Initialize search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('search-input');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.classList.add('is-invalid');
            } else {
                searchInput.classList.remove('is-invalid');
            }
        });
    }
    
    // Initialize source toggle in search
    const sourceToggle = document.querySelectorAll('input[name="search-source"]');
    if (sourceToggle.length) {
        sourceToggle.forEach(radio => {
            radio.addEventListener('change', function() {
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('source', this.value);
                if (currentUrl.searchParams.has('q')) {
                    window.location.href = currentUrl.toString();
                }
            });
        });
    }
    
    // Handle book deletion confirmation
    const deleteButtons = document.querySelectorAll('.delete-book-btn');
    if (deleteButtons.length) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Вы уверены, что хотите удалить эту книгу из вашей библиотеки?')) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // Handle rating stars in forms
    const ratingInputs = document.querySelectorAll('.rating-input');
    if (ratingInputs.length) {
        ratingInputs.forEach(input => {
            const stars = input.querySelectorAll('.rating-star');
            const hiddenInput = input.querySelector('input[type="hidden"]');
            
            stars.forEach((star, index) => {
                // Set initial state
                if (hiddenInput.value && index < parseInt(hiddenInput.value)) {
                    star.classList.add('active');
                }
                
                // Add click handler
                star.addEventListener('click', function() {
                    const rating = index + 1;
                    hiddenInput.value = rating;
                    
                    // Update UI
                    stars.forEach((s, i) => {
                        if (i < rating) {
                            s.classList.add('active');
                        } else {
                            s.classList.remove('active');
                        }
                    });
                });
            });
        });
    }
}

// Function to show loading overlay
function showLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
    }
}

// Function to hide loading overlay
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('d-none');
    }
}

// Function to display error message
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.classList.remove('d-none');
        
        // Hide after 5 seconds
        setTimeout(() => {
            errorContainer.classList.add('d-none');
        }, 5000);
    }
}
