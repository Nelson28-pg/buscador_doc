# app/auth/__init__.py
from flask import Blueprint

# Define un Blueprint para la autenticación.
# Las plantillas se buscarán automáticamente en la carpeta 'app/templates/auth'
auth_bp = Blueprint('auth', __name__)

# Importa las rutas al final para evitar importaciones circulares.
from . import routes