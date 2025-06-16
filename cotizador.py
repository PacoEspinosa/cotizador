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
        num_parametros_facturacion = data['num_parametros_facturacion']
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
        max_valor_deducible = config['fiscal']['max_valor_deducible']
        precio_activo = config['Cotizacion_Config']['precio_activo']/100
        tasa_descuento = config['Cotizacion_Config']['tasa_descuento']/100
        deducibilidad = config['Cotizacion_Config']['deducibilidad']/100
        disminucion_valor = config['Cotizacion_Config']['disminucion_valor']/100
        tasa_credito = config['credito']['tasa_credito']/100
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
        
        
        if (tipo_respuesta == 2 or tipo_respuesta == 4 ):
            #**** Seccion Tabla resumen ****
            #[solo_leasing]
            total_deducible_fiscal_leasing = renta_mensual_descuento*deducibilidad*plazo_meses
            devolucion_inversion_solo_leasing = monto_inversion
            rendimiento = plazo_meses*descuento_mensual
            monto_pagado_leasing = pago_inicial_total - rentas_deposito
            total_pagado_plan_solo_leasing = plazo_meses*renta_mensual_descuento + monto_pagado_leasing
            ahorro_isr_esperado_leasing = total_deducible_fiscal_leasing*isr
            total_iva_acreditable_leasing = plazo_meses*iva_renta_mensual_descuento*deducibilidad
            devolucion_rentas_deposito = (rentas_deposito if monto_inversion == 0 else 0)
            beneficio_solo_leasing = ahorro_isr_esperado_leasing + total_iva_acreditable_leasing + devolucion_rentas_deposito
            costo_neto_solo_leasing = total_pagado_plan_solo_leasing - beneficio_solo_leasing
            
            #[leasing_compra]
            valor_comercial_esperado = valor_factura*(1-(disminucion_valor/12))**plazo_meses
            total_pagado_plan_leasing_compra = total_pagado_plan_solo_leasing + valor_residual
            total_iva_acreditable_leasing_compra = total_iva_acreditable_leasing + iva_residual
            ahorro_compra = valor_comercial_esperado - valor_residual
            beneficio_leasing_compra = ahorro_isr_esperado_leasing + total_iva_acreditable_leasing_compra + ahorro_compra + devolucion_rentas_deposito
            costo_neto_leasing_compra = total_pagado_plan_leasing_compra - beneficio_leasing_compra
            
            #[Credito]
            monto_pagado_credito = enganche
            pago_credito = nf.pmt(((tasa_credito*(1+iva))/12),plazo_meses,-(valor_siva - enganche_siva),0)
            tmp_intereses_credito = 0
            for n in range(plazo_meses):
                tmp_intereses_credito += -nf.ipmt(((tasa_credito*(1+iva))/12),(n+1),plazo_meses,(valor_siva - enganche_siva))
            total_intereses_credito = tmp_intereses_credito/(1+iva)
            total_pagado_plan_credito = monto_pagado_credito + (pago_credito * plazo_meses)
            total_deducible_fiscal_credito = (max_valor_deducible if total_pagado_plan_credito>max_valor_deducible else total_pagado_plan_credito)
            ahorro_isr_esperado_credito = total_deducible_fiscal_credito*isr
            total_iva_acreditable_credito = (total_deducible_fiscal_credito*iva) + (total_intereses_credito*iva)
            beneficio_credito = ahorro_isr_esperado_credito + total_iva_acreditable_credito
            costo_neto_credito = total_pagado_plan_credito - beneficio_credito
            
            tabla_resumen = {
                "Total Deducible Fiscal": {
                    "Solo Leasing": total_deducible_fiscal_leasing,
                    "Leasing + compra": total_deducible_fiscal_leasing,
                    "Credito": total_deducible_fiscal_credito,
                    "Compra": total_deducible_fiscal_credito
                    },
                "Devolucion inversion":{
                    "Solo Leasing": devolucion_inversion_solo_leasing,
                    "Leasing + compra": devolucion_inversion_solo_leasing,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Rendimiento":{
                    "Solo Leasing": rendimiento,
                    "Leasing + compra": rendimiento,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Valor Residual":{
                    "Solo Leasing": residual_siva,
                    "Leasing + compra": residual_siva,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Valor Comercial proyectado":{
                    "Solo Leasing": 0,
                    "Leasing + compra": valor_comercial_esperado,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Total Pagado Plan":{
                    "Solo Leasing": total_pagado_plan_solo_leasing,
                    "Leasing + compra": total_pagado_plan_leasing_compra,
                    "Credito": total_pagado_plan_credito,
                    "Compra": 0  
                    },
                "Ahorro ISR Esperado":{
                    "Solo Leasing": ahorro_isr_esperado_leasing,
                    "Leasing + compra": ahorro_isr_esperado_leasing,
                    "Credito": ahorro_isr_esperado_credito,
                    "Compra": 0  
                    },
                "Total IVA Acreditable":{
                    "Solo Leasing": devolucion_inversion_solo_leasing,
                    "Leasing + compra": devolucion_inversion_solo_leasing,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Ahorro Adquisicion":{
                    "Solo Leasing": 0,
                    "Leasing + compra": ahorro_compra,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Devolucion Rentas en Deposito":{
                    "Solo Leasing": devolucion_rentas_deposito,
                    "Leasing + compra": devolucion_rentas_deposito,
                    "Credito": 0,
                    "Compra": 0  
                    },
                "Beneficio total":{
                    "Solo Leasing": beneficio_solo_leasing,
                    "Leasing + compra": beneficio_leasing_compra,
                    "Credito": beneficio_credito,
                    "Compra": 0  
                    },
                "Costo neto":{
                    "Solo Leasing": costo_neto_solo_leasing,
                    "Leasing + compra": costo_neto_leasing_compra,
                    "Credito": costo_neto_credito,
                    "Compra": 0  
                    }
                }

        elif (tipo_respuesta == 3 or tipo_respuesta == 4):
            tabla_facturacion = {}
            num_parametros_facturacion = num_parametros_facturacion
        elif (tipo_respuesta == 1 or tipo_respuesta == 4):
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
                "renta_mensual_descuento": round(renta_mensual_descuento, 2),
                "tabla_amortizacion": tabla_amortizacion
            }
        elif tipo_respuesta == 2:
            response = {
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "pago_credito_calculada": round(pago_credito, 2),
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
                "renta_mensual_descuento": round(renta_mensual_descuento, 2),
                "pago_credito_calculada": round(pago_credito, 2),
                "tabla_amortizacion": tabla_amortizacion,
                "tabla_resumen": tabla_resumen,
                "tabla_facturacion": tabla_facturacion
            }
        return jsonify(response)

    except KeyError as e:
        return jsonify({"error": f"Falta una clave en el JSON de entrada: {e}. Asegurate de incluir 'plazo_meses', 'valor_factura' y 'tasa_interes_anual'."}), 400
    except Exception as e:
        return jsonify({"error": f"Ha ocurrido un error inesperado: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)