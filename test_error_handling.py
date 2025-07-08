# -*- coding: utf-8 -*-
"""
Created on Mon Jul  7 20:37:03 2025

@author: paco_
"""

import requests
import json

def consume_cotizador_api(api_key: str, data: dict, base_url: str = "http://127.0.0.1:5000") -> dict or None:
    """
    Consume el endpoint '/cotizador_optimo' de la API Flask con validación por API Key.

    Args:
        api_key (str): La API key para autenticación.
        data (dict): El diccionario con los datos a enviar al cotizador.
        base_url (str): La URL base de la API.

    Returns:
        dict or None: Un diccionario con la respuesta exitosa o el mensaje de error de la API,
                      o None en caso de un error de conexión no manejado.
    """
    endpoint = "/cotizador_optimo"
    url = f"{base_url}{endpoint}"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        # Siempre es bueno imprimir el status code para depuración
        print(f"Código de estado HTTP recibido: {response.status_code}")

        # Intentamos decodificar la respuesta JSON, sin importar si es éxito o error
        try:
            response_json = response.json()
            # Si el status code indica un error (4xx o 5xx), pero hay JSON, lo imprimimos
            if not response.ok: # response.ok es True para 2xx, False para 4xx/5xx
                print(f"Error detallado de la API (JSON): {json.dumps(response_json, indent=2)}")
                return response_json # Devolvemos el JSON de error
            return response_json # Si fue exitoso, devolvemos el JSON de éxito
        except json.JSONDecodeError:
            # Si no es JSON, imprimimos el texto plano de la respuesta
            if not response.ok:
                print(f"Error detallado de la API (Texto): {response.text}")
                return {"error": "API returned non-JSON error", "details": response.text}
            else:
                print(f"Respuesta exitosa de la API no JSON: {response.text}")
                return {"message": "API returned non-JSON success", "details": response.text}


    except requests.exceptions.RequestException as e:
        # Esto captura errores de red, DNS, timeouts, etc., antes de recibir una respuesta HTTP
        print(f"Error de conexión con la API: {e}")
        return None

# --- Ejemplo de Uso ---
if __name__ == "__main__":
    my_api_key = "g4c)R@[UW2`4--Y£" # Tu API Key
    api_base_url = "http://127.0.0.1:5000"

    # Ejemplo de datos correctos (ajusta según lo que tu API espera)
    # Suponiendo que 'cotizador_optimo' espera ciertos parámetros.
    # Si estos datos son incorrectos, la API debería devolver un 400 con un mensaje.
    correct_data = {
        "parametro1": "valor1",
        "parametro2": 123,
        "lista_items": ["itemA", "itemB"]
    }

    # Ejemplo de datos INCORRECTOS (para forzar un BAD REQUEST)
    # Por ejemplo, falta un campo obligatorio, tipo de dato incorrecto, etc.
    incorrect_data = {
        "parametro1": "valor1",
        # "parametro2" faltante o incorrecto
        "lista_items": "esto no es una lista" # Tipo de dato incorrecto
    }

    print("\n--- Intento con datos CORRECTOS (si se espera éxito) ---")
    response_success = consume_cotizador_api(my_api_key, correct_data, api_base_url)
    if response_success:
        print("\nRespuesta del cotizador (EXITO o ERROR CON MENSAJE):")
        print(json.dumps(response_success, indent=2))
    else:
        print("No se pudo obtener respuesta del cotizador (error de conexión).")

    print("\n--- Intento con datos INCORRECTOS (para forzar un 400 Bad Request) ---")
    response_error = consume_cotizador_api(my_api_key, incorrect_data, api_base_url)
    if response_error:
        print("\nRespuesta del cotizador (ERROR 400 DETALLADO):")
        print(json.dumps(response_error, indent=2))
    else:
        print("No se pudo obtener respuesta del cotizador (error de conexión).")