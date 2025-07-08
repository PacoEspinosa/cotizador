# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 19:13:44 2025

@author: paco_
"""

import json
import requests
import numpy_financial as nf
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Cambia esto por una clave secreta fuerte

CONFIG_FILE = 'config.info'
text = open(CONFIG_FILE)
config = json.loads(text.read())
text.close()
API_URL = config["cotizacion_admin_config"]["url_produccion"]

def load_config():
    """Carga la configuración desde el archivo JSON."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_config(config_data):
    """Guarda la configuración en el archivo JSON."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=2)

@app.route('/')
def index():
    """Redirige a la página de configuración por defecto."""
    return redirect(url_for('configuracion'))

@app.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    """
    Maneja la visualización y edición del archivo de configuración.
    Permite a los usuarios ver y modificar los parámetros del JSON.
    """
    config_data = load_config()
    if request.method == 'POST':
        try:
            # Obtener los datos del formulario y actualizarlos en la configuración
            # Se asume que los campos del formulario corresponden directamente a las claves del JSON
            form_data = request.form.to_dict()
            
            # Convertir valores a tipos apropiados (int/float)
            for key, value in form_data.items():
                if value.replace('.', '', 1).isdigit(): # Check if it's a number
                    if '.' in value:
                        form_data[key] = float(value)
                    else:
                        form_data[key] = int(value)

            # Actualizar la estructura del JSON con los nuevos datos
            # Esto es un ejemplo simple, para una estructura anidada se necesitaría un parser más robusto
            # Para este ejemplo, haremos un merge simple para los campos de primer nivel
            for main_key in config_data:
                if isinstance(config_data[main_key], dict):
                    for sub_key in config_data[main_key]:
                        flat_key = f"{main_key}_{sub_key}" # keys are flattened in form
                        if flat_key in form_data:
                            config_data[main_key][sub_key] = form_data[flat_key]
                else: # For direct keys if any (though current config doesn't have them)
                    if main_key in form_data:
                        config_data[main_key] = form_data[main_key]

            # Manejo específico para catalogo_base_deducible
            for tipo in ['H', 'E', 'G']:
                key = f"catalogo_base_deducible_{tipo}"
                if key in form_data:
                    config_data["catalogo_base_deducible"][tipo] = form_data[key]

            # Manejo específico para catalogo_tasa_comision
            for tipo in ['min', 'max']:
                key = f"catalogo_tasa_comision_{tipo}"
                if key in form_data:
                    config_data["catalogo_tasa_comision"][tipo] = form_data[key]

            # Manejo específico para catalogo_otros_gastos
            for plazo in ['12', '24', '36', '48']:
                key = f"catalogo_otros_gastos_{plazo}"
                if key in form_data:
                    config_data["catalogo_otros_gastos"][plazo] = form_data[key]

            # Manejo específico para catalogo_conceptos_factura
            for concepto in config_data["catalogo_conceptos_factura"]:
                for param in ['media', 'variacion']:
                    key = f"catalogo_conceptos_factura_{concepto}_{param}"
                    if key in form_data:
                        config_data["catalogo_conceptos_factura"][concepto][param] = form_data[key]

            save_config(config_data)
            flash('Configuración actualizada exitosamente!', 'success')
            return redirect(url_for('configuracion'))
        except Exception as e:
            flash(f'Error al actualizar la configuración: {e}', 'error')
            
    # Para la visualización, aplanamos el diccionario para que el formulario sea más fácil de manejar
    flat_config = {}
    for key, value in config_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict): # For nested dictionaries like catalogo_conceptos_factura
                    for final_key, final_value in sub_value.items():
                        flat_config[f"{key}_{sub_key}_{final_key}"] = final_value
                else:
                    flat_config[f"{key}_{sub_key}"] = sub_value
        else:
            flat_config[key] = value

    return render_template('configuracion.html', config=flat_config)


@app.route('/identificar_ofertas', methods=['GET', 'POST'])
def identificar_ofertas():
    """
    Permite al usuario ingresar parámetros para calcular una tasa de interés.
    """
    tasa_interes = None
    valor_factura = 0.0
    plazo = 0
    enganche_c_iva = 0.0
    valor_residual_s_iva = 0.0
    pago_mensual = 0.0
    comision_apertura = 0.0
    if request.method == 'POST':
        try:
            valor_factura = float(request.form['valor_factura'])
            plazo = int(request.form['plazo'])
            enganche_c_iva = float(request.form['enganche_c_iva'])
            valor_residual_s_iva = float(request.form['valor_residual_s_iva'])
            pago_mensual = float(request.form['pago_mensual'])
            comision_apertura = float(request.form['comision_apertura'])
            es_credito = request.form.get('es_credito') == 'on'

            text = open('config.info')
            config = json.loads(text.read())
            cat_otros_gastos = config['catalogo_otros_gastos']
            if plazo <= 12:
                gastos_olr = cat_otros_gastos['12']
            elif plazo <= 24:
                gastos_olr = cat_otros_gastos['24']
            elif plazo <= 36:
                gastos_olr = cat_otros_gastos['36']
            else:
                gastos_olr = cat_otros_gastos['48']

            if pago_mensual > 0 and plazo > 0:
                monto_a_financiar = valor_factura - enganche_c_iva
                if monto_a_financiar > 0:
                    tasa_int = nf.rate(plazo,-pago_mensual,((valor_factura-enganche_c_iva+comision_apertura+(0 if es_credito else gastos_olr))/(1.16)),valor_residual_s_iva,0)
                    tasa_interes = (tasa_int/(1.16 if es_credito else 1))*1200
                    #flash(f'Tasa de Interés Anual Calculada (Estimación): {tasa_interes:.4f}%', 'success')
                else:
                    flash('El monto a financiar debe ser mayor que cero para calcular la tasa.', 'warning')
            else:
                flash('Pago Mensual y Plazo deben ser mayores que cero.', 'warning')

        except ValueError:
            flash('Por favor, ingresa valores numéricos válidos en todos los campos.', 'error')
        except Exception as e:
            flash(f'Ocurrió un error al calcular la tasa de interés: {e}', 'error')

    return render_template('identificar_ofertas.html', tasa_interes=tasa_interes, valor_factura=valor_factura, plazo=plazo,
                           enganche_c_iva=enganche_c_iva, pago_mensual=pago_mensual, comision_apertura=comision_apertura,
                           valor_residual_s_iva=valor_residual_s_iva)


@app.route('/cotizador', methods=['GET', 'POST'])
def cotizador():
    """
    Realiza una consulta a la API externa y muestra el resultado.
    """
    api_response = None
    error_message = None
    payload = {}

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            valor_factura = float(request.form.get('valor_factura', 0))
            accesorios = float(request.form.get('accesorios', 0))
            plazo_meses = int(request.form.get('plazo_meses', 0))
            seguro = float(request.form.get('seguro', 0))
            pago_inicial_total = float(request.form.get('pago_inicial_total', 0))
            residual_siva = float(request.form.get('residual_siva', 0))
            tasa_residual_siva = float(request.form.get('tasa_residual_siva', 0))
            if (residual_siva > 0 and tasa_residual_siva > 0):
                error_message = "Se tomará el porcentaje del residual, solo debes proporcionar uno de los 2."
                flash(error_message, 'success')
                residual_siva = (tasa_residual_siva/100) * (valor_factura/1.16)
                
            deposito_garantia = float(request.form.get('deposito_garantia', 0))
            fondo_reserva = float(request.form.get('fondo_reserva', 0))
            tipo_activo = request.form.get('tipo_activo', 'Auto')
            tipo_vehiculo = request.form.get('tipo_vehiculo', 'G')
            tasa_comision_apertura = float(request.form.get('tasa_comision_apertura', 1))
            tasa_interes_anual = float(request.form.get('tasa_interes_anual', 0))
            plan_tasa = request.form.get('plan_tasa')
            if (plan_tasa != '' and tasa_interes_anual > 0) or (plan_tasa == '' and tasa_interes_anual == 0):
                error_message = "Solo debes proporcionar uno de los dos, Plan del leasing o la tasa de interes anual."
                flash(error_message, 'error')
            elif plan_tasa != '':
                tasa_interes_anual = config["catalogo_tasa_anual"][plan_tasa][tipo_activo]
                plan_tasa = ''
            
            num_parametros_facturacion = int(request.form.get('num_parametros_facturacion', 10))
            tipo_respuesta = int(6)
            fuente_consulta = 1
            
            payload = {
                "valor_factura": valor_factura,
                "accesorios": accesorios,
                "plazo_meses": plazo_meses,
                "seguro": seguro,
                "pago_inicial_total": pago_inicial_total,
                "residual_siva": residual_siva,
                "deposito_garantia": deposito_garantia,
                "fondo_reserva": fondo_reserva,
                "tipo_activo": tipo_activo,
                "tipo_vehiculo": tipo_vehiculo,
                "tasa_comision_apertura": tasa_comision_apertura,
                "tasa_interes_anual": tasa_interes_anual,
                "plan_tasa": plan_tasa,
                "num_parametros_facturacion": num_parametros_facturacion,
                "tipo_respuesta": tipo_respuesta,
                "fuente_consulta": fuente_consulta
            }
            #flash(payload,"success")
            headers = {'Content-Type': 'application/json'}
            response = requests.post(API_URL, json=payload, headers=headers)
            if not response.ok: # response.ok es True para 2xx, False para 4xx/5xx
                error = response.json()
                error_message = f"Error al conectar con la API: {error['error']}"
                flash(error_message, 'error')
            else:
                api_response = response.json()
                if 'admin_message' in api_response:
                    flash(api_response['admin_message'], 'success')

        except json.JSONDecodeError:
            # Si no es JSON, imprimimos el texto plano de la respuesta
            if not response.ok:
                flash("Error detallado de la API: {response.text}","error")
            else:
                flash("Respuesta exitosa de la API no JSON: {response.text}","error")
        except ValueError:
            error_message = "Por favor, verifica que todos los campos numéricos tengan valores válidos."
            flash(error_message, 'error')
        except Exception as e:
            error_message = f"Ocurrió un error inesperado: {e}"
            flash(error_message, 'error')

    return render_template('cotizador.html', api_response = api_response, error_message=error_message, tbl_tipo_activo=config["catalogo_tipo_activo"],
                           tbl_tipo_vehiculo = config["catalogo_tipo_vehiculo"],tbl_planes = config["catalogo_tasa_anual"], input_lines = (payload if len(payload) > 0 else []))

if __name__ == '__main__':
    app.run(debug=True,port=5001)
