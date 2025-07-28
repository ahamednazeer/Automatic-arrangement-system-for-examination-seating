# Examination Seating System Configuration
# Generated on 2025-07-28 22:38:56

# Application Settings
DEBUG = True
SECRET_KEY = 'change-this-in-production-20250728'

# Database Settings
DATABASE_URL = 'sqlite:///exam_system.db'

# Upload Settings
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Report Settings
REPORTS_FOLDER = 'reports'
EXPORTS_FOLDER = 'exports'

# Security Settings
SESSION_TIMEOUT = 3600  # 1 hour
PASSWORD_MIN_LENGTH = 6

# Email Settings (for notifications)
MAIL_SERVER = 'localhost'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''

# Pagination
ITEMS_PER_PAGE = 20

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/app.log'
