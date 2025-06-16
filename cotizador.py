# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 13:22:15 2025

@author: paco_
"""

from flask import Flask, request, jsonify
import json
import numpy_financial as nf

app = Flask(__name__)

@app.route('/cotizador_optimo', methods=['POST'])
def cotizador_optimo():
    try:
        data = request.get_json()

        valor_factura = data['valor_factura']
        accesorios = data['accesorios']
        plazo_meses = data['plazo_meses']
        seguro = data['seguro']
        pago_inicial_total = data['pago_inicial_total']
        residual_siva = data['residual_siva']
        monto_inversion = data['monto_inversion']
        deposito_garantia = data['deposito_garantia']
        tipo_vehiculo =  data['tipo_vehiculo']
        tasa_comision_apertura = data['tasa_comision_apertura']
        tasa_interes_anual = data['tasa_interes_anual']
        tipo_respuesta = data['tipo_respuesta']

        # Validaciones básicas
        if not all(isinstance(arg, (int, float)) for arg in [valor_factura,accesorios,plazo_meses, seguro, pago_inicial_total,
                                                             residual_siva,monto_inversion,deposito_garantia,tasa_comision_apertura,
                                                             tasa_interes_anual,tipo_respuesta]):
            return jsonify({"error": "Todos los campos deben ser numeros."}), 400
        if plazo_meses <= 0 or valor_factura <= 0 or tasa_interes_anual <= 0:
            return jsonify({"error": "Plazo, monto inicial y tasa de interés anual deben ser mayores que cero."}), 400
        if tasa_comision_apertura <= 0 or tasa_comision_apertura > 4:
            return jsonify({"error": "Comision de apertura solo puede estar entre 0 y 4."}), 400

        # constantes configuracion
        text = open('config.info')
        config = json.loads(text.read())
        iva = config['fiscal']['IVA']/100
        isr = config['fiscal']['ISR']/100
        precio_activo = config['Cotizacion_Config']['precio_activo']/100
        tasa_descuento = config['Cotizacion_Config']['tasa_descuento']/100
        deducibilidad = config['Cotizacion_Config']['deducibilidad']/100
        tasa_enganche = config['credito']['tasa_enganche']/100
        cat_base_deducible = config['catalogo_base_deducible']
        
        # variables para calculo
        valor_siva = valor_factura/(1+iva)
        iva_auto = valor_siva*iva
        accesorios_siva = accesorios/(1+iva)
        iva_accesorios = accesorios_siva*iva
        pago_inicial_total_siva = pago_inicial_total/(1+iva)
        iva_pago_inicial_total = pago_inicial_total*iva
        seguro_siva = seguro/(1+iva)
        iva_seguro =  seguro*iva
        if monto_inversion == 0:
            if deposito_garantia > 0:
                rentas_deposito = deposito_garantia
            else:
                if ((pago_inicial_total-seguro)/valor_siva) > precio_activo:
                    rentas_deposito = (pago_inicial_total-seguro) - (valor_siva*precio_activo)
                else:
                    rentas_deposito = 0
        else:
            rentas_deposito = monto_inversion
        iva_residual = residual_siva*iva
        valor_residual = residual_siva + iva_residual
        if plazo_meses <= 12:
            otros_gastos_siva = 9800
        elif plazo_meses <= 24:
            otros_gastos_siva = 14100
        elif plazo_meses <= 36:
            otros_gastos_siva = 18400
        else:
            otros_gastos_siva = 22700
        iva_otros_gastos = otros_gastos_siva*iva
        otros_gastos = otros_gastos_siva + iva_otros_gastos
        valor_inicial_arrenda = pago_inicial_total - seguro - rentas_deposito
        comision_apertura = (valor_factura + accesorios + otros_gastos - valor_inicial_arrenda)*(tasa_comision_apertura/100)
        comision_apertura_siva = comision_apertura/(1+iva)
        iva_comision_apertura = comision_apertura_siva*iva
        monto_arrendamiento = (valor_factura + accesorios + otros_gastos + comision_apertura-valor_inicial_arrenda)
        monto_arrendamiento_siva = monto_arrendamiento/(1+iva)
        iva_monto_arrendamiento = monto_arrendamiento_siva*iva
        enganche = valor_factura*tasa_enganche
        enganche_siva = enganche/(1+iva)
        iva_enganche = enganche_siva*iva
        
        
        # Convertir tasa de interés anual a mensual
        tasa_interes_mensual = (tasa_interes_anual / 100) / 12

        # Calcular pago mensual
        if tasa_interes_mensual == 0:
            renta_mensual_calculada = (valor_inicial_arrenda - residual_siva) / plazo_meses
        else:
            renta_mensual_calculada = nf.pmt(tasa_interes_mensual,plazo_meses,-monto_arrendamiento_siva,residual_siva)
        iva_renta_mensual_calculada = renta_mensual_calculada*iva
        total_renta_mensual_calculada = renta_mensual_calculada+iva_renta_mensual_calculada
        descuento_mensual = (0 if monto_inversion == 0 else monto_inversion*(tasa_descuento/12))
        renta_mensual_descuento = renta_mensual_calculada-descuento_mensual
        iva_renta_mensual_descuento = renta_mensual_descuento+iva
        total_renta_mensual_descuento = renta_mensual_descuento+iva_renta_mensual_descuento
        renta_mensual_deducible = cat_base_deducible[tipo_vehiculo]
        if (renta_mensual_descuento*deducibilidad)>renta_mensual_deducible:
            complemento_renta = (renta_mensual_descuento*deducibilidad-renta_mensual_deducible)
        else:
            complemento_renta = 0
        
        #**** Seccion Tabla resumen ****
        #[solo_leasing]
        total_deducible_fiscal_leasing = renta_mensual_descuento*dedudibilidad*plazo_meses
        devolucion_inversion_solo_leasing = monto_inversion
        rendimiento = plazo_meses*descuento_mensual
        monto_pagado = pago_inicial_total - rentas_deposito
        total_pagado_plan_solo_leasing = plazo_meses*renta_mensual_descuento + monto_pagado
        ahorro_isr_esperado_solo_leasing = total_deducible_fiscal_leasing+isr
        total_iva_acreditable_leasing = plazo_meses*iva_renta_mensual_descuento*deducibilidad
        devolucion_rentas_deposito = (rentas_deposito if monto_inversion == 0 else 0)
        beneficio_solo_leasing = ahorro_isr_esperado_solo_leasing + total_iva_acreditable_leasing + devolucion_rentas_deposito
        costo_neto_solo_leasing = total_pagado_plan_solo_leasing - beneficio_solo_leasing
        
        #[leasing_compra]
        
        
        
        # Generar tabla de amortización
        tabla_amortizacion = []
        saldo_pendiente = monto_arrendamiento_siva

        for mes in range(1, plazo_meses + 1):
            interes_pagado = saldo_pendiente * tasa_interes_mensual
            capital_pagado = renta_mensual_calculada - interes_pagado
            saldo_pendiente -= capital_pagado

            # Asegurarse de que el último saldo no sea negativo debido a errores de punto flotante
            if mes == plazo_meses:
                capital_pagado += saldo_pendiente  # Ajustar para que el saldo sea 0 al final
                saldo_pendiente = 0

            tabla_amortizacion.append({
                "mes": mes,
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "interes_pagado": round(interes_pagado, 2),
                "capital_pagado": round(capital_pagado, 2),
                "saldo_pendiente": round(max(residual_siva, saldo_pendiente), 2)  # Asegura que el saldo no sea negativo
            })

        if tipo_respuesta == 1:
            response = {
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "tabla_amortizacion": tabla_amortizacion
            }
        elif tipo_respuesta == 2:
            response = {
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "tabla_resumen": tabla_resumen
            }
        elif tipo_respuesta == 3:
            response = {
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "tabla_facturacion": tabla_facturacion
            }
        elif tipo_respuesta == 4:
            response = {
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "tabla_amortizacion": tabla_amortizacion
                "tabla_resumen": tabla_resumen
                "tabla_facturacion": tabla_facturacion
            }
        return jsonify(response)

    except KeyError as e:
        return jsonify({"error": f"Falta una clave en el JSON de entrada: {e}. Asegúrate de incluir 'plazo_meses', 'monto_inicial' y 'tasa_interes_anual'."}), 400
    except Exception as e:
        return jsonify({"error": f"Ha ocurrido un error inesperado: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)