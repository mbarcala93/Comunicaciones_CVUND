# -*- coding: utf-8 -*-

import paramiko
from scp import SCPClient
import os
from datetime import datetime
import sqlite3
import configparser
import sys

def get_db(archivo):
    db = sqlite3.connect(f"./{archivo}")
    db.row_factory = sqlite3.Row
    return  db

def leer_configuracion():
    config = configparser.ConfigParser()
    config.read('backup.conf')
    return config

def log(texto, v=None):
    f = open("log_backup.txt", "+a")
    f.write(texto)
    f.write("\n")
    f.close()
    if v:
        print(texto)

if __name__ == "__main__":
    configuracion = leer_configuracion()
    SERVIDOR = configuracion['servidor']['servidor']
    USUARIO = configuracion['servidor']['usuario']
    CONTRASENA = configuracion['servidor']['contrasena']
    CONTRASENA = configuracion['servidor']['contrasena']
    RUTA_BBDD = configuracion['servidor']['ruta_BBDD']
    BBDD = configuracion['servidor']['BBDD']
    RUTA_FOTOS = configuracion['servidor']['ruta_fotos']    
    RUTA_LOCAL = configuracion['local']['ruta_local']
    OTROS_ARCHIVOS = configuracion['servidor']['otros_archivos']

    verbose = 1 if sys.argv[1:] else 0

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVIDOR, username=USUARIO, password=CONTRASENA)

    fecha = datetime.now().strftime("%Y%m%d_%H:%M:%S")
    archivo = f"{BBDD}"
    scp = SCPClient(client.get_transport())
    log(f"\n   ~~~~~~~~~~ Inicio copia de seguridad {fecha} ~~~~~~~~~~   \n", verbose)
    scp.get(f"{RUTA_BBDD}{BBDD}", archivo, recursive=True)

    db = get_db(archivo)
    cur = db.cursor()
    cur.execute("""
        SELECT ruta 
        FROM fotos
    """)
    fotos = cur.fetchall()

    fotos_con_bakcup = os.listdir(RUTA_LOCAL)
    fotos_sin_backup = []
    for foto in fotos:
        if foto['ruta'] not in fotos_con_bakcup:
            fotos_sin_backup.append(foto['ruta'])
    contador_copias = 0
    contador_errores = 0
    for foto in fotos_sin_backup:
        try:
            scp.get(f"{RUTA_FOTOS}{foto}", f"{RUTA_LOCAL}{foto}", recursive=True)
            contador_copias += 1
            log(f"{foto} - {fecha}", verbose)
        except Exception as e:
            log(f"### Error copiando la foto {foto} ### {fecha} ###\n{e}", verbose)
            contador_errores += 1

    db.close()
    
    for OTRO in OTROS_ARCHIVOS.split(","):
        scp.get(f"{RUTA_BBDD}{OTRO}", OTRO)

    log(f"\n{contador_copias} foto(s) copiada(s) con éxito. {contador_errores} error(es).\n", verbose)
    log(f"   ~~~~~~~~~~ Fin copia de seguridad  ~~~~~~~~~~   \n", verbose)
