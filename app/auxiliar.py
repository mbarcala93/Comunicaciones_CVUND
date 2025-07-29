# -*- coding: utf-8 -*-

import sqlite3
from os import path, makedirs, listdir
from app import app
from flask import g, send_from_directory, session, url_for, request, redirect,\
    jsonify, render_template, abort
from datetime import datetime
import json
from shapely.geometry import Point, MultiPoint, LineString, Polygon
from shapely.ops import nearest_points
import ast
from urllib.parse import unquote_plus

import utm
import locale
from PIL import Image
import configparser

locale.setlocale(locale.LC_TIME, '')


def leer_configuracion():
    config = configparser.ConfigParser()
    config.read('redes.conf')
    return config

def escribir_configuracion(config):
    with open('redes.conf', 'w') as configfile:
        config.write(configfile)

def tiempo_sesion(tiempo=None):
    config = leer_configuracion()
    if not tiempo:
        tiempo = config['configuracion']['tiempo_sesion']
        try:
            tiempo = int(tiempo)
        except:
            tiempo = 60
            config['configuracion']['tiempo_sesion'] = str(tiempo)
            escribir_configuracion(config)
    else:
        if not isinstance(tiempo, int) or tiempo < 60:
            tiempo = 60
        config['configuracion']['tiempo_sesion'] = str(tiempo)
        escribir_configuracion(config)
    app.config.update({"PERMANENT_SESSION_LIFETIME": tiempo})

def connect_db():
    """Connects to the specific database."""
    BBDD = '../redes.sqlite'
    # if session.get('test'):
    #     BBDD = './test/sisbagal_test.sqlite'
    rv = sqlite3.connect(path.join(app.root_path, BBDD))
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("sqlite_db", None)
    if db is not None:
        db.close()

def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)

def remote_ip(request):
    try:
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0].split(",")[0]
        else:
            ip = request.remote_addr
    except:
        ip = "unknow"
    return ip

def log(usuario, pagina, exito=1):
    """Registro de accesos a cada página"""
    f = open("log.txt","a")
    time = datetime.now()
    cadena = str(time) +"|"+ usuario +"|"+ str(pagina) + "|" + str(exito) + "\n"
    f.write(cadena)
    f.close()

def logCambios(usuario, elemento, id_elemento, tipo_cambio, cambio, geometria):
    db = get_db()
    cur = db.cursor()
    fecha = str(datetime.now())
    cur.execute("INSERT INTO cambios (usuario, fecha, elemento, id_elemento, tipo_cambio, cambio, geometria) VALUES (?, ?, ?, ?, ?, ?, ?)", (usuario, fecha, elemento, id_elemento, tipo_cambio, cambio, geometria))
    db.commit()

def compruebaFloat(numero_como_cadena):
    try:
        float(numero_como_cadena)
        return 1
    except:
        return 0

def logeado(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            log(remote_ip(request), request.url, 0)
            return redirect(url_for('login',url=request.path[1:]))
        kwargs['usuario'] = session['username']
        if request.method == "GET":
            log(session['username'], request.url)
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def logeado_AJAX(func):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            log(remote_ip(request), request.url, 0)
            return jsonify({"exito":-1, "error": "Usuario non logeado, recargue a páxina e intenteo de novo."}), 401
        kwargs['usuario'] = session['username']
        if request.method == "GET":
            log(session['username'], request.url)
        return func(*args, **kwargs)
    wrap.__name__ = func.__name__+"ajax"
    return wrap

def tokenCSRF(accion):
    def tokenCSRF_decorador(fn):
        def wrap(*args, **kwargs):
            TOKEN_form = request.args.get("token")
            if not TOKEN_form:
                TOKEN_form = request.form.get("token")
            if TOKEN_form != session['TOKEN']:
                log(kwargs['usuario'], request.url, 0)
                return jsonify({"codigo": -2, "error": "[CSRF] Erro ó {}. Recargue a páxina e inténteo de novo".format(accion)}), 403
            return fn(*args, **kwargs)
        wrap.__name__ = fn.__name__+"CRSF"
        return wrap
    return tokenCSRF_decorador


def verificaPermiso(ambito, permiso):
    def verificaPermiso_decorador(fn):
        def wrap(*args, **kwargs):
            validado = verificarPermiso(session, ambito, permiso)
            if not validado:
                log(kwargs['usuario'], request.url, 0)
                return jsonify({
                    "codigo": -2,
                    "error": "Non dispón dos permisos oportunos."}), 403
            return fn(*args, **kwargs)
        wrap.__name__ = fn.__name__+"permiso"
        return wrap
    return verificaPermiso_decorador


def verificarPermiso(session, ambito, permiso):
    """Comprueba el ámbito (edar) y
    el permiso (lectura, escritura, total)
    """
    ambitos_usuario = session['ambito'].split("|")
    permiso_usuario = session['permiso']

    resultado = 0
    ambito = ambito.split("|")

    cumple_ambito = all(elem in ambitos_usuario for elem in ambito)
    if ambitos_usuario == ['galicia']:
        cumple_ambito = 1

    if cumple_ambito and permiso <= permiso_usuario:
        resultado = 1

    if 'admin' in ambitos_usuario and permiso_usuario == 2:
        resultado = 1
    
    return resultado


def verificaPermisoAuditoria(claves, permiso, filtro=None):
    def verificaPermisoAudit_decorador(fn):
        def wrap(*args, **kwargs):
            cumple_permiso = 0
            cumple_ambito = 0
            if permiso <= session['permiso']:
                cumple_permiso = 1
            if usuarioGlobal():
                cumple_ambito = 1
            else:
                db = get_db()
                cur = db.cursor()
                lista_id_auditorias = tuple(session['auditorias'].split("|"))
                for clave in claves.split("|"):
                    if clave == 'id_auditoria' and filtro:
                        filtro_SQL = f"WHERE a.id in {lista_id_auditorias}"
                        cumple_ambito = 1
                    elif clave == 'cod_edar':
                        cur.execute(f"""
                            SELECT cod_edar
                            FROM edar e
                            LEFT JOIN auditorias a ON a.id_edar = e.id
                            WHERE a.id in {lista_id_auditorias}
                        """)
                        lista_cod_edar = sqliteRow2dict_dict(
                            cur.fetchall(),
                            "cod_edar"
                            ).keys()
                        
                        if kwargs.get('cod_edar') in lista_cod_edar:
                            cumple_ambito = 1
                    elif clave == 'id_tratamiento':
                        cur.execute(f"""
                            SELECT t.id
                            FROM tratamientos t
                            LEFT JOIN instalaciones i 
                                ON t.id_instalacion = i.id
                            LEFT JOIN edar e ON i.id_edar = e.id
                            LEFT JOIN auditorias a ON a.id_edar = e.id
                            WHERE a.id in {lista_id_auditorias}
                        """)
                        lista_id_tratamientos = sqliteRow2dict_dict(
                            cur.fetchall()
                            ).keys()
                        id_tratamiento = obten_argumento(
                            'id_tratamiento',
                            kwargs)
                        if int(id_tratamiento) in lista_id_tratamientos:
                            cumple_ambito = 1
                    elif clave == 'id_equipo':
                        cur.execute(f"""
                            SELECT eq.id
                            FROM equipos eq
                            LEFT JOIN tratamientos t 
                                ON eq.id_tratamiento = t.id
                            LEFT JOIN instalaciones i 
                                ON t.id_instalacion = i.id
                            LEFT JOIN edar e ON i.id_edar = e.id
                            LEFT JOIN auditorias a ON a.id_edar = e.id
                            WHERE a.id in {lista_id_auditorias}
                        """)
                        lista_id_equipos = sqliteRow2dict_dict(
                            cur.fetchall()
                            ).keys()
                        id_equipo = obten_argumento('id_equipo', kwargs)
                        if int(id_equipo) in lista_id_equipos:
                            cumple_ambito = 1
                    elif clave == 'id_motor':
                        cur.execute(f"""
                            SELECT m.id
                            FROM motores m
                            LEFT JOIN equipos eq ON m.id_equipo = eq.id
                            LEFT JOIN tratamientos t 
                                ON eq.id_tratamiento = t.id
                            LEFT JOIN instalaciones i 
                                ON t.id_instalacion = i.id
                            LEFT JOIN edar e ON i.id_edar = e.id
                            LEFT JOIN auditorias a ON a.id_edar = e.id
                            WHERE a.id in {lista_id_auditorias}
                        """)
                        lista_id_motores = sqliteRow2dict_dict(
                            cur.fetchall()
                            ).keys()
                        id_motor = obten_argumento('id_motor', kwargs)
                        if int(id_motor) in lista_id_motores:
                            cumple_ambito = 1
                    elif clave == 'id_auditoria':
                        id_auditoria = obten_argumento('id_auditoria', kwargs)
                        if id_auditoria in lista_id_auditorias:
                            cumple_ambito = 1
                    elif clave == 'tipo_prueba3':
                        id_equipo = obten_argumento('id_equipo', kwargs)
                        cur.execute("""
                            SELECT id_tipo_prueba
                            FROM equipos
                            WHERE id = ?
                            """, (id_equipo,))
                        id_tipo_prueba = cur.fetchone()['id_tipo_prueba']
                        if id_tipo_prueba == 3:
                            cumple_ambito = 1
                if filtro:
                    kwargs['filtro'] = filtro_SQL
            if not (cumple_permiso and cumple_ambito):
                log(kwargs['usuario'], request.url, 0)
                abort(403)
            return fn(*args, **kwargs)
        wrap.__name__ = fn.__name__+"permisoAudit"
        return wrap
    return verificaPermisoAudit_decorador


def usuarioGlobal():
    if session['ambito'] == 'admin' or session['ambito'] == 'galicia':
        return 1
    else:
        return 0


def obten_argumento(clave, argumentos):
    resultado = argumentos.get(clave)
    if not resultado:
        resultado = request.args.get(clave)
    if not resultado:
        resultado = request.form.get(clave)
    return resultado


class Configuracion():
    config = leer_configuracion()
    ruta_app = config['configuracion']['ruta_app']
    telefono = config['configuracion']['telefono']

def obtener_capas_geoJSON(edar):
    """Dada una EDAR devuelve un listado de diccionarios con nombre
    y color de cada archivo geoJSON encontrado en la ruta static/capas/[EDAR]
    No devuelve "features", que se cargan por JS individualmente
    """
    if not path.exists(Configuracion.ruta_app + 'static/capas/'):
        makedirs(Configuracion.ruta_app + 'static/capas/')

    colores = ["#9A086E", "#09A309", "#067A7A", "#CC620B", "#7E0000", "#006500", "#004B4B", "#7E3900", "#5F0042"]
    iconos = ["blueCircleIcon", "greenCircleIcon", "fucsiaCircleIcon", "turquesaCircleIcon", "limaCircleIcon"]
    url_iconos = ["azul_circulo", "verde_circulo", "fucsia_circulo", "turquesa_circulo", "lima_circulo"]
    color = 0
    icono = 0
    geoJSON = []
    try:
        archivos = listdir(Configuracion.ruta_app + 'static/capas/' + edar )
    except:
        return []
    for capa in archivos:
        # try:
        if capa[0] == ".":
            continue
        with open(Configuracion.ruta_app + "static/capas/" + edar + "/" + capa, encoding="utf-8") as f:
            contenido = f.read()
        dict_contenido = json.loads(contenido)
        if dict_contenido.get("features")[0].get("geometry").get("type") == "Point":
            color_capa = "#222"
            icono_capa = iconos[icono]
            url_icono = "static/images/mapas/" + url_iconos[icono] + ".png"
        else:
            color_capa = colores[color]
            icono_capa = 'blackCircleIcon'
            url_icono = ""
        geoJSON.append({"nombre": capa.split(".geojson")[0], "color": color_capa, "icono": icono_capa, "url_icono": url_icono})
        color += 1
        icono += 1
        if color > 8:
            color = 0
        if icono > 4:
            icono = 0
        # except:
        #     continue
    return geoJSON

@logeado_AJAX
@app.route("/_obtener_geoJSON")
def obtener_geoJSON():
    edar = request.args.get("edar")
    capa = request.args.get("capa")
    TOKEN_form = request.args.get("token")
    usuario = session['username']
    if any(elem in edar for elem in "()/\\") or any(elem in capa for elem in "()/\\"):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "A ruta non pode ter caracteres especiais. Recarge a páxina e inténteo de novo"}), 403
    ruta = 'static/capas/' + edar + '/' + capa + '.geojson'
    if not path.exists(Configuracion.ruta_app + ruta):
        return jsonify({"codigo":-1, "error": "A ruta da capa non existe. Consulte co administrador"}), 403
    if TOKEN_form != session['TOKEN']:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "[CSRF] Erro cargando a capa. Recargue a páxina e inténteo de novo"}), 403
    if not verificarPermiso(session, edar, 0):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-3, "error": "Sen permisos para visualizar a capa."}), 403


    with open(Configuracion.ruta_app + ruta, encoding="utf-8") as f:
        contenido = f.read()
    dict_contenido = json.loads(contenido)
    features = dict_contenido['features']

    return jsonify({"features": features})


def ambitoN_a_ambitoT(ambitoN):
    if ambitoN == "admin" or ambitoN == "0":
        return "Administrador"
    elif ambitoN == "galicia":
        return "Galicia"
    ambito_texto = ""
    for ambito in ambitoN.split("|"):
        ambito_texto = ambito_texto + ambito + ", "
    ambito_texto = ambito_texto[:-2]
    return ambito_texto


@app.errorhandler(404)
def pagina_no_encontrada(e):
    resultados = {"error": "Erro 404",
                  "texto": "Páxina non atopada",
                  "permiso": 0,
                  "recomendacion": "Asegúrese de que a dirección URL estivera ben escrita."
                  }
    if request.path.startswith("/_"):
        return jsonify({"error": resultados['texto'] + ". " + resultados['recomendacion']}), 404
    return render_template('html/error.html', resultados=resultados), 404


@app.errorhandler(500)
def error_servidor(e):
    resultados = {"error": "Erro 500",
                  "texto": "Fallo no servidor",
                  "permiso": 0,
                  "recomendacion": "Intente repetir a acción."
                  }
    if request.path.startswith("/_"):
        return jsonify({"error": resultados['texto'] + ". " + resultados['recomendacion']}), 500
    return render_template('html/error.html', resultados=resultados), 500


@app.errorhandler(403)
def error_servidor(e):
    resultados = {"error": "Erro 403",
                  "texto": "Non dispón dos permisos oportunos",
                  "permiso": 0,
                  "recomendacion": "Asegúrese que está accedendo ao recurso adecuado."
                  }
    if request.path.startswith("/_"):
        return jsonify({"error": resultados['texto'] + ". " + resultados['recomendacion']}), 403
    return render_template('html/error.html', resultados=resultados), 403


@app.route("/static_p/<path:archivo>")
def sirve_static(archivo):
    if not session.get('logged_in'):
        log(remote_ip(request), request.url, 0)
        return send_from_directory('static_p/', 'fotos/sin_foto.png')
    return send_from_directory('static_p/', archivo)

# @app.route("/coordenadas")
# def coord():
#     tabla = "censo"
#     db = get_db()
#     cur = db.cursor()
#     cur = db.execute('SELECT latitud, longitud, latitud_PV, longitud_PV, id FROM {}'.format(tabla))
#     coordenadas = cur.fetchall()
#     for registro in coordenadas:
#         # print(registro['id'], registro['coord_y'], registro['coord_x'], registro['coord_y_PV'], registro['coord_x_PV'])
#         if registro['latitud'] != None and registro['longitud'] != None:
#             lat, lon = utm.to_latlon(int(registro['latitud']), int(registro['longitud']), 29, 'N')
#             # print(lat, lon, registro['coord_y'], registro['coord_x'], registro['id'])
#             cur.execute('UPDATE {} SET latitud = ?, longitud = ? WHERE id = ?'.format(tabla), (lat, lon, registro['id']))
#         if registro['latitud_PV'] != None and registro['longitud_PV'] != None:
#             print()
#             lat_PV, lon_PV = utm.to_latlon(int(registro['latitud_PV']), int(registro['longitud_PV']), 29, 'N')
#             # print(lat_PV, lon_PV)
#             cur.execute('UPDATE {} SET latitud_PV = ?, longitud_PV = ? WHERE id = ?'.format(tabla), (lat_PV, lon_PV, registro['id']))
#
#     db.commit()
#     return "Tabla de {} actualizada".format(tabla)

@app.route("/_que_concello")
@logeado_AJAX
def _que_concello(usuario=None, latitud=None, longitud=None):
    """Dadas una latitud y longitud, determina el concello en el que está.
    Si repasamos la lista de concellos, generamos un polígono con cada geometría
    y comprobamos en cada una la pertenencia del punto, tarda >1s en concellos del
    final (p.ej. Zas). Por eso se hace buscando primero el centroide más cercano.
    Se mira cuál es el centroide más cercano y comprueba si está dentro de ese concello.
    En caso negativo, repite la operación quitando el centroide más cercano del conjunto.
    """
    if not latitud and not longitud:
        latitud = float(request.args.get("lat"))
        longitud = float(request.args.get("lon"))
    db = get_db()
    cur = db.cursor()
    punto_elemento = Point(latitud, longitud)
    cur.execute('SELECT id, cod_ine, denominacion, geometria, centroides FROM concellos WHERE geometria is not null')
    concellos = cur.fetchall()
    centroides = []
    concellos_x_centroide = {}
    for concello in concellos:
        if not concello['centroides']:
            continue
        centroides.append(Point(ast.literal_eval(concello['centroides'])))
        concellos_x_centroide.update({str(concello['centroides']): {"geometria": concello['geometria'], "cod_ine": concello['cod_ine'], "denominacion": concello['denominacion']}})
    cod_ine = ""
    denominacion = ""
    while not cod_ine or len(centroides) > 100:
        punto_cercano = nearest_points(punto_elemento, MultiPoint(centroides))[1]
        perimetro_concello = LineString(ast.literal_eval(concellos_x_centroide[str([punto_cercano.x, punto_cercano.y])]["geometria"]))
        poligono = Polygon(perimetro_concello)
        if poligono.contains(punto_elemento):
            cod_ine = concellos_x_centroide[str([punto_cercano.x, punto_cercano.y])]['cod_ine']
            denominacion = concellos_x_centroide[str([punto_cercano.x, punto_cercano.y])]['denominacion']
            break
        else:
            centroides.remove(punto_cercano)
    return jsonify({"exito": 1, "cod_ine": cod_ine, "denominacion": denominacion})

def interpola(x0, y0, x1, y1, x):
    m = (y1-y0)/(x1-x0)
    y = m*(x-x0)+y0
    return y

def obten_columnas(cur, tabla):
    cur.execute("PRAGMA table_info({})".format(tabla))
    datos = cur.fetchall()
    columnas_BD = []
    for dato in datos:
        columnas_BD.append(dato['name'])
    return columnas_BD

def extrae_id(tabla_BD):
    """Dada una búsqueda de BD, devuelve una lista con los campos id
    """
    listado_id = []
    for registro in tabla_BD:
        listado_id.append(registro['id'])
    return listado_id

def lista_id(sqliteRow, campo='id'):
    """Dado un sqliteRow, devuelve un string de los valores del campo
    separados por comas, listo para ser usado en una query.
    Si no se incluye un nombre de campo, devuelve el campo 'id'.
    """
    lista = []
    for elemento in sqliteRow:
        valor = str(elemento[campo])
        if valor not in lista:
            try:
                float(valor)
            except:
                valor = f'"{valor}"'
            lista.append(valor)

    resultado = ", ".join(lista)
    return resultado


def lista_enteros(lista_enteros):
    """Dada una lista de enteros no validados, devuelve string de valores
    separados por comas, para ser usado en una query"""
    lista = []
    for elemento in lista_enteros:
        try:
            int(elemento)
        except:
            return ""
        if elemento not in lista:
            lista.append(elemento)
    resultado = ", ".join(lista)
    return resultado


@app.template_filter()
def numero_bonito(numero):
    if type(numero) is float or type(numero) is int:
        numero = str("{:,}".format(numero))
    elif type(numero) is str:
        pass
    else:
        return numero
    numero = str(numero).replace(".", "|").replace(",", ".").replace("|", ",")
    return numero

@app.template_filter()
def fecha_bonita(fecha):
    try:
        fecha = str(fecha)
        fecha = fecha[6:8] + "/" + fecha[4:6] + "/" + fecha[0:4]
    except:
        pass
    return fecha

@app.template_filter()
def fecha_hora_bonita(fecha_timestamp_unix, formato="%d/%m/%Y %H:%M"):
    try:
        fecha_python = datetime.fromtimestamp(fecha_timestamp_unix)
        fecha_hora_texto = fecha_python.strftime(
            formato
            )
        return fecha_hora_texto
    except Exception as e:
        return ""
    
@app.template_filter()
def intenta_float(cadena):
    try:
        cadena = float(cadena)
    except Exception as e:
        pass
    return cadena

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


def sqliteRow2dict_dict(sqliteRow, columna='id'):
    """Toma una lista de sqliteRows (resultado de un fetchall) y lo convierte
    a un diccionario cuyas claves son la columna (por defecto id) y los
    valores son un diccionario con el resto de columnas.
    """
    resultado = {}
    for elemento in sqliteRow:
        subresultado = {}
        for key in elemento.keys():
            subresultado.update({key:elemento[key]})
        resultado.update({elemento[columna]: subresultado})
    return resultado


def gira_imagen(ruta, grados=-90):
    imagen = Image.open(ruta)
    girada = imagen.rotate(grados, expand=True)
    girada.save(ruta)

PROHIBIDOS = {
    "censo": ["id", "permiso"],
    "inspecciones_ind": ["id", "permiso", "latitud", "longitud"],
    "muestras": ["id", "id_inspecciones_ind"],
    "analiticas": ["id", "id_muestra"]
    }

CAMPOS_JS = {
    "censo": ["id", "nome_industria", "cod_industria", "sistema", "actividade", "latitud", "longitud"],
    "inspecciones_ind": ["id"],
    "muestras": ["id"],
    "analiticas": ["id"]
    }

def serializado_a_diccionario(
        serializados,
        formato_fecha="%d/%m/%Y",
        multivalor=None
        ):
    resultado = {}
    for par in serializados.split("&"):
        clave, valor = par.split("=")
        clave = unquote_plus(clave)
        valor = unquote_plus(valor)
        # if 'fecha' in clave:
        #     try:
        #         valor = datetime.strptime(valor, formato_fecha)
        #     except:
        #         formato_fecha_texto = formato_fecha.replace("%d", "dd")
        #         formato_fecha_texto = formato_fecha_texto.replace("%m", "mm")
        #         formato_fecha_texto = formato_fecha_texto.replace("%Y", "aaaa")
        #         formato_fecha_texto = formato_fecha_texto.replace("%H", "hh")
        #         formato_fecha_texto = formato_fecha_texto.replace("%M", "mm")
        #         return {"exito": 0,
        #                 "error": "Comprobe que a data ten "
        #                         + f"o formato {formato_fecha_texto}",
        #                 "codigo_error": 403
        #                 }
        if multivalor and resultado[clave]:
            if type(resultado[clave]) is not list:
                resultado[clave] = [
                    resultado[clave]
                    ]
            else:
                resultado[clave].append(valor)
        else:
            resultado.update({clave: valor})
    return resultado


def actualiza_BBDD_diccionario(diccionario,
                               tabla,
                               id_elemento                            
                               ):
    db = get_db()
    cur = db.cursor()
    SQL_string = f"UPDATE {tabla} SET"

    if diccionario:
        columnas = obten_columnas(cur, tabla)
        lista_valores = []
        for key in diccionario:
            if key not in columnas or key == 'id':
                return {
                    "error": "[KEY] Hai datos que non se poden actualizar.",
                    'status_code': 400
                    }
            if PROHIBIDOS.get(tabla) and key in PROHIBIDOS.get(tabla):
                return {
                    "error": "[JS] Hai datos que non se poden actualizar.",
                    'status_code': 400
                    }
            if CAMPOS_JS.get(tabla) and\
                    key in CAMPOS_JS.get(tabla) and\
                    any(a in key for a in "\"\'();$%&@!"):
                return {
                    "error": f"Los siguientes campos: {CAMPOS_JS[tabla]} no pueden "
                     + "tener caracteres especiales. Sustitúyalos e inténtelo " 
                     + "de nuevo.",
                     "status_code": 400
                     } 
            SQL_string += " {} = ?,".format(key)
            lista_valores.append(diccionario[key])
        SQL_string = SQL_string[:-1] + " WHERE id = ?"
        lista_valores.append(id_elemento)
        cur.execute(SQL_string, tuple(lista_valores))
        db.commit()
    return {"status_code": 200}

def log_fracaso():
    log(session['username'], request.path, 0)

def obten_sumario(revisiones):
    sumario = {0: 0, 1: 0, 2: 0, 3: 0}
    for revision in revisiones:
        sumario[revision['estado']] += 1
    if revisiones:
        sumario = (sumario[1] + sumario[2] + sumario[3]) / len(revisiones)
    else:
        sumario = 0
    return sumario

