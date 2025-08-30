# run.py
# -*- coding: utf-8 -*-
"""
Script principal para ejecutar la aplicación.

Este script importa la factory 'create_app' desde el paquete 'app'
y la utiliza para crear y ejecutar la instancia de la aplicación Flask.
"""
import os
from app import create_app

# Crea la aplicación usando la factory.
# Lee la variable de entorno FLASK_CONFIG o usa 'development' por defecto.
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # El host '0.0.0.0' hace que el servidor sea accesible desde otras máquinas en la red.
    # El modo debug y otras configuraciones se gestionan a través de la configuración cargada en la factory.
    app.run(host='0.0.0.0', port=5000)
