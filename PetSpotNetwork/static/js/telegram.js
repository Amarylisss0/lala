// Telegram Web App API integration

// Global variable to store Telegram WebApp instance
let telegramWebApp = null;

// Initialize Telegram Web App
function initTelegramApp() {
    try {
        // Check if Telegram WebApp is available
        if (window.Telegram && window.Telegram.WebApp) {
            telegramWebApp = window.Telegram.WebApp;
            
            // Initialize Web App
            telegramWebApp.ready();
            
            // Expand Web App if needed
            telegramWebApp.expand();
            
            // Set theme based on Telegram colors
            setTelegramTheme();
            
            // Check if user is already authenticated
            checkAuthentication();
            
            // Add header button if needed
            if (isUserAuthenticated()) {
                addMainButton();
            }
            
            // Log initialization
            console.log('Telegram WebApp initialized');
        } else {
            console.log('Telegram WebApp not available, running in standalone mode');
            // Handle standalone mode (outside of Telegram)
            checkAuthentication();
        }
    } catch (error) {
        console.error('Error initializing Telegram WebApp:', error);
    }
}

// Set theme colors based on Telegram theme
function setTelegramTheme() {
    if (!telegramWebApp) return;
    
    // Get Telegram theme colors
    const themeParams = telegramWebApp.themeParams;
    
    if (themeParams) {
        // Create CSS variables for Telegram colors
        const root = document.documentElement;
        
        // Set main colors
        root.style.setProperty('--tg-theme-bg-color', themeParams.bg_color || '#ffffff');
        root.style.setProperty('--tg-theme-text-color', themeParams.text_color || '#000000');
        root.style.setProperty('--tg-theme-hint-color', themeParams.hint_color || '#999999');
        root.style.setProperty('--tg-theme-link-color', themeParams.link_color || '#2678b6');
        root.style.setProperty('--tg-theme-button-color', themeParams.button_color || '#2678b6');
        root.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color || '#ffffff');
        
        // Set secondary colors
        root.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color || '#f0f0f0');
        
        // Add theme data attribute to body for CSS targeting
        document.body.setAttribute('data-theme', telegramWebApp.colorScheme || 'light');
    }
}

// Check if user is authenticated
function checkAuthentication() {
    // Get auth element if exists
    const authElement = document.getElementById('telegram-auth');
    
    if (authElement && telegramWebApp) {
        // If we have auth element and Telegram WebApp, we need to authenticate
        authElement.addEventListener('click', handleTelegramAuth);
    }
}

// Check if user is authenticated
function isUserAuthenticated() {
    // Check if we have a user_id in the session
    return document.body.hasAttribute('data-user-authenticated');
}

// Handle Telegram authentication process
function handleTelegramAuth() {
    if (!telegramWebApp) {
        showError('Телеграм WebApp недоступен. Пожалуйста, запустите приложение в Telegram.');
        return;
    }
    
    try {
        // Show loading overlay
        showLoading();
        
        // Get authentication data from Telegram
        const user = telegramWebApp.initDataUnsafe.user;
        
        if (!user) {
            hideLoading();
            showError('Не удалось получить данные пользователя Telegram');
            return;
        }
        
        // Create authentication data object
        const authData = {
            id: user.id,
            first_name: user.first_name,
            last_name: user.last_name,
            username: user.username,
            photo_url: user.photo_url,
            auth_date: telegramWebApp.initDataUnsafe.auth_date,
            hash: telegramWebApp.initDataUnsafe.hash
        };
        
        // Send authentication data to backend
        fetch('/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(authData)
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                // Authentication successful, redirect to library
                window.location.href = data.redirect || '/library';
            } else {
                showError(data.error || 'Ошибка авторизации');
            }
        })
        .catch(error => {
            hideLoading();
            showError('Ошибка при авторизации: ' + error.message);
            console.error('Auth error:', error);
        });
    } catch (error) {
        hideLoading();
        showError('Ошибка аутентификации: ' + error.message);
        console.error('Auth error:', error);
    }
}

// Add Telegram main button if needed
function addMainButton() {
    if (!telegramWebApp) return;
    
    // Check if we're on specific pages that need a main button
    const path = window.location.pathname;
    
    if (path === '/library') {
        // Add button to library page
        telegramWebApp.MainButton.setText('Добавить книгу');
        telegramWebApp.MainButton.onClick(() => {
            window.location.href = '/add-book';
        });
        telegramWebApp.MainButton.show();
    } else if (path === '/search') {
        // Add search button
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            telegramWebApp.MainButton.setText('Искать книги');
            telegramWebApp.MainButton.onClick(() => {
                document.getElementById('search-form').submit();
            });
            telegramWebApp.MainButton.show();
        }
    } else if (path.includes('/add-book') || path.includes('/edit')) {
        // Add save button for book forms
        telegramWebApp.MainButton.setText('Сохранить книгу');
        telegramWebApp.MainButton.onClick(() => {
            document.querySelector('form').submit();
        });
        telegramWebApp.MainButton.show();
    } else {
        // Hide button on other pages
        telegramWebApp.MainButton.hide();
    }
}

// Send data back to Telegram bot if needed
function sendDataToTelegram(data) {
    if (!telegramWebApp) return;
    
    telegramWebApp.sendData(JSON.stringify(data));
}

// Close the Web App
function closeTelegramWebApp() {
    if (!telegramWebApp) return;
    
    telegramWebApp.close();
}
