# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 11:10:20 2025

@author: paco_
"""

import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Define la ruta del archivo de configuración
CONFIG_FILE = 'config.info'
API_KEYS = {
    "g4c)R@[UW2`4--Y£": "API1",
    "997_/<[sow9m1,1H": "API2"
}


# --- Funciones para manejar el archivo de configuración ---

def read_config():
    """
    Lee la configuración desde el archivo config.info.
    Si el archivo no existe, lo crea con la configuración por defecto.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"Archivo de configuración '{CONFIG_FILE}' no encontrado.")
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo JSON '{CONFIG_FILE}': {e}")
        # En caso de un JSON inválido, se podría intentar respaldar el archivo corrupto
        # y crear uno nuevo con la configuración por defecto.
        return {"error": "Config file is corrupted", "details": str(e)}
    except Exception as e:
        print(f"Error inesperado al leer '{CONFIG_FILE}': {e}")
        return {"error": "Unexpected error reading config file", "details": str(e)}

def write_config(data):
    """
    Escribe la configuración en el archivo config.info.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al escribir en el archivo '{CONFIG_FILE}': {e}")
        return False

def deep_merge(source, destination):
    """
    Fusiona recursivamente dos diccionarios.
    Los valores del diccionario 'source' sobrescriben los de 'destination' si las claves son las mismas.
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            # Si ambos son diccionarios, fusiona recursivamente
            destination[key] = deep_merge(value, destination[key])
        else:
            # Si no son diccionarios o la clave no existe en destino, sobrescribe
            destination[key] = value
    return destination

# --- Endpoints de la API ---

@app.before_request
def authenticate_api_key():
    api_key = request.headers.get('X-API-Key')
    if api_key not in API_KEYS:
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 401

@app.route('/config', methods=['GET'])
def get_config():
    """
    Endpoint para consultar la configuración completa.
    """
    config_data = read_config()
    if "error" in config_data:
        return jsonify(config_data), 500
    return jsonify(config_data)

@app.route('/config', methods=['PUT'])
def update_config():
    """
    Endpoint para actualizar la configuración.
    Permite actualizaciones parciales fusionando el JSON recibido con la configuración existente.
    """
    if not request.is_json:
        return jsonify({"error": "Los cambios deben estar en formato JSON."}), 400

    new_data = request.get_json()
    if not isinstance(new_data, dict):
        return jsonify({"error": "Los cambios deben estar en el formato indicado en la documentacion."}), 400

    current_config = read_config()
    if "error" in current_config:
        return jsonify(current_config), 500

    # Fusiona la nueva data con la configuración actual
    updated_config = deep_merge(new_data, current_config)

    if write_config(updated_config):
        return jsonify({"message": "Actualización exitosa", "nueva configuracion": updated_config}), 200
    else:
        return jsonify({"error": "Error al escribir los cambios"}), 500

# --- Ejecución de la API ---
if __name__ == '__main__':
    # Asegúrate de que el archivo de configuración exista al iniciar la API
    # Esto también manejará el caso de un archivo corrupto al intentar leerlo.
    initial_config = read_config()
    if "error" in initial_config:
        print("Advertencia: El archivo de configuración inicial tiene errores.")
    else:
        print("Archivo de configuración cargado o creado exitosamente.")

    # Ejecuta la aplicación Flask
    # En producción, usarías un servidor WSGI como Gunicorn o uWSGI
    # Para desarrollo, puedes ejecutarlo así:
    app.run(debug=True, port=5002)

