# app/main/routes.py
# -*- coding: utf-8 -*-
"""
Define las rutas principales de la aplicación (búsqueda, carga, etc.).
"""
from flask import render_template, request, jsonify, send_file, session, current_app, make_response
from functools import wraps
from . import main_bp
from app.auth.routes import login_required
from app.auth.models import users
import pandas as pd
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import io
import csv
import json # Importar el módulo json

# Obtiene el logger configurado en la factory de la aplicación
logger = logging.getLogger(__name__)

# --- Decoradores Específicos del Módulo ---
def nocache(view):
    """Decorador para evitar que una vista se guarde en la caché del navegador."""
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return no_cache

# --- Datos Internos y Variables Globales ---
# Ruta al archivo JSON de datos internos
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.json')

INTERNAL_DATA = []
try:
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        INTERNAL_DATA = json.load(f)
    logger.info(f"Datos internos cargados desde {DATA_FILE_PATH}: {len(INTERNAL_DATA)} registros.")
except FileNotFoundError:
    logger.warning(f"Archivo de datos internos no encontrado en {DATA_FILE_PATH}. Usando datos de ejemplo.")
    # Fallback a datos de ejemplo si el archivo no se encuentra
    INTERNAL_DATA = [
        {"nombre": "Contrato de Servicio B", "tipo": "ruc", "id": "DOC002", "contenido": "024 contrato servicio prestación", "fecha": "2024-01-15", "estado": "activo"},
        {"nombre": "Factura #12345", "tipo": "obligado", "id": "DOC004", "contenido": "024 factura número doce mil", "fecha": "2024-02-10", "estado": "procesado"}
    ]
except json.JSONDecodeError as e:
    logger.error(f"Error al decodificar JSON en {DATA_FILE_PATH}: {e}. Usando datos de ejemplo.")
    INTERNAL_DATA = [
        {"nombre": "Contrato de Servicio B", "tipo": "ruc", "id": "DOC002", "contenido": "024 contrato servicio prestación", "fecha": "2024-01-15", "estado": "activo"},
        {"nombre": "Factura #12345", "tipo": "obligado", "id": "DOC004", "contenido": "024 factura número doce mil", "fecha": "2024-02-10", "estado": "procesado"}
    ]

# El historial no es específico de la sesión en esta implementación.
search_history = []
upload_history = []

# --- Rutas Principales ---
@main_bp.route('/')
@login_required
@nocache
def index():
    """Renderiza la página principal de la aplicación."""
    username = session.get('user')
    user_details = users.get(username, {})
    user_name = user_details.get('name', 'Usuario')
    
    show_welcome_curtain = False
    if session.pop('just_logged_in', False):
        show_welcome_curtain = True

    if show_welcome_curtain:
        current_hour = datetime.now().hour
        if 0 <= current_hour <= 14:
            subtitle_text = 'aa'
        elif 14 < current_hour <= 17:
            subtitle_text = 'bb'
        else:
            subtitle_text = 'cc'
        return render_template('loading.html', user_name=user_name, subtitle_text=subtitle_text)
    return render_template('main/search.html', user_name=user_name)

@main_bp.route('/search_page')
@login_required
@nocache
def search_page():
    """Renderiza la página de búsqueda de documentos."""
    username = session.get('user')
    user_details = users.get(username, {})
    user_name = user_details.get('name', 'Usuario')
    return render_template('main/search.html', user_name=user_name)

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Maneja la carga y procesamiento de archivos Excel."""
    if 'file' not in request.files:
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        
        try:
            file.save(filepath)
            df = pd.read_excel(filepath, engine='openpyxl')
            df = df.dropna(how='all').fillna('')
            
            session['excel_data'] = df.to_dict('records')
            session['current_filename'] = file.filename
            
            upload_history.append({
                'filename': file.filename, 'timestamp': datetime.now().isoformat(),
                'records': len(session['excel_data']), 'user': session.get('user')
            })
            
            os.remove(filepath)
            return jsonify({'success': True, 'filename': file.filename, 'records': len(session['excel_data'])})
            
        except Exception as e:
            logger.error(f"Error procesando archivo para {session.get('user')}: {e}")
            if os.path.exists(filepath): os.remove(filepath)
            return jsonify({'error': f'Error al leer el archivo: {str(e)}'}), 400
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@main_bp.route('/search', methods=['POST'])
@login_required
def search():
    """Ejecuta una búsqueda sobre los datos internos o el archivo cargado."""
    data = request.get_json()
    query = data.get('query', '').lower().strip()
    data_source = data.get('dataSource', 'internal')

    if not query:
        return jsonify({'results': [], 'query': query})

    search_history.append({
        'query': query, 'timestamp': datetime.now().isoformat(), 'user': session.get('user')
    })

    data_to_search = session.get('excel_data', []) if data_source == 'excel' else INTERNAL_DATA
    
    results = []
    for item in data_to_search:
        if any(query in str(value).lower() for value in item.values()):
            results.append(item)
            
    return jsonify({
        'results': results, 'query': query,
        'is_excel_data': data_source == 'excel', 'total_records': len(data_to_search)
    })

@main_bp.route('/clear', methods=['POST'])
@login_required
def clear_data():
    """Limpia los datos de Excel de la sesión del usuario."""
    session.pop('excel_data', None)
    session.pop('current_filename', None)
    return jsonify({'success': True})

@main_bp.route('/status')
@login_required
def status():
    """Devuelve el estado actual de los datos del usuario."""
    return jsonify({
        'has_excel_data': 'excel_data' in session,
        'filename': session.get('current_filename', ''),
        'records': len(session.get('excel_data', [])),
        'sample_records': len(INTERNAL_DATA) # Usar INTERNAL_DATA aquí
    })


@main_bp.route('/update_data', methods=['POST'])
@login_required
def update_data():
    """Actualiza un campo de un registro en la base de datos interna."""
    data = request.get_json()
    exp_bn = data.get('exp_bn')
    field = data.get('field')
    value = data.get('value')

    if not all([exp_bn, field]):
        return jsonify({'success': False, 'error': 'Datos incompletos'}), 400

    global INTERNAL_DATA
    updated = False
    for item in INTERNAL_DATA:
        if item.get('EXP BN') == exp_bn:
            item[field] = value
            updated = True
            break

    if not updated:
        return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404

    try:
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(INTERNAL_DATA, f, indent=4, ensure_ascii=False)
        logger.info(f"Dato actualizado en {DATA_FILE_PATH}: EXP BN={exp_bn}, campo={field}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error al escribir en {DATA_FILE_PATH}: {e}")
        return jsonify({'success': False, 'error': 'Error al guardar los datos'}), 500

# --- Funciones de Utilidad ---
def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls', 'csv'}