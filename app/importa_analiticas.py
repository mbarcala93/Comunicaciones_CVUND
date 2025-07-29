# -*- coding: utf-8 -*-
import os 
import json
import sqlite3

def extrae_lineas(nombre_archivo):
    f = open(nombre_archivo, "r", encoding='ANSI')
    lineas = f.readlines()
    f.close()
    return lineas


def linea_a_dict(lineas):
    resultado = {}
    for indice, linea in enumerate(lineas):
        muestra = {}
        cod_muestra = ""
        if indice % 2 == 0:
            encabezados = linea.split(";")
            try:
                valores = lineas[indice + 1].split(";")
            except:
                return resultado
            for idx, encabezado in enumerate(encabezados):
                valor = valores[idx].replace(",", ".")
                valor = valor.replace("\n", "")
                encabezado = encabezado.replace("\n", "")
                if encabezado == "RefMuestra":
                    cod_muestra = valor
                muestra.update({encabezado: valor})
            resultado.update({cod_muestra: muestra})
    return resultado


def get_db():
    db = sqlite3.connect("redes.sqlite")
    db.row_factory = sqlite3.Row
    return db


if __name__ == "__main__":
    
    lineas = extrae_lineas("1.txt")
    dict_muestras = linea_a_dict(lineas)
    

    """TODO:
    - Iterar sobre el diccionario. 
    - Extraer de la BBDD las muestras con ese código.
    - Comprobar si coinciden los parámetros de cada muestra.
    - Sacar un listado de parámetros que cambian en muestras existentes.
    - Sacar un listado de muestras nuevas.
    - Persistir en base de datos parámetros que cambian en muestras existentes.
    - Persistir en base de datos muestras nuevas.
    """