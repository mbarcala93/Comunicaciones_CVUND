# -*- coding: utf-8 -*-

from os import path, remove, makedirs, listdir
from urllib.parse import unquote_plus
from datetime import datetime
import json
import sqlite3
import re

from flask import render_template, request, session, jsonify, abort

from app import app

from app.auxiliar import get_db, logCambios, verificaPermiso, log, logeado,\
    logeado_AJAX, tokenCSRF, Configuracion, sqliteRow2list_dict, lista_id,\
    gira_imagen, obten_columnas, sqliteRow2dict_dict, lista_enteros


MUESTRAS = {
    "20230928_RIAN_COR_M1": {
        "Sólidos en suspensión": 47.9,
        "DQO":962,
        "DBO{_5}":511,
        "Nitrógeno total Kjeldahl":358,
        "Nitrogeno oxidado (NO{_2} + NO{_3})":0,
        "Nitrógeno total":358,
        "Fósforo Total":2.55
    },
    "20231006_DODR_POL_M1": {
        "Sólidos en suspensión": 94.9,
        "DQO": 320,
        "DBO{_5}": 216,
        "Nitrógeno total Kjeldahl": 38.9,
        "Nitrogeno oxidado (NO{_2} + NO{_3})": 0,
        "Nitrógeno total": 38.9,
        "Fósforo Total": 6.93 
    }
}

def extrae_lineas(nombre_archivo):
    ENCODING = "cp1252"
    # ENCODING = "ANSI"
    f = open(nombre_archivo, "r", encoding=ENCODING)
    lineas = f.readlines()
    f.close()
    return lineas


def linea_a_dict(lineas, filtro_muestra=None):
    resultado = {}
    errores = []
    for indice, linea in enumerate(lineas):
        muestra = {}
        cod_muestra = ""
        if indice % 2 == 0:
            linea = linea.replace(chr(9), ";")
            encabezados = linea.split(";")
            try:
                valores = lineas[indice + 1].replace("	", ";").split(";")
            except:
                return [resultado, errores]
            for idx, encabezado in enumerate(encabezados):
                valor = valores[idx].replace(",", ".")
                valor = valor.replace("\n", "")
                encabezado = encabezado.replace("\n", "")
                if encabezado == "RefMuestra":
                    formato_muestra = re.search("20[2-5][0-9][0-1][0-9][0-3][0-9]_\w\w\w\w_\w\w\w_M[0-9]", valor)
                    # formato_blanco = re.search("20[2-5][0-9][0-1][0-9][0-3][0-9]_\w\w\w\w_\w\w\w_B[C,E,T][C,E,T][C,E,T]", valor)
                    if formato_muestra:
                        cod_muestra = valor
                    else:
                        errores.append(valor)
                        continue
                muestra.update({encabezado: pruebaFloat(valor)})
            if filtro_muestra and filtro_muestra == cod_muestra:
                resultado.update({cod_muestra: muestra})
                break
            elif not filtro_muestra:
                resultado.update({cod_muestra: muestra})
    
    return [resultado, errores]

def pruebaFloat(valor):
    try:
        return float(valor)
    except:
        return valor

def obten_dict_laboratorio():
    with open("laboratorio.json", "r", encoding="utf-8") as archivo:
        texto = archivo.read()
    return json.loads(texto)


def traduce_parametros(muestra: tuple, parametros_laboratorio: dict):
    cod_muestra, parametros = muestra
    muestra_traducida = {}
    for parametro in parametros:
        if parametro in parametros_laboratorio:            
            muestra_traducida.update({
                parametros_laboratorio[parametro]: parametros[parametro]
            })
    return {cod_muestra: muestra_traducida}


def traduce_muestras(muestras: dict, parametros_laboratorio: dict):
    muestras_traducidas = {}
    for muestra in muestras.items():
         muestras_traducidas.update(
            traduce_parametros(muestra, parametros_laboratorio)
            )
    return muestras_traducidas


def obten_incertidumbre(parametro: str,
                        dict_incertidumbre: dict,
                        valor: float):
    if (isinstance(valor, str) and "<" in valor) or valor == 0.0:
        return None
    elif isinstance(valor, str):
        return
    if parametro in dict_incertidumbre:
        for rango_incert, valor_incert in dict_incertidumbre[parametro].items():
            if "<" in rango_incert and valor < float(rango_incert.split("<")[1]):
                return valor_incert
            elif "≤" in rango_incert and valor <= float(rango_incert.split("≤")[1]):
                return valor_incert
            elif "≥" in rango_incert and valor >= float(rango_incert.split("≥")[1]):
                return valor_incert
            elif ">" in rango_incert and valor > float(rango_incert.split(">")[1]):
                return valor_incert
    return None


def valida_muestras(diccionario: dict):
    """validado significa:
    - 1. Muestra ya subida a la BBDD con todos los parámetros iguales a los del
         laboratorio o bien sin datos del laboratorio (in situ)
    - 2. Muestra subida a la BBDD con algún dato pendiente en el laboratorio
    - 3. Muestras con valores discrepantes entre BBDD y laboratorio
    """
    for muestra, parametros in diccionario.items():
        validado = 1
        for nombre, valores in parametros.items():
            # descartamos el parámetro "nueva"
            if isinstance(valores, int) or validado == 3:
                continue
            for elemento in valores.values():
                # descartamos los parámetros id_censo e id_inspeccion
                if isinstance(elemento, int):
                    continue
                if elemento[1] == None and elemento[0] != None:
                    pass
                elif elemento[0] == elemento[1]:
                    pass
                elif elemento[1] != None and elemento[0] == None:
                    validado = 2
                elif elemento[0] != elemento[1]:
                    validado = 3
                    break
        diccionario[muestra].update({"validado": validado})
    return diccionario


@app.route("/laboratorio")
@logeado
def laboratorio(usuario):
    resultados = { 
                   "pagina": "laboratorio", 
                 }
    return render_template("html/laboratorio/index.html",
                           resultados=resultados)



@app.route("/_compara_muestras", methods=['POST'])
@logeado_AJAX
def _compara_muestras(usuario):
    archivo = request.files.get('archivo')
    if not archivo:
        return jsonify({
            "error": "Erro no ficheiro."
        }), 400
    if not path.exists("./app/static_p/temp/"):
        makedirs("./app/static_p/temp")
    archivo.save("./app/static_p/temp/laboratorio.txt")
    dic_validado = compara_BBDD_laboratorio()
    resultados = { 
                   "pagina": "laboratorio", 
                 }
    
    comparacion =  render_template(
        "html/laboratorio/muestras.html",
        diccionario_validado=dic_validado,
        resultados=resultados
        )
    return jsonify({"comparacion": comparacion})


def compara_BBDD_laboratorio(cod_muestra=None):
    lineas = extrae_lineas("./app/static_p/temp/laboratorio.txt")
    dict_muestras, errores = linea_a_dict(lineas, filtro_muestra=cod_muestra)
    dict_laboratorio = obten_dict_laboratorio()
    parametros_laboratorio = dict_laboratorio['parametros']
    muestras_lab = traduce_muestras(dict_muestras, parametros_laboratorio)
    tupla_cod_muestra = tuple(muestras_lab.keys())
    if len(tupla_cod_muestra) == 1:
        tupla_cod_muestra = str(tupla_cod_muestra).replace(",", "")
    db = get_db()
    cur = db.cursor()
    cur.execute(f"""
        SELECT 
            m.cod_muestra, a.id,
            etiqueta, valor, unidades, incertidumbre
        FROM muestras m
        LEFT JOIN analiticas a ON a.id_muestra = m.id
        WHERE m.cod_muestra in {tupla_cod_muestra}
        ORDER BY cod_muestra DESC, etiqueta
        """)
    muestras_BBDD = cur.fetchall()
    
    diccionario_comparacion = genera_diccionario_comparacion(
        muestras_BBDD, muestras_lab, dict_laboratorio
    )

    diccionario_validado = valida_muestras(diccionario_comparacion)
    return diccionario_validado


def genera_diccionario_comparacion(
        muestras_BBDD: dict,
        muestras_lab: dict,
        dict_laboratorio: dict):
    """
    Dadas las muestras de la BBDD y del laboratorio, genera un diccionario de la forma:
    {cod_muestra: {DBO5: {valor: [None, 25], unidades:["mg/l", "mg/l"], incertidumbre: [0.25, 0.20]}}}
    """
    diccionario_comparacion = {}
    for muestra_BBDD in muestras_BBDD:        
        if not muestra_BBDD['cod_muestra']:
            continue
        cod_muestra = muestra_BBDD['cod_muestra']
        id_analitica = muestra_BBDD['id']
        etiqueta = muestra_BBDD['etiqueta']
        valor = muestra_BBDD['valor']
        unidades = muestra_BBDD['unidades']
        incertidumbre = muestra_BBDD['incertidumbre']
        if isinstance(incertidumbre, str):
            try:
                incertidumbre = float(incertidumbre)
            except:
                incertidumbre = 0
        if cod_muestra not in diccionario_comparacion:
            diccionario_comparacion[cod_muestra] = {}
        if etiqueta not in muestras_lab[cod_muestra]:            
            diccionario_comparacion[cod_muestra].update({
                etiqueta: {
                    "valor": [valor, None],
                    "unidades": [unidades, None],
                    "incertidumbre": [incertidumbre, None]
                }
            })
        else:
            valor_labo = muestras_lab[cod_muestra][etiqueta]
            if not isinstance(valor_labo, float) and "±" in valor_labo:
                valor_labo = float(valor_labo.split("±")[0])
            diccionario_comparacion[cod_muestra].update({
                etiqueta: {
                    "valor": [valor, valor_labo],
                    "unidades": [
                        unidades,
                        dict_laboratorio['unidades'].get(etiqueta)],
                    "incertidumbre": [
                        incertidumbre,
                        obten_incertidumbre(
                            etiqueta,
                            dict_laboratorio['incertidumbre'],
                            muestras_lab[cod_muestra][etiqueta]
                        )
                    ]
                }
            })
            diccionario_comparacion[cod_muestra][etiqueta]['id_analitica'] = id_analitica
    for cod_muestra_lab, parametros_lab in muestras_lab.items():
        if cod_muestra_lab not in diccionario_comparacion:
            diccionario_comparacion[cod_muestra_lab] = {"nueva": 1}
        for parametro_lab, valor_lab in parametros_lab.items():
            if parametro_lab not in diccionario_comparacion[cod_muestra_lab]:
                diccionario_comparacion[cod_muestra_lab].update({
                    parametro_lab: {
                        "valor": [None, valor_lab],
                        "unidades": [
                            None,
                            dict_laboratorio['unidades'].get(parametro_lab)],
                        "incertidumbre": [
                            None,
                            obten_incertidumbre(
                                parametro_lab,
                                dict_laboratorio['incertidumbre'],
                                muestras_lab[cod_muestra_lab][parametro_lab]
                            )
                        ]
                    }
                })
    return diccionario_comparacion


@app.route("/_visor_industria")
@logeado_AJAX
def _visor_industria(usuario):
    cod_muestra = request.args.get('cod_muestra')
    db = get_db()
    cur = db.cursor()
    cur.execute(f"""
        SELECT c.id, c.latitud, c.longitud, c.sistema
        FROM muestras m
        LEFT JOIN inspecciones_ind ii ON ii.id = m.id_inspecciones_ind
        LEFT JOIN censo c ON c.id = ii.id_industria
        WHERE m.cod_muestra = ?
        """, (cod_muestra, ))
    ind = cur.fetchone()
    url = f"censo-{ind['sistema']}-{ind['id']},OpenStreetMap,{ind['latitud']},{ind['longitud']},18"
    url = f"{request.scheme}://{request.host}/{url}"
    return jsonify({"url": url})


@app.route("/_actualiza_muestra", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar a mostra")
@verificaPermiso('admin', 2)
def _actualiza_muestra(usuario):
    cod_muestra = request.form.get('cod_muestra')
    db = get_db()
    cur = db.cursor()
    VALIDA_ELEMENTO = ["valor", "unidades", "incertidumbre"]
    
    diccionario_validado = compara_BBDD_laboratorio(cod_muestra=cod_muestra)
    cambios = 0
    dic_nuevas = {}
    for muestra, parametros in diccionario_validado.items():
        if parametros['validado'] != 2:
            continue
        if "nueva" in parametros:
            continue
        for etiqueta, valores in parametros.items():
            if etiqueta in ["validado", "id_analitica"]:
                    continue
            for nombre, elemento in valores.items():
                if nombre == "id_analitica":
                    continue
                if nombre not in VALIDA_ELEMENTO:
                    return jsonify({
                        "error": 
                        "Erro determinando os parámetros a actualizar."}), 400
                if elemento[1] == None and elemento[0] != None:
                    pass
                elif elemento[0] == elemento[1]:
                    pass
                elif elemento[1] != None and elemento[0] == None:
                    if valores.get('id_analitica'):
                        id_analitica = valores['id_analitica']
                        cur.execute(f"""
                            UPDATE analiticas
                            SET {nombre} = ?
                            WHERE id = ?
                            """, (elemento[1], id_analitica))
                        logCambios(
                            session['username'],
                            "analiticas",
                            id_analitica,
                            "edita_analitica",
                            json.dumps(diccionario_validado, ensure_ascii=False),
                            ""
                        )
                        cambios = 1
                    else:
                        if not dic_nuevas.get(muestra):
                            dic_nuevas[muestra] = {etiqueta: {}}
                        if not dic_nuevas.get(muestra).get(etiqueta):
                            dic_nuevas[muestra].update({etiqueta: {}})
                        par_nombre_valor = {nombre: elemento[1]}
                        dic_nuevas[muestra][etiqueta].update(par_nombre_valor)
    for cod_muestra, parametros in dic_nuevas.items():
        cur.execute("""
            SELECT id
            FROM muestras
            WHERE cod_muestra = ?
            """, (cod_muestra,))
        id_muestra = cur.fetchone()['id']
        for etiqueta, valores in parametros.items():
            valor = valores.get('valor')
            unidades = valores.get('unidades')
            incertidumbre = valores.get('incertidumbre')
            cur.execute(f"""
                INSERT INTO analiticas
                (id_muestra, valor, etiqueta, unidades, incertidumbre)
                VALUES (?, ?, ?, ?, ?)
                """, (id_muestra, valor, etiqueta, unidades, incertidumbre))
        logCambios(
            session['username'],
            "analiticas",
            id_muestra,
            "inserta_analiticas",
            json.dumps(dic_nuevas, ensure_ascii=False),
            ""
        )
        cambios = 1
    db.commit()
    return jsonify({"cambios": cambios})
