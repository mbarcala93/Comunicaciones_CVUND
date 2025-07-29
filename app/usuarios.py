# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, session, jsonify
from app import app
from datetime import datetime
from urllib.parse import unquote_plus
import json
import utm

from app.auxiliar import get_db, log, logCambios, compruebaFloat, \
                        verificarPermiso, logeado, logeado_AJAX, tokenCSRF, \
                        Configuracion, extrae_id, obten_columnas, numero_bonito, \
                        sqliteRow2list_dict, lista_id, serializado_a_diccionario, \
                        actualiza_BBDD_diccionario, log_fracaso, verificaPermiso

@app.route('/usuarios')
@logeado
def usuarios(usuario):
    if not verificarPermiso(session, 'admin', 0):
        log(usuario, request.url, 0)
        return redirect('/')
    db = get_db()
    cur = db.cursor()

    cur.execute("""
                SELECT *
                FROM usuarios
                WHERE eliminado = 0""")
    usuarios = cur.fetchall()

    # Filtros
    # Valores con los que se corresponde un id al filtrar
    cur.execute("""
                SELECT u.id, u.nombre_completo, u.organizacion, u.correo
                FROM usuarios u
                WHERE eliminado = 0""")
    datos_filtro = cur.fetchall()

    # Lista de campos por los que se puede filtrar
    lista_campos = ['nombre_completo', 'organizacion', 'correo']
    # ######


    resultados = {"pagina": "usuarios",
                  "ambito": session['ambito'],
                  "usuario": session['username'],
                  'token': session['TOKEN'],
                  "permiso": session['permiso'],
                  "diestro": session['diestro'],
                  "titulo": "Usuarios",
                  "menu": "html/menu_lateral.html"}
    
    return render_template('html/usuarios/usuarios.html',
                           usuarios=usuarios,
                           datos_filtro=datos_filtro,
                           lista_campos=lista_campos,
                           resultados=resultados,)

@app.route('/_crea_usuario', methods = ['POST'])
@logeado
def _crea_usuario(usuario):
    if not verificarPermiso(session, "admin", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para crear un usuario. "}), 403

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                INSERT INTO usuarios (bloqueado, permiso, mareas,
                edicion_industrias, auditorias) 
                VALUES (?, ?, ?, ?, ?)""",
                (1, 0, 0, 0, 0))
    ultimo_id = cur.lastrowid

    db.commit()

    cur.execute("""
                SELECT *
                FROM usuarios
                WHERE id = ?
                """,(ultimo_id,))
    usuario_app = cur.fetchone()

    html = render_template('html/usuarios/panel_usuario.html', usuario = usuario_app)

    return {'html': html, 'id_usuario': ultimo_id}

@app.route('/_actualiza_usuario', methods = ['POST'])
@logeado
def _actualiza_usuario(usuario):
    id_usuario = request.form["id_usuario"]
    valores = request.form["valores"]

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para actualizar os datos do usuario."}), 403
    resultado = {}
    if valores == "":
        return jsonify({"sin_datos": 1}), 405
    """Creamos diccionarios vacíos y los llenamos con los pares clave-valor que
    vienen serializados del cliente."""
    
    diccionario = serializado_a_diccionario(valores)
    actualizacion = actualiza_BBDD_diccionario(
        diccionario,
        'usuarios',
        id_usuario
        )
    if actualizacion.get('status_code') != 200:
        log_fracaso()
        return {
            "status_code": actualizacion.get('cod_error'),
            "erro": actualizacion.get('error')
        }
    logCambios(usuario, "Usuario", id_usuario, "actualizaUsuario", valores, None)
    resultado.update({"codigo": 1, "permiso": session['permiso']})

    return jsonify(resultado)


@app.route('/_borra_usuario', methods = ['POST'])
@logeado
def _borra_usuario(usuario):
    id_usuario = request.form["id_usuario"]

    if not verificarPermiso(session, 'admin', 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo": -1, "error": "Non ten permisos para eliminar un usuario."}), 403

    db = get_db()
    cur = db.cursor()
    cur.execute("""
                UPDATE usuarios
                SET eliminado = 1
                WHERE id = ?""", (id_usuario,))
    db.commit()

    return {'exito': 1}

@app.route('/_registra_usuario', methods = ['POST'])
@logeado
def _registra_usuario(usuario):
    if not verificarPermiso(session, "admin", 1):
        log(usuario, request.url, 0)
        return jsonify({"codigo":-1, "error": "Non dispón dos permisos oportunos para crear un usuario. "}), 403

    nombre = request.form["nombre"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
                INSERT INTO usuarios (bloqueado, permiso, mareas,
                edicion_industrias, auditorias, nombre_completo) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (1, 0, 0, 0, 0, nombre))
    ultimo_id = cur.lastrowid

    db.commit()

    cur.execute("""
                SELECT *
                FROM usuarios
                WHERE id = ?
                """,(ultimo_id,))
    usuario_app = cur.fetchall()

    return {'id_usuario': ultimo_id}
