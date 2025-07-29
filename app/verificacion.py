# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, session, jsonify, send_file
from app import app
from datetime import datetime
from urllib.parse import unquote_plus
import json

from app.auxiliar import get_db, log, logCambios, verificarPermiso, logeado, logeado_AJAX, tokenCSRF, obten_columnas, interpola, compruebaFloat

@app.route('/verificaciones')
@logeado
def verificaciones(usuario):
    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return redirect('/')

    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT v.*, s.codigo FROM verificaciones v LEFT JOIN sondas s ON s.id = v.id_sonda ORDER BY v.id DESC')
    verificaciones = cur.fetchall()
    verificaciones_preparadas = []
    for verificacion in verificaciones:
        verificaciones_preparadas.append(prepara_verificacion(verificacion, None, None)[0])

    cur.execute('SELECT a.*, s.codigo FROM ajustes a LEFT JOIN sondas s ON s.id = a.id_sonda ORDER BY a.id DESC')
    ajustes = cur.fetchall()
    ajustes_preparados = []
    for ajuste in ajustes:
        ajustes_preparados.append(prepara_ajuste(ajuste, None, None)[0])

    resultados = {"pagina": "verificaciones",
                  "ambito": session['ambito'],
                  "usuario": session['username'],
                  'token': session['TOKEN'],
                  "permiso": session['permiso'],
                  "diestro": session['diestro'],
                  "titulo": "Verificacións",
                  "menu": "html/menu_lateral.html",
                  "host": request.host
    }

    return render_template('/html/lista_verificaciones.html',
                            resultados=resultados,
                            verificaciones=verificaciones_preparadas,
                            ajustes=ajustes_preparados)

@app.route('/descargar_verificacion-<id_verificacion>')
@logeado_AJAX
def descargar_verificacion(usuario, id_verificacion):

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return redirect('/')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT v.id, v.fecha_fin, s.codigo FROM verificaciones v INNER JOIN sondas s ON s.id = v.id_sonda WHERE v.id = ?", (id_verificacion,))
    verificacion = cur.fetchone()
    fecha_fin = datetime.fromtimestamp(verificacion['fecha_fin']).strftime("%Y%m%d")
    archivo = fecha_fin + "_" + verificacion['codigo'] + "_v" + str(verificacion['id']) + ".html"
    return send_file("static_p/verificaciones/" + archivo)

@app.route('/descargar_axuste-<id_ajuste>')
@logeado_AJAX
def descargar_ajuste(usuario, id_ajuste):

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return redirect('/')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT a.id, a.fecha_fin, s.codigo FROM ajustes a INNER JOIN sondas s ON s.id = a.id_sonda WHERE a.id = ?", (id_ajuste,))
    ajuste = cur.fetchone()
    fecha_fin = datetime.fromtimestamp(ajuste['fecha_fin']).strftime("%Y%m%d")
    archivo = fecha_fin + "_" + ajuste['codigo'] + "_a" + str(ajuste['id']) + ".html"
    return send_file("static_p/verificaciones/" + archivo)

@app.route('/verificacion-<id_verificacion>')
@app.route('/verificacion-<id_verificacion>-<imprimir>')
@logeado
def pag_verificacion(usuario, id_verificacion, imprimir=None, archivo=None):
    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return redirect('/')

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM verificaciones WHERE id = ?", (id_verificacion,))
    verificacion = cur.fetchone()

    if not imprimir:
        plantilla = "/html/verificacion.html"
        cur.execute("""
            SELECT *
            FROM patrones
            WHERE fecha_retirada is null
            ORDER BY verificacion DESC, parametro ASC
            """)
    else:
        plantilla = "/html/imprimir/verificacion_imprimir.html"
        id_patron_1 = verificacion["id_patron_1"]
        id_patron_2 = verificacion["id_patron_2"]
        if id_patron_1:
            SQL_string = f"WHERE id in ({id_patron_1}, {id_patron_2})"
        else:
            SQL_string = f"WHERE parametro = 'temperatura'"
        cur.execute(f"""
            SELECT *
            FROM patrones
            {SQL_string}
            ORDER BY verificacion DESC, parametro ASC
            """)
    patrones = cur.fetchall()
    patrones = prepara_patrones(patrones)
    cur.execute("SELECT * FROM sondas WHERE en_uso = 1")
    sondas = cur.fetchall()

    if verificacion['fecha_fin']:
        verificacion, sondas = prepara_verificacion(verificacion, patrones, sondas)

    resultados = {"pagina": "verificacion",
                  "ambito": session['ambito'],
                  "usuario": session['username'],
                  'token': session['TOKEN'],
                  "permiso": session['permiso'],
                  "diestro": session['diestro'],
                  "titulo": "Verificación",
                  "archivo": "pdf" if archivo else "web",
                  "ruta_static": "../../static" if archivo else "./static",
                  "menu": "html/menu_lateral_verificacion.html"
    }

    if archivo:
        return [render_template(plantilla, resultados=resultados, patrones=patrones, verificacion=verificacion, sondas=sondas), verificacion["comprobacion"]]
    return render_template(plantilla,
                            resultados=resultados,
                            patrones=patrones,
                            verificacion=verificacion,
                            sondas=sondas)

@app.route('/axuste-<id_ajuste>')
@app.route('/axuste-<id_ajuste>-<imprimir>')
@logeado
def pag_ajuste(usuario, id_ajuste, imprimir=None, archivo=None):
    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return redirect('/')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM patrones WHERE fecha_retirada is null ORDER BY verificacion ASC, parametro ASC")
    patrones = cur.fetchall()
    patrones = prepara_patrones(patrones)

    cur.execute("SELECT * FROM sondas WHERE en_uso = 1 AND parametro NOT LIKE '%temperatura%'")
    sondas = cur.fetchall()

    cur.execute("SELECT * FROM ajustes WHERE id = ?", (id_ajuste,))
    ajuste = cur.fetchone()

    ajuste, sondas = prepara_ajuste(ajuste, patrones, sondas)
    resultados = {"pagina": "ajuste",
                  "ambito": session['ambito'],
                  "usuario": session['username'],
                  'token': session['TOKEN'],
                  "permiso": session['permiso'],
                  "diestro": session['diestro'],
                  "titulo": "Axuste",
                  "archivo": "pdf" if archivo else "web",
                  "ruta_static": "../../static" if archivo else "./static",
                  "menu": "html/menu_lateral_verificacion.html"
    }
    if not imprimir:
        plantilla = "/html/ajuste.html"
    else:
        plantilla = "/html/imprimir/ajuste_imprimir.html"
    if archivo:
        return [render_template(plantilla, resultados=resultados, patrones=patrones, ajuste=ajuste, sondas=sondas), ajuste['comprobacion']]
    return render_template(plantilla,
                            resultados=resultados,
                            patrones=patrones,
                            ajuste=ajuste,
                            sondas=sondas)

def prepara_verificacion(verificacion, patrones, sondas):
    verificacion = sqliteRow2list_dict([verificacion])[0]
    try:
        verificacion['fecha_inicio'] = datetime.fromtimestamp(verificacion['fecha_inicio']).strftime("%d/%m/%Y %H:%M")
    except:
        pass
    try:
        verificacion['fecha_fin'] = datetime.fromtimestamp(verificacion['fecha_fin']).strftime("%d/%m/%Y %H:%M")
    except:
        pass
    if sondas:
        sondas = sqliteRow2list_dict(sondas)
        datos_sonda = {}
        for sonda in sondas:
            if sonda['id'] == verificacion['id_sonda']:
                datos_sonda = sonda
        comprobacion = comprueba_patrones_verificacion(verificacion, patrones, datos_sonda)
        verificacion.update({"comprobacion": comprobacion})
    return verificacion, sondas

def prepara_ajuste(ajuste, patrones, sondas):
    ajuste = sqliteRow2list_dict([ajuste])[0]
    try:
        ajuste['fecha_inicio'] = datetime.fromtimestamp(ajuste['fecha_inicio']).strftime("%d/%m/%Y %H:%M")
    except:
        pass
    if ajuste['resultado']:
        ajuste['resultado'] = json.loads(ajuste['resultado'])
    else:
        ajuste['resultado'] = {}
    try:
        ajuste['id_patrones'] = lista_string_2_int(ajuste['id_patrones'].split("|"))
    except:
        ajuste['id_patrones'] = []
    if sondas:
        sondas = sqliteRow2list_dict(sondas)
        datos_sonda = {}
        for sonda in sondas:
            if sonda['id'] == ajuste['id_sonda']:
                datos_sonda = sonda
            sonda['requisitos_ajuste'] = json.loads(sonda['requisitos_ajuste'])
        try:
            ajuste['fecha_fin'] = datetime.fromtimestamp(ajuste['fecha_fin']).strftime("%d/%m/%Y %H:%M")
            comprobacion = comprueba_patrones_ajuste(ajuste, patrones, datos_sonda)
            ajuste.update({"comprobacion": comprobacion})
        except:
            pass

    return ajuste, sondas

def prepara_patrones(patrones):
    patrones = sqliteRow2list_dict(patrones)
    hoy = int(datetime.now().timestamp())
    for patron in patrones:
        if patron['caducidad'] < hoy:
            patron['caducado'] = 1
        elif (patron['caducidad'] - 15*3600*24) < hoy:
            patron['caducado'] = 2
        else:
            patron['caducado'] = 0
        patron['caducidad'] = datetime.fromtimestamp(patron['caducidad']).strftime("%d/%m/%Y")

    return patrones

@app.route("/_retirar_patron", methods=["POST"])
@logeado_AJAX
@tokenCSRF('retirar patrón')
def _retirar_patron(usuario):
    id_patron = request.form["id_patron"]
    hoy = int(datetime.now().timestamp())

    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE patrones SET fecha_retirada = ? WHERE id = ?', (hoy, id_patron))
    db.commit()

    logCambios(usuario, 'Patrón', id_patron, 'Retirada', '', '')
    return jsonify({})

def sqliteRow2list_dict(sqliteRow):
    """Toma una lista de sqliteRows (resultado de un fetchall) y lo convierte
    a una lista de diccionarios de python.
    """
    resultado = []
    for elemento in sqliteRow:
        subresultado = {}
        for key in elemento.keys():
            subresultado.update({key:elemento[key]})
        resultado.append(subresultado)
    return resultado

@app.route("/_nueva_verificacion", methods=["POST"])
@logeado_AJAX
def _nueva_verificacion(usuario):
    TOKEN_form = request.form["token"]
    ajuste = request.form["ajuste"]

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para facer verificacións."}), 403
    if TOKEN_form != session['TOKEN']:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "[CSRF] Erro creando a verificación. Recargue a páxina e inténteo de novo"}), 403
    db = get_db()
    cur = db.cursor()
    fecha_inicio = int(datetime.now().timestamp())
    tipo_verificacion = {"0": ["verificaciones", "verificacion"], "1": ["ajustes", "axuste"]}
    cur.execute("INSERT INTO {} (inspector, fecha_inicio) VALUES (?, ?)".format(tipo_verificacion[ajuste][0]), (session['username'], fecha_inicio))
    id_verificacion = cur.lastrowid
    db.commit()
    url = "/{}-{}".format(tipo_verificacion[ajuste][1], str(id_verificacion))
    fecha = datetime.fromtimestamp(fecha_inicio).strftime("%d/%m/%Y %H:%M")
    logCambios(usuario, "Verificacion", id_verificacion, "creada", "", "")
    return jsonify({'url': url, "id_verificacion": id_verificacion, "fecha": fecha})

@app.route("/_eliminar_verificacion", methods=["POST"])
@logeado_AJAX
def _eliminar_verificacion(usuario):
    id_verificacion = request.form["id_verificacion"]
    es_ajuste = request.form["es_ajuste"]
    TOKEN_form = request.form["token"]

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para eliminar a verificacion."}), 403
    if TOKEN_form != session['TOKEN']:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "[CSRF] Erro eliminando a verificación. Recargue a páxina e inténteo de novo"}), 403
    tabla = "verificaciones"
    if es_ajuste != "0":
        tabla = "ajustes"
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM {} WHERE id = ?".format(tabla), (id_verificacion,))
    db.commit()

    logCambios(usuario, tabla, id_verificacion, "eliminada", "", "")
    return jsonify({})

@app.route("/_actualiza_verificacion", methods=["POST"])
@logeado_AJAX
def _actualiza_verificacion(usuario):
    id_verificacion = request.form["id_verificacion"]
    valores = request.form["valores"]
    es_ajuste = int(request.form["es_ajuste"])
    finalizar = int(request.form["finalizar"])
    TOKEN_form = request.form["token"]

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para facer a verificacion."}), 403
    if TOKEN_form != session['TOKEN']:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "[CSRF] Erro actualizando os datos da verificación. Recargue a páxina e inténteo de novo"}), 403
    if valores == "":
        return jsonify({"codigo": -3, "error": "Faltan datos"}), 400
    campos_javascript = ["id"]
    diccionario = {}
    diccionario_requisitos = {}
    for par in valores.split("&"):
        clave, valor = par.split("=")
        valor = unquote_plus(valor)
        clave = unquote_plus(clave)
        if clave in campos_javascript or any(elem in valor for elem in "(){}$%&#@!'\""):
            log(usuario, request.url, 0)
            return jsonify({"codigo": -2, "error": "Os campos non poden ter caracteres especiais: (){}$%&#@!'\". Revise os campos e inténteo de novo"}), 403
        if len(clave.split("requisitosæ")) > 1:
            if valor:
                diccionario_requisitos.update({clave.split("requisitosæ")[1]: float(valor)})
        else:
            diccionario.update({clave: valor})
    db = get_db()
    cur = db.cursor()

    if diccionario.get("id_patron_1") == diccionario.get("id_patron_2")\
            and not es_ajuste\
            and not (
                compruebaFloat(diccionario.get("medicion_patron1")) and
                compruebaFloat(diccionario.get("medicion_patron2"))
                ):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -6, "error": "Os patróns deben ser distintos. Revise os patróns e inténteo de novo"}), 400

    if diccionario_requisitos:
        diccionario.update({"resultado": json.dumps(diccionario_requisitos, ensure_ascii=False)})

    tablas = {0: ["verificaciones", "verificacion"], 1: ["ajustes", "axuste"]}

    SQL_string = ""
    if diccionario:
        SQL_string = "UPDATE {} SET".format(tablas[es_ajuste][0])
        columnas = obten_columnas(cur, tablas[es_ajuste][0])
        lista_valores = []
        for key in diccionario:
            if key in ["id"]:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -4, "error": "Erro actualizando os datos da verificación. Recargue a páxina e inténteo de novo"}), 400
            if key not in columnas:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -5, "error": "Erro actualizando os datos da verificación. Recargue a páxina e inténteo de novo"}), 400
            SQL_string += " {} = ?,".format(key)
            lista_valores.append(diccionario[key])


        lista_valores.append(id_verificacion)

    resultado = {}
    if finalizar:
        cur.execute("SELECT codigo FROM sondas WHERE id = ?", (diccionario['id_sonda'],))
        datos_sonda = cur.fetchone()
        fecha_fin = int(datetime.now().timestamp())
        SQL_string += " fecha_fin = {} ".format(fecha_fin)

    SQL_string = SQL_string[:-1] + " WHERE id = ?"
    if diccionario:
        cur.execute(SQL_string, tuple(lista_valores))

    db.commit()

    if finalizar:
        url = "/{}-".format(tablas[es_ajuste][1]) + str(id_verificacion)+ "-imprimir"
        resultado.update({"codigo":1, "permiso": session['permiso'], "url": url})

        fecha = datetime.fromtimestamp(fecha_fin).strftime("%Y%m%d")
        f = open("app/static_p/verificaciones/" + fecha[:8] + "_" + datos_sonda['codigo'] + "_" + tablas[es_ajuste][0][0:1] + str(id_verificacion) +".html", "w", encoding='utf8')

        try:
            valido = 1
            if not es_ajuste:
                pagina, comprobacion = pag_verificacion(id_verificacion=id_verificacion, imprimir=1, archivo=1)
                if comprobacion.get('patron_1').get('valido') == 0 or comprobacion.get('patron_2').get('valido') == 0:
                    valido = 0
            elif es_ajuste:
                pagina, comprobacion = pag_ajuste(id_ajuste=id_verificacion, imprimir=1, archivo=1)
                if comprobacion.get('valido') == 0:
                    valido = 0

            f.write(pagina)
            resultado.update({'valido': valido})
        except Exception as e:
            cur.execute("UPDATE verificaciones SET fecha_fin = null WHERE id = ?", (id_verificacion,))
            db.commit()
            log(usuario, request.url, 0)
            return jsonify({"codigo": -2, "error": "Erro verificando. Comprobe que están cubertos todos os datos (sonda, patróns, medicións, etc.) e inténteo de novo."}), 400

        f.close()

    logCambios(usuario, tablas[es_ajuste][1], id_verificacion, "actualizaVerificacion", valores, "")

    return jsonify(resultado)

def comprueba_patrones_verificacion(diccionario, valores_patrones, datos_sonda):
    incertidumbre = datos_sonda['incertidumbre']
    porcentual = datos_sonda['incertidumbre_porcentual']
    comprobacion = {"patron_1": {"valido": 0, "diferencia": 0, "valor_patron_interpolado": 0}, "patron_2": {"valido": 0, "diferencia": 0, "valor_patron_interpolado": 0}}
    #para el caso de verificación de temperatura, sacamos el valor del patrón
    #de la medición hecha en la verificación.
    if "temperatura" in diccionario['parametro']: 
        valores_patrones = []
        for i in ["1", "2"]:
            diccionario['id_patron_' + i] = i
            valores_patrones.append({
                "id": int(i),
                "valor": diccionario['medicion_patron' + i]
                })
    for valor_patron in valores_patrones:
        for i in ["1", "2"]:
            if valor_patron['id'] == int(diccionario['id_patron_' + i]):
                valor_patron_interpolado = interpola_patron(
                    valor_patron['valor'],
                    diccionario.get('temperatura_' + i)
                    )
                comprobacion['patron_'+i]['valor_patron_interpolado'] = round(valor_patron_interpolado, 2)
                comprobacion['patron_'+i]['diferencia'] = round(abs(valor_patron_interpolado - float(diccionario['medicion_'+i])) *(1-porcentual) + abs(valor_patron_interpolado - float(diccionario['medicion_'+i])) * (100*porcentual/valor_patron_interpolado), 2)
                comprobacion['patron_'+i]['incertidumbre_porcentual'] = porcentual
                if comprobacion['patron_'+i]['diferencia'] < (incertidumbre*100*porcentual) + (incertidumbre * (1 - porcentual)):
                    comprobacion['patron_'+i]['valido'] = 1

    return comprobacion

def comprueba_patrones_ajuste(diccionario, valores_patrones, datos_sonda):
    comprobacion = {}
    valido = 1
    for requisito in datos_sonda['requisitos_ajuste'].keys():
        if requisito == "n_patrons":
            continue

        if diccionario['resultado'][requisito] > datos_sonda['requisitos_ajuste'][requisito][0] and diccionario['resultado'][requisito] < datos_sonda['requisitos_ajuste'][requisito][1]:
            comprobacion.update({requisito: 1})
        else:
            comprobacion.update({requisito: 0})
            valido = 0
    comprobacion.update({"valido": valido})
    return comprobacion

def interpola_patron(valor_patron, temperatura):
    try:
        return float(valor_patron)
    except:
        return busca_cercano(valor_patron, temperatura)

def busca_cercano(diccionario, clave):
    diccionario = json.loads(diccionario)
    if diccionario.get(clave):
        return diccionario[clave]
    previo = -1
    for key in diccionario:
        if float(key) > float(clave):
            siguiente = key
            break
        else:
            previo = key
    resultado = interpola(float(previo), diccionario[previo], float(siguiente), diccionario[siguiente], float(clave))
    return resultado

def lista_string_2_int(lista):
    resultado = []
    for elemento in lista:
        try:
            resultado.append(int(elemento))
        except:
            pass
    return resultado
