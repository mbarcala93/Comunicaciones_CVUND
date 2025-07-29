# -*- coding: utf-8 -*-

from flask import render_template, request, session, jsonify, send_from_directory
from os import path, remove, makedirs
from urllib.parse import unquote_plus
from datetime import datetime
import json
from PIL import Image
import pandas
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment

from app import app

from app.auxiliar import get_db, logCambios, log, logeado,\
    logeado_AJAX, tokenCSRF, Configuracion, sqliteRow2list_dict, lista_id,\
    gira_imagen, obten_columnas, sqliteRow2dict_dict, lista_enteros,\
    verificaPermisoAuditoria, obten_sumario


@app.route("/auditorias_EDAR")
@logeado
@verificaPermisoAuditoria("id_auditoria", 0, 1)
def auditorias_EDAR(usuario, filtro=""):
    db = get_db()
    cur = db.cursor()
    cur.execute(f"""
        SELECT a.*, e.cod_edar, e.nombre, f.ruta as foto
        FROM auditorias a
        LEFT JOIN edar e ON e.id = a.id_edar
        LEFT JOIN fotos_equipos f ON a.id_foto = f.id
        {filtro}
        ORDER BY fecha DESC""")
    auditorias = sqliteRow2list_dict(cur.fetchall())
    lista_edar = []
    for indice, auditoria in enumerate(auditorias):
        if auditoria["cod_edar"] not in lista_edar:
            lista_edar.append(auditoria["cod_edar"])
            auditoria["antigua"] = 0
        else:
            auditoria["antigua"] = 1
    cur.execute("""
        SELECT id, cod_edar, nombre
        FROM edar
        WHERE asis_tecnica = 1
        ORDER BY cod_edar
        """)
    edars = cur.fetchall()
    resultados = {"pagina": "inicio"}
    return render_template(
        "html/auditorias/auditorias_EDAR.html",
        auditorias=auditorias,
        edars=edars,
        resultados=resultados
    )


@app.route("/instalacions-<cod_edar>")
@app.route("/instalacions-<cod_edar>-a<id_auditoria>")
@logeado
@verificaPermisoAuditoria("cod_edar", 0)
def instalaciones(usuario, cod_edar, id_auditoria=None):
    if id_auditoria:
        session['id_auditoria'] = int(id_auditoria)
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT i.*, e.cod_edar
        FROM instalaciones i
        LEFT JOIN edar e ON e.id = i.id_edar
        WHERE cod_edar = ?
        """, (cod_edar,))
    instalaciones = cur.fetchall()
    if instalaciones:
        id_edar = instalaciones[0]['id_edar']
        cur.execute("""
            SELECT *
            FROM importaciones
            WHERE id_edar = ?
            """, (id_edar,))
        importaciones = cur.fetchall()
    else:
        importaciones = []
    cur.execute("""
        SELECT a.*, e.cod_EDAR, e.nombre
        FROM auditorias a
        LEFT JOIN edar e ON e.id = a.id_edar
        WHERE cod_edar = ?
        ORDER BY fecha DESC
        """, (cod_edar,))
    auditorias = cur.fetchall()

    resultados = {"pagina": "instalaciones",
                  "cod_EDAR": cod_edar}
    id_instalaciones = lista_id(instalaciones)
    cur.execute(f"""
        SELECT *
        FROM tratamientos
        WHERE id_instalacion in ({id_instalaciones})
        """)
    tratamientos = cur.fetchall()
    return render_template(
        "html/auditorias/instalaciones.html",
        instalaciones=instalaciones,
        auditorias=auditorias,
        tratamientos=tratamientos,
        importaciones=importaciones,
        resultados=resultados
    )


@app.route("/equipos-edar-<cod_edar>")
@app.route("/equipos-<int:id_tratamiento>")
@logeado
@verificaPermisoAuditoria("cod_edar|id_tratamiento", 0)
def equipos(usuario, cod_edar=None, pendientes=None, id_tratamiento=None):
    resultados = {}
    db = get_db()
    cur = db.cursor()

    SQL_pendientes = ""
    if pendientes:
        SQL_pendientes += "AND e.sumario != 1.0 "
    
    SQL_motores = ""
    if session['auditorias'] is not None:
        SQL_motores = "LEFT JOIN motores m ON m.id_equipo = e.id"
        SQL_pendientes += "AND (m.id is not null OR e.id_tipo_prueba = 3) "

    if cod_edar:
        cur.execute(f"""
            SELECT e.*, ed.cod_EDAR, ed.nombre as nombre_EDAR
            FROM equipos e
            LEFT JOIN tratamientos t ON t.id = e.id_tratamiento
            LEFT JOIN instalaciones i ON i.id = t.id_instalacion
            LEFT JOIN edar ed ON i.id_edar = ed.id
            {SQL_motores}
            WHERE ed.cod_EDAR = ? {SQL_pendientes}""", (cod_edar,))
        equipos = cur.fetchall()
        tratamiento_texto = None
        nombre_EDAR = equipos[0]['nombre_EDAR']
    else:
        cur.execute(f"""
            SELECT e.*
            FROM equipos e
            {SQL_motores}
            WHERE id_tratamiento = ?
            {SQL_pendientes}
            """, (id_tratamiento, ))
        equipos = cur.fetchall()
        cur.execute("""
            SELECT t.nombre, ed.cod_EDAR, ed.nombre as nombre_EDAR
            FROM tratamientos t
            LEFT JOIN instalaciones i ON i.id = t.id_instalacion
            LEFT JOIN edar ed ON i.id_edar = ed.id
            WHERE t.id = ?""", (id_tratamiento,))
        tratamiento = cur.fetchone()
        tratamiento_texto = tratamiento['nombre']
        cod_edar = tratamiento['cod_EDAR']
        nombre_EDAR = tratamiento['nombre_EDAR']
    resultados = {'pagina': "equipos",
                  'tratamiento': tratamiento_texto,
                  'cod_EDAR': cod_edar,
                  'nombre_EDAR': nombre_EDAR}
    cur.execute("""
        SELECT a.*, e.cod_EDAR, e.nombre
        FROM auditorias a
        LEFT JOIN edar e ON e.id = a.id_edar
        WHERE cod_edar = ?
        ORDER BY fecha DESC
        """, (cod_edar,))
    auditorias = cur.fetchall()

    id_equipos = lista_id(equipos)
    cur.execute(f"""
        SELECT id, id_equipo, id_auditoria, estado_equipo, estado_motor,
                hay_motor, hay_fotos_equipo, hay_fotos_motor
        FROM observaciones_audit_equipo
        WHERE id_equipo in ({id_equipos})
        """)
    observaciones = cur.fetchall()
    return render_template(
        "html/auditorias/equipos.html",
        equipos=equipos,
        auditorias=auditorias,
        observaciones=observaciones,
        resultados=resultados
    )


@app.route("/equipo-<int:id_equipo>")
@logeado
@verificaPermisoAuditoria("id_equipo", 0)
def equipo(usuario, id_equipo):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT *
        FROM tipos_pruebas
        WHERE obsoleta is null
        OR obsoleta = 0
        """)
    tipos_pruebas = cur.fetchall()

    cur.execute("""
        SELECT eq.*, tp.titulo
        FROM equipos eq
        LEFT JOIN tipos_pruebas tp ON tp.id = eq.id_tipo_prueba
        WHERE eq.id = ?""", (id_equipo,))
    equipo = cur.fetchone()

    cur.execute("""
        SELECT *, re.id_equipo as id_elemento
        FROM revisiones_equipos re
        LEFT JOIN revisiones_disponibles rd
        ON rd.id = re.id_revision_disponible
        WHERE id_equipo = ?
        ORDER BY id_auditoria""", (id_equipo,))
    revisiones = cur.fetchall()
    cur.execute("""
        SELECT *
        FROM observaciones_audit_equipo
        WHERE id_equipo = ?
        ORDER BY id_auditoria""", (id_equipo,))
    observaciones = cur.fetchall()
    cur.execute("""
        SELECT t.nombre, ed.cod_EDAR, ed.nombre as nombre_EDAR
        FROM tratamientos t
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar ed ON i.id_edar = ed.id
        WHERE t.id = ?""", (equipo['id_tratamiento'],))
    tratamiento = cur.fetchone()

    cur.execute("""
        SELECT id, ruta, tipo
        FROM fotos_equipos
        WHERE id_equipo = ?
        AND tipo = 1
        """, (id_equipo,))
    foto_portada = cur.fetchone()

    cur.execute("""
        SELECT id, denominacion
        FROM motores
        WHERE id_equipo = ?
        """, (id_equipo,))
    motores = cur.fetchall()

    cur.execute(f"""
        SELECT a.*
        FROM auditorias a
        LEFT JOIN edar ed ON a.id_edar = ed.id
        LEFT JOIN instalaciones i ON i.id_edar = ed.id
        LEFT JOIN tratamientos t ON t.id_instalacion = i.id
        LEFT JOIN equipos e ON e.id_tratamiento = t.id
        WHERE e.id = ?
        """, (id_equipo,))
    auditorias = cur.fetchall()

    resultados = {'pagina': "equipo",
                  'tratamiento': tratamiento['nombre'].capitalize(),
                  'cod_EDAR': tratamiento['cod_EDAR'],
                  'nombre_EDAR': tratamiento['nombre_EDAR']}

    return render_template(
        "html/auditorias/equipo.html",
        equipo=equipo,
        elemento="",
        revisiones=revisiones,
        foto_portada=foto_portada,
        tipos_pruebas=tipos_pruebas,
        observaciones=observaciones,
        motores=motores,
        auditorias=auditorias,
        resultados=resultados
    )


@app.route("/_navega_equipo")
@logeado
@verificaPermisoAuditoria('id_equipo', 0)
def _navega_equipo(usuario):
    id_equipo = request.args.get('id_equipo')
    id_tratamiento = request.args.get('id_tratamiento')
    siguiente = int(request.args.get('siguiente'))
    SIGNOS = ["<", ">"]
    MAXMIN = ['MAX', 'MIN']
    db = get_db()
    cur = db.cursor()
    cur.execute(f"""
        SELECT {MAXMIN[siguiente]}(id) as id_navegar
        FROM equipos
        WHERE id {SIGNOS[siguiente]} ?
        AND id_tratamiento = ?
        """, (id_equipo, id_tratamiento))
    id_navegar = cur.fetchone()['id_navegar']
    if id_navegar:
        url =  f"{request.scheme}://{request.host}/equipo-{id_navegar}"
    else:
        url = None
    return jsonify({"url": url})

@app.route("/revisions_pendentes-<cod_edar>")
@logeado
@verificaPermisoAuditoria("cod_edar", 0)
def revisiones_pendentes(usuario, cod_edar):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT re.*, e.denominacion, e.id as id_equipo,
                e.tipo, e.posicion, ed.cod_edar, ed.nombre as nombre_EDAR,
                rd.actividad
        FROM revisiones_equipos re
        LEFT JOIN revisiones_disponibles rd
            ON rd.id = re.id_revision_disponible
        LEFT JOIN equipos e
            ON e.id = re.id_equipo
        LEFT JOIN tratamientos t
            ON t.id = e.id_tratamiento
        LEFT JOIN instalaciones i
            ON i.id = t.id_instalacion
        LEFT JOIN edar ed
            ON i.id_edar = ed.id
        WHERE re.estado = 0 AND ed.cod_edar = ?""", (cod_edar, ))
    revisiones = cur.fetchall()
    resultados = {
        'pagina': "tareas_pte",
        "cod_EDAR": revisiones[0]['cod_edar'],
        "nombre_EDAR": revisiones[0]['nombre_EDAR']}
    return render_template(
        "html/auditorias/revisiones_pendientes.html",
        revisiones=revisiones,
        resultados=resultados
    )


@app.route("/fichas-<cod_edar>")
@app.route("/ficha-<int:id_equipo>")
@logeado
@verificaPermisoAuditoria("galicia", 0)
def ficha_equipo(usuario, cod_edar=None, id_equipo=None):
    db = get_db()
    cur = db.cursor()

    resultados = {
        "cod_EDAR": cod_edar,
        "id_equipo": id_equipo
    }
    if not cod_edar:
        filtro_SQL = "WHERE eq.id = ?"
        tupla_SQL = (id_equipo,)
        cur.execute("""
        SELECT a.id
        FROM auditorias a
        LEFT JOIN edar e ON a.id_edar = e.id
        LEFT JOIN instalaciones i ON i.id_edar = e.id
        LEFT JOIN tratamientos t ON t.id_instalacion = i.id
        LEFT JOIN equipos eq ON eq.id_tratamiento = t.id
        WHERE eq.id = ?
        """, (id_equipo,))
    else:
        filtro_SQL = """
            LEFT JOIN edar ed ON i.id_edar = ed.id
            WHERE ed.cod_EDAR = ?
            """
        tupla_SQL = (cod_edar,)
        cur.execute("""
        SELECT a.id
        FROM auditorias a
        LEFT JOIN edar e ON a.id_edar = e.id
        WHERE e.cod_EDAR = ?
        """, (cod_edar,))
    ids_auditoria = sqliteRow2dict_dict(cur.fetchall())
    if 'id_auditoria' in session and session['id_auditoria'] in ids_auditoria:
        id_auditoria = session['id_auditoria']
    else:
        id_auditoria = max(ids_auditoria)

    cur.execute(f"""
        SELECT eq.*, t.nombre as n_tratamiento, tp.*
        FROM equipos eq
        LEFT JOIN tratamientos t ON t.id = eq.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        INNER JOIN tipos_pruebas tp ON tp.id = eq.id_tipo_prueba
        {filtro_SQL}
        ORDER BY tp.id
        """, tupla_SQL)
    equipos = cur.fetchall()
    id_equipos = lista_id(equipos)
        
    cur.execute(f"""
        SELECT *
        FROM revisiones_equipos re
        LEFT JOIN revisiones_disponibles rd
        ON rd.id = re.id_revision_disponible
        WHERE id_equipo in ({id_equipos})
        AND id_auditoria = ?
        """, (id_auditoria,))
    revisiones = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM observaciones_audit_equipo
        WHERE id_equipo in ({id_equipos})
        AND id_auditoria = ?
        """, (id_auditoria,))
    observaciones = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM fotos_equipos
        WHERE id_equipo in ({id_equipos})
        AND id_auditoria = ?
        ORDER BY portada DESC, tipo
        """, (id_auditoria,))
    fotos = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM motores
        WHERE id_equipo in ({id_equipos})
        """)
    motores = cur.fetchall()
    id_motores = lista_id(motores)
    cur.execute(f"""
        SELECT *
        FROM revisiones_motores re
        LEFT JOIN revisiones_disponibles rd
        ON rd.id = re.id_revision_disponible
        WHERE id_motor in ({id_motores})
        AND id_auditoria = ?
        """, (id_auditoria,))
    revisiones_motores = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM fotos_motores
        WHERE id_motor in ({id_motores})
        AND id_auditoria = ?
        ORDER BY portada DESC
        """, (id_auditoria,))
    fotos_motores = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM observaciones_audit_motor
        WHERE id_motor in ({id_motores})
        AND id_auditoria = ?
        """, (id_auditoria,))
    observaciones_motores = cur.fetchall()
    
    old = "_legacy" if id_auditoria < 10 else ""

    plantilla = f"html/auditorias/ficha_equipos_imprimir{old}.html"

    return render_template(
        plantilla,
        equipos=equipos,
        revisiones=revisiones,
        fotos=fotos,
        observaciones=observaciones,
        motores=motores,
        revisiones_motores=revisiones_motores,
        fotos_motores=fotos_motores,
        observaciones_motores=observaciones_motores,
        resultados=resultados
        )

@app.route("/revisions-<cod_edar>")
@app.route("/revision-<int:id_equipo>")
@logeado
@verificaPermisoAuditoria("galicia", 0)
def ficha_equipo_2(usuario, cod_edar=None, id_equipo=None):
    db = get_db()
    cur = db.cursor()

    resultados = {
        "cod_EDAR": cod_edar,
        "id_equipo": id_equipo
    }
    if not cod_edar:
        filtro_SQL = "WHERE eq.id = ?"
        tupla_SQL = (id_equipo,)
        cur.execute("""
        SELECT a.id
        FROM auditorias a
        LEFT JOIN edar e ON a.id_edar = e.id
        LEFT JOIN instalaciones i ON i.id_edar = e.id
        LEFT JOIN tratamientos t ON t.id_instalacion = i.id
        LEFT JOIN equipos eq ON eq.id_tratamiento = t.id
        WHERE eq.id = ?
        """, (id_equipo,))
    else:
        filtro_SQL = """
            LEFT JOIN edar ed ON i.id_edar = ed.id
            WHERE eq.id >4249 AND ed.cod_EDAR = ?
            """
        tupla_SQL = (cod_edar,)
        cur.execute("""
        SELECT a.id
        FROM auditorias a
        LEFT JOIN edar e ON a.id_edar = e.id
        WHERE e.cod_EDAR = ?
        """, (cod_edar,))
    ids_auditoria = sqliteRow2dict_dict(cur.fetchall())
    if 'id_auditoria' in session and session['id_auditoria'] in ids_auditoria:
        id_auditoria = session['id_auditoria']
    else:
        id_auditoria = max(ids_auditoria)

    cur.execute(f"""
        SELECT eq.*, t.nombre as n_tratamiento, tp.*
        FROM equipos eq
        LEFT JOIN tratamientos t ON t.id = eq.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        INNER JOIN tipos_pruebas tp ON tp.id = eq.id_tipo_prueba
        {filtro_SQL}
        ORDER BY tp.id
        """, tupla_SQL)
    equipos = cur.fetchall()
    id_equipos = lista_id(equipos)
        
    cur.execute(f"""
        SELECT *
        FROM revisiones_equipos re
        LEFT JOIN revisiones_disponibles rd
        ON rd.id = re.id_revision_disponible
        WHERE id_equipo in ({id_equipos})
        AND id_auditoria = ?
        """, (id_auditoria,))
    revisiones = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM observaciones_audit_equipo
        WHERE id_equipo in ({id_equipos})
        AND id_auditoria = ?
        """, (id_auditoria,))
    observaciones = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM fotos_equipos
        WHERE id_equipo in ({id_equipos})
        AND id_auditoria = ?
        AND portada = 1
        ORDER BY portada DESC, tipo
        """, (id_auditoria,))
    fotos = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM motores
        WHERE id_equipo in ({id_equipos})
        """)
    motores = cur.fetchall()
    id_motores = lista_id(motores)
    cur.execute(f"""
        SELECT *
        FROM revisiones_motores re
        LEFT JOIN revisiones_disponibles rd
        ON rd.id = re.id_revision_disponible
        WHERE id_motor in ({id_motores})
        AND id_auditoria = ?
        """, (id_auditoria,))
    revisiones_motores = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM fotos_motores
        WHERE id_motor in ({id_motores})
        AND id_auditoria = ?
        ORDER BY portada DESC
        """, (id_auditoria,))
    fotos_motores = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM observaciones_audit_motor
        WHERE id_motor in ({id_motores})
        AND id_auditoria = ?
        """, (id_auditoria,))
    observaciones_motores = cur.fetchall()
    
    old = "_legacy" if id_auditoria < 10 else ""

    plantilla = f"html/auditorias/ficha_equipos_imprimir_rev{old}.html"

    return render_template(
        plantilla,
        equipos=equipos,
        revisiones=revisiones,
        fotos=fotos,
        observaciones=observaciones,
        motores=motores,
        revisiones_motores=revisiones_motores,
        fotos_motores=fotos_motores,
        observaciones_motores=observaciones_motores,
        resultados=resultados
        )



@app.route("/_nueva_auditoria", methods=['POST'])
@logeado_AJAX
@tokenCSRF("crear auditoría")
@verificaPermisoAuditoria("galicia", 1)
def _nueva_auditoria(usuario):
    id_edar = request.form.get("id_edar")
    db = get_db()
    cur = db.cursor()
    fecha = int(datetime.now().timestamp())
    cur.execute("""
        INSERT INTO auditorias (id_edar, fecha)
        VALUES (?, ?)
        """, (id_edar, fecha))
    id_auditoria = cur.lastrowid
    cur.execute(f"""
        SELECT e.id, {id_auditoria} as id_auditoria
        FROM equipos e
        LEFT JOIN tratamientos t ON t.id = e.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar ed ON ed.id = i.id_edar
        WHERE ed.id = ?
        """, (id_edar,))
    equipos_id_auditoria = cur.fetchall()
    cur.executemany("""
        INSERT INTO observaciones_audit_equipo
        (id_equipo, id_auditoria)
        VALUES (?, ?)
        """, equipos_id_auditoria)

    cur.execute(f"""
        SELECT m.id, {id_auditoria} as id_auditoria
        FROM motores m
        LEFT JOIN equipos e ON e.id = m.id_equipo
        LEFT JOIN tratamientos t ON t.id = e.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar ed ON ed.id = i.id_edar
        WHERE ed.id = ?
        """, (id_edar,))
    motores_id_auditoria = cur.fetchall()
    
    cur.executemany("""
        INSERT INTO observaciones_audit_motor
        (id_motor, id_auditoria)
        VALUES (?, ?)
        """, motores_id_auditoria)
    
    db.commit()

    cur.execute("""
        SELECT cod_edar, nombre
        FROM edar
        WHERE id = ?
        """, (id_edar,))
    
    cod_edar, nombre = cur.fetchone()
    nueva_auditoria = {
        "cod_edar": cod_edar,
        "nombre": nombre,
        "fecha": fecha
    }
    boton_nueva_auditoria = render_template(
        'html/auditorias/boton_auditoria.html',
        auditoria=nueva_auditoria)
    logCambios(
        usuario,
        "auditorias",
        id_auditoria,
        "C",
        json.dumps(nueva_auditoria, ensure_ascii=False),
        "")
    return jsonify({"boton_nueva_auditoria": boton_nueva_auditoria})


@app.route("/_nueva_instalacion", methods=['POST'])
@logeado_AJAX
@tokenCSRF("crear instalación")
@verificaPermisoAuditoria("galicia", 1)
def _nueva_instalacion(usuario):
    nombre = request.form.get("nombre")
    cod_edar = request.form.get("cod_edar")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id
        FROM edar
        WHERE cod_edar = ?
        """, (cod_edar,))
    id_edar = cur.fetchone()['id']
    cur.execute("""
        INSERT INTO instalaciones (id_edar, nombre)
        VALUES (?, ?)
        """, (id_edar, nombre))
    id_instalacion = cur.lastrowid
    db.commit()
    instalacion = {
            'id': id_instalacion,
            'nombre': nombre,
            'id_edar': id_edar
            }
    panel_nueva_instalacion = render_template(
        'html/auditorias/panel_instalacion.html',
        instalacion=instalacion,
        tratamientos=[]
        )
    logCambios(
        usuario,
        "instalaciones",
        id_instalacion,
        "C",
        json.dumps(instalacion),
        "")
    return jsonify({"panel_nueva_instalacion": panel_nueva_instalacion})


@app.route("/_nuevo_tratamiento", methods=['POST'])
@logeado_AJAX
@tokenCSRF("crear tratamento")
@verificaPermisoAuditoria("galicia", 1)
def _nuevo_tratamiento(usuario):
    nombre = request.form.get("nombre")
    id_instalacion = request.form.get("id_instalacion")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO tratamientos (id_instalacion, nombre)
        VALUES (?, ?)
        """, (id_instalacion, nombre))
    id_tratamiento = cur.lastrowid
    db.commit()
    tratamiento = {
            'id': id_tratamiento,
            'nombre': nombre,
            'id_instalacion': id_instalacion
            }
    instalacion = {"id": id_instalacion}
    panel_nuevo_tratamiento = render_template(
        'html/auditorias/panel_tratamiento.html',
        tratamiento=tratamiento,
        instalacion=instalacion
        )
    logCambios(
        usuario,
        "tratamientos",
        id_tratamiento,
        "C",
        nombre,
        "")
    return jsonify({"panel_nuevo_tratamiento": panel_nuevo_tratamiento})


@app.route("/_nuevo_equipo", methods=['POST'])
@logeado_AJAX
@tokenCSRF("crear equipo")
@verificaPermisoAuditoria("galicia", 1)
def _nuevo_equipo(usuario):
    denominacion = request.form.get("denominacion")
    id_tratamiento = request.form.get("id_tratamiento")
    db = get_db()
    cur = db.cursor()
    
    cur.execute("""
        INSERT INTO equipos (id_tratamiento, denominacion)
        VALUES (?, ?)
        """, (id_tratamiento, denominacion))
    id_equipo = cur.lastrowid
    cur.execute("""
        SELECT max(a.id) as max_id
        FROM equipos eq
        LEFT JOIN tratamientos t ON t.id = eq.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar ed ON ed.id = i.id_edar
        LEFT JOIN auditorias a ON a.id_edar = ed.id
        WHERE eq.id = ?
        """, (id_equipo,))
    id_auditoria = cur.fetchone()['max_id']
    cur.execute("""
        INSERT INTO observaciones_audit_equipo
        (id_equipo, id_auditoria)
        VALUES (?, ?)
        """, (id_equipo, id_auditoria))
    db.commit()
    equipo = {
            'id': id_equipo,
            'denominacion': denominacion,
            'id_tratamiento': id_tratamiento
        }
    observaciones = [{
        "id_equipo": id_equipo,
        "id_auditoria": id_auditoria,
        "estado_equipo": 0,
        "estado_motor": 0,
        "hay_motor": 0,
        "hay_fotos_equipo": 0,
        "hay_fotos_motor": 0
    }]
    boton_nuevo_equipo = render_template(
        'html/auditorias/boton_equipo.html',
        equipo=equipo,
        observaciones=observaciones
        )
    logCambios(
        usuario,
        "equipos",
        id_equipo,
        "C",
        json.dumps(equipo),
        "")
    return jsonify({"boton_nuevo_equipo": boton_nuevo_equipo})


@app.route("/_borra_instalacion", methods=['POST'])
@logeado_AJAX
@tokenCSRF("eliminar a instalación")
@verificaPermisoAuditoria("galicia", 1)
def _borra_instalacion(usuario):
    id_instalacion = request.form.get("id_instalacion")
    
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT id
        FROM tratamientos
        WHERE id_instalacion = ?
        """, (id_instalacion,))                
    tratamientos = cur.fetchall()
    for tratamiento in tratamientos:
        _borra_tratamiento(id_tratamiento=tratamiento['id'])

    cur.execute("""
        DELETE FROM instalaciones
        WHERE id = ?
        """, (id_instalacion,))
    db.commit()

    logCambios(
        usuario,
        "instalaciones",
        id_instalacion,
        "D",
        "",
        "")
    return jsonify({})


@app.route("/_borra_tratamiento", methods=['POST'])
@logeado_AJAX
@tokenCSRF("eliminar o tratamento")
@verificaPermisoAuditoria("galicia", 1)
def _borra_tratamiento(usuario, id_tratamiento=None):
    if not id_tratamiento:
        id_tratamiento = request.form.get("id_tratamiento")
    
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT id
        FROM equipos
        WHERE id_tratamiento = ?
        """, (id_tratamiento,))                
    equipos = cur.fetchall()
    for equipo in equipos:
        _borra_equipo(id_equipo=equipo['id'])
    cur.execute("""
        SELECT e.cod_edar
        FROM tratamientos t
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar e ON e.id = i.id_edar
        WHERE t.id = ?
        """, (id_tratamiento,))
    cod_edar = cur.fetchone()['cod_edar']
    cur.execute("""
        DELETE FROM tratamientos
        WHERE id = ?
        """, (id_tratamiento,))
    
    db.commit()
    logCambios(
        usuario,
        "tratamientos",
        id_tratamiento,
        "D",
        "",
        "")
    redireccion = f"{request.scheme}://{request.host}/instalacions-{cod_edar}"
    return jsonify({"redireccion": redireccion})


@app.route("/_borra_equipo", methods=['POST'])
@logeado_AJAX
@tokenCSRF("eliminar o equipo")
@verificaPermisoAuditoria("galicia", 1)
def _borra_equipo(usuario, id_equipo=None):
    if not id_equipo:
        id_equipo = request.form.get("id_equipo")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id_tratamiento
        FROM equipos e
        WHERE e.id = ?
        """, (id_equipo,))
    id_tratamiento = cur.fetchone()['id_tratamiento']
    cur.execute("""
        SELECT id
        FROM fotos_equipos
        WHERE id_equipo = ?
        """, (id_equipo,))                
    fotos = cur.fetchall()
    for foto in fotos:
        _borra_foto_elem_audit(id_foto=foto['id'], elemento='equipos')
    
    cur.execute("""
        DELETE FROM revisiones_equipos
        WHERE id_equipo = ?
        """, (id_equipo,))
    cur.execute("""
        DELETE FROM observaciones_audit_equipo
        WHERE id_equipo = ?
        """, (id_equipo,))

    cur.execute("""
        SELECT id
        FROM motores
        WHERE id_equipo = ?
        """, (id_equipo,))                
    motores = cur.fetchall()
    for motor in motores:
        _borra_motor(id_motor=motor['id'])

    cur.execute("""
        DELETE FROM equipos
        WHERE id = ?
        """, (id_equipo,))
    db.commit()

    logCambios(
        usuario,
        "equipos",
        id_equipo,
        "D",
        "",
        "")
    redireccion = f"{request.scheme}://{request.host}/equipos-{id_tratamiento}"
    return jsonify({"redireccion": redireccion})



@app.route("/_actualiza_datos_equipo", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar os datos do equipo")
@verificaPermisoAuditoria("galicia", 1)
def _actualiza_datos_equipo(usuario):
    cambios = request.form['cambios']
    id_equipo = request.form['id_equipo']

    db = get_db()
    cur = db.cursor()
    diccionario = {}
    if cambios:
        for par in cambios.split("&"):
            clave, valor = par.split("=")
            valor = unquote_plus(valor)
            diccionario.update({clave: valor})
    else:
        log(usuario, request.url, 0)
        return jsonify({
            "error": "Cambios non validos"
        })
    if diccionario:
        SQL_string = "UPDATE equipos SET"
        columnas = obten_columnas(cur, 'equipos')
        lista_valores = []
        for key in diccionario:
            if key in ["id", "observaciones", "marca", "modelo", "num_serie", "criticidad", "mediciones"]:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -4, "error": "Erro actualizando os datos. Recargue a páxina e inténteo de novo"}), 400
            if key not in columnas:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -5, "error": "Erro actualizando os datos. Recargue a páxina e inténteo de novo"}), 400
            SQL_string += " {} = ?,".format(key)
            lista_valores.append(diccionario[key])
        SQL_string = SQL_string[:-1] + " WHERE id = ?"
        lista_valores.append(id_equipo)
        cur.execute(SQL_string, tuple(lista_valores))
        db.commit()
        logCambios(
            usuario,
            "equipos",
            id_equipo,
            "U",
            cambios,
            "")
    return jsonify(), 200


@app.route("/_actualiza_equipo", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar os datos do equipo")
@verificaPermisoAuditoria("id_auditoria|tipo_prueba3", 1)
def _actualiza_equipo(usuario):
    usuario = session['username']
    cambios = json.loads(request.form['cambios'])
    observaciones_json = request.form.get("observaciones")
    observaciones = json.loads(observaciones_json)
    marca = request.form['marca']
    modelo = request.form['modelo']
    num_serie = request.form['num_serie']
    criticidad = request.form['criticidad']
    mediciones = request.form['mediciones']
    id_equipo = request.form['id_equipo']

    db = get_db()
    cur = db.cursor()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    id_auditoria = None
    for revision in cambios:
        cur.execute("""
            UPDATE revisiones_equipos
            SET id_inspector = ?, fecha = ?, estado = ?
            WHERE id = ?""", (usuario, fecha, cambios[revision], revision))
        id_auditoria = session['id_auditoria']
        if not id_auditoria:
            cur.execute("""
                SELECT id_auditoria
                FROM revisiones_equipos
                WHERE id = ?""", (revision))
            id_auditoria = cur.fetchone()['id_auditoria']
    if id_auditoria:
        cur.execute("""
                SELECT estado
                FROM revisiones_equipos
                WHERE id_equipo = ?
                AND id_auditoria = ?
                """, (id_equipo, id_auditoria))
        revisiones_equipo = cur.fetchall()
        sumario = obten_sumario(revisiones_equipo)
        cur.execute("""
            UPDATE observaciones_audit_equipo
            SET estado_equipo = ?
            WHERE id_equipo = ?
            AND id_auditoria = ?
            """, (sumario, id_equipo, id_auditoria))

    if mediciones:
        for par in mediciones.split("&"):
            id_revision, valor = par.split("=")
            valor = unquote_plus(valor)
            cur.execute("""
                UPDATE revisiones_equipos
                SET medicion = ?
                WHERE id = ?
                """, (valor, id_revision))

    cur.execute("""
        UPDATE equipos
        SET marca = ?, modelo = ?, num_serie = ?, criticidad = ?
        WHERE id = ?
        """, (
            marca,
            modelo,
            num_serie,
            criticidad,
            id_equipo
            ))
    if observaciones:
        for id, observacion in observaciones.items():
            cur.execute("""
                UPDATE observaciones_audit_equipo
                SET observacion = ?
                WHERE id = ?
                """, (observacion, id))
    db.commit()
    logCambios(
        usuario,
        "equipos",
        id_equipo,
        "U",
        json.dumps(cambios),
        "")
    return jsonify({"id_inspector": usuario.upper(), "fecha": fecha})


@app.route("/_ver_fotos_equipo")
@logeado_AJAX
@verificaPermisoAuditoria("id_equipo", 0)
def _ver_fotos_equipo(usuario):
    id_equipo = request.args.get("id_equipo")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT ruta, tipo, id, id_auditoria, portada
        FROM fotos_equipos
        WHERE id_equipo = ?
        ORDER BY tipo""", (id_equipo,))
    fotos = cur.fetchall()
    paneles_fotos = ""
    num_foto = 0
    elemento = "equipos"
    for foto in fotos:
        paneles_fotos += render_template(
            "html/comunes/panel_foto.html",
            num_foto=num_foto,
            elemento=elemento,
            foto=foto)
        num_foto += 1
    return jsonify(fotos=paneles_fotos)


ALLOWED_EXTENSIONS = {
    "imagen": ["jpg", 'png', 'jpeg'],
    "excel": ["xlsx"]
    }


def allowed_file(filename, tipo):
    return '.' in filename and \
           filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS[tipo]


@app.route("/_subir_foto_equipo", methods=['POST'])
@logeado_AJAX
@tokenCSRF("subir foto do equipo")
@verificaPermisoAuditoria("galicia", 1)
def _subir_foto_equipo(usuario):
    file = request.files['foto']
    id_equipo = request.form["id_equipo"]
    db = get_db()
    cur = db.cursor()
    if file and allowed_file(file.filename, 'imagen'):
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S%f")
        extension = "." + file.filename.split(".")[-1]
        ruta = fecha + "-eq" + id_equipo + extension
        ruta_completa = f"app/static_p/fotos_audit/"
        if not path.exists(ruta_completa):
            makedirs(ruta_completa)
        file.save(ruta_completa + ruta)
    else:
        return jsonify({
            "codigo": -5,
            "erro": "Erro subindo o ficheiro. "
                    + "Recargue a páxina e comprobe que se trata dun "
                    + "ficheiro de imaxen."}), 400
    cur.execute("""
        SELECT a.id 
        FROM equipos eq
        LEFT JOIN tratamientos t ON t.id = eq.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar ed ON ed.id = i.id_edar
        LEFT JOIN auditorias a ON a.id_edar = ed.id
        WHERE eq.id = ?
        """, (id_equipo,))
    auditorias = sqliteRow2dict_dict(cur.fetchall())
    if session["id_auditoria"] in auditorias:
        id_auditoria = session["id_auditoria"]
    else:
        id_auditoria = max(auditorias.keys())
    cur.execute("""
        SELECT max(tipo) as tipo
        FROM fotos_equipos
        WHERE id_equipo = ?
        """, (id_equipo,))
    foto_existente = cur.fetchone()
    if foto_existente['tipo']:
        tipo = foto_existente['tipo'] + 1
        tipo = 3 if tipo > 3 else tipo
    else:
        tipo = 1
    cur.execute("""
        INSERT INTO fotos_equipos (
            id_equipo,
            tipo,
            ruta,
            id_auditoria
            )
        VALUES (?, ?, ?, ?)
        """, (id_equipo, tipo, ruta, id_auditoria))
    id_foto = cur.lastrowid
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET hay_fotos_equipo = 1
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (id_equipo, id_auditoria))
    resultado = {"tipo": tipo, "ruta": ruta}
    db.commit()

    generarThumbnail(ruta_completa, ruta, 300, 'tn')

    logCambios(
        usuario,
        "fotos_equipos",
        id_foto,
        "C",
        ruta,
        "")
    return jsonify(resultado)


def generarThumbnail(ruta_imagen, archivo, dimensiones, carpeta):
    try:
        img = Image.open(f'{ruta_imagen}{archivo}').convert('RGB')
        SIZE = (dimensiones, dimensiones)
        img.thumbnail(SIZE)
        if not path.exists(f'{ruta_imagen}{carpeta}/'):
            makedirs(f'{ruta_imagen}{carpeta}/')
        img.save(f'{ruta_imagen}{carpeta}/{archivo}')
    except Exception as e:
        print(f"---- {e}")
        print(archivo)


@app.route("/_borra_foto_elem_audit", methods=['POST'])
@logeado_AJAX
@tokenCSRF("borrar foto do equipo")
@verificaPermisoAuditoria("galicia", 1)
def _borra_foto_elem_audit(usuario, id_foto=None, elemento=None):
    if not id_foto:
        id_foto = request.form.get("id_foto")
    if not elemento:
        elemento = request.form.get('elemento')
    db = get_db()
    cur = db.cursor()
    TABLAS = {"equipos": {
                "tabla": "fotos_equipos",
                "id": "id_equipo",
                "hay_fotos": "equipo"
                },
              "motores": {
                  "tabla": "fotos_motores",
                  "id": "id_motor",
                  "hay_fotos": "motor"
                }
            }
    cur.execute(f"""
        SELECT ruta, tipo,
            {TABLAS[elemento]['id']} as id_elemento, id_auditoria
        FROM {TABLAS[elemento]['tabla']}
        WHERE id = ?
        """, (id_foto,))
    datos_foto = cur.fetchone()
    ruta_completa = f"{Configuracion.ruta_app}static_p/fotos_audit/"
    try:
        remove(ruta_completa + datos_foto['ruta'])
        remove(ruta_completa + 'tn/' + datos_foto['ruta'])
    except Exception as e:
        pass
    _cambia_tipo(id_foto=id_foto, tipo=3, elemento=elemento)
    cur.execute(f"""
        DELETE FROM {TABLAS[elemento]['tabla']}
        WHERE id = ?
        """, (id_foto,))

    cur.execute(f"""
        SELECT id
        FROM {TABLAS[elemento]['tabla']}
        WHERE {TABLAS[elemento]['id']} = ?
        AND id_auditoria = ?
        """, (datos_foto['id_elemento'], datos_foto['id_auditoria']))
    otras_fotos = cur.fetchall()
    if otras_fotos:
        hay_foto = 1
    else:
        hay_foto = 0
    cur.execute(f"""
        UPDATE observaciones_audit_equipo
        SET hay_fotos_{TABLAS[elemento]['hay_fotos']} = ?
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (hay_foto,
              datos_foto['id_elemento'],
              datos_foto['id_auditoria'])
              )

    db.commit()
    logCambios(
        usuario,
        TABLAS[elemento]['tabla'],
        id_foto,
        "D",
        datos_foto['ruta'],
        "")
    return jsonify({})


@app.route("/_gira_foto", methods=['POST'])
@logeado_AJAX
@tokenCSRF("xirar a foto")
@verificaPermisoAuditoria("galicia", 1)
def _gira_foto(usuario):
    id_foto = request.form.get('id_foto')
    elemento = request.form.get('elemento')
    db = get_db()
    cur = db.cursor()
    TABLAS = {"equipos": "fotos_equipos",
              "motores": "fotos_motores"}
    cur.execute(f"""
        SELECT ruta
        FROM {TABLAS[elemento]}
        WHERE id = ?
        """, (id_foto,))
    ruta = cur.fetchone()
    if ruta:
        ruta_completa = f"{Configuracion.ruta_app}static_p/fotos_audit/"
        ruta = ruta['ruta']
        gira_imagen(ruta_completa + ruta)
        gira_imagen(ruta_completa + "tn/" + ruta)
    return jsonify({"ruta": ruta})


@app.route("/_promociona_foto", methods=['POST'])
@logeado_AJAX
@tokenCSRF("promocionar a foto")
@verificaPermisoAuditoria("galicia", 1)
def _promociona_foto(usuario):
    id_foto = request.form.get('id_foto')
    elemento = request.form.get('elemento')
    db = get_db()
    cur = db.cursor()
    TABLAS = {"equipos": "fotos_equipos",
              "motores": "fotos_motores"}
    cur.execute(f"""
        SELECT portada
        FROM {TABLAS[elemento]}
        WHERE id = ?
        """, (id_foto,))
    portada = cur.fetchone()['portada']
    portada = 0 if not portada else portada
    portada = abs(portada - 1)
    cur.execute(f"""
        UPDATE {TABLAS[elemento]}
        SET portada = ?
        WHERE id = ?
        """, (portada, id_foto))
    db.commit()
    return jsonify({})


@app.route("/_promociona_auditoria", methods=['POST'])
@logeado_AJAX
@tokenCSRF("promocionar a foto")
@verificaPermisoAuditoria("galicia", 1)
def _promociona_auditoria(usuario):
    id_foto = request.form.get('id_foto')
    elemento = request.form.get('elemento')
    if elemento == 'motores':
        return jsonify({
            "erro": "So se poden aisgnar como fotos da auditoría fotos de equipos."
        }), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE auditorias
        SET id_foto = ?
        WHERE id = 
            (SELECT a.id
            FROM auditorias a
            LEFT JOIN edar ed ON a.id_edar = ed.id
            LEFT JOIN instalaciones i ON i.id_edar = ed.id
            LEFT JOIN tratamientos t ON t.id_instalacion = i.id
            LEFT JOIN equipos e ON e.id_tratamiento = t.id
            LEFT JOIN fotos_equipos f ON f.id_equipo = e.id
            WHERE f.id = ?)
        """, (id_foto, id_foto))
    db.commit()
    return jsonify({})


@app.route("/_cambia_tipo", methods=['POST'])
@logeado_AJAX
@tokenCSRF("cambiar o tipo de foto")
@verificaPermisoAuditoria("galicia", 1)
def _cambia_tipo(usuario, id_foto=None, tipo=None, elemento=None):
    if not id_foto:
        id_foto = request.form.get("id_foto")
    if not tipo:
        tipo = request.form.get("tipo")
    if not elemento:
        elemento = request.form.get("elemento")
    TABLAS = {"equipos": ["fotos_equipos", "id_equipo"],
              "motores": ["fotos_motores", "id_motor"]}
    db = get_db()
    cur = db.cursor()
    cur.execute(f"""
        SELECT {TABLAS[elemento][1]}, tipo, ruta
        FROM {TABLAS[elemento][0]}
        WHERE id = ? """, (id_foto,))
    id_equipo, tipo_antiguo, ruta = cur.fetchone()
    cur.execute(f"""
        UPDATE {TABLAS[elemento][0]}
        SET tipo = 3
        WHERE {TABLAS[elemento][1]} = ?
        AND tipo = ?""", (id_equipo, tipo))
    if tipo_antiguo == 1 or tipo_antiguo == 2:
        cur.execute(f"""
        UPDATE {TABLAS[elemento][0]}
        SET tipo = ?
        WHERE id =
            (SELECT min(id)
            FROM {TABLAS[elemento][0]}
            WHERE {TABLAS[elemento][1]} = ?
            AND tipo = 3)
        """, (tipo_antiguo, id_equipo))

    cur.execute(f"""
        UPDATE {TABLAS[elemento][0]}
        SET tipo = ?
        WHERE id = ? """, (tipo, id_foto))
    db.commit()
    return jsonify({"ruta": ruta, f"{TABLAS[elemento][1]}": id_equipo})


@app.route("/_cambia_tipo_prueba", methods=['POST'])
@logeado_AJAX
@tokenCSRF("cambiar o tipo de proba")
@verificaPermisoAuditoria("galicia", 1)
def _cambia_tipo_prueba(usuario):
    id_equipo = request.form.get("id_equipo")
    id_tipo_prueba = request.form.get("id_tipo_prueba")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE equipos
        SET id_tipo_prueba = ?
        WHERE id = ?
        """, (id_tipo_prueba, id_equipo))
    db.commit()
    return jsonify()


@app.route("/_cambia_filtro_auditoria", methods=['POST'])
@logeado_AJAX
@verificaPermisoAuditoria("id_auditoria", 0)
def _cambia_filtro_auditoria(usuario):
    id_auditoria = request.form.get("id_auditoria")
    id_auditoria = int(id_auditoria)
    if session.get('id_auditoria') == id_auditoria:
        session['id_auditoria'] = None
    else:
        session['id_auditoria'] = id_auditoria
    return jsonify()


@app.route("/_muestra_ficha_motor")
@logeado_AJAX
@verificaPermisoAuditoria("id_motor", 0)
def _muestra_ficha_motor(usuario):
    id_motor = request.args.get("id_motor")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT m.*
        FROM motores m
        WHERE m.id = ?
        """, (id_motor,))
    motor = cur.fetchone()

    cur.execute("""
        SELECT *, rm.id_motor as id_elemento
        FROM revisiones_motores rm
        LEFT JOIN revisiones_disponibles rd
        ON rm.id_revision_disponible = rd.id
        WHERE id_motor = ?
        """, (id_motor,))
    revisiones_motor = cur.fetchall()
    
    cur.execute("""
        SELECT *
        FROM observaciones_audit_motor
        WHERE id_motor = ?
        """, (id_motor,))

    observaciones = cur.fetchall()

    panel = render_template(
        "html/auditorias/panel_motor.html",
        motor=motor,
        revisiones_motor=revisiones_motor,
        observaciones=observaciones,
        elemento="Motor"
        )
    return jsonify({"panel": panel})


@app.route("/_nuevo_motor", methods=['POST'])
@logeado_AJAX
@tokenCSRF("crear novo motor")
@verificaPermisoAuditoria("galicia", 1)
def _nuevo_motor(usuario):
    id_equipo = request.form.get("id_equipo")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT denominacion
        FROM equipos
        WHERE id = ?
        """, (id_equipo,))
    denominacion_equipo = cur.fetchone()['denominacion']
    cur.execute("""
        INSERT INTO motores
        (denominacion, id_equipo)
        VALUES(?, ?)
        """, (denominacion_equipo, id_equipo,))
    id_motor = cur.lastrowid
    motor = {
        "id": id_motor,
        "denominacion": denominacion_equipo
    }

    cur.execute("""
        SELECT max(a.id) as max_id
        FROM motores m
        LEFT JOIN equipos eq ON eq.id = m.id_equipo
        LEFT JOIN tratamientos t ON t.id = eq.id_tratamiento
        LEFT JOIN instalaciones i ON i.id = t.id_instalacion
        LEFT JOIN edar ed ON ed.id = i.id_edar
        LEFT JOIN auditorias a ON a.id_edar = ed.id
        WHERE m.id = ?
        """, (id_motor,))
    id_auditoria = cur.fetchone()['max_id']
    cur.execute("""
        INSERT INTO observaciones_audit_motor
        (id_motor, id_auditoria)
        VALUES (?, ?)
        """, (id_motor, id_auditoria))
    observacion = {
        "id_auditoria": id_auditoria,
        "id": cur.lastrowid,
        "observacion": ""
    }
    boton = render_template(
        "html/auditorias/boton_motor.html",
        motor=motor
    )
    panel = render_template(
        "html/auditorias/panel_motor.html",
        motor=motor,
        observaciones=[observacion],
        elemento="Motor"
    )
    cur.execute("""
        SELECT estado
        FROM revisiones_motores rm
        LEFT JOIN motores m ON m.id = rm.id_motor
        LEFT JOIN equipos e ON e.id = m.id_equipo
        WHERE e.id = ?
        """, (id_equipo,))
    revisiones_motores = cur.fetchall()
    sumario = obten_sumario(revisiones_motores)
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET hay_motor = 1
        WHERE id_equipo = ?
        """, (id_equipo,))
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET estado_motor = ?,
            hay_fotos_motor = 0
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (sumario,
              id_equipo,
              id_auditoria)
              )
    db.commit()
    logCambios(
        usuario,
        "motores",
        motor['id'],
        "C",
        "",
        "")
    return jsonify({
        "boton": boton,
        "panel": panel,
        "id_motor": motor['id']
        })


@app.route("/_actualiza_datos_motor", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar os datos do motor")
@verificaPermisoAuditoria("galicia", 1)
def _actualiza_datos_motor(usuario):
    cambios = request.form['cambios']
    id_motor = request.form['id_motor']

    db = get_db()
    cur = db.cursor()
    diccionario = {}
    if cambios:
        for par in cambios.split("&"):
            clave, valor = par.split("=")
            valor = unquote_plus(valor)
            diccionario.update({clave: valor})
    else:
        log(usuario, request.url, 0)
        return jsonify({
            "error": "Cambios non validos"
        })
    if diccionario:
        SQL_string = "UPDATE motores SET"
        columnas = obten_columnas(cur, 'equipos')
        lista_valores = []
        for key in diccionario:
            if key in ["id"]:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -4, "error": "Erro actualizando os datos. Recargue a páxina e inténteo de novo"}), 400
            if key not in columnas:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -5, "error": "Erro actualizando os datos. Recargue a páxina e inténteo de novo"}), 400
            SQL_string += " {} = ?,".format(key)
            lista_valores.append(diccionario[key])
        SQL_string = SQL_string[:-1] + " WHERE id = ?"
        lista_valores.append(id_motor)
        cur.execute(SQL_string, tuple(lista_valores))
        db.commit()
        logCambios(
            usuario,
            "motores",
            id_motor,
            "U",
            cambios,
            "")
    return jsonify(), 200


@app.route("/_actualiza_motor", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar datos do motor")
@verificaPermisoAuditoria("id_motor", 1)
def _actualiza_motor(usuario):
    id_motor = request.form.get("id_motor")
    datos_motor = request.form.get("datos_motor")
    estado_revisiones_json = request.form.get("estado_revisiones")
    observaciones_json = request.form.get("observaciones")
    mediciones = request.form.get("mediciones")
    
    estado_revisiones = json.loads(estado_revisiones_json)
    observaciones = json.loads(observaciones_json)
    db = get_db()
    cur = db.cursor()
    columnas = obten_columnas(cur, "motores")
    string_SQL = ""
    lista_SQL = []
    if datos_motor:
        for par in datos_motor.split("&"):
            clave, valor = par.split("=")
            valor = unquote_plus(valor)
            if clave not in columnas:
                log(usuario, request.url, 0)
                return jsonify({
                    "codigo": -2,
                    "error": "[Columnas] Recargue a páxina e intenteo de novo"
                    }), 403
            string_SQL += f" {clave} = ?,"
            lista_SQL.append(valor)
    lista_SQL.append(id_motor)
    cur.execute(f"""
        UPDATE motores
        SET {string_SQL[:-1]}
        WHERE id = ?
        """, tuple(lista_SQL))
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    revisiones_act = {}
    id_auditoria = session['id_auditoria']
    for revision in estado_revisiones:
        estado = estado_revisiones[revision]
        cur.execute("""
            UPDATE revisiones_motores
            SET estado = ?, id_inspector = ?, fecha = ?
            WHERE id = ?
            """, (estado, usuario, fecha, revision))
        revisiones_act[revision] = {"fecha": fecha, "usuario": usuario}
        if not id_auditoria:
            cur.execute("""
                SELECT r.id_auditoria FROM revisiones_motores r
                WHERE r.id = ?
                """, (revision,))
            id_auditoria = cur.fetchone()['id_auditoria']

    cur.execute("""
        SELECT e.id FROM equipos e
        LEFT JOIN motores m ON m.id_equipo = e.id
        WHERE m.id = ?
        """, (id_motor,))
    id_equipo = cur.fetchone()['id']
    cur.execute("""
        SELECT estado
        FROM revisiones_motores rm
        LEFT JOIN motores m ON m.id = rm.id_motor
        LEFT JOIN equipos e ON e.id = m.id_equipo
        WHERE e.id = ?
        AND rm.id_auditoria = ?
        """, (id_equipo, id_auditoria))
    revisiones_motores = cur.fetchall()
    sumario = obten_sumario(revisiones_motores)
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET estado_motor = ?
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (sumario,
              id_equipo,
              id_auditoria)
              )

    if mediciones:
        for par in mediciones.split("&"):
            id_revision, valor = par.split("=")
            valor = unquote_plus(valor)
            cur.execute("""
                UPDATE revisiones_motores
                SET medicion = ?
                WHERE id = ?
                """, (valor, id_revision))
    if observaciones:
        for id, observacion in observaciones.items():
            cur.execute("""
                UPDATE observaciones_audit_motor
                SET observacion = ?
                WHERE id = ?
                """, (observacion, id))
    db.commit()
    logCambios(
        usuario,
        "motores",
        id_motor,
        "U",
        datos_motor,
        "")
    logCambios(
        usuario,
        "revisiones_motores",
        id_motor,
        "U",
        estado_revisiones_json,
        "")
    logCambios(
        usuario,
        "observaciones_audit_motor",
        id_motor,
        "U",
        observaciones_json,
        "")
    return jsonify({"revisiones_act": revisiones_act})


@app.route("/_borra_motor", methods=['POST'])
@logeado_AJAX
@tokenCSRF("borrar motor")
@verificaPermisoAuditoria("galicia", 1)
def _borra_motor(usuario, id_motor=None):
    if not id_motor:
        id_motor = request.form.get("id_motor")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        DELETE FROM revisiones_motores
        WHERE id_motor = ?
        """, (id_motor,))
    cur.execute("""
        DELETE FROM fotos_motores
        WHERE id_motor = ?
        """, (id_motor,))
    cur.execute("""
        DELETE FROM observaciones_audit_motor
        WHERE id_motor = ?
        """, (id_motor,))

    cur.execute("""
    SELECT a.id
    FROM motores m
    LEFT JOIN equipos eq ON eq.id = m.id_equipo
    LEFT JOIN tratamientos t ON t.id = eq.id_tratamiento
    LEFT JOIN instalaciones i ON i.id = t.id_instalacion
    LEFT JOIN edar ed ON ed.id = i.id_edar
    LEFT JOIN auditorias a ON a.id_edar = ed.id
    WHERE m.id = ?
    """, (id_motor,))
    auditorias = cur.fetchall()
    cur.execute("""
        SELECT e.id
        FROM equipos e
        LEFT JOIN motores m ON e.id = m.id_equipo
        WHERE m.id = ?
        """, (id_motor,))
    id_equipo = cur.fetchone()['id']
    cur.execute("""
        SELECT count(id) as num_motores
        FROM motores
        WHERE id_equipo = ?
        """, (id_equipo,))
    num_motores = cur.fetchone()['num_motores']
    hay_motor = 1 if num_motores > 1 else 0
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET hay_motor = ?
        WHERE id_equipo = ?
        """, (hay_motor, id_equipo))
    for auditoria in auditorias:
        cur.execute("""
            SELECT estado
            FROM revisiones_motores rm
            LEFT JOIN motores m ON m.id = rm.id_motor
            LEFT JOIN equipos e ON e.id = m.id_equipo
            WHERE e.id = ?
            AND rm.id_auditoria = ?
            """, (id_equipo, auditoria['id']))
        revisiones_motores = cur.fetchall()
        sumario = obten_sumario(revisiones_motores)
        cur.execute(f"""
            UPDATE observaciones_audit_equipo
            SET estado_motor = ?
            WHERE id_equipo = ?
            AND id_auditoria = ?
            """, (sumario,
                id_equipo,
                auditoria['id'])
                )
    cur.execute("""
        DELETE FROM motores
        WHERE id = ?
        """, (id_motor,))
    db.commit()
    logCambios(
        usuario,
        "motores",
        id_motor,
        "D",
        "",
        "")
    return jsonify({})


@app.route("/_subir_foto_motor", methods=['POST'])
@logeado_AJAX
@tokenCSRF("subir foto do motor")
@verificaPermisoAuditoria("galicia", 1)
def _subir_foto_motor(usuario):
    file = request.files['foto']
    id_motor = request.form["id_motor"]
    id_auditoria = request.form["id_auditoria"]
    db = get_db()
    cur = db.cursor()
    if file and allowed_file(file.filename, 'imagen'):
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S%f")
        extension = "." + file.filename.split(".")[-1]
        ruta = fecha + "-mt" + id_motor + extension
        ruta_completa = f"app/static_p/fotos_audit/"
        if not path.exists(ruta_completa):
            makedirs(ruta_completa)
        file.save(ruta_completa + ruta)
    else:
        return jsonify({
            "codigo": -5,
            "erro": "Erro subindo o ficheiro. "
                    + "Recargue a páxina e comprobe que se trata dun "
                    + "ficheiro de imaxen."}), 400
    cur.execute("""
        SELECT max(tipo) as tipo
        FROM fotos_motores
        WHERE id_motor = ?
        """, (id_motor,))
    foto_existente = cur.fetchone()
    if foto_existente['tipo']:
        tipo = foto_existente['tipo'] + 1
        tipo = 3 if tipo > 3 else tipo
    else:
        tipo = 1
    cur.execute("""
        INSERT INTO fotos_motores 
            (
            id_motor,
            tipo,
            ruta,
            id_auditoria
            )
        VALUES (?, ?, ?, ?)
        """, (id_motor, tipo, ruta, id_auditoria))
    ultimo_id = cur.lastrowid
    resultado = {"tipo": tipo}
    cur.execute("""
        SELECT e.id
        FROM equipos e
        LEFT JOIN motores m ON e.id = m.id_equipo
        WHERE m.id = ?
        """, (id_motor,))
    id_equipo = cur.fetchone()['id']
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET hay_fotos_motor = 1
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (id_equipo, id_auditoria))
    db.commit()

    generarThumbnail(ruta_completa, ruta, 300, 'tn')

    logCambios(
        usuario,
        "fotos_motores",
        ultimo_id,
        "C",
        ruta,
        "")
    return jsonify(resultado)


@app.route("/_ver_fotos_motor")
@logeado_AJAX
@verificaPermisoAuditoria("id_motor", 0)
def _ver_fotos_motor(usuario):
    id_motor = request.args.get("id_motor")
    id_auditoria = request.args.get("id_auditoria")
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT ruta, tipo, id, id_auditoria, portada
        FROM fotos_motores
        WHERE id_motor = ?
        AND id_auditoria = ?
        ORDER BY tipo""", (id_motor, id_auditoria))
    fotos = cur.fetchall()
    paneles_fotos = ""
    num_foto = 0
    elemento = "motores"
    for foto in fotos:
        paneles_fotos += render_template(
            "html/comunes/panel_foto.html",
            num_foto=num_foto,
            elemento=elemento,
            foto=foto)
        num_foto += 1

    return jsonify(fotos=paneles_fotos)


@app.route("/_ver_revisiones_disponibles")
@logeado_AJAX
# @verificaPermisoAuditoria("galicia", 0)
def _ver_revisiones_disponibles(usuario):
    elemento = request.args.get("elemento")
    id_elemento = request.args.get("id_elemento")
    TABLAS = {
        "Motor": ["motores", "id_motor"] ,
        "": ["equipos", "id_equipo"]
    }
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT *
        FROM revisiones_disponibles
        ORDER BY orden
        """)
    revisiones_disponibles = cur.fetchall()
    cur.execute("""
        SELECT gr.id, gr.nombre,
            group_concat(ardg.id_revision_disponible) as ids_rev_disp
        FROM grupos_revisiones gr
        LEFT JOIN asocia_rev_disp_grupos ardg 
        ON ardg.id_grupo_revision = gr.id
        GROUP BY gr.id
        """)
    grupos_revisiones = cur.fetchall()
    cur.execute(f"""
        SELECT *
        FROM revisiones_{TABLAS[elemento][0]}
        WHERE {TABLAS[elemento][1]} = ?
        AND id_auditoria = ?
        """, (id_elemento, session['id_auditoria']))
    revisiones_asignadas = sqliteRow2dict_dict(
        cur.fetchall(),
        "id_revision_disponible"
        )
    boton_rev_disp = ""
    boton_rev_disp_oculto = ""
    for revision_disponible in revisiones_disponibles:
        if not revision_disponible['oculta']:
            boton_rev_disp += render_template(
                "html/auditorias/boton_rev_disp.html",
                revision=revision_disponible,
                elemento=elemento,
                id_elemento=id_elemento,
                revisiones_asignadas=revisiones_asignadas)
        else:
            boton_rev_disp_oculto += render_template(
                "html/auditorias/boton_rev_disp.html",
                revision=revision_disponible,
                elemento=elemento,
                id_elemento=id_elemento,
                revisiones_asignadas=revisiones_asignadas)
    boton_grupo_rev = ""
    for grupo_rev in grupos_revisiones:
        boton_grupo_rev += render_template(
            "html/auditorias/boton_grupo_rev.html",
            grupo_rev=grupo_rev,
            elemento=elemento,
            id_elemento=id_elemento
        )
    return jsonify({
        "boton_rev_disp": boton_rev_disp,
        "boton_grupo_rev": boton_grupo_rev,
        "boton_rev_disp_oc_": boton_rev_disp_oculto
        })


@app.route("/_asigna_revisiones", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar revisions do equipo")
@verificaPermisoAuditoria("galicia", 1)
def _asigna_revisiones(usuario):
    id_equipo = int(request.form.get("id_equipo"))
    id_auditoria = int(request.form.get("id_auditoria"))
    nuevas_revisiones = request.form.getlist("nuevas_revisiones[]")
    eliminar_revisiones = request.form.getlist("eliminar_revisiones[]")
    
    lista_nuevas_revisiones = lista_enteros(nuevas_revisiones)
    lista_eliminar_revisiones = lista_enteros(eliminar_revisiones)
    db = get_db()
    cur = db.cursor()

    cur.execute(f"""
        DELETE FROM revisiones_equipos
        WHERE id_revision_disponible in ({lista_eliminar_revisiones})
        AND id_equipo = ?
        AND id_auditoria = ?
        """, (id_equipo, id_auditoria))

    lista_id_nuevas_revisiones = []
    for id_revision_disp in nuevas_revisiones:
        cur.execute(f"""
            INSERT INTO revisiones_equipos
            (id_equipo, id_revision_disponible, id_auditoria, estado)
                    VALUES (?, ?, ?, ?)
            """, (id_equipo, id_revision_disp, id_auditoria, 0))
        lista_id_nuevas_revisiones.append(cur.lastrowid)
        revision = {
            "id": cur.lastrowid,
            "id_auditoria": id_auditoria,
            "id_revision_disponible": id_revision_disp,
            "estado": 0
        }
    db.commit()

    cur.execute("""
        SELECT *, id_equipo as id_elemento
        FROM revisiones_equipos re
        LEFT JOIN revisiones_disponibles rd
        ON re.id_revision_disponible = rd.id
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (id_equipo, id_auditoria))
    revisiones_equipo = cur.fetchall()
    sumario = obten_sumario(revisiones_equipo)
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET estado_equipo = ?
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (sumario,
              id_equipo,
              id_auditoria)
              )
    boton = ""
    for revision in revisiones_equipo:
        boton += render_template(
            "html/auditorias/boton_revision.html",
            revision=revision,
            elemento=""
        )

    logCambios(
        usuario,
        "revisiones_equipos",
        str(lista_id_nuevas_revisiones),
        "C",
        "",
        "")
    return jsonify({
        "boton": boton
        })


@app.route("/_asigna_revisiones_motor", methods=['POST'])
@logeado_AJAX
@tokenCSRF("actualizar revisions do motor")
@verificaPermisoAuditoria("galicia", 1)
def _asigna_revisiones_motor(usuario):
    id_motor = request.form.get("id_motor")
    nuevas_revisiones = request.form.getlist("nuevas_revisiones[]")
    eliminar_revisiones = request.form.getlist("eliminar_revisiones[]")
    
    lista_nuevas_revisiones = lista_enteros(nuevas_revisiones)
    lista_eliminar_revisiones = lista_enteros(eliminar_revisiones)
    db = get_db()
    cur = db.cursor()
    cur.execute(f"""
        DELETE FROM revisiones_motores
        WHERE id_revision_disponible in ({lista_eliminar_revisiones})
        AND id_motor = ?
        AND id_auditoria = ?
        """, (id_motor, session['id_auditoria']))

    lista_id_nuevas_revisiones = []
    for id_revision_disp in nuevas_revisiones:
        cur.execute(f"""
            INSERT INTO revisiones_motores
            (id_motor, id_revision_disponible, id_auditoria, estado)
                    VALUES (?, ?, ?, ?)
            """, (id_motor, id_revision_disp, session['id_auditoria'], 0))
        lista_id_nuevas_revisiones.append(cur.lastrowid)
        revision = {
            "id": cur.lastrowid,
            "id_auditoria": session['id_auditoria'],
            "id_revision_disponible": id_revision_disp,
            "estado": 0
        }
    
    cur.execute("""
        SELECT *, id_motor as id_elemento, rd.tiene_medicion
        FROM revisiones_motores rm
        LEFT JOIN revisiones_disponibles rd
        ON rm.id_revision_disponible = rd.id
        WHERE id_motor = ?
        """, (id_motor,))
    revisiones_motor = cur.fetchall()

    boton = ""
    input_medicion = ""
    for revision in revisiones_motor:
        boton += render_template(
            "html/auditorias/boton_revision.html",
            revision=revision,
            elemento="Motor"
        )
        if revision['tiene_medicion']:
            input_medicion += render_template(
                'html/auditorias/input_medicion_revision.html',
                revision=revision,
                motor={"id": id_motor}
        )

    cur.execute("""
        SELECT e.id FROM equipos e
        LEFT JOIN motores m ON m.id_equipo = e.id
        WHERE m.id = ?
        """, (id_motor,))
    id_equipo = cur.fetchone()['id']
    cur.execute("""
        SELECT estado
        FROM revisiones_motores rm
        LEFT JOIN motores m ON m.id = rm.id_motor
        LEFT JOIN equipos e ON e.id = m.id_equipo
        WHERE e.id = ?
        AND rm.id_auditoria = ?
        """, (id_equipo, session['id_auditoria']))
    revisiones_motores = cur.fetchall()
    sumario = obten_sumario(revisiones_motores)
    cur.execute("""
        UPDATE observaciones_audit_equipo
        SET estado_motor = ?
        WHERE id_equipo = ?
        AND id_auditoria = ?
        """, (sumario,
              id_equipo,
              session['id_auditoria'])
              )

    db.commit()
    logCambios(
        usuario,
        "revisiones_motores",
        str(lista_id_nuevas_revisiones),
        "C",
        "",
        "")
    return jsonify({
        "boton": boton,
        "input_medicion": input_medicion
        })


@app.route("/_genera_plantilla_importacion-sistema<cod_edar>")
@logeado_AJAX
@verificaPermisoAuditoria('galicia', 0)
def _genera_plantilla(usuario, cod_edar):
    """
    Dados un listado de columnas genera un xlsx y lo envía como archivo.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT eq.id, eq.id_tratamiento, eq.id_tipo_prueba, eq.cod_antiguo,
        cod_equipo, eq.denominacion, eq.posicion, eq.unid_servicio,
        marca, eq.modelo, eq.num_serie, eq.data_fabricacion,
        data_posta_marcha, eq.criticidad, eq.tipo,
        cod_equipo_instalacion, eq.fuera_servicio
        FROM equipos eq
        LEFT JOIN tratamientos t ON eq.id_tratamiento = t.id
        LEFT JOIN instalaciones i ON t.id_instalacion = i.id
        LEFT JOIN edar e ON i.id_edar = e.id
        WHERE e.cod_edar = ?
        """, (cod_edar,))
    equipos = cur.fetchall()
    cur.execute(f"""
        SELECT i.id as id_inst, i.nombre as nombre_inst, 
                t.id as id_trat, t.nombre as nombre_trat
        FROM instalaciones i
        LEFT JOIN tratamientos t ON t.id_instalacion = i.id
        LEFT JOIN edar e ON e.id = i.id_edar
        WHERE e.cod_edar = ?
        ORDER BY t.id
        """, (cod_edar,)
        )
    tratamientos = cur.fetchall()
    cur.execute("SELECT id, titulo FROM tipos_pruebas")
    tipos_pruebas = cur.fetchall()

    
    cabeceras_equipos = [
        'id', 'id_tratamiento', 'id_tipo_prueba', 'cod_antiguo',
        'cod_equipo', 'denominacion', 'posicion', 'unid_servicio',
        'marca', 'modelo', 'num_serie', 'data_fabricacion',
        'data_posta_marcha', 'criticidad', 'tipo',
        'cod_equipo_instalacion', 'fuera_servicio'
        ]
    cabeceras_tratamientos = [
        "id_instalacion",
        "Instalación",
        "id_tratamento",
        "Tratamento"
        ]
    cabeceras_tipos_pruebas = ['id', 'Proba']

    tabla_tratamientos = pandas.DataFrame(tratamientos)
    tabla_tipos_pruebas = pandas.DataFrame(tipos_pruebas)
    if equipos:
        tabla_equipos = pandas.DataFrame(equipos)
    else:
        tabla_equipos = pandas.DataFrame(columns=cabeceras_equipos)

    if not path.exists(Configuracion.ruta_app + 'temp/'):
        makedirs(Configuracion.ruta_app + 'temp/')

    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    archivo = f'{fecha}_{cod_edar}_{usuario}.xlsx'

    writer = pandas.ExcelWriter(Configuracion.ruta_app + f'temp/{archivo}')
    
    tabla_equipos.to_excel(
        writer,
        sheet_name="Equipos",
        header=cabeceras_equipos,
        index=False)
    hoja = writer.sheets["Equipos"]
    ancho_columnas = [
        10, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 22, 17, 17, 22, 17
        ]
    for linea in equipos:
        for indice, columna in enumerate(linea):
            if ancho_columnas[indice] < len(str(columna)):
                ancho_columnas[indice] = len(str(columna))
    for indice, ancho in enumerate(ancho_columnas, 1):
        letra = get_column_letter(indice)
        hoja.column_dimensions[letra].width = ancho

    tabla_tratamientos.to_excel(
        writer,
        sheet_name="Tratamentos",
        header=cabeceras_tratamientos,
        index=False)
    hoja1 = writer.sheets['Tratamentos']
    ancho_columnas = [17, 17, 17, 17]
    for linea in tratamientos:
        for indice, columna in enumerate(linea):
            if ancho_columnas[indice] < len(str(columna)):
                ancho_columnas[indice] = len(str(columna))
    for indice, ancho in enumerate(ancho_columnas, 1):
        letra = get_column_letter(indice)
        hoja1.column_dimensions[letra].width = ancho

    tabla_tipos_pruebas.to_excel(
        writer,
        sheet_name="TiposProbas",
        header=cabeceras_tipos_pruebas,
        index=False)
    
    hoja2 = writer.sheets['TiposProbas']
    ancho_columnas = [10, 40]
    for linea in tipos_pruebas:
        for indice, columna in enumerate(linea):
            if ancho_columnas[indice] < len(str(columna)):
                ancho_columnas[indice] = len(str(columna))
    for indice, ancho in enumerate(ancho_columnas, 1):
        letra = get_column_letter(indice)
        hoja2.column_dimensions[letra].width = ancho
    
    writer.close()
    return send_from_directory('temp/', archivo)


@app.route("/_carga_equipos", methods=['GET', 'POST'])
@logeado_AJAX
@verificaPermisoAuditoria('galicia', 1)
def _carga_equipos(usuario):
    """Recibe un archivo, valida la extensión xlsx.
    Lo guarda en /temp con la forma `YYYYMMDD`_`cod_edar`_`usuario`
    Crea los equipos en la BBDD.
    Borra el archivo.
    """
    db = get_db()
    cur = db.cursor()
    file = request.files['file']
    cod_edar = request.form['cod_edar']

    if file and allowed_file(file.filename, 'excel'):
        fecha = datetime.now()
        fecha_str = fecha.strftime("%Y%m%d_%H%M")
        extension = "xlsx"
        ruta = f"{fecha_str}_{cod_edar}_{usuario}.{extension}"
        if not path.exists(Configuracion.ruta_app + 'temp/'):
            makedirs(Configuracion.ruta_app + 'temp/')
        ruta_completa = Configuracion.ruta_app + "temp/" + ruta
        file.save(ruta_completa)
    else:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1,
                        "error": "Erro subindo o ficheiro."
                        + " Recargue a página e comprobe que se trata "
                        + "dun ficheiro .xlsx."
                        }), 400
    fecha_entero = int(fecha.timestamp())
    cur.execute("""
        SELECT e.id, max(a.id)
        FROM edar e
        LEFT JOIN auditorias a ON e.id = a.id_edar
        WHERE e.cod_edar = ?
        """, (cod_edar, ))
    id_edar, id_auditoria = cur.fetchone()
    cur.execute("""
        INSERT INTO importaciones
        (id_usuario, id_edar, fecha, ruta)
        VALUES (?, ?, ?, ?)
        """, (session['id_usuario'], id_edar, fecha_entero, ruta)
        )
    try:
        df = pandas.read_excel(ruta_completa, dtype=str)
        df = df.fillna("")        
        datos = df.to_dict(orient='records')
    except Exception as e:
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1,
                        "error": "Erro procesando os "
                        + "datos. Comprobe que todas celas conteñan "
                        + "números decimais ou enteiros."
                        }), 400
    lista_tuplas_nuevos = []
    lista_tuplas_existentes = []
    columnas_BD = obten_columnas(cur, "equipos")
    for equipo in datos:
        id_equipo = equipo['id']
        valores_equipo = []
        for nombre_columna, valor in equipo.items():
            if nombre_columna not in columnas_BD:
                log(usuario, request.url, 0)
                return jsonify({"codigo": -1,
                        "error": "Erro procesando os datos. "
                        + "Comprobe que non se modificaran os encabezados "
                        + "da folla descargada."
                        }), 400
            if nombre_columna != 'id':
                valores_equipo.append(valor)
        if id_equipo == '':
            lista_tuplas_nuevos.append(tuple(valores_equipo))
        else:
            valores_equipo.append(id_equipo)
            lista_tuplas_existentes.append(tuple(valores_equipo))
    for tupla_nuevo in lista_tuplas_nuevos:
        cur.execute("""
            INSERT INTO equipos (id_tratamiento, id_tipo_prueba, cod_antiguo,
            cod_equipo, denominacion, posicion, unid_servicio,
            marca, modelo, num_serie, data_fabricacion,
            data_posta_marcha, criticidad, tipo,
            cod_equipo_instalacion, fuera_servicio)
            VALUES (?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?)
            """, tupla_nuevo)
        id_equipo = cur.lastrowid
        cur.execute("""
            INSERT INTO observaciones_audit_equipo
            (id_equipo, id_auditoria)
            VALUES (?, ?)
            """, (id_equipo, id_auditoria))
    cur.executemany("""
        UPDATE equipos
        SET id_tratamiento = ?, id_tipo_prueba = ?, cod_antiguo = ?,
        cod_equipo = ?, denominacion = ?, posicion = ?, unid_servicio = ?,
        marca = ?, modelo = ?, num_serie = ?, data_fabricacion = ?,
        data_posta_marcha = ?, criticidad = ?, tipo = ?,
        cod_equipo_instalacion = ?, fuera_servicio = ?
        WHERE id = ?
        """, lista_tuplas_existentes)
    db.commit()
    logCambios(
        usuario,
        "equipos",
        cod_edar,
        "C",
        json.dumps(lista_tuplas_nuevos),
        "")
    return jsonify()


@app.route("/actualiza_estados")
@logeado
@verificaPermisoAuditoria('admin', 1)
def _carga_equipos(usuario):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, id_equipo, id_auditoria
        FROM observaciones_audit_equipo
        """)
    observaciones = cur.fetchall()
    for observacion in observaciones:
        id_equipo = observacion['id_equipo']
        id_auditoria = observacion['id_auditoria']
        cur.execute("""
                SELECT estado
                FROM revisiones_equipos
                WHERE id_equipo = ?
                AND id_auditoria = ?
                """, (id_equipo, id_auditoria))
        revisiones_equipo = cur.fetchall()
        sumario_eq = obten_sumario(revisiones_equipo)
        cur.execute("""
            SELECT id
            FROM motores
            WHERE id_equipo = ?
            LIMIT 1
            """, (id_equipo,))
        datos_motor = cur.fetchone()
        hay_motor = 0
        if datos_motor:
            hay_motor = 1
        cur.execute("""
            SELECT rm.estado
            FROM revisiones_motores rm
            LEFT JOIN motores m ON m.id = rm.id_motor
            WHERE m.id_equipo = ?
            AND id_auditoria = ?
            """, (id_equipo, id_auditoria))
        revisiones_motor = cur.fetchall()
        sumario_mo = obten_sumario(revisiones_motor)
        cur.execute("""
            SELECT id
            FROM fotos_equipos
            WHERE id_equipo = ?
            AND id_auditoria = ?
            LIMIT 1
            """, (id_equipo, id_auditoria))
        fotos_equipo = cur.fetchall()
        hay_fotos_equipo = 1 if fotos_equipo else 0
        cur.execute("""
            SELECT fm.id
            FROM fotos_motores fm
            LEFT JOIN motores m ON m.id = fm.id_motor
            WHERE m.id_equipo = ?
            AND fm.id_auditoria = ?
            LIMIT 1
            """, (id_equipo, id_auditoria))
        fotos_motor = cur.fetchall()
        hay_fotos_motor = 1 if fotos_motor else 0
        cur.execute("""
            UPDATE observaciones_audit_equipo
            SET estado_equipo = ?,
                    estado_motor = ?,
                    hay_motor = ?,
                    hay_fotos_equipo = ?,
                    hay_fotos_motor = ?
                    WHERE id = ?
            """, (sumario_eq,
                  sumario_mo,
                  hay_motor,
                  hay_fotos_equipo,
                  hay_fotos_motor,
                  observacion['id']))
        print(observacion['id'],
            sumario_eq,
            sumario_mo,
            hay_motor,
            hay_fotos_equipo,
            hay_fotos_motor)
    db.commit()
    return "Al menos no petó™"