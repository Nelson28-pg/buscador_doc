# app/__init__.py
# -*- coding: utf-8 -*-
"""
Factory de la aplicación.

Este archivo inicializa la aplicación Flask, carga la configuración,
y registra los blueprints que contienen las diferentes partes de la aplicación.
"""
import os
import logging
from flask import Flask
from config import config

def create_app(config_name=None):
    """
    Crea y configura una instancia de la aplicación Flask.
    
    :param config_name: El nombre de la configuración a usar (ej: 'development', 'production').
    :return: La instancia de la aplicación Flask.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    # Se define 'static_folder' y 'template_folder' a nivel de aplicación para una gestión centralizada.
    # Se añade static_url_path para asegurar que la URL de los archivos estáticos sea correcta.
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates', 
                static_folder='static',
                static_url_path='/static') # Añadido para asegurar la ruta URL de los estáticos
    
    # Carga la configuración desde el objeto importado de config.py
    app.config.from_object(config[config_name])
    
    # Asegurarse de que la carpeta de instancia exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configurar el logging
    setup_logging(app)

    # Registrar Blueprints (módulos de la aplicación)
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    return app

def setup_logging(app):
    """Configura el sistema de logging para la aplicación."""
    if app.debug or app.testing:
        return

    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicación BuscadorDoc iniciada')
