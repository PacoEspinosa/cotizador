# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 14:57:29 2025

@author: paco_
"""
import numpy_financial as nf
plazo_meses  = 12
tasa_credito = 28/100
valor_siva =  653534.48 
enganche_siva =  65353.45 

total_intereses_credito = 0
for n in range(plazo_meses):
    interes = -nf.ipmt(((tasa_credito*(1.16))/12),(n+1),plazo_meses,(valor_siva - enganche_siva))
    total_intereses_credito += interes
    print('interes: ', interes, ' Acumulado: ', total_intereses_credito)

#***********************
import numpy_financial as nf
plazo  = 36
pago_mensual = 132864.55
valor_factura =  4574200 
enganche_c_iva =  0 
comision_apertura = 0
gastos_olr = 21344
es_credito = True
valor_residual_s_iva = 0

tasa_int = nf.rate(plazo,-pago_mensual,((valor_factura-enganche_c_iva+comision_apertura+(0 if es_credito else gastos_olr))/(1.16)),valor_residual_s_iva,0)
tasa_int = (tasa_int/(1.16 if es_credito else 1))*12

print(tasa_int)

# ********************
import json

tipo_respuesta = 'H'
tipo_vehiculo = 'A'

text = open('config.info')
config = json.loads(text.read())
cat_base_deducible = config['catalogo_base_deducible']
cat_conceptos_factura = config['catalogo_conceptos_factura']
tasa_comision_min = config['catalogo_tasa_comision']['min']
tasa_comision_max = config['catalogo_tasa_comision']['max']

print(tasa_comision_min,tasa_comision_max )

print(cat_base_deducible[tipo_respuesta])
print(cat_conceptos_factura)
print(cat_conceptos_factura['g_administracion']['media'])

#***********
import random

random_num = 0.2831 + random.uniform(-0.0931,0.0931)
print(random_num)

#*****************************
print(type(cat_conceptos_factura['g_administracion']['variacion']))
print(type(0.0931))
g_administracion = cat_conceptos_factura['g_administracion']['media'] + random.uniform(-cat_conceptos_factura['g_administracion']['variacion'],cat_conceptos_factura['g_administracion']['variacion'])
print(g_administracion)

#******************
if tipo_vehiculo not in cat_base_deducible:
    print("Tipo_vehiculo no contiene un valor permitido.")

#***********
import os
os.chdir('d:\\python scripts\\Projects\\Cotizador_optimo\\')
print(os.getcwd())

import json
import os

def load_json_file(filename):
    """Loads a JSON file and returns its content."""
    filepath = os.path.join('d:\\python scripts\\Projects\\Cotizador_optimo\\', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. Check file integrity.")
        return None


response = load_json_file('todos.json')

amortizacion_data = response['tabla_amortizacion']

#********************
import requests
import json
API_URL = "http://54.152.171.128:5000/cotizador_optimo"
api_response = None
error_message = None

try:
    # Obtener datos del formulario
    valor_factura = 758100
    accesorios = 0
    plazo_meses = 12
    seguro = 0
    pago_inicial_total = 0
    residual_siva = 20000
    monto_inversion = 0
    deposito_garantia = 0
    tipo_vehiculo = "H"
    tasa_comision_apertura = 1
    tasa_interes_anual = 36
    num_parametros_facturacion = 10
    tipo_respuesta = int(6)

    payload = {
        "valor_factura": valor_factura,
        "accesorios": accesorios,
        "plazo_meses": plazo_meses,
        "seguro": seguro,
        "pago_inicial_total": pago_inicial_total,
        "residual_siva": residual_siva,
        "monto_inversion": monto_inversion,
        "deposito_garantia": deposito_garantia,
        "tipo_vehiculo": tipo_vehiculo,
        "tasa_comision_apertura": tasa_comision_apertura,
        "tasa_interes_anual": tasa_interes_anual,
        "num_parametros_facturacion": num_parametros_facturacion,
        "tipo_respuesta": tipo_respuesta
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status() # Lanza un HTTPError si la respuesta fue un error
    api_response = response.json()
except requests.exceptions.RequestException as e:
    error_message = f"Error al conectar con la API: {e}"
    print(error_message, 'error')

#*************************************
renta_mensual = 12345.6789
print(renta_mensual)
formato_moneda = f"${renta_mensual:,.2f} MXN"
print(formato_moneda)  # Output: $12,345.68 MXN

print("$%.2f" | format(renta_mensual))