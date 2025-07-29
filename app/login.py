# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, session, url_for
from app import app

import hashlib
from secrets import token_urlsafe
from app.auxiliar import remote_ip, get_db, log, Configuracion

@app.route('/login/<url>', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login(url="menu"):
    log(remote_ip(request), request.url)
    resultados = {}
    error = None
    resultados.update({'telefono': Configuracion.telefono})
    if request.method == 'POST':
        usuario = request.form['username']
        contrasena = request.form['password']
        contr = hashlib.sha1()
        contr.update(contrasena.encode('utf-8'))
        contrasena_form = contr.hexdigest()

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            SELECT id, pass, ambito, permiso, bloqueado, diestro,
                    mareas, edicion_industrias, auditorias
            FROM usuarios
            WHERE usuario like ?""", (usuario,))
        usuario_DB = cur.fetchone()
        try:
            contrasena_guardada = usuario_DB['pass']
        except:
            contrasena_guardada = ""
        if contrasena_form != contrasena_guardada:
            error = 'Erro no usuario ou no password.'
        elif usuario_DB['bloqueado']:
            error = 'Usuario bloqueado. Contacte co administrador'
        else:
            session['logged_in'] = True
            session['username'] = usuario.upper()
            session['ambito'] = usuario_DB['ambito']
            session['permiso'] = usuario_DB['permiso']
            session['id_usuario'] = usuario_DB['id']
            session['diestro'] = usuario_DB['diestro']
            session['mareas'] = usuario_DB['mareas']
            session['edicion_industrias'] = usuario_DB['edicion_industrias']
            session['auditorias'] = usuario_DB['auditorias']
            session['TOKEN'] = token_urlsafe()
            session.permanent = True
            return redirect("/" + url)
    return render_template('html/login.html', error=error, url={"url": url_for("login", url=url)}, resultados=resultados)

@app.route('/logout')
def logout():
    log(remote_ip(request), request.url)
    session.pop('logged_in', None)
    return redirect('/login')
