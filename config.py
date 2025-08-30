# config.py - Configuración centralizada de la aplicación
import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""
    
    # Configuración básica de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-cambiar-en-produccion'
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 32 * 1024 * 1024))  # 32MB
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Configuración de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Límites de la aplicación
    MAX_SEARCH_HISTORY = int(os.environ.get('MAX_SEARCH_HISTORY', 100))
    MAX_UPLOAD_HISTORY = int(os.environ.get('MAX_UPLOAD_HISTORY', 20))
    
    # Configuración de seguridad
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    
class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # Configuración de seguridad más estricta
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging más detallado
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB para tests

# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}