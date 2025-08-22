# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, session, jsonify, send_file
from app import app
from os import path, remove, makedirs, getcwd
from base64 import b64decode
from datetime import datetime
from urllib.parse import unquote_plus
import json
import utm

from app.auxiliar import get_db, log, logCambios, compruebaFloat, \
                        verificarPermiso, logeado, logeado_AJAX, tokenCSRF, \
                        Configuracion, obtener_capas_geoJSON, _que_concello, \
                        extrae_id, obten_columnas, numero_bonito, \
                        sqliteRow2list_dict, lista_id, serializado_a_diccionario, \
                        actualiza_BBDD_diccionario, log_fracaso, verificaPermiso


@app.route('/censo')
@app.route('/censo-<cod_edar>-<globo_abierto>,<capa_base>,<latitud>,<longitud>,<zoom>')
@app.route('/censo-<cod_edar>')
@logeado
def censo(usuario, cod_edar=None, globo_abierto=None, capa_base='OpenStreetMap', latitud=None, longitud=None, zoom=None):
    if not verificarPermiso(session, 'galicia', 0):
        log(usuario, request.url, 0)
        return redirect('/')
    db = get_db()
    cur = db.cursor()
    filtro_SQL = ""
    tupla_filtro = ()
    if cod_edar is None or cod_edar == "None":
        geoJSON = ""
    elif cod_edar:
        filtro_SQL = " WHERE sistema = ?"
        geoJSON = obtener_capas_geoJSON(cod_edar)
        tupla_filtro = (cod_edar, )
    cur.execute("""
                SELECT c.id, latitud, longitud, nome_industria,
                sistema||'_'||cod_industria as ref, actividade
                FROM censo c""" + filtro_SQL,
                tupla_filtro)
    industrias = cur.fetchall()
    cur.execute('SELECT c.geometria, e.provincia, cod_ine FROM concellos c INNER JOIN edar e ON e.provincia||e.municipio = c.cod_ine WHERE e.cod_edar = ?', (cod_edar,))
    concello = cur.fetchone()
    cur.execute("SELECT * from usuarios where inspector = 1")
    inspectores = cur.fetchall()
    cur.execute("SELECT * from usuarios")
    usuarios = cur.fetchall()
    cur.execute("SELECT * from organismos")
    organismos = cur.fetchall()
    cur.execute(f"SELECT * from doc_normativos WHERE cod_concello LIKE '%{concello['cod_ine']}%' OR cod_concello = 1")
    docs_norm = cur.fetchall()
    cur.execute("SELECT * from parametros")
    parametros = cur.fetchall()
    cur.execute("SELECT * from sondas")
    sondas = cur.fetchall()
    resultados = {"mapa": 'censo',
                  "cod_edar": cod_edar,
                  "url": request.path,
                  "globo_abierto": globo_abierto,
                  "capa_base": capa_base,
                  "concello": 0,
                  "latitud": latitud,
                  "longitud": longitud,
                  "zoom": zoom,
                  "ambito": session['ambito'],
                  "usuario": session['username'],
                  'token': session['TOKEN'],
                  "permiso": session['permiso'],
                  "diestro": session['diestro'],
                  "titulo": "Censo",
                  "menu": "html/menu_lateral_visor.html"}
    return render_template('html/visor.html',
                           resultados=resultados,
                           industrias=industrias,
                           concello=concello,
                           inspectores=inspectores,
                           usuarios=usuarios,
                           organismos=organismos,
                           docs_norm=docs_norm,
                           parametros=parametros,
                           sondas=sondas,
                           geoJSON=geoJSON)

@app.route('/censo-<cod_edar>_<cod_industria>')
@logeado
def redirige_censo(usuario, cod_edar, cod_industria):
    if not verificarPermiso(session, 'galicia', 0):
        log(usuario, request.url, 0)
        return redirect('/')
    db = get_db()
    cur = db.cursor()
    ref_industria = cod_edar + "_" + cod_industria
    cur.execute('SELECT id, latitud, longitud FROM censo WHERE sistema||"_"||cod_industria = ?', (ref_industria, ))
    id_industria, latitud, longitud = cur.fetchone()
    url = f"/censo-{cod_edar}-{id_industria},OpenStreetMap,{latitud},{longitud},17"
    return redirect(url)

@app.route('/censoConcello-<cod_concello>-<globo_abierto>,<capa_base>,<latitud>,<longitud>,<zoom>')
@app.route('/censoConcello-<cod_concello>')
@logeado
def censo_concello(usuario, cod_concello, globo_abierto=None, capa_base='OpenStreetMap', latitud=None, longitud=None, zoom=None):
    if not verificarPermiso(session, 'galicia', 0):
        log(usuario, request.url, 0)
        return redirect('/')
    db = get_db()
    cur = db.cursor()

    geoJSON = obtener_capas_geoJSON(cod_concello)

    cur.execute("SELECT id, latitud, longitud, nome_industria, sistema||'_'||cod_industria as ref, sistema as cod_edar FROM censo WHERE cod_concello = ?", (cod_concello, ))
    industrias = cur.fetchall()
    cur.execute('SELECT c.geometria FROM concellos c WHERE c.cod_ine = ?', (cod_concello,))
    concello = cur.fetchone()
    resultados = {"mapa": 'censo',
                  "cod_edar": industrias[0]['cod_edar'],
                  "concello": 1,
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
                  "titulo": "Censo",
                  "menu": "html/menu_lateral_visor.html"}
    return render_template('html/visor.html', resultados=resultados, industrias=industrias, concello=concello, geoJSON=geoJSON)

@app.route('/_muestra_ficha_industria')
@logeado_AJAX
@tokenCSRF('consultar datos da industria')
def _muestra_ficha_industria(usuario):
    id = request.args.get("id")
    db = get_db()
    cur = db.cursor()
    cur.execute("""SELECT c.*, f.ruta as ruta_foto, co.denominacion,
                u.nombre_completo AS 'representante',
                u.nif AS 'dni_representante',
                u.telefono_1 AS 'telf1_representante',
                u.telefono_2 AS 'telf2_representante',
                u.correo AS 'correo_representante',
                u2.usuario AS 'inspector'
                FROM censo c
                LEFT JOIN fotos f ON c.foto_principal = f.id
                LEFT JOIN usuarios u ON u.id = c.id_representante
                LEFT JOIN usuarios u2 ON u2.usuario = c.inspector
                LEFT JOIN concellos co ON co.cod_ine = c.cod_concello WHERE c.id = ?""", (id, ))
    datos_industria = cur.fetchone()
    cur.execute("SELECT cod_industria, sistema FROM censo")
    codigos_industria = cur.fetchall()
    cur.execute("SELECT id, fecha, tipo_inspeccion FROM inspecciones_ind WHERE id_industria = ?", (id, ))
    inspecciones = cur.fetchall()
    listado_codigos = []
    for codigo in codigos_industria:
        if codigo['cod_industria']:
            listado_codigos.append(codigo['sistema'] + "_" + codigo['cod_industria'])
        else:
            listado_codigos.append(codigo['sistema'] + "_XXX")

    if not verificarPermiso(session, datos_industria['sistema'], 0):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "Sen permisos para consultar datos da industria."}), 403

    try:
        coord_utm = utm.from_latlon(datos_industria['latitud_PV'], datos_industria['longitud_PV'])
        coord_x_PV = coord_utm[0]
        coord_y_PV = coord_utm[1]
    except:
        coord_x_PV = None
        coord_y_PV = None
    resultados = {"id": id,
                  "permiso": session["permiso"],
                  "ficha": "industria",
                  "enlace_gmaps": f"https://www.google.es/maps/@{datos_industria['latitud']},{datos_industria['longitud']},16z",
                  "coord_x_PV": coord_x_PV,
                  "coord_y_PV": coord_y_PV}
    plantilla = "html/fichas/ficha_industria.html"
    rendered = render_template(plantilla, industria=datos_industria, resultados=resultados, inspecciones=inspecciones)
    return jsonify({"valor": rendered, "listado_codigos": listado_codigos, "edicion_industrias": session["edicion_industrias"]})


@app.route('/_muestra_ficha_inspeccion_industria')
@logeado_AJAX
@tokenCSRF('mostrar ficha')
def _muestra_ficha_inspeccion_industria(usuario):
    todas = request.args.get("todas")
    id = request.args.get("id")
    #id_industria = request.form["id_industria"]
    db = get_db()
    cur = db.cursor()
    lista_ids = {"0": "i.id", "1": "i.id_industria"}
    cur.execute("""
                SELECT i.*, c.id AS id_ind, c.sistema, c.cod_industria,
                o.denominacion AS 'organismo_sol',
                u.usuario AS 'inspector_rel',
                u3.usuario AS 'supervisor',
                u2.nombre_completo AS 'interlocutor',
                u2.nif AS 'dni_interlocutor',
                u2.cargo AS 'interlocutor_cargo',
                u2.telefono_1 AS 'interlocutor_telf1',
                u2.telefono_2 AS 'interlocutor_telf2',
                u2.organizacion AS 'interlocutor_org',
                u2.correo AS 'interlocutor_correo'
                FROM inspecciones_ind i
                INNER JOIN censo c ON i.id_industria = c.id
                LEFT JOIN organismos o ON o.id = i.id_organismo_sol
                LEFT JOIN usuarios u ON u.usuario= i.inspector
                LEFT JOIN usuarios u2 ON u2.id = i.id_interlocutor
                LEFT JOIN usuarios u3 ON u3.usuario= i.supervisor
                WHERE {} = ? ORDER BY i.id DESC""".format(lista_ids[todas]),
                (id,))
    inspecciones = cur.fetchall()  


    ids_inspecciones = lista_id(inspecciones)

    cur.execute(f"""
                SELECT idn.id_inspeccion AS 'id_insp',
                dn.id,
                dn.titulo
                FROM inspecciones_doc_normativos idn
                INNER JOIN doc_normativos dn ON dn.id = idn.id_doc_normativo
                WHERE idn.id_inspeccion IN ({ids_inspecciones})""")
    doc_normativos_ind = cur.fetchall()

    if todas == '0':
        cur.execute(f"""
                    SELECT c.cod_concello
                    FROM inspecciones_ind i
                    INNER JOIN censo c ON i.id_industria = c.id
                    WHERE i.id = {id} """)
    else:
        cur.execute(f"""
                    SELECT cod_concello
                    FROM censo c 
                    WHERE c.id = {id} """)
    cod_concello = cur.fetchone()['cod_concello']

    cur.execute(f"""
                SELECT
                dn.id,
                dn.titulo
                FROM doc_normativos dn
                WHERE cod_concello LIKE '%{cod_concello}%'""")
    doc_normativos = cur.fetchall()

    if not verificarPermiso(session, inspecciones[0]['sistema'], 0):
        log(usuario, request.url, 0)
        return jsonify({"exito": -1, "erro": "sen permisos para consultar inspeccións deste sistema"}), 403

    lista_ids = []
    lista_interrogantes = ""
    for inspeccion in inspecciones:
        lista_ids.append(inspeccion['id'])
        lista_interrogantes += "?,"
    cur.execute("SELECT m.* FROM muestras m WHERE m.id_inspecciones_ind in ({})".format(lista_interrogantes[:-1]), tuple(lista_ids))
    muestras = cur.fetchall()
    lista_ids = []
    lista_interrogantes = ""
    for muestra in muestras:
        lista_ids.append(muestra['id'])
        lista_interrogantes += "?,"
    cur.execute("""SELECT a.id, a.in_situ, a.id_muestra, a.valor, p.etiqueta, 
                a.unidades, a.incertidumbre, s.codigo AS 'sonda', 
                s.parametro AS 'sonda_param'
                FROM analiticas a
                LEFT JOIN parametros p ON p.id = a.id_param
                LEFT JOIN sondas s ON s.id = a.id_sonda
                WHERE a.id_muestra in ({})""".format(lista_interrogantes[:-1]), tuple(lista_ids))
    analiticas = cur.fetchall()
    cur.execute("""SELECT *
                FROM envases e
                WHERE id_muestra in ({})""".format(lista_interrogantes[:-1]), tuple(lista_ids))
    envases = cur.fetchall()
    resultados = {"id": id,
                  "permiso": session["permiso"],
                  "ficha": "inspeccion_industria",
                  "hay_muestra": len(muestras)
                  }
    rendered = ""
    for inspeccion in inspecciones:
        if inspeccion['estado_insp'] == 0:
            plantilla = "html/fichas/ficha_planificacion_industria.html"
        else:
            plantilla = "html/fichas/ficha_inspeccion_industria.html"         

        cur.execute("""
                select c.*, ii.justificacion_muestras, ii.localizacion_pv, ii.id AS id_insp from censo c
                inner join inspecciones_ind ii  ON c.id=ii.id_industria 
                where c.id = ? order by ii.fecha DESC limit 1 offset 1""", (inspeccion['id_ind'],)) #OFFSET 1 salta el primero (más reciente) y devuelve el siguiente
        industria=cur.fetchone()
        print(' Muestra inspeccion:', industria['id_insp'])    
        rendered += render_template(plantilla, elemento=inspeccion, industria=industria, doc_normativos=doc_normativos, doc_normativos_ind=doc_normativos_ind, resultados=resultados, muestras=muestras, analiticas=analiticas, envases=envases)
    return jsonify({"valor": rendered})


@app.route('/ficha_industria-<id_industria>')
@logeado
def ficha_industria_imprimir(usuario, id_industria):
    if not verificarPermiso(session, 'galicia', 0):
        log(usuario, request.url, 0)
        return redirect('/')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT c.*, f.ruta as ruta_foto FROM censo c LEFT JOIN fotos f on 'ind'||c.foto_principal = f.tabla||f.id WHERE c.id = ?", (id_industria,))
    industria = cur.fetchone()

    cur.execute("SELECT * FROM inspecciones_ind WHERE id_industria = ? ORDER BY fecha", (id_industria,))
    inspecciones = cur.fetchall()
    id_inspecciones = lista_id(inspecciones)

    cur.execute(f"SELECT * FROM muestras WHERE id_inspecciones_ind in ({id_inspecciones})")
    muestras = cur.fetchall()
    id_muestras = lista_id(muestras)

    cur.execute("""
        SELECT *
        FROM doc_normativos DN
        INNER JOIN parametros_DN p ON p.id_DN = DN.id
        WHERE cod_concello = ?
        OR DN.id = 1
        """, (industria['concello_PV'],))
    doc_normativos_parametros = cur.fetchall()
    etiquetas_DN = lista_id(doc_normativos_parametros, 'etiqueta')
 
    cur.execute(f"""
        SELECT *
        FROM analiticas
        WHERE id_muestra in ({id_muestras})
        AND etiqueta in ({etiquetas_DN})""")
    analiticas = sqliteRow2list_dict(cur.fetchall())
    for analitica in analiticas:
        if analitica['valor'] and isinstance(analitica['valor'], str):
            valor = float(analitica['valor'].replace("<", "").replace(">", ""))
            analitica['valor_sin_incertidumbre'] = valor
        else:
            if analitica['valor'] and analitica['incertidumbre'] and (analitica['etiqueta'] != 'pH' and analitica['etiqueta'] != 'Temperatura'):
                analitica['valor_sin_incertidumbre'] = analitica['valor'] - (analitica['valor'] * analitica['incertidumbre'])
            else:
                analitica['incertidumbre'] = 0 if not analitica['incertidumbre'] else analitica['incertidumbre']
                analitica['valor_sin_incertidumbre'] = analitica['valor'] - analitica['incertidumbre']


    cumplimiento = evalua_cumplimiento(analiticas, doc_normativos_parametros)
    tabla_resumen = genera_tabla_resumen(inspecciones, muestras, analiticas, cumplimiento)

    plantilla = "html/imprimir/ficha_industria_imprimir.html"

    resultados = {"mapa": 'industria',
                  "ambito": session['ambito'],
                  "usuario": session['username'],
                  'token': session['TOKEN'],
                  "permiso": session['permiso'],
                  "diestro": session['diestro'],
                  "titulo": "Ficha Industria"}
    coordenadas = {}

    coordenadas['industria'] = utm.from_latlon(industria['latitud'], industria['longitud'])

    coordenadas['PV'] = utm.from_latlon(industria['latitud_PV'], industria['longitud_PV'])
    return render_template(plantilla,
                           industria=industria,
                           resultados=resultados,
                           inspecciones=inspecciones,
                           muestras=muestras,
                           analiticas=analiticas,
                           cumplimiento=cumplimiento,
                           tabla_resumen=tabla_resumen,
                           coordenadas=coordenadas)


def genera_tabla_resumen(inspecciones, muestras, analiticas, cumplimiento):
    """Dados las analíticas y cumplimiento, ordena los datos para generar una
    tabla en HTML.
    El resultado será una lista de listas (filas y celda de esa fila)
    Rizando el rizo: lista de listas de listas (filas, valor celda, clase celda)
    """

    resultado = [[["Parámetro", 'encabezado_tabla']],
                 [["Límite", 'encabezado_tabla']],
                 [["Unidades", 'encabezado_tabla']]]

    parametros_unidades = []
    fechas_valores = {}
    cumple_nocumple = {"CONFORME": "verde", "NON CONFORME": "rojo", "INCERTEZA": "amarillo", "-": "amarillo"}
    if cumplimiento.get('local'):
        doc_normativo = 'local'
    else:
        doc_normativo = 'decreto'
    for inspeccion in inspecciones:
        fecha = inspeccion['fecha'][-2:] + "/" + inspeccion['fecha'][4:6] + "/" + inspeccion['fecha'][0:4]
        for muestra in muestras:
            if muestra['id_inspecciones_ind'] == inspeccion['id']:
                if fecha in fechas_valores:
                    fecha += "_d"
                fechas_valores[fecha] = {}
                resultado.append([[fecha, 'encabezado_tabla']])
                for analitica in analiticas:
                    if analitica['id_muestra'] == muestra['id']:
                        for parametro_cumplimiento in cumplimiento[doc_normativo]:
                            if parametro_cumplimiento == analitica['etiqueta']:
                                for muestra_cumplimiento in cumplimiento[doc_normativo][parametro_cumplimiento]:
                                    if muestra_cumplimiento == analitica['id_muestra']:
                                        cumple = cumple_nocumple[cumplimiento[doc_normativo][parametro_cumplimiento][muestra_cumplimiento][0]]
                                        fechas_valores[fecha][analitica['etiqueta']] = [analitica['valor'], cumple]
                                        break
    for parametro in cumplimiento[doc_normativo].keys():
        if parametro == 'titulo':
            continue
        resultado[0].append([parametro, 'encabezado_tabla gris'])
        for muestra in cumplimiento[doc_normativo][parametro]:
            resultado[1].append([cumplimiento[doc_normativo][parametro][muestra][1], 'cursiva'])
            break
        for analitica in analiticas:
            if analitica['etiqueta'] == parametro and parametro not in parametros_unidades:
                resultado[2].append([analitica['unidades'], ''])
                parametros_unidades.append(parametro)
        contador_fecha = 3
        for fecha in fechas_valores:
            hay_parametro = 0
            for parametro_valor in fechas_valores[fecha]:
                if parametro_valor == parametro and not hay_parametro:
                    hay_parametro = 1
                    resultado[contador_fecha].append([fechas_valores[fecha][parametro][0], fechas_valores[fecha][parametro][1]])
                    contador_fecha += 1
            if not hay_parametro:
                resultado[contador_fecha].append(["-", ""])
                contador_fecha += 1
    return resultado


def evalua_cumplimiento(analiticas, doc_normativos_parametros):
    """Dados un listado de diccionario de analíticas y un listado de
    parámetros de diferentes documentos normativos, devuelve un diccionario de
    la forma: {"decreto": {etiqueta_parametro_1: {id_muestra: ['Conforme/No Conforme', valor_limite], id_muestra_2: ['Conforme/No Conforme', valor_limite]...}
                "local: ... "}}
    """
    cumplimiento = {"decreto": {}, "local": {}}
    analiticas = sqliteRow2list_dict(analiticas)
    for analitica in analiticas:
        if analitica['valor'] and isinstance(analitica['valor'], str):
            analitica['valor'] = float(analitica['valor'].replace("<", "").replace(">", ""))
            
        for parametroDN in doc_normativos_parametros:
            if parametroDN['etiqueta'] == analitica['etiqueta']:
                DN = "local"
                if parametroDN['id_DN'] == 1:
                    DN = "decreto"
                if not cumplimiento[DN].get('titulo'):
                    cumplimiento[DN]['titulo'] = parametroDN['titulo']
                if not cumplimiento[DN].get(analitica['etiqueta']):
                    cumplimiento[DN][analitica['etiqueta']] = {}
                parametroDN_max_min = parametroDN['valor_limite'].split('-')
                if len(parametroDN_max_min) > 1:
                    if not analitica['valor'] or not analitica['incertidumbre']:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                    elif (analitica['valor'] - analitica['incertidumbre']) > float(max(parametroDN_max_min)) or (analitica['valor'] + analitica['incertidumbre']) < float(min(parametroDN_max_min)):
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["NON CONFORME", parametroDN['valor_limite']]})
                    elif (analitica['valor'] + analitica['incertidumbre']) < float(max(parametroDN_max_min)) and (analitica['valor'] - analitica['incertidumbre']) > float(min(parametroDN_max_min)):
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["CONFORME", parametroDN['valor_limite']]})
                    else:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["INCERTEZA", parametroDN['valor_limite']]})
                elif parametroDN['etiqueta'] != "Temperatura":
                    try:
                        if not analitica['valor'] or not analitica['incertidumbre']:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                        elif (analitica['valor'] * (1 - analitica['incertidumbre'])) > float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["NON CONFORME", parametroDN['valor_limite']]})
                        elif (analitica['valor'] * (1 + analitica['incertidumbre'])) < float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["CONFORME", parametroDN['valor_limite']]})
                        else:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["INCERTEZA", parametroDN['valor_limite']]})
                    except:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                elif parametroDN['etiqueta'] == "Temperatura":
                    try:
                        if not analitica['valor'] or not analitica['incertidumbre']:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                        elif (analitica['valor'] - analitica['incertidumbre']) > float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["NON CONFORME", parametroDN['valor_limite']]})
                        elif (analitica['valor'] + analitica['incertidumbre']) < float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["CONFORME", parametroDN['valor_limite']]})
                        else:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["INCERTEZA", parametroDN['valor_limite']]})
                    except:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                            
    return cumplimiento


def cumple_todos_parametros(cumplimiento, analiticas):
    cumple = 1
    texto = ""
    incumplimientos = ""
    decreto_local = 'local'
    if not cumplimiento[decreto_local]:
        decreto_local = 'decreto'

    for parametro in cumplimiento[decreto_local]:
        if parametro == 'titulo':
            continue
        for muestra in cumplimiento[decreto_local][parametro]:
            if cumplimiento[decreto_local][parametro][muestra][0] == "NON CONFORME":
                for analitica in analiticas:
                    if analitica['etiqueta'] == parametro:
                        texto += "{} ({} {}), ".format(parametro, numero_bonito(analitica['valor']), analitica['unidades'])
                        incumplimientos += "{} ({} {}), ".format(parametro, numero_bonito(int(cumplimiento[decreto_local][parametro][muestra][1])), analitica['unidades'])
                        break
                cumple = 0
    if texto:
        texto = texto[:-2] + " superan os valores límite impostos no " + cumplimiento[decreto_local]['titulo'] + " (" + incumplimientos[:-2] + ")"
    return [cumple, texto]


@app.route("/_subir_foto_industria", methods=['POST'])
@logeado_AJAX
@tokenCSRF('subir foto')
def subir_foto_industria(usuario):
    foto = request.form["foto"]
    etiqueta = request.form["etiqueta"]
    id_industria = request.form["id"]
    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Sen permisos para subir fotos."}), 403
    if any(elem in etiqueta for elem in "();$%&#@!"):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "A etiqueta non pode ter caracteres especiais. Cambie a etiqueta e inténteo de novo"}), 403
    resultado = {}
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT i.foto_principal, i.latitud, i.longitud, sistema FROM censo i WHERE i.id = ?", (id_industria,))
    i_principal, latitud, longitud, sistema = cur.fetchone()
    if len(foto) > 1000:
        fecha = datetime.now().strftime("%Y%m%d_%H%M_%S_%f")
        ruta = fecha + "_" + sistema + "_" + id_industria + ".jpg"
        if not path.exists(Configuracion.ruta_app + 'static_p/fotos'):
            makedirs(Configuracion.ruta_app + 'static_p/fotos')
        fh = open(Configuracion.ruta_app + "static_p/fotos/" + ruta, "wb")
        fh.write(b64decode(foto))
        fh.close()
    else:
        log(usuario, request.url, 0)
        return jsonify({"exito": 0, "error": "Erro no contido."}), 400
    cur.execute('INSERT INTO fotos (id_tabla, ruta, etiqueta, tabla) VALUES (?, ?, ?, "ind")', (id_industria, ruta, etiqueta))
    ultimo_id = cur.lastrowid
    resultado.update({"codigo": 1})
    if not i_principal:
        cur.execute("UPDATE censo SET foto_principal = ? WHERE id = ?", (ultimo_id, id_industria))
        resultado.update({"principal_industria": 1})

    db.commit()
    resultado.update({"ruta": ruta})
    logCambios(usuario, "Industria", id_industria, "subeFoto", ruta, str([latitud, longitud]))
    return jsonify(resultado)


@app.route('/_borra_foto_industria', methods=['POST'])
@logeado_AJAX
@tokenCSRF('borrar foto')
def _borra_foto_industria(usuario):
    ruta = request.form["ruta"]
    foto_principal_cli = request.form["foto_principal"]
    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Sen permisos para borrar a foto."}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT c.latitud, c.longitud, c.id as id_industria FROM fotos f LEFT JOIN censo c ON f.tabla||f.id_tabla = 'ind'||c.id WHERE f.ruta = ?", (ruta,))
    latitud, longitud, id_industria = cur.fetchone()
    try:
        remove(Configuracion.ruta_app + "static_p/fotos/" + ruta)
    except:
        #en caso de que no haya foto, seguimos, para borrarla de la BBDD
        pass
    cur.execute("DELETE FROM fotos WHERE ruta = ? ", (ruta, ))
    resultado = {"codigo": 1}

    otra_foto = None
    if foto_principal_cli == ruta:
        cur.execute("SELECT id, ruta FROM fotos WHERE id_tabla = ? AND tabla = 'ind' LIMIT 1", (id_industria,))
        otra_foto = cur.fetchone()
        if not otra_foto:
            nueva_ruta = "sin_foto.png"
            cur.execute("UPDATE censo SET foto_principal == null WHERE id = ?", (id_industria,))
        else:
            nueva_ruta = otra_foto['ruta']
            cur.execute("UPDATE censo SET foto_principal == ? WHERE id = ?", (otra_foto['id'], id_industria))
        resultado.update({"nueva_ruta": nueva_ruta})

    db.commit()
    logCambios(usuario, "Industria", id_industria, "borraFoto", ruta, str([latitud, longitud]))
    return jsonify(resultado)


@app.route('/_establece_principal_industria', methods=['POST'])
@logeado_AJAX
@tokenCSRF('establecer como foto principal')
def _establece_principal_industria(usuario):
    id_foto = request.form["id"]
    ruta = request.form["ruta"]
    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Sen permisos para cambiar foto principal."}), 403
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT c.id, f.id FROM censo c LEFT JOIN fotos f ON f.id_tabla = c.id AND f.tabla = 'ind' WHERE f.ruta = ?", (ruta,))
    id_industria, id_foto = cur.fetchone()
    cur.execute("UPDATE censo SET foto_principal = ? WHERE id = ?", (id_foto, id_industria, ))
    db.commit()
    logCambios(usuario, "Industria", id_industria, "cambiada_foto_principal", id_foto, "")
    return jsonify({"codigo": 1, "id_industria": id_industria})


@app.route('/_carga_mas_fotos_industria')
@logeado_AJAX
@tokenCSRF('cargar fotos')
def _carga_mas_fotos_industria(usuario):
    id = request.args.get("id")
    if not verificarPermiso(session, 'galicia', 0):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Sen permisos para visualizar máis fotos."}), 403
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT ruta, id, etiqueta FROM fotos WHERE id_tabla = ? AND tabla = 'ind'", (id,))
    fotos = cur.fetchall()
    lista_rutas = []
    lista_ids = []
    lista_etiquetas = []
    for foto in fotos:
        lista_rutas.append(foto['ruta'])
        lista_ids.append(foto['id'])
        lista_etiquetas.append(foto['etiqueta'])
    return jsonify({"rutas": lista_rutas, "ids": lista_ids, "etiquetas": lista_etiquetas})


@app.route('/_actualiza_industria', methods=['POST', 'GET'])
@logeado_AJAX
@tokenCSRF('actualizar industria')
def _actualiza_industria(usuario):
    id = request.form["id"]
    valores = request.form["valores"]

    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para actualizar os datos da industria."}), 403
    resultado = {}
    if valores == "":
        return jsonify({"sin_datos": 1})
    """Creamos diccionarios vacíos y los llenamos con los pares clave-valor que
    vienen serializados del cliente. Cuando se trata de una muestra o analítica,
    la metemos en diccionarios aparte."""
    
    diccionario = serializado_a_diccionario(valores)
    actualizacion = actualiza_BBDD_diccionario(
        diccionario,
        'censo',
        id
        )
    if actualizacion.get('status_code') != 200:
        log_fracaso()
        return {
            "status_code": actualizacion.get('cod_error'),
            "erro": actualizacion.get('error')
        }
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM censo WHERE id = ?", (id,))
    datos = cur.fetchone()
    datos_popUp = {"cod_industria": datos['cod_industria'], "lat": datos['latitud'], "lng": datos['longitud'],
                "sistema": datos['sistema'], "nome_industria": datos['nome_industria'], "actividade": datos['actividade']}
    geometria = str([datos['latitud'], datos['longitud']])
    
    # SQL_string = "UPDATE censo SET"
    # else:
    #     cur.execute("SELECT * FROM inspecciones_ind WHERE id = ?", (id,))
    #     datos = cur.fetchone()
    #     datos_popUp = {"fecha": datos['fecha'], "tipo_inspeccion": datos['tipo_inspeccion']}
    #     geometria = ""
    #     SQL_string = "UPDATE inspecciones_ind SET"

    # actualiza censo
    # actualiza insp
    # if diccionario:
    #     columnas = datos.keys()
    #     lista_valores = []
    #     for key in diccionario:
    #         if key in ["id", "permiso", "latitud", "longitud"]:
    #             log(usuario, request.url, 0)
    #             return jsonify({"codigo": -3, "error": "Erro actualizando os datos da {}. Recargue a páxina e inténteo de novo".format(industria_inspeccion)}), 400
    #         if key not in columnas:
    #             log(usuario, request.url, 0)
    #             return jsonify({"codigo": -4, "error": "Erro actualizando os datos da {}. Recargue a páxina e inténteo de novo".format(industria_inspeccion)}), 400
    #         if key in datos_popUp:
    #             datos_popUp[key] = diccionario[key]
    #         SQL_string += " {} = ?,".format(key)
    #         lista_valores.append(diccionario[key])
    #     SQL_string = SQL_string[:-1] + " WHERE id = ?"
    #     lista_valores.append(id)
    #     cur.execute(SQL_string, tuple(lista_valores))

    # id_nuevas_muestras = {}

    # actualiza muestras
    # if diccionario_muestras:
    #     elementos_muestra = {"cod_muestra": 1, "fecha_resultados": 2} #indicamos qué lugar ocupa el parámetro en la lista dic_muestras_individuales[nueva][numMuestra]
    #     dic_muestras_individuales = {"nueva": {}, "existente": {}}
    #     for elemento in diccionario_muestras:
    #         nueva, numMuestra, tipo_elemento = elemento.split("|")
    #         if not dic_muestras_individuales[nueva].get(numMuestra):
    #             dic_muestras_individuales[nueva][numMuestra] = [id, "", ""]
    #         dic_muestras_individuales[nueva][numMuestra][elementos_muestra[tipo_elemento]] = diccionario_muestras[elemento]

    #     lista_muestras = []
    #     for muestra in dic_muestras_individuales['nueva']:
    #         lista_muestras.append(tuple(dic_muestras_individuales['nueva'][muestra]))
    #     cur.executemany("INSERT INTO muestras (id_inspecciones_ind, cod_muestra, fecha_resultados) VALUES (?, ?, ?)", lista_muestras)

    #     for muestra in dic_muestras_individuales['nueva']:
    #         cur.execute("SELECT id FROM muestras WHERE id_inspecciones_ind = ? AND cod_muestra = ?", (dic_muestras_individuales['nueva'][muestra][0], dic_muestras_individuales['nueva'][muestra][1]))
    #         id_nuevas_muestras[muestra] = cur.fetchone()['id']

    #     lista_muestras = []
    #     for muestra in dic_muestras_individuales['existente']:
    #         cur.execute("SELECT id_inspecciones_ind FROM muestras WHERE id = ?", (muestra,))
    #         if int(id) != cur.fetchone()['id_inspecciones_ind']:
    #             log(usuario, request.url, 0)
    #             return jsonify({"codigo": -5, "error": "Erro actualizando o elemento. Recargue a páxina e intenteo de novo."}), 403
    #         SQL_string = "UPDATE muestras SET"
    #         lista_valores = []
    #         for elemento_muestra in elementos_muestra:
    #             if dic_muestras_individuales['existente'][muestra][elementos_muestra[elemento_muestra]]:
    #                 SQL_string += " {} = ?,".format(elemento_muestra)
    #                 lista_valores.append(dic_muestras_individuales['existente'][muestra][elementos_muestra[elemento_muestra]])
    #         SQL_string = SQL_string[:-1] + " WHERE id = ?"
    #         lista_valores.append(muestra)
    #         cur.execute(SQL_string, tuple(lista_valores))


    # actaliza analiticas
    # if diccionario_analiticas:
    #     elementos_medicion = {"valor": 1, "etiqueta": 2, "unidades": 3, "incertidumbre": 4}
    #     dic_mediciones_individuales = {"nueva": {}, "existente": {}}
    #     for elemento in diccionario_analiticas:
    #         nueva, numMedicion, tipo_elemento, idMuestra = elemento.split("|")
    #         if nueva == 'nueva' and idMuestra in id_nuevas_muestras:
    #             idMuestra = id_nuevas_muestras[idMuestra]
    #         if not dic_mediciones_individuales[nueva].get(numMedicion):
    #             dic_mediciones_individuales[nueva][numMedicion] = [idMuestra, "", "", "", ""]
    #         dic_mediciones_individuales[nueva][numMedicion][elementos_medicion[tipo_elemento]] = diccionario_analiticas[elemento]
    #     lista_mediciones = []

    #     for medicion in dic_mediciones_individuales['nueva']:
    #         lista_mediciones.append(tuple(dic_mediciones_individuales['nueva'][medicion]))
    #     cur.executemany("INSERT INTO analiticas (id_muestra, valor, etiqueta, unidades, incertidumbre) VALUES (?, ?, ?, ?, ?)", lista_mediciones)
    #     lista_mediciones = []

    #     for medicion in dic_mediciones_individuales['existente']:
    #         cur.execute("SELECT m.id_inspecciones_ind, m.id FROM analiticas a INNER JOIN muestras m ON m.id = a.id_muestra WHERE a.id = ?", (medicion,))
    #         id_inspeccion_BD, id_muestra_BD = cur.fetchone()
    #         if int(id) != id_inspeccion_BD or int(dic_mediciones_individuales['existente'][medicion][0]) != id_muestra_BD:
    #             log(usuario, request.url, 0)
    #             return jsonify({"codigo": -6, "error": "Erro actualizando o elemento. Recargue a páxina e intenteo de novo."}), 403
    #         SQL_string = "UPDATE analiticas SET"
    #         lista_valores = []
    #         for elemento_medicion in elementos_medicion:
    #             if dic_mediciones_individuales['existente'][medicion][elementos_medicion[elemento_medicion]]:
    #                 SQL_string += " {} = ?,".format(elemento_medicion)
    #                 lista_valores.append(dic_mediciones_individuales['existente'][medicion][elementos_medicion[elemento_medicion]])
    #         SQL_string = SQL_string[:-1] + " WHERE id = ?"
    #         lista_valores.append(medicion)
    #         cur.execute(SQL_string, tuple(lista_valores))

    db.commit()
    logCambios(usuario, "Industria", id, "actualizaFicha", valores, geometria)
    resultado.update({"codigo": 1, "permiso": session['permiso'], "datos_popUp": datos_popUp})

    return jsonify(resultado)

@app.route('/_actualiza_inspeccion', methods=['POST', 'GET'])
@logeado_AJAX
@tokenCSRF('actualizar inspeccion')
def _actualiza_inspeccion(usuario):
    id = request.form["id"]
    valores = request.form["valores"]

    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para actualizar os datos da inspeccion."}), 403
    resultado = {}
    if valores == "":
        return jsonify({"sin_datos": 1}), 403
    """Creamos diccionarios vacíos y los llenamos con los pares clave-valor que
    vienen serializados del cliente. Cuando se trata de una muestra o analítica,
    la metemos en diccionarios aparte."""

    diccionario = serializado_a_diccionario(valores)

    actualizacion = actualiza_BBDD_diccionario(
        diccionario,
        'inspecciones_ind',
        id
        )
    if actualizacion.get('status_code') != 200:
        log_fracaso()
        return {
            "status_code": actualizacion.get('cod_error'),
            "erro": actualizacion.get('error')
        }

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM inspecciones_ind WHERE id = ?", (id,))
    datos = cur.fetchone()
    datos_popUp = {"fecha": datos['fecha'], "tipo_inspeccion": datos['tipo_inspeccion']}
    geometria = ""
    db.commit()
    logCambios(usuario, "Industria", id, "actualizaFicha", valores, geometria)
    resultado.update({"codigo": 1, "permiso": session['permiso'], "datos_popUp": datos_popUp})

    return jsonify(resultado)

@app.route("/_eliminar_parametro", methods=['POST'])
@logeado_AJAX
@tokenCSRF('eliminar parámetro')
def _eliminar_parametro(usuario):
    id_parametro = request.form["id_parametro"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para eliminar o parámetro."}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id_muestra FROM analiticas WHERE id = ?', (id_parametro, ))
    id_muestra = cur.fetchone()['id_muestra']
    cur.execute('DELETE FROM analiticas WHERE id = ?', (id_parametro,))
    db.commit()
    resultado = {"exito": 1}

    logCambios(usuario, 'Parámetro', id_muestra, "eliminar", "", "")
    return jsonify(resultado)


@app.route("/_eliminar_muestra", methods=['POST'])
@logeado_AJAX
@tokenCSRF('eliminar muestra')
def _eliminar_muestra(usuario):
    id_muestra = request.form["id_muestra"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para eliminar a mostra."}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM analiticas WHERE id_muestra = ?', (id_muestra,))
    cur.execute('DELETE FROM muestras WHERE id = ?', (id_muestra,))
    db.commit()
    resultado = {"exito": 1}

    logCambios(usuario, 'Muestra', id_muestra, "eliminar", "", "")
    return jsonify(resultado)


@app.route("/_mueve_industria", methods=['POST'])
@logeado_AJAX
@tokenCSRF('mover industria')
def _mueve_industria(usuario):
    id = request.form["id"]
    lat = request.form["lat"]
    lon = request.form["lon"]

    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para mover a industria."}), 403

    if not compruebaFloat(lat) or not compruebaFloat(lon):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Imposible mover a industria."}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT latitud, longitud FROM censo WHERE id = ?", (id, ))
    latitud_antigua, longitud_antigua = cur.fetchone()

    cur.execute("UPDATE censo set latitud = ?, longitud = ? WHERE id = ?", (lat, lon, id))

    logCambios(usuario, 'Industria', id, "mover", "Antes", str([float(latitud_antigua), float(longitud_antigua)]))
    logCambios(usuario, 'Industria', id, "mover", "Despois", str([float(lat), float(lon)]))
    return jsonify({"codigo": 1})


@app.route("/_crea_industria", methods=['POST'])
@logeado_AJAX
@tokenCSRF('crear industria')
def _crea_industria(usuario):
    """Recibe datos de lat, long y cod_edar desde el servidor y crea una
    industria en la BBDD.
    """
    lat = float(request.form["lat"])
    lon = float(request.form["lon"])
    cod_edar = request.form["cod_edar"]

    if not verificarPermiso(session, cod_edar, 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para crear a industria."}), 403

    if not compruebaFloat(lat) or not compruebaFloat(lon):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Imposible crear a industria."}), 400
    db = get_db()
    cur = db.cursor()
    ahora = datetime.now()
    hora = ahora.strftime("%H:%M")
    fecha = ahora.strftime("%Y%m%d")
    concello = _que_concello(usuario=usuario, latitud=lat, longitud=lon).json
    cur.execute('INSERT INTO censo (sistema, latitud, longitud, data_censo_prelim, cod_concello, inspector_censo_prelim) VALUES (?, ?, ?, ?, ?, ?)', (cod_edar, lat,lon, fecha, concello['cod_ine'], usuario))
    ultimo_id_industria = cur.lastrowid

    logCambios(usuario, "Industria", ultimo_id_industria, "creado", "", str([lat,lon]))
    db.commit()

    cur.execute("SELECT cod_industria, sistema FROM censo")
    codigos_industria = cur.fetchall()
    listado_codigos = []
    for codigo in codigos_industria:
        if codigo['cod_industria']:
            listado_codigos.append(codigo['sistema'] + "_" + codigo['cod_industria'])
        else:
            listado_codigos.append(codigo['sistema'] + "_XXX")
    enlace_gmaps = f"https://www.google.es/maps/@{lat},{lon},16z"
    plantilla = "html/fichas/ficha_industria.html"
    datos_elemento = {"id": ultimo_id_industria, "sistema": cod_edar,
                      "latitud": lat, "longitud": lon,
                      "cod_concello": concello['cod_ine'] + " - " + concello['denominacion'],
                      "enlace_gmaps": enlace_gmaps,
                      "data_censo_prelim": fecha, "inspector_censo_prelim": usuario}
    rendered = render_template(plantilla, industria=datos_elemento, resultados={"permiso": 1, 'coord_x_PV': None, 'coord_y_PV': None})
    resultado = {"codigo": 1,
                "id_elem": ultimo_id_industria,
                "permiso": session['permiso'],
                "ficha_renderizada": rendered,
                "listado_codigos": listado_codigos
                }
    return jsonify(resultado)


@app.route("/_eliminar_industria", methods=['POST'])
@logeado_AJAX
@tokenCSRF('eliminar industria')
def _eliminar_industria(usuario):
    id = request.form["id"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para eliminar a industria."}), 403

    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT latitud, longitud FROM censo WHERE id = ?', (id,))
    latitud, longitud = cur.fetchone()

    cur.execute('SELECT ruta FROM fotos WHERE id_tabla = ? AND tabla ="ind"', (id,))
    rutas_a_eliminar = cur.fetchall()
    for ruta_a_eliminar in rutas_a_eliminar:
        try:
            remove(Configuracion.ruta_app + "static_p/fotos/"+ruta_a_eliminar[0])
        except:
            pass
    cur.execute('DELETE FROM fotos WHERE id_tabla = ? AND tabla = "ind"', (id,))
    cur.execute('DELETE FROM censo WHERE id = ?', (id,))
    db.commit()
    resultado = {"exito": 1}

    logCambios(usuario, 'Industria', id, "eliminar", "", str([latitud, longitud]))
    return jsonify(resultado)


@app.route("/_existe_cod_industria")
@logeado_AJAX
@tokenCSRF('comprobar existencia código industria')
def _existe_cod_industria(usuario):
    cod_edar = request.args.get("cod_edar")
    cod_industria = request.args.get("cod_industria")
    if not verificarPermiso(session, cod_edar, 0):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para comprobar a industria."}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT cod_industria FROM censo WHERE sistema = ?', (cod_edar,))
    codigos_industria = cur.fetchall()
    resultado = {"exito": 1, "valido": 1}
    for codigo in codigos_industria:
        if cod_industria ==  codigo:
            resultado = {"codigo": 1, "valido": 0}
    return jsonify(resultado)


ALLOWED_EXTENSIONS = ["pdf"]


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/_subir_perVer", methods=['POST'])
@logeado_AJAX
@tokenCSRF('subir o permiso de vertido')
def _subir_perVer(usuario):
    id_industria = request.form["id_industria"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para subir o ficheiro. "}), 403

    if 'perVer' not in request.files:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "Erro subindo o ficheiro, comprobe que está correctamente seleccionado."}), 400
    file = request.files['perVer']
    if file.filename == '':
        log(usuario, request.url, 0)
        return jsonify({"codigo": -4, "error": "Erro co nome do ficheiro."}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT cod_industria, sistema FROM censo WHERE id = ?', (id_industria,))
    cod_industria, sistema = cur.fetchone()

    if file and allowed_file(file.filename):
        ahora = datetime.now()
        fecha = ahora.strftime("%Y%m%d")
        nombre_archivo = sistema + "_" + cod_industria + "_" + fecha
        if not path.exists(Configuracion.ruta_app + 'static_p/PV'):
            makedirs(Configuracion.ruta_app + 'static_p/PV')
        file.save(Configuracion.ruta_app + "static_p/PV/"+nombre_archivo+".pdf")
    else:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -5, "error": "Erro subindo o ficheiro. Recargue a páxina e comprobe que a extensión é '.pdf'."}), 400
    cur.execute('UPDATE censo SET ruta_PV = ? WHERE id = ?', (nombre_archivo+".pdf", id_industria))
    db.commit()
    logCambios(usuario, "PV", "", "subido", "static_p/PV/"+nombre_archivo+".pdf", "")
    return jsonify({"ruta": "/static_p/PV/"+nombre_archivo+".pdf", "filename": nombre_archivo+".pdf"})


@app.route("/_borrar_per_vert", methods=['POST'])
@logeado_AJAX
@tokenCSRF('borrar o permiso de vertido')
def _borrar_per_vert(usuario):
    id_industria = request.form["id_industria"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para subir o ficheiro. "}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT ruta_PV FROM censo WHERE id = ?", (id_industria,))
    ruta = cur.fetchone()['ruta_PV']
    try:
        remove(Configuracion.ruta_app + "static_p/PV/" + ruta)
    except:
        #en caso de que no haya archivo, seguimos, para borrar la ruta de la BBDD
        pass
    cur.execute("UPDATE censo SET ruta_PV = null WHERE id = ?", (id_industria,))
    db.commit()
    logCambios(usuario, "PV", "", "borrado", "static_p/PV/"+ruta+".pdf" + id_industria, "")
    return jsonify({"codigo": 1})


@app.route("/_subir_aai", methods=['POST'])
@logeado_AJAX
@tokenCSRF('subir a AAI')
def _subir_aai(usuario):
    id_industria = request.form["id_industria"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para subir o ficheiro. "}), 403

    if 'AAI' not in request.files:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "Erro subindo o ficheiro, comprobe que está correctamente seleccionado."}), 400
    file = request.files['AAI']
    if file.filename == '':
        log(usuario, request.url, 0)
        return jsonify({"codigo": -4, "error": "Erro co nome do ficheiro."}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT cod_industria, sistema FROM censo WHERE id = ?', (id_industria,))
    cod_industria, sistema = cur.fetchone()

    if file and allowed_file(file.filename):
        ahora = datetime.now()
        fecha = ahora.strftime("%Y%m%d")
        nombre_archivo = sistema + "_" + cod_industria + "_" + fecha
        if not path.exists(Configuracion.ruta_app + 'static_p/AAI'):
            makedirs(Configuracion.ruta_app + 'static_p/AAI')
        file.save(Configuracion.ruta_app + "static_p/AAI/"+nombre_archivo+".pdf")
    else:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -5, "error": "Erro subindo o ficheiro. Recargue a páxina e comprobe que a extensión é '.pdf'."}), 400
    cur.execute('UPDATE censo SET ruta_AAI = ? WHERE id = ?', (nombre_archivo+".pdf", id_industria))
    db.commit()
    logCambios(usuario, "AAI", "", "subido", "static_p/AAI/"+nombre_archivo+".pdf", "")
    return jsonify({"ruta": "/static_p/AAI/"+nombre_archivo+".pdf", "filename": nombre_archivo+".pdf"})


@app.route("/_borrar_aai", methods=['POST'])
@logeado_AJAX
@tokenCSRF('borrar a AAI')
def _borrar_aai(usuario):
    id_industria = request.form["id_industria"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para borrar o ficheiro. "}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT ruta_AAI FROM censo WHERE id = ?", (id_industria,))
    ruta = cur.fetchone()['ruta_AAI']
    try:
        remove(Configuracion.ruta_app + "static_p/AAI/" + ruta)
    except:
        #en caso de que no haya archivo, seguimos, para borrar la ruta de la BBDD
        pass
    cur.execute("UPDATE censo SET ruta_AAI = null WHERE id = ?", (id_industria,))
    db.commit()
    logCambios(usuario, "AAI", "", "borrado", "static_p/AAI/"+ruta+".pdf" + id_industria, "")
    return jsonify({"codigo": 1})


@app.route("/_nueva_inspeccion_industria", methods=['POST'])
@logeado_AJAX
@tokenCSRF('crear nova inspección')
def _nueva_inspeccion_ind(usuario):
    id_industria = request.form["id_industria"]

    lista_muestras = ['M1', 'M2', 'M3']

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para crear unha inspección. "}), 403

    ahora = datetime.now()
    fecha_iso = ahora.strftime("%Y%m%d")
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M")

    db = get_db()
    cur = db.cursor()
    cur.execute("""
                SELECT *
                FROM censo c
                WHERE c.id = ?
                """,(id_industria,))
    censo = cur.fetchone()

    cur.execute("""
                SELECT latitud, longitud, sistema, cod_industria, ubicacion,
                sistema_dep, mezcla_corrientes, aguas, agua_residual,
                puntos_vertido, pluviales, num_trabajadores
                FROM censo WHERE id = ?""",
                (id_industria, ))
    (latitud, longitud, sistema, cod_industria, ubicacion,
    sistema_dep, mezcla_corrientes, aguas, agua_residual,
    puntos_vertido, pluviales, num_trabajadores) = cur.fetchone()
    cod_inspeccion = fecha_iso + "_" + sistema + "_" + cod_industria
    cur.execute("""
                INSERT INTO inspecciones_ind (id_industria, inspector, fecha,
                hora, cod_inspeccion, ubicacion, sistema_dep,
                mezcla_corrientes, aguas, agua_residual, puntos_vertido,
                pluviales, num_trabajadores, estado_insp,
                ruta_PV, ruta_AAI) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                (id_industria, usuario, fecha_iso, hora, cod_inspeccion,
                 ubicacion, sistema_dep, mezcla_corrientes, aguas,
                 agua_residual, puntos_vertido, pluviales, num_trabajadores,
                 censo['ruta_PV'],censo['ruta_AAI']))
    ultimo_id = cur.lastrowid

    cur.execute("""
                INSERT INTO inspecciones_doc_normativos (id_inspeccion, id_doc_normativo) 
                VALUES (?, ?)""",
                (ultimo_id, 1))

    db.commit()
    geometria = str([latitud, longitud])
    logCambios(usuario, "Inspección industria", "", "creado", id_industria, geometria)
    for muestra in lista_muestras:
        cod_muestra = f'{cod_inspeccion}_{muestra}'
        _nueva_muestra_inspeccion(id_inspeccion = ultimo_id, cod_muestra = cod_muestra)

    import sqlite3
    db = sqlite3.connect("redes.sqlite")
    db.row_factory = sqlite3.Row   # 👈 convierte los resultados en "dict-like"
    cur = db.cursor()
    cur.execute("""
                SELECT * FROM inspecciones_ind 
                WHERE id = ?""",
                (ultimo_id, ))
    inspeccion = cur.fetchone()
    print(inspeccion['fecha'])
    #CAST(CAST(fecha AS INTEGER) + 1 AS TEXT) AS fecha_insp
    #print(inspeccion['fecha_insp'])

    cur.execute("""
                select c.*, ii.justificacion_muestras, ii.localizacion_pv, ii.id AS id_insp from censo c
                inner join inspecciones_ind ii  ON c.id=ii.id_industria 
                where c.id = ? order by ii.fecha DESC limit 1""", (id_industria,))
    industria=cur.fetchone()
    print('antigua inspeccion:', industria["id_insp"])    

    cur.execute("""
                select c.*, ii.justificacion_muestras, ii.localizacion_pv, ii.id AS id_insp from censo c
                inner join inspecciones_ind ii  ON c.id=ii.id_industria 
                where c.id = ? order by ii.fecha DESC limit 1""", (id_industria,))
    industriaN=cur.fetchone()
    print('actual inspeccion:', industriaN["id_insp"])


    resultados={}

    cur.execute("""
                SELECT * FROM muestras
                WHERE id_inspecciones_ind = ?""",
                (ultimo_id, ))
    muestras = cur.fetchall()

    ids_muestras = lista_id(muestras)
    cur.execute(f"""
                SELECT a.id, a.in_situ, a.id_muestra, a.valor, p.etiqueta, 
                a.unidades, a.incertidumbre
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                WHERE a.id_muestra IN({ids_muestras})""")
    analiticas = cur.fetchall()

    resultados = {"id": '',
                  "permiso": session["permiso"],
                  "ficha": "inspeccion_industria",
                  "hay_muestra": len(muestras)
                  }

    html = render_template("html/fichas/ficha_planificacion_industria.html",
                           elemento=inspeccion,
                           resultados=resultados,
                           muestras=muestras,
                           analiticas=analiticas,
                           industria=industria,
                           creacion = 1)
    return jsonify({"id_inspeccion": ultimo_id,
                    "fecha": fecha })


@app.route("/_eliminar_inspeccion_ind", methods=['POST'])
@logeado_AJAX
@tokenCSRF('eliminar a inspección')
def _eliminar_inspeccion_ind(usuario):
    id_inspeccion = request.form["id_inspeccion"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para eliminar a inspección. "}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM muestras WHERE id_inspecciones_ind = ?", (id_inspeccion,))
    id_muestras = cur.fetchall()
    listado_id = []
    for id_muestra in id_muestras:
        listado_id.append(id_muestra['id'])

    cur.execute("DELETE FROM analiticas WHERE id_muestra in ({}) ".format(', '.join(str(e) for e in listado_id)))
    cur.execute("DELETE FROM muestras WHERE id_inspecciones_ind = ?", (id_inspeccion, ))
    cur.execute("DELETE FROM inspecciones_ind WHERE id = ?", (id_inspeccion, ))
    db.commit()
    logCambios(usuario, "Inspección industria", "", "borrado", id_inspeccion, "")
    return jsonify({"codigo": 1})


@app.route("/_cumple_inspeccion")
@logeado_AJAX
@tokenCSRF('analizar cumprimento')
def _cumple_inspeccion(usuario):
    id_inspeccion = request.args.get("id_inspeccion")
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT a.* FROM analiticas a " +
                "INNER JOIN muestras m ON m.id = a.id_muestra " +
                "WHERE m.id_inspecciones_ind = ?", (id_inspeccion,))
    analiticas = cur.fetchall()
    cur.execute("SELECT concello_pv FROM censo c "+
                "INNER JOIN inspecciones_ind i ON c.id = i.id_industria "+
                "WHERE i.id = ?", (id_inspeccion,))
    cod_concello_pv = cur.fetchone()['concello_pv']
    cur.execute("SELECT * FROM doc_normativos dn " +
                "INNER JOIN parametros_DN pdn ON pdn.id_DN = dn.id " +
                "WHERE cod_concello = ? OR dn.id = 1", (cod_concello_pv,))
    doc_normativos_parametros = cur.fetchall()

    cumplimiento = evalua_cumplimiento(analiticas, doc_normativos_parametros)

    if not cumplimiento['decreto']:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -2, "error": "Erro ó avaliar cumprimento. Comprobe que a industria teña establecido o concello de punto de vertido e exista mostra."}), 404

    cumple, texto = cumple_todos_parametros(cumplimiento, analiticas)

    return jsonify({'cumple': cumple, "texto": texto})


@app.route("/desprega-<numero>")
@logeado
def despliega(usuario, numero):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE usuarios SET edicion_industrias = ? WHERE USUARIO = ?", (numero, usuario))
    resultados = {"error": "Despregue ficha censo",
                  "texto": f"Opcións de despregue cambiadas para {usuario}",
                  "permiso": 0,
                  "recomendacion": f"Nas fichas do censo despregarase o menú {numero} para o usuario {usuario}."
                  }
    session['edicion_industrias'] = numero
    return render_template('html/error.html', resultados=resultados)


@app.route('/_muestra_ficha_filtro_censo')
@logeado_AJAX
def _muestra_ficha_filtro_censo(usuario):
    sistema = request.args.get("sistema")
    diccionarios_filtro = extrae_diccionarios(request)
    db = get_db()
    cur = db.cursor()
    filtro_SQL = ""
    tupla_filtro = ()

    if sistema != "None":
        filtro_SQL = " WHERE c.sistema = ?"
        tupla_filtro = (sistema, )
    cur.execute("SELECT id, nome_industria, razon_social, cod_concello, sistema||'_'||cod_industria as ref, inspector_censo_prelim, sistema, actividade, outras_entidades_admin FROM censo c" + filtro_SQL, tupla_filtro)
    industrias = cur.fetchall()
    categorias = {"Concellos": [], "Sistemas": [], "Actividades": [], "Entidades": []}
    claves_categorias = {"cod_concello": "Concellos", "sistema": "Sistemas", "actividade": "Actividades", "outras_entidades_admin": "Entidades"}
    inspectores = []
    for industria in industrias:
        if industria['inspector_censo_prelim'].upper() not in inspectores:
            inspectores.append(industria['inspector_censo_prelim'].upper())
        for clave_BBDD, clave_categoria in claves_categorias.items():
            if industria[clave_BBDD] not in categorias[clave_categoria]:
                categorias[clave_categoria].append(industria[clave_BBDD])
    cur.execute("SELECT i.id, i.id_industria, i.fecha, c.sistema, c.cod_industria, fecha_evaluacion, conforme, evaluacion_afeccion_sistema, evaluacion_gestion_vertido, recomendacion_canon, recomendacion_envio_concello, fecha_envio_AG, fecha_envio_canon, fecha_registro_AG FROM inspecciones_ind i INNER JOIN censo c ON i.id_industria = c.id"+ filtro_SQL + " ORDER BY i.fecha DESC", tupla_filtro)
    inspecciones = cur.fetchall()
    plantilla = "html/fichas/ficha_filtro_censo.html"
    rendered = render_template(plantilla,
                               categorias=categorias,
                               inspectores=inspectores,
                               sistema=sistema,
                               inspecciones=inspecciones,
                               diccionarios_filtro=diccionarios_filtro)
    return jsonify({"valor": rendered})


def extrae_diccionarios(request):
    """Extrae de la request los diccionarios de filtro que están vigentes en la
    página y los ordena para ser utilizados en la generación de la ficha de filtro.
    """
    diccionarios_filtro = [{"censoæConcellos": [], "censoæprioridade_censo_prelim": [], "censoæSistemas": [], "censoæActividades": [], "censoæEntidades": []}, {"censoæConcellos": [], "censoæprioridade_censo_prelim": [], "censoæSistemas": [], "censoæActividades": [], "censoæEntidades": []}]
    claves_categorias = {"cod_concello": "Concellos", "prioridade_censo_prelim": "prioridade_censo_prelim", "sistema": "Sistemas", "actividade": "Actividades", "outras_entidades_admin": "Entidades"}
    for r in request.args:
        trozos = r.split("diccionarios_filtro")
        if len(trozos) > 1:
            indice = int(trozos[1].split("[")[1][:-1])
            clave = trozos[1].split("[")[2][:-1]
            if clave.split("æ")[1] in claves_categorias:
                clave = clave.split("æ")[0] + "æ" + claves_categorias[clave.split("æ")[1]]
                diccionarios_filtro[indice][clave] = request.args.getlist(r)
            else:
                diccionarios_filtro[indice][clave] = request.args[r]
    return diccionarios_filtro


def obten_diccionario(valores):
    claves_categorias = {"Concellos": "cod_concello", "Sistemas": "sistema", "Actividades": "actividade", "Entidades": "outras_entidades_admin"}
    diccionario = {}
    if valores:
        for par in valores.split("&"):
            clave, valor = par.split("=")
            clave = unquote_plus(clave)
            valor = unquote_plus(valor)

            if clave.split("æ")[1] in claves_categorias:
                clave = "censoæ" + claves_categorias[clave.split("æ")[1]]
            if clave in diccionario:
                if type(diccionario[clave]) is not list:
                    diccionario[clave] = [diccionario[clave]]
                diccionario[clave].append(valor)
            else:
                diccionario.update({clave: valor})
    return diccionario


def diccionario_a_SQL(diccionario, columnas, negacion, usuario):
    SQL_string = ""
    lista_valores = []
    niega = "not" if negacion else ""
    or_niega = "and" if negacion else "or "
    categorias_filtrar_muestras = ['fecha_evaluacion', "conforme", "evaluacion_afeccion_sistema", "evaluacion_gestion_vertido", "fecha_envio_AG", "fecha_envio_canon"]
    lista_valores = []
    tablas = {"censo": "c", "inspeccion": "i"}
    hay_filtro_industrias = ''
    hay_filtro_muestras = ''
    for clave in diccionario:
        key = clave.split("æ")[1]
        tabla = tablas[clave.split("æ")[0]]
        if tabla == "i":
            hay_filtro_industrias = ' and c.id = i.id_industria '

        if key not in columnas:
            log(usuario, request.url, 0)
            return ["1=0", []]

        if type(diccionario[clave]) is list:
            SQL_string += " and ("
            for filtro_multiple in diccionario[clave]:
                SQL_string += " {}.{} is {} ? {}".format(tabla, key, niega, or_niega)
                lista_valores.append(filtro_multiple)
            SQL_string = SQL_string[:-3] + ")"
        else:
            valor = diccionario[clave]
            if key in categorias_filtrar_muestras:
                if valor =='notnull':
                    valor = None
                    niega = "" if negacion else "not"
                elif valor == "null":
                    valor = None
                hay_filtro_muestras = ' INNER JOIN muestras m ON m.id_inspecciones_ind = i.id '
            SQL_string += " and {}.{} is {} ?".format(tabla, key, niega)
            lista_valores.append(valor)
    SQL_string = SQL_string[4:] + hay_filtro_industrias

    return [SQL_string, lista_valores, hay_filtro_muestras]


@app.route('/_filtra_censo')
@app.route('/_filtra_censo-<descargar>')
@logeado_AJAX
def _filtra_censo(usuario, descargar=None):
    sistema = request.args.get("sistema")
    valores = request.args.get("valores")
    valores_not = request.args.get("valores_not")
    if not verificarPermiso(session, 'galicia', 0):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para filtrar."}), 403
    diccionario = obten_diccionario(valores)
    diccionario_not = obten_diccionario(valores_not)
    db = get_db()
    cur = db.cursor()

    tablas = ["censo", "inspecciones_ind"]
    columnas = []
    for tabla in tablas:
        columnas.extend(obten_columnas(cur, tabla))
    SQL_string, lista_valores, hay_filtro_muestras = ["", [], ""]
    if diccionario:
        SQL_string, lista_valores, hay_filtro_muestras = diccionario_a_SQL(diccionario, columnas, 0, usuario)
    if diccionario_not:
        if diccionario:
            SQL_string += " and"
        SQL_string_not, lista_valores_not, hay_filtro_muestras_not = diccionario_a_SQL(diccionario_not, columnas, 1, usuario)
        SQL_string = SQL_string + SQL_string_not
        lista_valores = lista_valores + lista_valores_not
        hay_filtro_muestras = hay_filtro_muestras or hay_filtro_muestras_not
    if sistema != "None":
        if diccionario or diccionario_not:
            SQL_string += " and"
        SQL_string += " sistema = ?"
        lista_valores.append(sistema)
    if not SQL_string and not lista_valores and sistema == "None":
        SQL_string = "1 = ?"
        lista_valores = [1]

    if hay_filtro_muestras:
        SQL_string += " and i.id = m.id_inspecciones_ind "

    cur.execute("SELECT c.id, c.nome_industria, c.cod_industria, c.sistema, c.recomendase_contacto_inicial "+
                "FROM censo c "+
                "INNER JOIN inspecciones_ind i {} ".format(hay_filtro_muestras) +
                "WHERE {} ".format(SQL_string)+
                "GROUP BY c.id "+
                "ORDER BY c.sistema ASC, c.cod_industria ASC", tuple(lista_valores))
    industrias_encontradas = cur.fetchall()

    lista_id_censo = []
    for id in industrias_encontradas:
        lista_id_censo.append(id['id'])

    cur.execute("SELECT id_industria, tipo_inspeccion, count(id) as num_tipo "+
                "FROM inspecciones_ind "+
                "WHERE id_industria in ({}) ".format(', '.join(str(e) for e in lista_id_censo)) +
                "GROUP BY id_industria, tipo_inspeccion "+
                "ORDER BY tipo_inspeccion DESC")
    numero_inspecciones_tipo = cur.fetchall()

    cur.execute("SELECT i.id FROM inspecciones_ind i INNER JOIN censo c ON c.id = i.id_industria {} WHERE {}".format(hay_filtro_muestras, SQL_string), tuple(lista_valores))
    inspecciones_filtradas = cur.fetchall()
    lista_id_inspecciones = []
    for id in inspecciones_filtradas:
        lista_id_inspecciones.append(id['id'])

    if not descargar:
        SQL_string = SQL_string.replace(" and ", " e ").replace(" or ", " ou ").replace(" is not ", " non é ").replace(" is ", " é ").replace(" é 'None' ", " é nulo").replace("?", "'{}'")#.replace("c.", "")
        plantilla = "html/fichas/tabla_filtro_censo.html"

        rendered = render_template(plantilla,
                                   industrias=industrias_encontradas,
                                   sistema=sistema,
                                   numero_inspecciones_tipo=numero_inspecciones_tipo,
                                   filtros=SQL_string.format(*lista_valores))

        diccionarios_filtro = [diccionario, diccionario_not]
        return jsonify({"listado_id_censo": lista_id_censo, "tabla": rendered, "diccionarios_filtro": diccionarios_filtro, "listado_id_inspecciones": lista_id_inspecciones})
    elif descargar:
        genera_CSV(industrias_encontradas, sistema)
        return jsonify({"exito": 1})


def genera_CSV(tabla, sistema):
    if sistema == "None":
        sistema = "censo"
    f = open(Configuracion.ruta_app + "static_p/CSV/" +  session['username'] + ".csv", "w")
    primero = 1
    for cabecera in tabla[0].keys():
        if primero:
            primero = 0
        else:
            f.write("|")
        f.write(cabecera)
    f.write("\n")
    for registro in tabla:
        primero = 1
        for elemento in registro:
            if primero:
                primero = 0
            else:
                f.write("|")
            f.write(str(elemento))
        f.write("\n")
    f.close()


@app.route("/_descarga_CSV")
def envia_CSV():
    if not session.get('logged_in'):
        log(remote_ip(request), request.url, 0)
        return "logout"
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = fecha + ".csv"
    return send_file('static_p/CSV/'+ session['username'] + ".csv", download_name=archivo)

@app.route("/_actualiza_datos", methods=['POST'])
@logeado_AJAX
@tokenCSRF('actualiza datos')
def _actualiza_datos(usuario):
    datos = request.form["datos"]
    elemento = request.form["elemento"]
    id_elemento = request.form["id"]

    if not verificarPermiso(session, 'galicia', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para actualizar os datos da inspeccion."}), 403
    resultado = {}
    if datos == "":
        return jsonify({"sin_datos": 1})
    """Creamos diccionarios vacíos y los llenamos con los pares clave-valor que
    vienen serializados del cliente. Cuando se trata de una muestra o analítica,
    la metemos en diccionarios aparte."""

    db = get_db()
    cur = db.cursor()

    diccionario_datos = json.loads(datos)

    for tabla in diccionario_datos:
        for id in diccionario_datos[tabla]:
            diccionario = serializado_a_diccionario(diccionario_datos[tabla][id])

            ids_doc_normativo = None
            if 'ids_doc_normativo' in diccionario:
                ids_doc_normativo = diccionario.pop('ids_doc_normativo')
            
            actualizacion = _actualizar_datos(id, tabla, diccionario)
            if(elemento == 'industria'):
                cur.execute("SELECT * FROM censo WHERE id = ?", (id_elemento,))
                datos = cur.fetchone()
                datos_popUp = {"cod_industria": datos['cod_industria'], "lat": datos['latitud'], "lng": datos['longitud'],
                            "sistema": datos['sistema'], "nome_industria": datos['nome_industria'], "actividade": datos['actividade']}
                geometria = str([datos['latitud'], datos['longitud']])

                resultado.update({"codigo": 1, "permiso": session['permiso'], "datos_popUp": datos_popUp})
                logCambios(usuario, tabla, id, "actualizaFicha", json.dumps(diccionario_datos[tabla][id]), geometria)

            if actualizacion.get('status_code') != 200:
                return actualizacion

        if(elemento != 'industria'):
            if ids_doc_normativo:
                cur.execute("""
                        DELETE FROM inspecciones_doc_normativos
                        WHERE id_inspeccion = ?""",
                        (id,))
                for id_doc_normativo in ids_doc_normativo.split(','):
                    cur.execute("""
                                INSERT INTO inspecciones_doc_normativos (id_inspeccion,id_doc_normativo)
                                VALUES (?,?)""",
                                (id,id_doc_normativo))
            cur.execute("SELECT * FROM inspecciones_ind WHERE id = ?", (id_elemento,))
            datos = cur.fetchone()
            datos_popUp = {"fecha": datos['fecha'], "tipo_inspeccion": datos['tipo_inspeccion']}
            geometria = ""
            resultado.update({"codigo": 1, "permiso": session['permiso'], "datos_popUp": datos_popUp})

            logCambios(usuario, tabla, id, "actualizaFicha", json.dumps(diccionario_datos[tabla][id]), geometria)

    return jsonify(resultado)

def _actualizar_datos(id, tabla, diccionario):
    actualizacion = actualiza_BBDD_diccionario(
        diccionario,
        tabla,
        id
        )
    if actualizacion.get('status_code') != 200:
        log_fracaso()
        return {
            "status_code": actualizacion.get('cod_error'),
            "erro": actualizacion.get('error')
        }
    return actualizacion

# crea muestra
@app.route("/_nueva_muestra_inspeccion", methods=['POST'])
@logeado_AJAX
@tokenCSRF('crear nova muestra')
def _nueva_muestra_inspeccion(usuario, id_inspeccion = None, cod_muestra = None):
    db = get_db()
    cur = db.cursor()
    if not id_inspeccion:
        id_inspeccion = request.form["id_inspeccion"]
        cur.execute("""
                SELECT cod_inspeccion
                FROM inspecciones_ind WHERE id = ?""",
                (id_inspeccion, ))
        cod_inspeccion = cur.fetchone()['cod_inspeccion']
        cod_muestra = f'{cod_inspeccion}_'

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para crear unha mostra. "}), 403

    cur.execute("SELECT * FROM parametros WHERE por_defecto = 1")
    parametros = cur.fetchall()

    cur.execute("""
                INSERT INTO muestras (id_inspecciones_ind, cod_muestra) 
                VALUES (?, ?)""",
                (id_inspeccion, cod_muestra))
    ultimo_id = cur.lastrowid
    db.commit()
    cur.execute("""
                SELECT *
                FROM muestras WHERE id = ?""",
                (ultimo_id, ))
    muestra = cur.fetchone()

    for parametro in parametros:
        if '_M1' in cod_muestra:
            _nueva_medicion_muestra(id_muestra = ultimo_id, id_param = parametro['id'])

    _nuevo_envase_muestra(id_muestra = ultimo_id, material = 'Plástico', volumen = 1, num_envases = 1)

    cur.execute("""
                SELECT a.id, a.in_situ, a.id_muestra, a.valor, p.etiqueta, 
                a.unidades, a.incertidumbre
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                WHERE a.id_muestra = ?""",
                (ultimo_id, ))
    analiticas = cur.fetchall()

    inspeccion = {'id': id_inspeccion}

    cur.execute("""
                SELECT *
                FROM inspecciones_ind WHERE id = ?""",
                (id_inspeccion, ))
    inspeccion = cur.fetchone()

    if inspeccion['estado_insp'] == 0:
        plantilla = "html/fichas/ficha_muestra_plani.html"
    else:
        plantilla = "html/fichas/ficha_muestra.html"

    html = render_template(plantilla,analiticas = analiticas, muestra = muestra, elemento = inspeccion)
    logCambios(usuario, "Muestra inspección", "", "creado", id_inspeccion, '')
    return jsonify({"id_muestra": ultimo_id, "html": html })

# crea medicion
@app.route("/_nueva_medicion_muestra", methods=['POST'])
@logeado_AJAX
@tokenCSRF('crear nova medicion')
def _nueva_medicion_muestra(usuario, id_muestra = None, id_param = None):
    if not id_muestra:
        id_muestra = request.form["id_muestra"]
        id_param = None

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para crear unha medición. "}), 403

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                SELECT id_inspecciones_ind
                FROM muestras 
                WHERE id = ?""",
                (id_muestra, ))
    id_inspeccion = cur.fetchone()['id_inspecciones_ind']
    cur.execute("""
                SELECT IFNULL(estado_insp,0) AS 'estado_insp'
                FROM inspecciones_ind 
                WHERE id = ?""",
                (id_inspeccion, ))
    estado_insp = cur.fetchone()['estado_insp']
    cur.execute("""
                INSERT INTO analiticas (id_muestra, id_param, etapa_insp) 
                VALUES (?, ?, ?)""",
                (id_muestra, id_param, estado_insp))
    ultimo_id = cur.lastrowid
    db.commit()
    cur.execute("""
                SELECT *
                FROM muestras WHERE id = ?""",
                (id_muestra, ))
    muestra = cur.fetchone()
    cur.execute("""
                SELECT a.id, a.in_situ, a.id_muestra, a.valor, p.etiqueta, 
                a.unidades, a.incertidumbre
                FROM analiticas a
                LEFT JOIN parametros p ON p.id = a.id_param
                WHERE a.id = ?""",
                (ultimo_id, ))
    parametro = cur.fetchone()

    inspeccion = {'id': id_inspeccion}

    if estado_insp == 0:
        plantilla = "html/fichas/ficha_parametro_plani.html"
    else:
        plantilla = "html/fichas/ficha_parametro.html"

    html = render_template(plantilla, parametro = parametro,muestra=muestra, elemento = inspeccion, estado_insp=estado_insp)
    logCambios(usuario, "Parametro muestra", "", "creado", id_muestra, '')
    return jsonify({"id_param": ultimo_id, "html": html })

# crea envase
@app.route("/_nuevo_envase_muestra", methods=['POST'])
@logeado_AJAX
@tokenCSRF('crear novo envase')
def _nuevo_envase_muestra(usuario, id_muestra = None, material = None, volumen = None, num_envases = None):
    if not id_muestra:
        id_muestra = request.form["id_muestra"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para crear un envase. "}), 403

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                SELECT id_inspecciones_ind
                FROM muestras 
                WHERE id = ?""",
                (id_muestra, ))
    id_inspeccion = cur.fetchone()['id_inspecciones_ind']
    cur.execute("""
                INSERT INTO envases (id_muestra, material, volumen, num_envases) 
                VALUES (?, ?, ?, ?)""",
                (id_muestra, material, volumen, num_envases))
    ultimo_id = cur.lastrowid
    db.commit()
    cur.execute("""
                SELECT *
                FROM muestras WHERE id = ?""",
                (id_muestra, ))
    muestra = cur.fetchone()
    cur.execute("""
                SELECT *
                FROM envases e
                WHERE e.id = ?""",
                (ultimo_id, ))
    envase = cur.fetchone()

    inspeccion = {'id': id_inspeccion}

    html = render_template("html/fichas/ficha_envase_plani.html", envase = envase, muestra=muestra, elemento = inspeccion)
    logCambios(usuario, "Envase muestra", "", "creado", id_muestra, '')
    return jsonify({"id_envase": ultimo_id, "html": html })

# elimina envase
@app.route("/_eliminar_envase", methods=['POST'])
@logeado_AJAX
@tokenCSRF('eliminar envase')
def _eliminar_envase(usuario):
    id_envase = request.form["id_envase"]

    if not verificarPermiso(session, "galicia", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para eliminar o envase."}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id_muestra FROM envases WHERE id = ?', (id_envase, ))
    id_muestra = cur.fetchone()['id_muestra']
    cur.execute('DELETE FROM envases WHERE id = ?', (id_envase,))
    db.commit()
    resultado = {"exito": 1}

    logCambios(usuario, 'Envase', id_muestra, "eliminar", "", "")
    return jsonify(resultado)


#@app.route('/_informe_planificacion', methods=['POST'])
@app.route('/planificacion-<id_insp>')
@logeado
@verificaPermiso("galicia", 0)
def _informe_planificacion(id_insp, usuario):

    #id_insp = request.form["id_insp"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                UPDATE inspecciones_ind
                SET estado_insp = 1
                WHERE id=?""", (id_insp,))
    db.commit()

    cur.execute("""
                SELECT ii.*
                FROM inspecciones_ind ii
                WHERE ii.id=?""", (id_insp,))
    inspeccion = cur.fetchone()

    cur.execute(f"""
                SELECT *
                FROM doc_normativos dn
                INNER JOIN inspecciones_doc_normativos idn ON dn.id = idn.id_doc_normativo
                WHERE idn.id_inspeccion = ?
                """, (id_insp,))
    doc_normativos = cur.fetchall()

    cur.execute("""
                SELECT *
                FROM usuarios u
                WHERE u.usuario=?""", (inspeccion['inspector'],))
    inspector = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM usuarios u
                WHERE u.usuario=?""", (inspeccion['supervisor'],))
    supervisor = cur.fetchone()

    cur.execute("""
                SELECT c.*, p.nombre AS 'provincia'
                FROM censo c
                LEFT JOIN concellos co ON co.cod_ine = c.cod_concello
                LEFT JOIN provincias p ON p.id = co.id_provincia
                WHERE c.id=?""", (inspeccion['id_industria'],))
    censo = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM organismos
                WHERE id=?""", (inspeccion['id_organismo_sol'],))
    organizacion_sol = cur.fetchone()

    try:
        coord_utm = utm.from_latlon(censo['latitud_PV'], censo['longitud_PV'])
        coord_x_PV = coord_utm[0]
        coord_y_PV = coord_utm[1]
    except:
        coord_x_PV = None
        coord_y_PV = None

    cur.execute("""
                SELECT *
                FROM usuarios u
                WHERE u.id=?""", (inspeccion['id_interlocutor'],))
    representante = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM muestras m
                WHERE m.id_inspecciones_ind =?
                AND cod_muestra LIKE '%_M%'""", (inspeccion['id'],))
    muestras = cur.fetchall()

    ids_muestras = lista_id(muestras)

    cur.execute(f"""
                SELECT DISTINCT p.etiqueta, a.in_situ, s.codigo
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                LEFT JOIN sondas s ON a.id_sonda = s.id
                WHERE a.id_muestra IN ({ids_muestras})""")
    parametros = cur.fetchall()

    cur.execute(f"""
                SELECT material,
                volumen AS volumen,
                num_envases AS num_envases
                FROM envases e
                WHERE e.id_muestra IN ({ids_muestras})
                AND material IS NOT NULL
                AND volumen IS NOT NULL
                AND num_envases IS NOT NULL""")
    envases = cur.fetchall()

    cur.execute("""
                SELECT *
                FROM muestras m
                WHERE m.id_inspecciones_ind =?
                AND cod_muestra NOT LIKE '%_M%'""", (inspeccion['id'],))
    blancos = cur.fetchall()

    ids_blancos= lista_id(blancos)

    cur.execute(f"""
                SELECT DISTINCT p.etiqueta
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                WHERE a.id_muestra IN ({ids_blancos})""")
    parametros_b = cur.fetchall()

    plantilla = "html/imprimir/informe_planificacion.html"
    hoy = datetime.now()

    css = open(Configuracion.ruta_app
                 + f"static/css/estilo_imprimir.css", mode="r", encoding="utf-8")
    css_val = css.read()
    css.close()

    html = render_template(
        plantilla,
        censo=censo,
        coord_x_PV=coord_x_PV,
        coord_y_PV=coord_y_PV,
        representante=representante,
        organizacion_sol=organizacion_sol,
        inspeccion=inspeccion,
        doc_normativos=doc_normativos,
        inspector=inspector,
        supervisor=supervisor,
        muestras=muestras,
        envases=envases,
        parametros=parametros,
        blancos=blancos,
        parametros_b=parametros_b,
        css_val=css_val,
        fecha=hoy.strftime("%d/%m/%Y"))

    nombre_doc = f"informe_planificacion_{censo['sistema']}_{censo['cod_industria']}_{inspeccion['fecha']}.html"
    if not path.exists(Configuracion.ruta_app
                       + f'static_p/informes/planificacion/'):
        makedirs(Configuracion.ruta_app
                 + f'static_p/informes/planificacion/')

    f = open(Configuracion.ruta_app
                 + f'static_p/informes/planificacion/{nombre_doc}', "w")
    f.write(html)
    f.close()

    logCambios(usuario, "Informe Planificacion",
               f'{id_insp}', "generar", "", "")

    return html


#@app.route('/informe_inspeccion', methods=['POST'])
@app.route('/conformidade-<id_insp>')
@logeado
@verificaPermiso("galicia", 0)
def informe_inspeccion(usuario, id_insp):

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                UPDATE inspecciones_ind
                SET estado_insp = 1
                WHERE id=?""", (id_insp,))
    db.commit()

    cur.execute("""
                SELECT ii.*
                FROM inspecciones_ind ii
                WHERE ii.id=?""", (id_insp,))
    inspeccion = cur.fetchone()

    cur.execute(f"""
                SELECT *
                FROM doc_normativos dn
                INNER JOIN inspecciones_doc_normativos idn ON dn.id = idn.id_doc_normativo
                WHERE idn.id_inspeccion = ?
                """, (id_insp,))
    doc_normativos = cur.fetchall()

    cur.execute("""
                SELECT c.*, p.nombre AS 'provincia', e.nombre AS 'nome_EDAR'
                FROM censo c
                LEFT JOIN concellos co ON co.cod_ine = c.cod_concello
                LEFT JOIN provincias p ON p.id = co.id_provincia
                LEFT JOIN edar e ON e.cod_edar = c.sistema
                WHERE c.id=?""", (inspeccion['id_industria'],))
    censo = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM organismos
                WHERE id=?""", (inspeccion['id_organismo_sol'],))
    organizacion_sol = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM muestras m
                WHERE m.id_inspecciones_ind =?
                AND cod_muestra LIKE '%_M%'""", (inspeccion['id'],))
    muestras = cur.fetchall()

    ids_muestras = lista_id(muestras)

    cur.execute(f"""
                SELECT DISTINCT p.etiqueta, a.in_situ, s.codigo
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                LEFT JOIN sondas s ON a.id_sonda = s.id
                WHERE a.id_muestra IN ({ids_muestras})""")
    parametros = cur.fetchall()

    cur.execute("SELECT * FROM inspecciones_ind WHERE id_industria = ? ORDER BY fecha", (inspeccion['id_industria'],))
    inspecciones = cur.fetchall()

    cur = db.cursor()
    cur.execute(f"SELECT * FROM analiticas WHERE id_param=6 AND id_muestra IN ({ids_muestras})")
    insitupH = cur.fetchone()

    cur = db.cursor()
    cur.execute("SELECT * FROM analiticas WHERE id_param=7 AND id_muestra =  ?", (ids_muestras,))
    insituCdtv = cur.fetchone()

    cur = db.cursor()
    cur.execute("SELECT * FROM analiticas WHERE id_param=13 AND id_muestra =  ?", (ids_muestras,))
    insituTra = cur.fetchone()

    cur = db.cursor()
    cur.execute("select * from doc_normativos DN inner join inspecciones_doc_normativos idn ON idn.id_doc_normativo = DN.id  where id_inspeccion = ?", (id_insp,))
    #INNER JOIN parametros_DN p ON p.id_DN = DN.id
    DN_conf = cur.fetchall()
    #for doc in DN_conf:
    #    print(doc['titulo'], doc['id_doc_normativo'])

    cur.execute("""
        SELECT *
        FROM doc_normativos DN
        INNER JOIN parametros_DN p ON p.id_DN = DN.id
        INNER JOIN inspecciones_doc_normativos idn ON idn.id_doc_normativo = DN.id
        where id_inspeccion = ?""", (id_insp,))        
        #WHERE cod_concello = ?
        #OR DN.id = 1
        #""", (industria['concello_PV'],))
    doc_normativos_parametros = cur.fetchall()
    #for doc in doc_normativos_parametros:
        #print(doc['titulo'], doc['cod_concello'], doc['etiqueta'], doc['unidades'])
    etiquetas_DN = lista_id(doc_normativos_parametros, 'etiqueta')

    cur.execute(f"SELECT * FROM muestras WHERE id_inspecciones_ind in ({id_insp})")
    muestras = cur.fetchall()
    id_muestras = lista_id(muestras)

    cur.execute(f"""
        SELECT *
        FROM analiticas
        WHERE id_muestra in ({id_muestras})
        AND etiqueta in ({etiquetas_DN})""")
    analiticas = sqliteRow2list_dict(cur.fetchall())

    cur.execute(f"""
        SELECT *
        FROM analiticas
        WHERE id_muestra in ({id_muestras})
        """)
    analit_labo = sqliteRow2list_dict(cur.fetchall())

    for analitica in analiticas:
        if analitica['valor'] and isinstance(analitica['valor'], str):
            valor = float(analitica['valor'].replace("<", "").replace(">", ""))
            analitica['valor_sin_incertidumbre'] = valor
        else:
            if analitica['valor'] and analitica['incertidumbre'] and (analitica['etiqueta'] != 'pH' and analitica['etiqueta'] != 'Temperatura'):
                analitica['valor_sin_incertidumbre'] = analitica['valor'] - (analitica['valor'] * analitica['incertidumbre'])
            else:
                analitica['incertidumbre'] = 0 if not analitica['incertidumbre'] else analitica['incertidumbre']
                analitica['valor_sin_incertidumbre'] = analitica['valor'] - analitica['incertidumbre']

    plantilla = "html/imprimir/Informe_CI.html"
    hoy = datetime.now()

    css = open(Configuracion.ruta_app
                 + f"static/css/estilo_imprimir.css", mode="r", encoding="utf-8")
    css_val = css.read()
    css.close()
    
    conformidade = evalua_conformidade(analiticas, doc_normativos_parametros)
    tabla_laboratorio = genera_tabla_laboratorio(analit_labo)
    # Para decreto
    tabla_decreto, no_verdes_decreto, amarillos_decreto = genera_tabla_conformidade(inspecciones, muestras, analiticas, {'decreto': conformidade['decreto']})
    # Para local
    print('Diccionario de DN local:', conformidade['local'])
    if conformidade['local']:
        print('está LLENO')
        tabla_local, no_verdes_local, amarillos_local = genera_tabla_conformidade(inspecciones, muestras, analiticas, {'local': conformidade['local']})
    else:
        print('está VACIO')
        tabla_local, no_verdes_local, amarillos_local = genera_tabla_conformidade(inspecciones, muestras, analiticas, {})
    #tabla_conformidade, contador_conformes, contador_amarillos = genera_tabla_conformidade(inspecciones, muestras, analiticas, conformidade)
    #tablas_conformidade = genera_tabla_conformidade_multi(inspecciones, muestras, analiticas, DN_conf, cur)


    return render_template(
        plantilla,
        censo=censo,
        #coord_x_PV=coord_x_PV,
        #coord_y_PV=coord_y_PV,
        #representante=representante,
        organizacion_sol=organizacion_sol,
        inspeccion=inspeccion,
        doc_normativos=doc_normativos,
        pH=insitupH,
        condutividade=insituCdtv,
        temperatura=insituTra,
        muestras=muestras,
        parametros=parametros,
        css_val=css_val,
        #industria=industria,
        tabla_laboratorio=tabla_laboratorio,
        DN_conf=DN_conf,
        tabla_decreto=tabla_decreto,
        no_verdes_decreto=no_verdes_decreto,
        amarillos_decreto=amarillos_decreto,
        tabla_local=tabla_local,
        no_verdes_local=no_verdes_local,
        amarillos_local=amarillos_local,
        #tablas_conformidade=tablas_conformidade,
        #tabla_conformidade=tabla_conformidade,
        #contador_conformes=contador_conformes,
        #contador_amarillos=contador_amarillos,
        fecha=hoy.strftime("%d/%m/%Y"))

def genera_tabla_laboratorio(analiticas):
    """Dados las analíticas ordena los datos para generar una
    tabla en HTML.
    El resultado será una lista de listas (filas y celda de esa fila)
    Rizando el rizo: lista de listas de listas (filas, valor celda, clase celda)
    """
    #print (analiticas)

    resultado = [[["Parámetro", 'encabezado_colum_tabla gris_azul']],
                [["Valor", 'encabezado_colum_tabla gris_azul']],
                [["Unidade", 'encabezado_colum_tabla gris_azul']],
                [["Incerteza", 'encabezado_colum_tabla gris_azul']]]    
    
    for analitica in analiticas:
        if analitica['id_param'] not in (6, 7, 13):        
            resultado[0].append([analitica['etiqueta'], 'encabezado_tabla gris'])  
            if analitica['valor'] != 0:
                resultado[1].append([analitica['valor'], ''])
            else:
                resultado[1].append('-')
            resultado[2].append([analitica['unidades'], ''])
            if analitica['incertidumbre']:
                resultado[3].append([analitica['incertidumbre'], ''])
            else:
                resultado[3].append('-')
    #print(resultado)
    resultado=transponer_resultado(resultado)
    #print (resultado)
    return resultado

def genera_tabla_conformidade(inspecciones, muestras, analiticas, cumplimiento):
    """Dados las analíticas y cumplimiento, ordena los datos para generar una
    tabla en HTML.
    El resultado será una lista de listas (filas y celda de esa fila)
    Rizando el rizo: lista de listas de listas (filas, valor celda, clase celda)
    """

    resultado = [[["Parámetro", 'encabezado_colum_tabla gris_azul']],
                [["Valor", 'encabezado_colum_tabla gris_azul']],
                [["Valor límite", 'encabezado_colum_tabla gris_azul']],
                [["Unidade", 'encabezado_colum_tabla gris_azul']]]

    parametros_unidades = []
    fechas_valores = {}
    cumple_nocumple = {"CONFORME": "verde", "NON CONFORME": "rojo", "INCERTEZA": "amarillo", "-": "amarillo"}
    cumplimiento = cumplimiento or {"decreto": {}, "local": {}}
    if cumplimiento.get('local'):
        doc_normativo = 'local'
    else:
        doc_normativo = 'decreto'
    for inspeccion in inspecciones:
        fecha = inspeccion['fecha'][-2:] + "/" + inspeccion['fecha'][4:6] + "/" + inspeccion['fecha'][0:4]
        for muestra in muestras:
            if muestra['id_inspecciones_ind'] == inspeccion['id']:
                if fecha in fechas_valores:
                    fecha += "_d"
                fechas_valores[fecha] = {}
                for analitica in analiticas:
                    #print(cumplimiento)
                    if analitica['id_muestra'] == muestra['id']:
                        for parametro_cumplimiento in cumplimiento[doc_normativo]:
                            #print(parametro_cumplimiento)
                            if parametro_cumplimiento == analitica['etiqueta']:
                                for muestra_cumplimiento in cumplimiento[doc_normativo][parametro_cumplimiento]:
                                    if muestra_cumplimiento == analitica['id_muestra']:
                                        cumple = cumple_nocumple[cumplimiento[doc_normativo][parametro_cumplimiento][muestra_cumplimiento][0]]
                                        fechas_valores[fecha][analitica['etiqueta']] = [analitica['valor'], cumple]
                                        break
    for parametro in cumplimiento[doc_normativo].keys():
        if parametro == 'titulo':
            continue
        resultado[0].append([parametro, 'encabezado_tabla gris'])
        for muestra in cumplimiento[doc_normativo][parametro]:
            resultado[2].append([cumplimiento[doc_normativo][parametro][muestra][1], 'cursiva'])
            break
        for analitica in analiticas:
            if analitica['etiqueta'] == parametro and parametro not in parametros_unidades:
                if analitica['unidades']:
                    resultado[3].append([analitica['unidades'], ''])
                    parametros_unidades.append(parametro)   
                else:   
                    resultado[3].append('-')
                    parametros_unidades.append(parametro)        
        for fecha in fechas_valores:
            hay_parametro = 0
            for parametro_valor in fechas_valores[fecha]:
                if parametro_valor == parametro and not hay_parametro:
                    hay_parametro = 1
                    resultado[1].append([fechas_valores[fecha][parametro][0], fechas_valores[fecha][parametro][1]])                    
            if not hay_parametro:
                resultado[1].append(["-", ""])                
    no_verdes=0
    for fecha in fechas_valores:
        for parametro, (valor, color) in fechas_valores[fecha].items():
            if color != "verde":
                no_verdes +=1
    amarillos=0
    for fecha in fechas_valores:
        for parametro, (valor, color) in fechas_valores[fecha].items():
            if color == "amarillo":
                amarillos +=1
    resultado=transponer_resultado(resultado)
    return resultado, no_verdes, amarillos


def transponer_resultado(resultado):
    # Transpone la lista de listas (filas a columnas)
    return [list(fila) for fila in zip(*resultado)]


def evalua_conformidade(analiticas, doc_normativos_parametros):
    """Dados un listado de diccionario de analíticas y un listado de
    parámetros de diferentes documentos normativos, devuelve un diccionario de
    la forma: {"decreto": {etiqueta_parametro_1: {id_muestra: ['Conforme/No Conforme', valor_limite], id_muestra_2: ['Conforme/No Conforme', valor_limite]...}
                "local: ... "}}"""
    
    """CAMBIOS CON RESPECTO A evalua_cumlimiento: En esta función se comprueba explícitamente None y "", para que los valores de 0.0 en las analíticas no salgan como AMARILLOS por incertidumbre.
    De esta manera, se asegura que el valor de 0 se trate como válido.
    """
    cumplimiento = {"decreto": {}, "local": {}}
    analiticas = sqliteRow2list_dict(analiticas)
    for analitica in analiticas:
        if analitica['valor'] and isinstance(analitica['valor'], str):
            analitica['valor'] = float(analitica['valor'].replace("<", "").replace(">", ""))
            
        for parametroDN in doc_normativos_parametros:
            if parametroDN['etiqueta'] == analitica['etiqueta']:
                DN = "local"
                if parametroDN['id_DN'] == 1:
                    DN = "decreto"
                if not cumplimiento[DN].get('titulo'):
                    cumplimiento[DN]['titulo'] = parametroDN['titulo']
                if not cumplimiento[DN].get(analitica['etiqueta']):
                    cumplimiento[DN][analitica['etiqueta']] = {}
                parametroDN_max_min = parametroDN['valor_limite'].split('-')
                if len(parametroDN_max_min) > 1:
                    if analitica['valor'] is None or analitica['valor'] == "" or analitica['incertidumbre'] is None:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                    elif (analitica['valor'] - analitica['incertidumbre']) > float(max(parametroDN_max_min)) or (analitica['valor'] + analitica['incertidumbre']) < float(min(parametroDN_max_min)):
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["NON CONFORME", parametroDN['valor_limite']]})
                    elif (analitica['valor'] + analitica['incertidumbre']) < float(max(parametroDN_max_min)) and (analitica['valor'] - analitica['incertidumbre']) > float(min(parametroDN_max_min)):
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["CONFORME", parametroDN['valor_limite']]})
                    else:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["INCERTEZA", parametroDN['valor_limite']]})
                elif parametroDN['etiqueta'] != "Temperatura":
                    try:
                        if analitica['valor'] is None or analitica['valor'] == "" or analitica['incertidumbre'] is None:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                        elif (analitica['valor'] * (1 - analitica['incertidumbre'])) > float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["NON CONFORME", parametroDN['valor_limite']]})
                        elif (analitica['valor'] * (1 + analitica['incertidumbre'])) < float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["CONFORME", parametroDN['valor_limite']]})
                        else:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["INCERTEZA", parametroDN['valor_limite']]})
                    except:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                elif parametroDN['etiqueta'] == "Temperatura":
                    try:
                        if analitica['valor'] is None or analitica['valor'] == "" or analitica['incertidumbre'] is None:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                        elif (analitica['valor'] - analitica['incertidumbre']) > float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["NON CONFORME", parametroDN['valor_limite']]})
                        elif (analitica['valor'] + analitica['incertidumbre']) < float(parametroDN['valor_limite']):
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["CONFORME", parametroDN['valor_limite']]})
                        else:
                            cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["INCERTEZA", parametroDN['valor_limite']]})
                    except:
                        cumplimiento[DN][analitica['etiqueta']].update({analitica['id_muestra']: ["-", parametroDN['valor_limite']]})
                            
    print(cumplimiento)
    return cumplimiento
def transponer_resultado(resultado):
    return [list(fila) for fila in zip(*resultado)]


#@app.route('/_acta_inspeccion', methods=['POST'])
@app.route('/acta_inspeccion-<id_insp>')
@logeado
@verificaPermiso("galicia", 0)
def _acta_inspeccion(id_insp, usuario):

    #id_insp = request.form["id_insp"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                UPDATE inspecciones_ind
                SET estado_insp = 1
                WHERE id=?""", (id_insp,))
    db.commit()

    cur.execute("""
                SELECT ii.*
                FROM inspecciones_ind ii
                WHERE ii.id=?""", (id_insp,))
    inspeccion = cur.fetchone()

    cur.execute(f"""
                SELECT *
                FROM doc_normativos dn
                INNER JOIN inspecciones_doc_normativos idn ON dn.id = idn.id_doc_normativo
                WHERE idn.id_inspeccion = ?
                """, (id_insp,))
    doc_normativos = cur.fetchall()

    cur.execute("""
                SELECT *
                FROM usuarios u
                WHERE u.usuario=?""", (inspeccion['inspector'],))
    inspector = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM usuarios u
                WHERE u.usuario=?""", (inspeccion['supervisor'],))
    supervisor = cur.fetchone()

    cur.execute("""
                SELECT c.*, p.nombre AS 'provincia'
                FROM censo c
                LEFT JOIN concellos co ON co.cod_ine = c.cod_concello
                LEFT JOIN provincias p ON p.id = co.id_provincia
                WHERE c.id=?""", (inspeccion['id_industria'],))
    censo = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM organismos
                WHERE id=?""", (inspeccion['id_organismo_sol'],))
    organizacion_sol = cur.fetchone()

    try:
        coord_utm = utm.from_latlon(censo['latitud_PV'], censo['longitud_PV'])
        coord_x_PV = coord_utm[0]
        coord_y_PV = coord_utm[1]
    except:
        coord_x_PV = None
        coord_y_PV = None

    cur.execute("""
                SELECT *
                FROM usuarios u
                WHERE u.id=?""", (inspeccion['id_interlocutor'],))
    representante = cur.fetchone()

    cur.execute("""
                SELECT *
                FROM muestras m
                WHERE m.id_inspecciones_ind =?
                AND cod_muestra LIKE '%_M%'""", (inspeccion['id'],))
    muestras = cur.fetchall()

    ids_muestras = lista_id(muestras)

    cur.execute(f"""
                SELECT DISTINCT p.etiqueta, a.in_situ, s.codigo
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                LEFT JOIN sondas s ON a.id_sonda = s.id
                WHERE a.id_muestra IN ({ids_muestras})""")
    parametros = cur.fetchall()

    cur.execute(f"""
                SELECT material,
                volumen AS volumen,
                num_envases AS num_envases
                FROM envases e
                WHERE e.id_muestra IN ({ids_muestras})
                AND material IS NOT NULL
                AND volumen IS NOT NULL
                AND num_envases IS NOT NULL""")
    envases = cur.fetchall()

    cur.execute("""
                SELECT *
                FROM muestras m
                WHERE m.id_inspecciones_ind =?
                AND cod_muestra NOT LIKE '%_M%'""", (inspeccion['id'],))
    blancos = cur.fetchall()

    ids_blancos= lista_id(blancos)

    cur.execute(f"""
                SELECT DISTINCT p.etiqueta
                FROM analiticas a
                INNER JOIN parametros p ON p.id = a.id_param
                WHERE a.id_muestra IN ({ids_blancos})""")
    parametros_b = cur.fetchall()

    plantilla = "html/imprimir/informe_planificacion.html"
    hoy = datetime.now()

    css = open(Configuracion.ruta_app
                 + f"static/css/estilo_imprimir.css", mode="r", encoding="utf-8")
    css_val = css.read()
    css.close()

    html = render_template(
        plantilla,
        censo=censo,
        coord_x_PV=coord_x_PV,
        coord_y_PV=coord_y_PV,
        representante=representante,
        organizacion_sol=organizacion_sol,
        inspeccion=inspeccion,
        doc_normativos=doc_normativos,
        inspector=inspector,
        supervisor=supervisor,
        muestras=muestras,
        envases=envases,
        parametros=parametros,
        blancos=blancos,
        parametros_b=parametros_b,
        css_val=css_val,
        fecha=hoy.strftime("%d/%m/%Y"))

    nombre_doc = f"informe_planificacion_{censo['sistema']}_{censo['cod_industria']}_{inspeccion['fecha']}.html"
    if not path.exists(Configuracion.ruta_app
                       + f'static_p/informes/planificacion/'):
        makedirs(Configuracion.ruta_app
                 + f'static_p/informes/planificacion/')

    f = open(Configuracion.ruta_app
                 + f'static_p/informes/planificacion/{nombre_doc}', "w")
    f.write(html)
    f.close()

    logCambios(usuario, "Informe Planificacion",
               f'{id_insp}', "generar", "", "")

    return html


