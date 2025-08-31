# app/auth/routes.py
# -*- coding: utf-8 -*-
"""
Define las rutas para la autenticación (login, logout).
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from . import auth_bp
from .models import users
from werkzeug.security import check_password_hash
from functools import wraps

def login_required(f):
    """
    Decorador que asegura que el usuario haya iniciado sesión.
    Si no ha iniciado sesión, lo redirige a la página de login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión del usuario."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not username or not password:
            if is_ajax:
                return jsonify({'message': 'Por favor, ingresa usuario y contraseña.'}), 400
            flash('Por favor, ingresa usuario y contraseña.', 'danger')
            return render_template('auth/login.html')

        user = users.get(username)

        if user is None or not check_password_hash(user['password'], password):
            if is_ajax:
                return jsonify({'message': 'Usuario o contraseña incorrectos.'}), 401
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('auth/login.html')
        else:
            session['user'] = username
            if is_ajax:
                return jsonify({'redirect_url': url_for('main.index')}), 200
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('main.index')) # Redirige a la ruta principal
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Maneja el cierre de sesión del usuario."""
    session.clear()
    flash('Has cerrado la sesión.', 'info')
    return redirect(url_for('auth.login'))
