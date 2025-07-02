# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 13:22:15 2025

@author: paco_
"""

from flask import Flask, request, jsonify
import json
import numpy_financial as nf
import random

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/cotizador_optimo', methods=['POST'])
def cotizador_optimo():
    admin_message = ''
    try:
        data = request.get_json()

        valor_factura = data['valor_factura']
        accesorios = data['accesorios']
        plazo_meses = data['plazo_meses']
        seguro = data['seguro']
        pago_inicial_total = data['pago_inicial_total']
        residual_siva = data['residual_siva']
        deposito_garantia = data['deposito_garantia']
        fondo_reserva = data['fondo_reserva']
        tipo_activo =  data['tipo_activo']
        tipo_vehiculo =  data['tipo_vehiculo']
        tasa_comision_apertura = data['tasa_comision_apertura']
        tasa_interes_anual = data['tasa_interes_anual']
        num_parametros_facturacion = data['num_parametros_facturacion']
        tipo_respuesta = data['tipo_respuesta']
        fuente_consulta = data['fuente_consulta']

        # [[[[[[[[[[[   Validaciones básicas   ]]]]]]]]]]]
        if not all(isinstance(arg, (int, float)) for arg in [valor_factura,accesorios,plazo_meses, seguro, pago_inicial_total,
                                                             residual_siva,deposito_garantia,fondo_reserva,tasa_comision_apertura,
                                                             tasa_interes_anual,tipo_respuesta]):
            return jsonify({"error": "Todos los campos deben ser numeros."}), 400
        if plazo_meses <= 0 or valor_factura <= 0 or tasa_interes_anual <= 0 or tipo_respuesta <= 0:
            return jsonify({"error": "Plazo, monto inicial, tasa de interes anual y tipo respuesta deben ser mayores que cero."}), 400
        if tipo_respuesta <= 0 or tipo_respuesta > 6:
            return jsonify({"error": "Tipo_respuesta solo puede estar entre 1 y 6."}), 400
        if deposito_garantia > 0 and fondo_reserva > 0:
            return jsonify({"error": "Solo debe proporcionar uno de los conceptos, deposito_garantia o fondo_reserva."}), 400
        if pago_inicial_total < (seguro + deposito_garantia):
            return jsonify({"error": "El pago inicial debe ser mayor a la suma del seguro y el monto en inversion."}), 400

        # constantes configuracion
        text = open('config.info')
        config = json.loads(text.read())
        text.close()
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
        cat_conceptos_factura = config['catalogo_conceptos_factura']
        tasa_comision_min = config['catalogo_tasa_comision']['min']
        tasa_comision_max = config['catalogo_tasa_comision']['max']
        cat_tipo_activo = config['catalogo_tipo_activo']
        cat_otros_gastos = config['catalogo_otros_gastos']
        cat_valor_residual = config['catalogo_valor_residual']
        
        if tasa_comision_apertura <= tasa_comision_min or tasa_comision_apertura > tasa_comision_max:
            if fuente_consulta == 0:
                return jsonify({"error": "Comision de apertura solo puede estar entre 0 y 4."}), 400
            else:
                admin_message = "Comision de apertura solo puede estar entre 0 y 4."
                
        if tipo_activo not in cat_tipo_activo:
            return jsonify({"error": "tipo_activo no contiene un valor permitido."}), 400

        # variables para calculo
        valor_siva = valor_factura/(1+iva)
        iva_auto = valor_siva*iva
        accesorios_siva = accesorios/(1+iva)
        iva_accesorios = accesorios_siva*iva
        pago_inicial_total_siva = pago_inicial_total/(1+iva)
        iva_pago_inicial_total = pago_inicial_total*iva
        seguro_siva = seguro/(1+iva)
        iva_seguro =  seguro*iva
        if deposito_garantia == 0:
            if fondo_reserva > 0:
                deposito_garantia = fondo_reserva
            else:
                if ((pago_inicial_total-seguro)/valor_siva) > precio_activo:
                    deposito_garantia = (pago_inicial_total-seguro) - (valor_siva*precio_activo)
                else:
                    deposito_garantia = 0
        else:
            deposito_garantia = deposito_garantia
        iva_residual = residual_siva*iva
        valor_residual = residual_siva + iva_residual
        tasa_residual = round((residual_siva/valor_siva),2)*100
        if plazo_meses <= 12:
            bucket_meses = '12'
        elif plazo_meses <= 24:
            bucket_meses = '24'
        elif plazo_meses <= 36:
            bucket_meses = '36'
        else:
            bucket_meses = '48'
        otros_gastos_siva = cat_otros_gastos[bucket_meses]
        iva_otros_gastos = otros_gastos_siva*iva
        otros_gastos = otros_gastos_siva + iva_otros_gastos
        valor_inicial_arrenda = pago_inicial_total - seguro - deposito_garantia
        comision_apertura = (valor_factura + accesorios + otros_gastos - valor_inicial_arrenda)*(tasa_comision_apertura/100)
        comision_apertura_siva = comision_apertura/(1+iva)
        iva_comision_apertura = comision_apertura_siva*iva
        monto_arrendamiento = (valor_factura + accesorios + otros_gastos + comision_apertura-valor_inicial_arrenda)
        monto_arrendamiento_siva = monto_arrendamiento/(1+iva)
        iva_monto_arrendamiento = monto_arrendamiento_siva*iva
        enganche = valor_factura*tasa_enganche
        enganche_siva = enganche/(1+iva)
        iva_enganche = enganche_siva*iva
        
        #[[[[[[[[[[[  Validaciones  ]]]]]]]]]]]
        if monto_arrendamiento<0:
            return jsonify({"error": "Revisar valor_factura, pago_inicial, deposito_garantia ó seguro, tienen algún valor erróneo."}), 400
        if valor_inicial_arrenda < 0 or valor_inicial_arrenda > (valor_siva*precio_activo):
            return jsonify({"error": "Revisar fondo_reserva, pago_inicial, deposito_garantia ó seguro, tienen algún valor erróneo."}), 400
        if fuente_consulta == 0:
            if tipo_activo == 'Bicicleta':
                if tasa_residual < cat_valor_residual[tipo_activo]["min"] or tasa_residual > cat_valor_residual[tipo_activo]["max"]:
                    return jsonify({"error": "El valor del residual debe ser entre el " + str(cat_valor_residual[tipo_activo]["min"]) + "% y el " + str(cat_valor_residual[tipo_activo]["max"]) + "%"}), 400
            else:
                if tasa_residual < cat_valor_residual[bucket_meses]["min"] or tasa_residual > cat_valor_residual[bucket_meses]["max"]:
                    return jsonify({"error": "El valor del residual debe ser entre el " + str(cat_valor_residual[bucket_meses]["min"]) + "% y el " + str(cat_valor_residual[bucket_meses]["max"]) + "%"}), 400
        else:
            if tipo_activo == 'Bicicleta':
                if tasa_residual < cat_valor_residual[tipo_activo]["min"] or tasa_residual > cat_valor_residual[tipo_activo]["max"]:
                    admin_message =  "El valor del residual debe ser entre el " + str(cat_valor_residual[tipo_activo]["min"]) + "% y el " + str(cat_valor_residual[tipo_activo]["max"]) + "%"
            else:
                if tasa_residual < cat_valor_residual[bucket_meses]["min"] or tasa_residual > cat_valor_residual[bucket_meses]["max"]:
                    admin_message =  "El valor del residual debe ser entre el " + str(cat_valor_residual[bucket_meses]["min"]) + "% y el " + str(cat_valor_residual[bucket_meses]["max"]) + "%"
            
        # Convertir tasa de interés anual a mensual
        tasa_interes_mensual = (tasa_interes_anual / 100) / 12

        # Calcular pago mensual
        if tasa_interes_mensual == 0:
            renta_mensual_calculada = (valor_inicial_arrenda - residual_siva) / plazo_meses
        else:
            renta_mensual_calculada = nf.pmt(tasa_interes_mensual,plazo_meses,-monto_arrendamiento_siva,residual_siva)
        iva_renta_mensual_calculada = renta_mensual_calculada*iva
        total_renta_mensual_calculada = renta_mensual_calculada+iva_renta_mensual_calculada
        descuento_mensual = (0 if deposito_garantia == 0 else deposito_garantia*(tasa_descuento/12))
        renta_mensual_descuento = renta_mensual_calculada-descuento_mensual
        iva_renta_mensual_descuento = renta_mensual_descuento*iva
        total_renta_mensual_descuento = renta_mensual_descuento+iva_renta_mensual_descuento
        renta_mensual_deducible = cat_base_deducible[tipo_vehiculo]
        if (renta_mensual_descuento*deducibilidad)>renta_mensual_deducible:
            complemento_renta = (renta_mensual_descuento*deducibilidad-renta_mensual_deducible)
        else:
            complemento_renta = 0
        
        
        #*********  Generar tabla de resumen  ******************+
        if (tipo_respuesta == 2 or tipo_respuesta == 6 ):
            #**** Seccion Tabla resumen ****
            #[solo_leasing]
            total_deducible_fiscal_leasing = renta_mensual_descuento*deducibilidad*plazo_meses
            devolucion_inversion_solo_leasing = deposito_garantia
            rendimiento = plazo_meses*descuento_mensual
            monto_pagado_leasing = pago_inicial_total - deposito_garantia
            total_pagado_plan_solo_leasing = plazo_meses*renta_mensual_descuento + monto_pagado_leasing
            ahorro_isr_esperado_leasing = total_deducible_fiscal_leasing*isr
            total_iva_acreditable_leasing = plazo_meses*iva_renta_mensual_descuento*deducibilidad
            devolucion_deposito_garantia = (deposito_garantia if deposito_garantia == 0 else 0)
            beneficio_solo_leasing = ahorro_isr_esperado_leasing + total_iva_acreditable_leasing + devolucion_deposito_garantia
            costo_neto_solo_leasing = total_pagado_plan_solo_leasing - beneficio_solo_leasing
            
            #[leasing_compra]
            valor_comercial_esperado = valor_factura*(1-(disminucion_valor/12))**plazo_meses
            total_pagado_plan_leasing_compra = total_pagado_plan_solo_leasing + valor_residual
            total_iva_acreditable_leasing_compra = total_iva_acreditable_leasing + iva_residual
            ahorro_compra = valor_comercial_esperado - valor_residual
            beneficio_leasing_compra = ahorro_isr_esperado_leasing + total_iva_acreditable_leasing_compra + ahorro_compra + devolucion_deposito_garantia
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
            total_iva_acreditable_credito = iva_enganche + (total_intereses_credito*iva)
            beneficio_credito = ahorro_isr_esperado_credito + total_iva_acreditable_credito
            costo_neto_credito = total_pagado_plan_credito - beneficio_credito
            
            #[Compra]
            total_pagado_plan_compra = valor_factura
            total_iva_acreditable_compra = total_deducible_fiscal_credito*iva
            beneficio_compra = ahorro_isr_esperado_credito + total_iva_acreditable_compra
            costo_neto_compra = total_pagado_plan_compra - beneficio_compra
            
            tabla_resumen = {
                "Total Deducible Fiscal": {
                    "Solo Leasing": round(total_deducible_fiscal_leasing, 2),
                    "Leasing + compra": round(total_deducible_fiscal_leasing, 2),
                    "Credito": round(total_deducible_fiscal_credito, 2),
                    "Compra": round(total_deducible_fiscal_credito, 2)
                    },
                "Devolucion inversion":{
                    "Solo Leasing": round(devolucion_inversion_solo_leasing, 2),
                    "Leasing + compra": round(devolucion_inversion_solo_leasing, 2),
                    "Credito": round(0, 2),
                    "Compra": round(0, 2)  
                    },
                "Rendimiento":{
                    "Solo Leasing": round(rendimiento, 2),
                    "Leasing + compra": round(rendimiento, 2),
                    "Credito": round(0, 2),
                    "Compra": round(0, 2)  
                    },
                "Valor Residual":{
                    "Solo Leasing": round(residual_siva, 2),
                    "Leasing + compra": round(residual_siva, 2),
                    "Credito": round(0, 2),
                    "Compra": round(0, 2)  
                    },
                "Valor Comercial proyectado":{
                    "Solo Leasing": round(0, 2),
                    "Leasing + compra": round(valor_comercial_esperado, 2),
                    "Credito": round(0, 2),
                    "Compra": round(0, 2) 
                    },
                "Total Pagado Plan":{
                    "Solo Leasing": round(total_pagado_plan_solo_leasing, 2),
                    "Leasing + compra": round(total_pagado_plan_leasing_compra, 2),
                    "Credito": round(total_pagado_plan_credito, 2),
                    "Compra":round(total_pagado_plan_compra, 2)  
                    },
                "Ahorro ISR Esperado":{
                    "Solo Leasing": round(ahorro_isr_esperado_leasing, 2),
                    "Leasing + compra": round(ahorro_isr_esperado_leasing, 2),
                    "Credito": round(ahorro_isr_esperado_credito, 2),
                    "Compra": round(ahorro_isr_esperado_credito, 2) 
                    },
                "Total IVA Acreditable":{
                    "Solo Leasing": round(total_iva_acreditable_leasing, 2),
                    "Leasing + compra": round(total_iva_acreditable_leasing_compra, 2),
                    "Credito": round(total_iva_acreditable_credito, 2),
                    "Compra": round(total_iva_acreditable_compra, 2)  
                    },
                "Ahorro Adquisicion":{
                    "Solo Leasing": round(0, 2),
                    "Leasing + compra": round(ahorro_compra, 2),
                    "Credito": round(0, 2),
                    "Compra": round(0, 2)  
                    },
                "Devolucion Rentas en Deposito":{
                    "Solo Leasing": round(devolucion_deposito_garantia, 2),
                    "Leasing + compra": round(devolucion_deposito_garantia, 2),
                    "Credito": round(0, 2),
                    "Compra": round(0, 2)  
                    },
                "Beneficio total":{
                    "Solo Leasing": round(beneficio_solo_leasing, 2),
                    "Leasing + compra": round(beneficio_leasing_compra, 2),
                    "Credito": round(beneficio_credito, 2),
                    "Compra": round(beneficio_compra, 2)  
                    },
                "Costo neto":{
                    "Solo Leasing": round(costo_neto_solo_leasing, 2),
                    "Leasing + compra": round(costo_neto_leasing_compra, 2),
                    "Credito": round(costo_neto_credito, 2),
                    "Compra": round(costo_neto_compra, 2)
                    }
                }

        #*************   Generar tabla de facturacion   ***********************
        if (tipo_respuesta == 3 or tipo_respuesta == 6):
            if num_parametros_facturacion < 1 or num_parametros_facturacion > 10:
                return jsonify({"error": "num_parametros_facturacion solo puede estar entre 1 y 10."}), 400
            if tipo_vehiculo not in cat_base_deducible:
                return jsonify({"error": "tipo_vehiculo no contiene un valor permitido."}), 400

            g_administracion = complemento_renta * (cat_conceptos_factura['g_administracion']['media'] + random.uniform(-cat_conceptos_factura['g_administracion']['variacion'],cat_conceptos_factura['g_administracion']['variacion']))
            g_arrendamiento = complemento_renta * (cat_conceptos_factura['g_arrendamiento']['media'] + random.uniform(-cat_conceptos_factura['g_arrendamiento']['variacion'],cat_conceptos_factura['g_arrendamiento']['variacion']))
            tmp_complemento_renta = complemento_renta - g_administracion - g_arrendamiento
            gps = tmp_complemento_renta * cat_conceptos_factura['gps']['media']
            instalacion_gps =  tmp_complemento_renta * cat_conceptos_factura['instalacion_gps']['media']
            alta_vehiculo =  tmp_complemento_renta * cat_conceptos_factura['alta_vehiculo']['media']
            gastos_notariales =  tmp_complemento_renta * cat_conceptos_factura['gastos_notariales']['media']
            seguro_fac =  tmp_complemento_renta * cat_conceptos_factura['seguro_fac']['media']
            telemetria =  tmp_complemento_renta * cat_conceptos_factura['telemetria']['media']
            gestoria_alta =  tmp_complemento_renta * cat_conceptos_factura['gestoria_alta']['media']
            gestoria_seguro =  tmp_complemento_renta * cat_conceptos_factura['gestoria_seguro']['media']
            suma_conceptos = g_administracion + g_arrendamiento + gps + instalacion_gps + alta_vehiculo
            suma_conceptos += gastos_notariales + seguro_fac + telemetria + gestoria_alta +gestoria_seguro
            renta_leasing = renta_mensual_descuento - suma_conceptos
            
            tabla_facturacion = {
                "Gastos_administracion": round(g_administracion,2),
                "Gastos_arrendamiento": round(g_arrendamiento,2),
                "GPS": round(gps,2),
                "Instalacion_GPS": round(instalacion_gps,2),
                "Alta_vehiculo": round(alta_vehiculo,2),
                "Gastos_notariales": round(gastos_notariales,2),
                "Seguro_factura": round(seguro_fac,2),
                "Telemetria": round(telemetria,2),
                "Gestoria_alta_vehiculo": round(gestoria_alta,2),
                "Gestoria_seguro": round(gestoria_seguro,2),
                "Renta_leasing":  round(renta_leasing,2)
            }
            num_parametros_facturacion = num_parametros_facturacion

        #****************+   Generar tabla de amortización   **********************
        if (tipo_respuesta == 1 or tipo_respuesta == 6):
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

        #**************   Tabla de Interna   ***********************
        if (tipo_respuesta == 4 or tipo_respuesta == 6 ):
            tabla_interna = {}
            
        #**************   Tabla de cotizacion   **********************
        if (tipo_respuesta == 5 or tipo_respuesta == 6 ):
            tabla_cotizacion = {
                "Residual_siva": round(residual_siva,2),
                "Valor_inicial_arrenda": round(valor_inicial_arrenda,2),
                "Pago_inicial_total": round(pago_inicial_total,2),
                "deposito_garantia": round(deposito_garantia,2),
                "Renta_mensual_calculada": round(renta_mensual_calculada,2),
                "Comision_apertura_siva": round(comision_apertura_siva,2),
                "Descuento_mensual": round(descuento_mensual,2),
                "Seguro": round(seguro,2),
                "Renta_mensual_descuento": round(renta_mensual_descuento,2),
                "Accesorios": round(accesorios,2),
                "Iva_renta_mensual_descuento": round(iva_renta_mensual_descuento,2),
                "Monto_arrendamiento_siva": round(monto_arrendamiento_siva,2),
                "Total_renta_mensual_descuento":  round(total_renta_mensual_descuento,2)
            }
            

            
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
                "descuento_mensual": round(descuento_mensual, 2),
                "base_deducible":  round(renta_mensual_deducible, 2),
                "tabla_facturacion": tabla_facturacion
            }
        elif tipo_respuesta == 4:
            response = {
                "tabla_interna": tabla_interna
            }
        elif tipo_respuesta == 5:
            response = {
                "tabla_cotizacion": tabla_cotizacion
            }
        elif tipo_respuesta == 6:
            response = {
                "renta_mensual_calculada": round(renta_mensual_calculada, 2),
                "descuento_mensual": round(descuento_mensual, 2),
                "renta_mensual_descuento": round(renta_mensual_descuento, 2),
                "pago_credito_calculada": round(pago_credito, 2),
                "tabla_amortizacion": tabla_amortizacion,
                "tabla_resumen": tabla_resumen,
                "tabla_cotizacion": tabla_cotizacion,
                "tabla_facturacion": tabla_facturacion
            }
        if fuente_consulta == 1 and admin_message != '':
            response["admin_message"] = admin_message
        return jsonify(response)

    except KeyError as e:
        return jsonify({"error": f"Falta una clave en el JSON de entrada: {e}. Asegurate de incluir 'plazo_meses', 'valor_factura' y 'tasa_interes_anual'."}), 400
    except Exception as e:
        return jsonify({"error": f"Ha ocurrido un error inesperado: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)