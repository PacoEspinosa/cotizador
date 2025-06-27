# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 12:15:32 2025

@author: paco_
"""

from flask import Flask, render_template
import json
import os

app = Flask(__name__)

def load_json_file(filename):
    """Loads a JSON file and returns its content."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. Check file integrity.")
        return None

@app.route('/')
def show_results():
    # Load the JSON data
    amortizacion_data = load_json_file('amortizacion.json')
    resumen_data = load_json_file('resumen.json')

    # Pass the data to the template
    return render_template('results.html',
                           amortizacion=amortizacion_data,
                           resumen=resumen_data)

if __name__ == '__main__':
    app.run(debug=True)

