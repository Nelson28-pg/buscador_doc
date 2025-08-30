# app/main/__init__.py
from flask import Blueprint

# Define un Blueprint para la funcionalidad principal.
# Las plantillas se buscarán en 'app/templates/main' y los archivos estáticos en 'app/static'
main_bp = Blueprint('main', __name__)

# Importa las rutas al final para evitar importaciones circulares.
from . import routes