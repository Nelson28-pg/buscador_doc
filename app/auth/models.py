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
    "Ernesto": {
        "password": generate_password_hash("ernesto4848"),
        "name": "Ernesto"
    },
    "invitado1": {
        "password": generate_password_hash("invitado14848"),
        "name": "invitado1"
    },
    "invitado2": {
        "password": generate_password_hash("invitado24848"),
        "name": "invitado2"
    }
}
