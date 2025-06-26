# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 10:42:18 2025

@author: paco_
"""

from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

JSON_FILE = 'config.info'

def read_json_data():
    """Reads data from the JSON file."""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {} # Return empty dict if file not found
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {JSON_FILE}. Check file integrity.")
        return {}

def write_json_data(data):
    """Writes data to the JSON file."""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def index():
    data = read_json_data()
    if request.method == 'POST':
        # Process form data and update the JSON
        updated_data = data.copy() # Start with a copy of existing data

        # Cotizacion_Config
        updated_data['Cotizacion_Config']['precio_activo'] = int(request.form['precio_activo'])
        updated_data['Cotizacion_Config']['tasa_descuento'] = int(request.form['tasa_descuento'])
        updated_data['Cotizacion_Config']['disminucion_valor'] = int(request.form['disminucion_valor'])
        updated_data['Cotizacion_Config']['deducibilidad'] = int(request.form['deducibilidad'])
        updated_data['Cotizacion_Config']['num_parametros_facturacion'] = int(request.form['num_parametros_facturacion'])

        # Credito
        updated_data['credito']['tasa_credito'] = int(request.form['tasa_credito'])
        updated_data['credito']['tasa_enganche'] = int(request.form['tasa_enganche'])

        # Fiscal
        updated_data['fiscal']['IVA'] = int(request.form['IVA'])
        updated_data['fiscal']['ISR'] = int(request.form['ISR'])
        updated_data['fiscal']['depreciacion'] = int(request.form['depreciacion'])
        updated_data['fiscal']['max_valor_deducible'] = int(request.form['max_valor_deducible'])

        # Catalogo_base_deducible
        updated_data['catalogo_base_deducible']['H'] = int(request.form['H'])
        updated_data['catalogo_base_deducible']['E'] = int(request.form['E'])
        updated_data['catalogo_base_deducible']['G'] = int(request.form['G'])

        # Catalogo_conceptos_factura (assuming these will be edited as text inputs for simplicity,
        # and converted to float; you might want more robust validation)
        for key in data['catalogo_conceptos_factura'].keys():
            updated_data['catalogo_conceptos_factura'][key]['media'] = float(request.form[f'{key}_media'])
            updated_data['catalogo_conceptos_factura'][key]['variacion'] = float(request.form[f'{key}_variacion'])


        write_json_data(updated_data)
        return redirect(url_for('index')) # Redirect to prevent form resubmission on refresh
    return render_template('setup.html', data=data)

if __name__ == '__main__':
    app.run(debug=True) # debug=True allows for automatic reloading and better error messages
