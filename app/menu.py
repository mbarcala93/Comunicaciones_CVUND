# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, session, url_for
from app import app
from app.auxiliar import get_db, log, remote_ip

@app.route('/menu')
def indice_menu():
    return redirect("/")

@app.route('/')
def indice():
    if not session.get('logged_in'):
        log(remote_ip(request), request.url, 0)
        return redirect (url_for('login',url="menu"))
    usuario = session['username']
    log(usuario, request.url)
    db = get_db()
    cur = db.cursor()

    cur.execute('SELECT id, cod_ine, denominacion, geometria FROM concellos WHERE substr(cod_ine, 3,5) != "000"')
    concellos = cur.fetchall()
    cur.execute('SELECT e.id, e.latitud, e.longitud, e.cod_edar, c.denominacion as concello FROM edar e LEFT JOIN concellos c ON e.provincia||e.municipio = c.cod_ine WHERE asis_tecnica = 1 AND e.cod_edar != "SCIB"')
    edar = cur.fetchall()
    resultados = { "mapa": "galicia",
                   "pagina": "inicio",
                   "extension": "galicia",
                   'token': session['TOKEN'],
                   "ambito": session['ambito'],
                   "usuario": session['username'],
                   "permiso": session['permiso']
                 }
    return render_template("html/menu.html", resultados=resultados, edars=edar, concellos=concellos)
