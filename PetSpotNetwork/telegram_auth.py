import hashlib
import hmac
import time
import logging
import os
from app import app

def validate_telegram_data(auth_data):
    """
    Validate Telegram authentication data
    
    Args:
        auth_data: Dictionary with Telegram authentication data
        
    Returns:
        bool: True if data is valid, False otherwise
    """
    try:
        # Get token from environment or use default for development
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        if not bot_token:
            logging.warning("No Telegram bot token found, validation will fail")
            return False
            
        # Extract auth_data
        auth_date = auth_data.get('auth_date')
        
        # Check if auth_date is recent (within 24 hours)
        if int(time.time()) - int(auth_date) > 86400:
            logging.warning("Auth date is too old")
            return False
            
        # Remove hash from data for validation
        data_check_string = '\n'.join(
            f"{key}={value}" for key, value in sorted(auth_data.items()) 
            if key != 'hash'
        )
        
        # Generate secret key
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare calculated hash with provided hash
        if calculated_hash == auth_data.get('hash'):
            return True
        else:
            logging.warning("Invalid Telegram auth hash")
            return False
            
    except Exception as e:
        logging.error(f"Error validating Telegram data: {str(e)}")
        return False
