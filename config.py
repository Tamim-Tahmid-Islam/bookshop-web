"""
Configuration module for PageVault.
Supports both direct MySQL Server connection and embedded fallback.
"""

import os

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = int(os.environ.get('PORT', 8080))

# MySQL Database configuration
MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'pagevault_db'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# Secret key for sessions/tokens
SECRET_KEY = os.environ.get('SECRET_KEY', 'pagevault-super-secure-secret-key-2026')
