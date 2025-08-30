# app/auth/models.py
# -*- coding: utf-8 -*-
"""
Define los modelos de datos para la autenticación.
En una aplicación más grande, esto usaría un ORM como SQLAlchemy.
"""

from werkzeug.security import generate_password_hash

# --- Almacén de Usuarios ---
# El nombre de usuario para iniciar sesión es la clave principal del diccionario (ej: "Elflaquis").
# Para una aplicación real, esto debería estar en una base de datos.
users = {
    "Elflaquis": {
        "password": generate_password_hash("admin0545"),
        "name": "Elflaquis"
    },
    "Panchis": {
        "password": generate_password_hash("panchis4848"),
        "name": "Panchis"
    },
    "invitado": {
        "password": generate_password_hash("invitado4848"),
        "name": "invitado"
    }
}
