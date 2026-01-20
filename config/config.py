import os

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for development
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_DOMAIN = None  # Don't set domain, let Flask handle it
    PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

    # Application
    SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'hazard_rules_schema_refined.json')

    # Logging
    LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')

    # Authentication
    USE_AUTHENTICATION = False

    # LDAP settings (only if USE_AUTHENTICATION = True)
    LDAP_HOST = 'ldap://ldap.phivolcs.local'
    LDAP_BASE_DN = 'dc=phivolcs,dc=local'
    LDAP_USER_DN = 'ou=users'
