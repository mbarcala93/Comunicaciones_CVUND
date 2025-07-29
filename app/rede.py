# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request, session, jsonify
from app import app
from os import path, remove, makedirs, getcwd
from urllib.parse import unquote_plus
from datetime import datetime
from base64 import b64decode
from app.auxiliar import get_db, log, logCambios, compruebaFloat, logeado, logeado_AJAX, tokenCSRF, verificarPermiso, remote_ip, Configuracion, obtener_capas_geoJSON
from app.mareas import obtenMarea
import ast

@app.route('/rede-<cod_edar>-<globo_abierto>,<capa_base>,<latitud>,<longitud>,<zoom>')
@app.route('/rede-<cod_edar>')
@logeado
def red(cod_edar, usuario, globo_abierto=None, capa_base='OpenStreetMap', latitud=None, longitud=None, zoom=None):
    if not verificarPermiso(session, cod_edar, 0):
        log(usuario, request.url, 0)
        return redirect('/rede-' + session['ambito'].split("|")[0])
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT c.geometria, e.provincia, e.latitud, e.longitud FROM concellos c INNER JOIN edar e ON e.provincia||e.municipio = c.cod_ine WHERE e.cod_edar = ?', (cod_edar,))
    concello = cur.fetchone()
    cur.execute('SELECT id, geometria, prioridad, tipo_elemento, tipo_agua_residual FROM elementos WHERE cod_edar = ?', (cod_edar,))
    elementos = cur.fetchall()
    geoJSON = obtener_capas_geoJSON(cod_edar)
    mareas = {}
    if session['mareas']:
        try:
            mareas = obtenMarea([concello['latitud'], concello['longitud']])
        except:
            pass
    resultados = { "mapa": 'red',
                   "cod_edar": cod_edar,
                   "url": request.path,
                   "globo_abierto": globo_abierto,
                   "capa_base": capa_base,
                   "latitud": latitud,
                   "longitud": longitud,
                   "zoom": zoom,
                   "ambito": session['ambito'],
                   "usuario": session['username'],
                   'token': session['TOKEN'],
                   "permiso": session['permiso'],
                   "diestro": session['diestro'],
                   "titulo": "Inspección de redes",
                   "menu": "html/menu_lateral_visor.html"
                 }
    return render_template("html/visor.html", resultados=resultados, elementos=elementos, geoJSON=geoJSON, concello=concello, mareas=mareas)

@app.route("/visor")
@app.route("/visor-<argumentos>")
def visor(argumentos=None):
    pagina = "/rede"
    if argumentos:
        pagina = "/rede-" + argumentos
    resultados = {"error": "404",
                  "texto": "Páxina non atopada",
                  "permiso": 0,
                  "recomendacion": "Debido á inclusión da función de censo, a páxina /visor pasa a chamarse /rede."
                  }
    return render_template('html/error.html', resultados=resultados, pagina=pagina)

@app.route("/_crea_elemento", methods=['POST'])
@logeado_AJAX
@tokenCSRF('crear o elemento')
def _crea_elemento(usuario):
    """Recibe datos de lat, long y cod_edar desde el servidor y crea un
    elemento en la BBDD.
    """
    lat = request.form["lat"]
    lon = request.form["lon"]
    cod_edar = request.form["cod_edar"]
    if not verificarPermiso(session, cod_edar, 1):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "error": "Non ten permisos para crear un elemento."}), 403
    if not compruebaFloat(lat) or not compruebaFloat(lon):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "error": "Erro nas coordenadas. Cree un elemento pinchando antes no mapa"}), 400
    """Crea elemento y la primera inspección
    """
    geometria = str([float(lat), float(lon)])
    db = get_db()
    cur = db.cursor()
    ahora = datetime.now()
    hora = ahora.strftime("%H:%M")
    fecha = ahora.strftime("%Y%m%d")
    SQL = 'INSERT INTO elementos (cod_edar, geometria, inspector, fecha, permiso) VALUES (?, ?, ?, ?, ?)'
    tupla_filtro = (cod_edar, geometria, usuario, fecha, 1)
    cur.execute(SQL, tupla_filtro)
    ultimo_id_elem = cur.lastrowid
    logCambios(usuario, "Elemento", ultimo_id_elem, "creado", "", geometria)
    cur.execute("INSERT INTO inspecciones (id_elemento, fecha, hora, inspector) VALUES (?, ?, ?, ?)", (ultimo_id_elem, fecha, hora, usuario))
    ultimo_id_insp = cur.lastrowid
    db.commit()
    logCambios(usuario, "Inspección", ultimo_id_insp, "creado", "", geometria)
    plantilla = "html/fichas/ficha_nuevo_elemento.html"
    datos_elemento = {"id": ultimo_id_elem}
    inspeccion = {"id": ultimo_id_insp}
    rendered = render_template(plantilla, elemento=datos_elemento, inspeccion=inspeccion)
    resultado = {"exito":1,
                "id_elem": ultimo_id_elem,
                "id_insp": ultimo_id_insp,
                "permiso": session['permiso'],
                "ficha_renderizada": rendered
                }
    return jsonify(resultado), 201

@app.route('/_nueva_inspeccion', methods=["POST"])
@logeado_AJAX
@tokenCSRF('crear a inspección')
def _nueva_inspeccion_elem(usuario):
    id_elem = request.form["id_elem"]
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT cod_edar, geometria FROM elementos WHERE id = ?", (id_elem,))
    cod_edar, geometria = cur.fetchone()
    if not verificarPermiso(session, cod_edar, 1):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "error": "Non ten permisos para crear unha inspección."}), 403
    ahora = datetime.now()
    hora = ahora.strftime("%H:%M")
    fecha = ahora.strftime("%Y%m%d")
    cur.execute("INSERT INTO inspecciones (id_elemento, fecha, hora, inspector) VALUES (?, ?, ?, ?)", (id_elem, fecha, hora, usuario))
    ultimo_id_insp = cur.lastrowid
    db.commit()
    logCambios(usuario, "Inspección", ultimo_id_insp, "creado", "", geometria)
    resultado = {"exito": 1, "id_insp": ultimo_id_insp, "fecha": fecha, "hora": hora}
    return jsonify(resultado), 201

@app.route('/_muestra_ficha_elemento')
@logeado_AJAX
@tokenCSRF('mostrar a ficha do elemento')
def _muestra_ficha_elemento(usuario):
    id = request.args.get("id")
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT e.*, f.ruta FROM elementos e LEFT JOIN fotos f ON e.foto_principal = f.id WHERE e.id = ?", (id, ))
    datos_elemento = cur.fetchone()
    cur.execute("SELECT id, fecha, hora FROM inspecciones WHERE id_elemento = ?", (id,))
    inspecciones = cur.fetchall()

    if not verificarPermiso(session, datos_elemento['cod_edar'], 0):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "error": "Non ten permisos para ver a ficha do elemento."}), 403

    resultados = {"id": id,
                  "permiso": session["permiso"],
                  "ficha": "elemento"
                  }
    plantilla = "html/fichas/ficha_elemento.html"
    rendered = render_template(plantilla, elemento=datos_elemento, resultados=resultados, inspecciones=inspecciones)
    return jsonify({"valor":rendered})

@app.route('/_muestra_ficha_inspeccion')
@logeado_AJAX
@tokenCSRF('mostrar a ficha da inpsección')
def _muestra_ficha_inspeccion(usuario):
    todas = request.args.get("todas")
    id = request.args.get("id")
    db = get_db()
    cur = db.cursor()
    lista_id = {"0":"i.id", "1": "id_elemento"}
    cur.execute("SELECT i.*, e.cod_edar, f.ruta FROM inspecciones i INNER JOIN elementos e ON i.id_elemento = e.id LEFT JOIN fotos f ON f.id = i.foto_principal WHERE {} = ? ORDER BY i.id DESC".format(lista_id[todas]), (id,))
    inspecciones = cur.fetchall()

    if not verificarPermiso(session, inspecciones[0]['cod_edar'], 0):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "error": "Non ten permisos para ver a ficha da inspección."}), 403

    lista_inspecciones = []
    lista_interrogantes = ""
    for inspeccion in inspecciones:
        lista_inspecciones.append(inspeccion['id'])
        lista_interrogantes += "?,"
    cur.execute("SELECT * FROM mediciones WHERE id_inspeccion in ({})".format(lista_interrogantes[:-1]), tuple(lista_inspecciones) )
    mediciones = cur.fetchall()
    cur.execute("SELECT id, etiqueta, ruta FROM fotos WHERE id_tabla in ({}) AND tabla = 'red'".format(lista_interrogantes[:-1]), tuple(lista_inspecciones) )
    fotos = cur.fetchall()

    resultados = {"id": id,
                  "permiso": session["permiso"],
                  "ficha": "inspeccion"
                  }
    plantilla = "html/fichas/ficha_inspeccion.html"
    rendered = ""
    for inspeccion in inspecciones:
        rendered += render_template(plantilla, elemento=inspeccion, resultados=resultados, mediciones=mediciones, fotos=fotos)
    return jsonify({"valor":rendered})

@app.route('/_actualiza_elem', methods=['POST'])
@logeado_AJAX
@tokenCSRF('actualizar os datos do elemento')
def _actualiza_elem(usuario):
    elemento = request.form["elemento"]
    id = request.form["id"]
    valores = request.form["valores"]
    resultado = {}
    """Creamos un diccionario vacío y lo llenamos con los pares clave-valor que
    vienen serializados del cliente. Cuando se trata de una medición, lo metemos
	en un diccionario aparte."""
    diccionario = {}
    diccionario_mediciones = {}

    for par in valores.split("&"):
        clave, valor = par.split("=")
        valor = unquote_plus(valor)
        if clave[0:8] == 'medicion':
            diccionario_mediciones.update({unquote_plus(clave[8:]): valor})
        else:
            diccionario.update({clave: valor})

    """Para evitar SQL injection buscamos los nombres de columna en la BBDD y
    comprobamos que cada key enviado por el cliente existe. Construimos la
    consulta SQL con las claves, y una lista de valores, para meter como tupla
    """
    db = get_db()
    cur = db.cursor()
    if elemento == "elementos":
        cur.execute("SELECT *, 'None' as hora FROM elementos WHERE id = ?", (id,))
        SQL_string = "UPDATE elementos SET"
    elif elemento == "inspecciones":
        cur.execute("SELECT i.*, e.cod_edar, e.geometria, 'None' as tipo_agua_residual FROM inspecciones i LEFT JOIN elementos e ON i.id_elemento = e.id WHERE i.id = ?", (id,))
        SQL_string = "UPDATE inspecciones SET"
    datos = cur.fetchone()

    datos_popUp = {"tipo_agua_residual": datos['tipo_agua_residual'], "fecha": datos['fecha'], "hora": datos['hora']}

    geometria = datos['geometria']
    if not verificarPermiso(session, datos['cod_edar'], 1):
        log(usuario, request.url, 0, elemento)
        return jsonify({"exito": -4, "error": "Non ten permisos para actualizar os datos."}), 403
    if diccionario:
        columnas = datos.keys()
        lista_valores = []
        for key in diccionario:
            if key in ["id", "permiso", "geometria", "cod_edar"]:
                log(usuario, request.url, 0)
                return jsonify({"exito":-3, "error": "Hai datos no listado que non se poden actualizar."}), 400
            if key not in columnas:
                log(usuario, request.url, 0)
                return jsonify({"exito":-3, "error": "Hai datos no listado que non se poden actualizar."}), 400
            if key in datos_popUp:
                datos_popUp[key] = diccionario[key]
            SQL_string += " {} = ?,".format(key)
            lista_valores.append(diccionario[key])
        SQL_string = SQL_string[:-1] + " WHERE id = ?"
        lista_valores.append(id)
        cur.execute(SQL_string, tuple(lista_valores))

    """Las mediciones tienen un tratamiento aparte. Con su diccionario creamos 1
    diccionario con 2 diccionarios (nueva y existente) con tuplas de valor,
    etiqueta y unidades	para cada medición.
    """
    if diccionario_mediciones:
        elementos_medicion = {"valor":1, "etiqueta": 2, "unidades": 3}
        dic_mediciones_individuales = {"nueva": {}, "existente": {}}
        for elemento1 in diccionario_mediciones:
            nueva, numMedicion, tipo_elemento = elemento1.split("|")
            if not dic_mediciones_individuales[nueva].get(numMedicion):
                dic_mediciones_individuales[nueva][numMedicion] = [id, "", "", ""]
            dic_mediciones_individuales[nueva][numMedicion][elementos_medicion[tipo_elemento]] = diccionario_mediciones[elemento1]
        lista_mediciones = []

        for medicion in dic_mediciones_individuales['nueva']:
            lista_mediciones.append(tuple(dic_mediciones_individuales['nueva'][medicion]))
        cur.executemany("INSERT INTO mediciones (id_inspeccion, valor, etiqueta, unidades) VALUES (?, ?, ?, ?)", lista_mediciones)
        lista_mediciones = []

        for medicion in dic_mediciones_individuales['existente']:
            cur.execute("SELECT id_inspeccion FROM mediciones WHERE id = ?", (medicion,))
            if int(id) != cur.fetchone()['id_inspeccion']:
                log(usuario, request.url, 0)
                return jsonify({"exito":-4, "error": "Imposible gardar o dato de medición."}), 400
            SQL_string = "UPDATE mediciones SET"
            lista_valores = []
            for elemento_medicion in elementos_medicion:
                if dic_mediciones_individuales['existente'][medicion][elementos_medicion[elemento_medicion]]:
                    SQL_string += " {} = ?,".format(elemento_medicion)
                    lista_valores.append(dic_mediciones_individuales['existente'][medicion][elementos_medicion[elemento_medicion]])
            SQL_string = SQL_string[:-1] + " WHERE id = ?"
            lista_valores.append(medicion)
            cur.execute(SQL_string, tuple(lista_valores))

    db.commit()
    logCambios(usuario, elemento, id, "actualizaFicha", valores, geometria)
    resultado.update({"exito":1, "datos_popUp": datos_popUp})
    return jsonify(resultado)

@app.route("/_subir_foto", methods=['POST'])
@logeado_AJAX
@tokenCSRF('subir a foto')
def subir_foto(usuario):
    foto = request.form["foto"]
    id_inspeccion = request.form["id"]
    etiqueta = request.form["etiqueta"]
    if any(elem in etiqueta for elem in "();$%&#@!"):
        log(usuario, request.url, 0)
        return jsonify({"exito": -3, "error": "A etiqueta non pode ter caracteres especiais. Cambie a etiqueta e inténteo de novo"}), 400
    resultado = {}
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT i.foto_principal, e.foto_principal, e.id, e.cod_edar, e.geometria FROM inspecciones i LEFT JOIN elementos e ON i.id_elemento = e.id WHERE i.id = ?", (id_inspeccion,))
    i_principal, e_principal, id_elemento, cod_edar, geometria = cur.fetchone()
    if not verificarPermiso(session, cod_edar, 1):
        log(usuario, request.url, 0)
        return jsonify({"exito":-1, "error": "Non ten permisos para subir a foto."}), 403
    if len(foto) > 1000:
        fecha = datetime.now().strftime("%Y%m%d_%H%M_%S_%f")
        ruta =  fecha + "_" + cod_edar + "_" + id_inspeccion + ".jpg"
        if not path.exists(Configuracion.ruta_app + 'static_p/fotos'):
            makedirs(Configuracion.ruta_app + 'static_p/fotos')
        fh = open(Configuracion.ruta_app + "static_p/fotos/"+ ruta, "wb")
        fh.write(b64decode(foto))
        fh.close()
    else:
        log(usuario, request.url, 0)
        return jsonify({"exito":0, "error": "Problema co archivo. Recargue a páxina e inténteo de novo."}),400

    cur.execute('INSERT INTO fotos (id_tabla, ruta, etiqueta, tabla) VALUES (?, ?, ?, "red")', (id_inspeccion, ruta, etiqueta))
    ultimo_id = cur.lastrowid
    resultado.update({"exito": 1})
    if etiqueta == 'Interior' and not i_principal:
        cur.execute("UPDATE inspecciones SET foto_principal = ? WHERE id = ?", (ultimo_id, id_inspeccion))
        resultado.update({"principal_inspeccion": 1})
    elif etiqueta == 'Exterior' and not e_principal:
        cur.execute("UPDATE elementos SET foto_principal = ? WHERE id = ?", (ultimo_id, id_elemento))
    db.commit()
    resultado.update({"ruta": ruta})
    logCambios(usuario, "Inspección", id_inspeccion, "subeFoto", ruta, geometria)
    return jsonify(resultado)

@app.route('/_carga_mas_fotos')
@logeado_AJAX
@tokenCSRF('cargar as fotos')
def _carga_mas_fotos(usuario):
    id = request.args.get("id")
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT e.cod_edar FROM inspecciones i LEFT JOIN elementos e ON i.id_elemento = e.id WHERE i.id = ?", (id,))
    cod_edar = cur.fetchone()['cod_edar']
    if not verificarPermiso(session, cod_edar, 0):
        log(usuario, request.url, 0)
        return jsonify({"exito":-1, "error": "Non ten permisos para cargar as fotos."}), 403
    cur.execute("SELECT ruta, id, etiqueta FROM fotos WHERE id_tabla = ? AND tabla = 'red'", (id,))
    fotos = cur.fetchall()
    lista_rutas = []
    lista_id = []
    lista_etiquetas = []
    for foto in fotos:
        lista_rutas.append(foto['ruta'])
        lista_id.append(foto['id'])
        lista_etiquetas.append(foto['etiqueta'])
    return jsonify({"rutas":lista_rutas, "ids":lista_id, "etiquetas": lista_etiquetas})

@app.route('/_borra_foto', methods=["POST"])
@logeado_AJAX
@tokenCSRF('borrar a foto')
def _borra_foto(usuario):
    ruta = request.form["ruta"]
    foto_principal_inspeccion_cli = request.form["foto_principal_inspeccion"]
    foto_principal_elemento_cli = request.form["foto_principal_elemento"]

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT e.cod_edar, e.geometria, e.permiso, e.id as id_elemento, i.id as id_inspeccion FROM fotos f LEFT JOIN inspecciones i ON f.tabla||f.id_tabla = 'red'||i.id LEFT JOIN elementos e ON i.id_elemento = e.id WHERE f.ruta = ?", (ruta,))
    cod_edar, geometria, permiso, id_elemento, id_inspeccion = cur.fetchone()
    if not verificarPermiso(session, cod_edar, permiso):
        log(usuario, request.url, 0)
        return jsonify({"exito":-1, "error": "Non ten permisos para borrar a foto."}), 403

    try:
        remove(Configuracion.ruta_app + "static_p/fotos/" + ruta)
    except:
        #en caso de que no haya foto, seguimos, para borrarla de la BBDD
        pass
    cur.execute("DELETE FROM fotos WHERE ruta = ? ", (ruta, ))
    resultado = {"exito": 1}

    otra_foto = None
    if foto_principal_elemento_cli == ruta:
        cur.execute("SELECT id, ruta FROM fotos WHERE id_tabla = ? AND tabla = 'red' LIMIT 1", (id_inspeccion,))
        otra_foto = cur.fetchone()
        if not otra_foto:
            nueva_ruta = "sin_foto.png"
            cur.execute("UPDATE elementos SET foto_principal == null WHERE id = ?", (id_elemento,))
        else:
            nueva_ruta = otra_foto['ruta']
            cur.execute("UPDATE elementos SET foto_principal == ? WHERE id = ?", (otra_foto['id'], id_elemento))
        resultado.update({"nueva_ruta_elemento": nueva_ruta})
    if foto_principal_inspeccion_cli == ruta:
        if not otra_foto:
            cur.execute("SELECT id, ruta FROM fotos WHERE id_tabla = ? AND tabla = 'red' LIMIT 1", (id_inspeccion,))
            otra_foto = cur.fetchone()
        if not otra_foto:
            nueva_ruta = "sin_foto.png"
            cur.execute("UPDATE inspecciones SET foto_principal == null WHERE id = ?", (id_inspeccion,))
        else:
            nueva_ruta = otra_foto['ruta']
            cur.execute("UPDATE inspecciones SET foto_principal == ? WHERE id = ?", (otra_foto['id'], id_inspeccion))
        resultado.update({"nueva_ruta_inspeccion": nueva_ruta})

    db.commit()
    logCambios(usuario, "Inspeccion", id_inspeccion, "borraFoto", ruta, geometria)
    return jsonify(resultado)

@app.route('/_establece_principal', methods=["POST"])
@logeado_AJAX
@tokenCSRF('establecer como foto principal')
def _establece_principal(usuario):
    id_foto = request.form["id"]
    foto_elemento = request.form["foto_elemento"]
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT e.cod_edar, e.permiso, i.id, e.id FROM inspecciones i LEFT JOIN elementos e ON i.id_elemento = e.id LEFT JOIN fotos f ON f.id_tabla = i.id AND f.tabla = 'red' WHERE f.id = ?", (id_foto,))
    cod_edar, permiso, id_insp, id_elem = cur.fetchone()
    if not verificarPermiso(session, cod_edar, permiso):
        log(usuario, request.url, 0)
        return jsonify({"exito":-1, "error": "Non ten permisos para establecer a foto como principal."}), 403
    tabla = "inspecciones"
    id = id_insp
    id_actualizar = id
    if foto_elemento == "1":
        tabla = "elementos"
        id = id_elem
        id_actualizar = ""
    cur.execute("UPDATE {} SET foto_principal = ? WHERE id = ?".format(tabla), (id_foto, id, ))
    db.commit()
    logCambios(usuario, tabla, id, "foto principal", id_foto, "")
    return jsonify({"exito": 1, "id_inspeccion": id_insp, "id_actualizar": id_actualizar})

@app.route("/_eliminar_elemento", methods=["POST"])
@logeado_AJAX
@tokenCSRF('eliminar o elemento')
def _eliminar_elemento(usuario):
    id = request.form["id"]

    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT geometria, permiso, cod_edar, tipo_elemento FROM elementos WHERE id = ?', (id,))
    geometria, permiso, cod_edar, tipo_elemento = cur.fetchone()
    if not verificarPermiso(session, cod_edar, permiso):
        log(usuario, request.url, 0)
        return jsonify({"exito":-1, "error": "Non ten permisos para eliminar o elemento."}), 403

    cur.execute('SELECT id FROM inspecciones WHERE id_elemento = ?', (id,))
    inspecciones = cur.fetchall()
    lista_inspecciones = str([inspeccion['id'] for inspeccion in inspecciones])
    cur.execute('SELECT ruta FROM fotos WHERE id_tabla in ({}) AND tabla ="red"'.format(lista_inspecciones[1:-1]))
    rutas_a_eliminar = cur.fetchall()
    for ruta_a_eliminar in rutas_a_eliminar:
        try:
            remove(Configuracion.ruta_app + "static_p/fotos/"+ruta_a_eliminar[0])
        except:
            pass
    cur.execute('DELETE FROM fotos WHERE id_tabla in ({}) AND tabla = "red"'.format(lista_inspecciones[1:-1]))
    cur.execute('DELETE FROM inspecciones WHERE id in ({})'.format(lista_inspecciones[1:-1]))
    cur.execute('DELETE FROM mediciones WHERE id_inspeccion in ({})'.format(lista_inspecciones[1:-1]))
    cur.execute('DELETE FROM elementos WHERE id = ?', (id,))
    db.commit()
    resultado = {"exito":1}

    logCambios(usuario, tipo_elemento, id, "eliminar", "", geometria)
    return jsonify(resultado)

@app.route('/_eliminar_inspeccion', methods=["POST"])
@logeado_AJAX
@tokenCSRF('eliminar a inspección')
def _eliminar_inspeccion_red(usuario):
    id_insp = request.form["id_insp"]

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT e.geometria, e.permiso, e.cod_edar, e.tipo_elemento FROM inspecciones i LEFT JOIN elementos e ON i.id_elemento = e.id WHERE i.id = ?', (id_insp,))
    geometria, permiso, cod_edar, tipo_elemento = cur.fetchone()
    if not verificarPermiso(session, cod_edar, permiso):
        log(usuario, request.url, 0)
        return jsonify({"exito":-1, "error": "Non ten permisos para eliminar a inspección."}), 403

    cur.execute('SELECT ruta FROM fotos WHERE id_tabla = ? AND tabla ="red"', (id_insp,))
    rutas_a_eliminar = cur.fetchall()
    for ruta_a_eliminar in rutas_a_eliminar:
        try:
            remove(Configuracion.ruta_app + "static_p/fotos/"+ruta_a_eliminar[0])
        except:
            pass
    cur.execute('DELETE FROM fotos WHERE id_tabla = ? AND tabla = "red"', (id_insp, ))
    cur.execute('DELETE FROM inspecciones WHERE id = ?', (id_insp, ))
    cur.execute('DELETE FROM mediciones WHERE id_inspeccion = ?', (id_insp, ))
    db.commit()
    resultado = {"exito":1}
    logCambios(usuario, tipo_elemento, id_insp, "eliminar", "Eliminar inspección", geometria)
    return jsonify(resultado)

@app.route("/_mueve_elemento", methods=["POST"])
@logeado_AJAX
@tokenCSRF('mover o elemento')
def _mueve_elemento(usuario):
    """Actualiza lat long de elemento
    """
    id = request.form["id"]
    lat = request.form["lat"]
    lon = request.form["lon"]
    if not compruebaFloat(lat) or not compruebaFloat(lon):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "error": "Seleccione as coordenadas clicando no mapa."}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT permiso, cod_edar, geometria, tipo_elemento FROM elementos WHERE id = ?", (id, ))
    permiso, cod_edar, geometria, tipo_elemento = cur.fetchone()
    if not verificarPermiso(session, cod_edar, permiso):
        log(usuario, request.url, 0)
        return jsonify({"exito": -3, "error": "Non ten permisos para mover o elemento."}), 403

    geometria2 = str([float(lat), float(lon)])
    cur.execute("UPDATE elementos set geometria = ? WHERE id = ?", (geometria2, id))

    logCambios(usuario, tipo_elemento, id, "mover", "Antes", geometria)
    logCambios(usuario, tipo_elemento, id, "mover", "Despois", geometria2)
    return jsonify({"exito": 1})

@app.route('/_muestra_ficha_filtro')
@logeado_AJAX
def _muestra_ficha_filtro_red(usuario):
    cod_edar = request.args.get("cod_edar")
    db = get_db()
    cur = db.cursor()
    filtro_SQL = ""
    tupla_filtro = ()
    cur.execute('SELECT e.id, e.inspector as elemento§inspector, e.tipo_elemento as elemento§tipo_elemento, e.tipo_agua_residual as elemento§tipo_agua_residual, i.fecha as inspeccion§fecha, i.estado as inspeccion§estado, i.inspector as inspeccion§inspector ' +
                'FROM elementos e ' +
                'INNER JOIN inspecciones i ON e.id = i.id_elemento ' +
                'WHERE cod_edar = ?', (cod_edar,))
    elementos_inspecciones = cur.fetchall()
    claves_categorias = {"elemento§inspector": ["Inspector elemento", [], {}],
                        "elemento§tipo_elemento": ["Tipo elemento", [], {}],
                        "elemento§tipo_agua_residual": ["Tipo agua residual", [], {0: "Fecais", 1: "Pluviais", 2: "Unitario", 3: "Descoñecido", 4: "Industrial"}],
                        "inspeccion§fecha": ["Fecha inspección", [], {}],
                        "inspeccion§estado": ["Estado", [], {0: "Non afectado", 1: "Afectado", 2: "Crítico"}],
                        "inspeccion§inspector": ["Inspector inspección", [], {}]}
    for elem_insp in elementos_inspecciones:
        for clave_BBDD, clave_categoria in claves_categorias.items():
            if elem_insp[clave_BBDD] not in claves_categorias[clave_BBDD][1]:
                if elem_insp[clave_BBDD] in claves_categorias[clave_BBDD][2]:
                    texto = claves_categorias[clave_BBDD][2][elem_insp[clave_BBDD]]
                    if texto not in claves_categorias[clave_BBDD][1]:
                        claves_categorias[clave_BBDD][1].append(texto)
                else:
                    texto = elem_insp[clave_BBDD]
                    claves_categorias[clave_BBDD][1].append(texto)
    plantilla = "html/fichas/ficha_filtro_red.html"
    rendered = render_template(plantilla, categorias=claves_categorias, sistema=cod_edar)
    return jsonify({"valor":rendered})

def obten_diccionario(valores):
    diccionario = {}
    if valores:
        for par in valores.split("&"):
            clave, valor = par.split("=")
            clave = unquote_plus(clave)
            valor = unquote_plus(valor)
            if clave in diccionario:
                if type(diccionario[clave]) is not list:
                    diccionario[clave] = [diccionario[clave]]
                diccionario[clave].append(valor)
            else:
                diccionario.update({clave: valor})
    return diccionario

ESTADOS_TIPOS = {"Fecais": 0, "Pluviais": 1, "Unitario": 2,"Descoñecido": 3, "Industrial": 4, "Non afectado": 0, "Afectado": 1, "Crítico": 2}

def diccionario_a_SQL(diccionario, columnas, negacion, usuario):
    SQL_string = ""
    lista_valores = []
    niega = "!" if negacion else ""
    or_niega = "and" if negacion else "or "
    lista_valores = []
    for key in diccionario:
        if key.split("§")[1] not in columnas:
            log(usuario, request.url, 0)
            return ["", []]
        if type(diccionario[key]) is list:
            SQL_string += " and ("
            for filtro_multiple in diccionario[key]:
                SQL_string += " {} {}= ? {}".format(key, niega, or_niega)
                if filtro_multiple in ESTADOS_TIPOS:
                    filtro_multiple = ESTADOS_TIPOS[filtro_multiple]
                lista_valores.append(filtro_multiple)
            SQL_string = SQL_string[:-3] + ")"
        else:
            SQL_string += " and {} {}= ?".format(key, niega)
            if diccionario[key] in ESTADOS_TIPOS:
                lista_valores.append(ESTADOS_TIPOS[diccionario[key]])
            else:
                lista_valores.append(diccionario[key])
    SQL_string = SQL_string[4:]
    SQL_string = SQL_string.replace("elemento§", "e.")
    SQL_string = SQL_string.replace("inspeccion§", "i.")
    return [SQL_string, lista_valores]

@app.route('/_filtra_elementos')
@logeado_AJAX
@tokenCSRF('filtrar elementos')
def _filtra_elementos(usuario):
    cod_edar = request.args.get("cod_edar")
    valores = request.args.get("valores")
    valores_not = request.args.get("valores_not")

    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para filtrar."}), 403
    diccionario = obten_diccionario(valores)
    diccionario_not = obten_diccionario(valores_not)
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT e.*, i.* FROM elementos e INNER JOIN inspecciones i ON e.id = i.id_elemento LIMIT 1")
    datos = cur.fetchone()
    columnas = datos.keys()
    SQL_string, lista_valores = ["", []]
    if diccionario:
        SQL_string, lista_valores = diccionario_a_SQL(diccionario, columnas, 0, usuario)
    if diccionario_not:
        if diccionario:
            SQL_string += " and"
        SQL_string_not, lista_valores_not = diccionario_a_SQL(diccionario_not, columnas, 1, usuario)
        SQL_string = SQL_string + SQL_string_not
        lista_valores = lista_valores + lista_valores_not
    if not SQL_string and not lista_valores:
        SQL_string += " cod_edar = ?"
    else:
        SQL_string += " and cod_edar = ?"
    lista_valores.append(cod_edar)
    cur.execute("SELECT e.id FROM elementos e INNER JOIN inspecciones i ON e.id = i.id_elemento WHERE {}".format(SQL_string), tuple(lista_valores))
    listado_id_BD = cur.fetchall()
    lista_id = []
    for id in listado_id_BD:
        lista_id.append(id['id'])
    return jsonify({"listado_id": lista_id})
