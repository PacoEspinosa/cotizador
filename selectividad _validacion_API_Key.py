# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 13:17:59 2025

@author: paco_
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = "g4c)R@[UW2`4--Y£"

# Middleware o decorador para verificación de API Key
def require_api_key(func):
    def wrapper(*args, **kwargs):
        if 'X-API-Key' not in request.headers or request.headers['X-API-Key'] != API_KEY:
            return jsonify({"error": "Unauthorized: Invalid or missing API Key"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__ # Importante para Flask para que el decorador no cambie el nombre de la función
    return wrapper

@app.route("/public_info", methods=["GET"])
def get_public_info():
    """Este endpoint no requiere API Key."""
    return jsonify({"message": "Esta es información pública. No necesitas API Key."})

@app.route("/get_config", methods=["GET"])
@require_api_key # Este endpoint SÍ requiere API Key
def get_config():
    """Este endpoint requiere API Key."""
    return jsonify({
        "cotizacion_admin_config": {
            "url_produccion": "http://127.0.0.1:5000/cotizador_optimo"
        },
        # ... resto de tu configuración
    })

@app.route("/config", methods=["POST"])
@require_api_key # Este endpoint SÍ requiere API Key
def update_config():
    """Este endpoint requiere API Key y recibe datos JSON."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    # Aquí iría la lógica para actualizar la configuración con 'data'
    print(f"Configuración recibida: {data}")
    return jsonify({"message": "Configuración actualizada exitosamente", "received_data": data})

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de salud, no requiere API Key."""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)