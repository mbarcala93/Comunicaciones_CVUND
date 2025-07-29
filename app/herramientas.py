# -*- coding: utf-8 -*-

@app.route("/busca_fallos_fotos_elementos")
@logeado
def busca_fallos_fotos_elementos(usuario):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM elementos")
    elementos = cur.fetchall()
    cur.execute("SELECT * FROM inspecciones")
    inspecciones = cur.fetchall()
    cur.execute("SELECT * FROM fotos")
    fotos = cur.fetchall()
    contador = 0
    posibles_fotos = []
    for elemento in elementos:
        for foto in fotos:
            if foto['id'] == elemento['foto_principal']:
                for inspeccion in inspecciones:
                    if foto['id_tabla'] == inspeccion['id'] and foto['tabla'] == "red":
                        if inspeccion['id_elemento'] != elemento['id']:
                            # print("Foto principal NO en inspección: ", foto['id'], " elemento: ", elemento['id'], " - ", elemento['cod_edar'])
                            posibles_fotos.append(propon_foto(elemento, inspecciones, fotos))
                            contador += 1

    cur.executemany("UPDATE elementos SET foto_principal = ? WHERE id = ?", posibles_fotos)
    db.commit()
    return "encontradas " + str(contador)

def propon_foto(elemento, inspecciones, fotos):
    encontrada_exterior = 0
    for inspeccion in inspecciones:
        if encontrada_exterior:
            break
        if inspeccion['id_elemento'] == elemento['id']:
            for foto in fotos:
                if foto['id_tabla'] == inspeccion['id'] and foto['tabla'] == "red" and (foto['etiqueta'] == "Exterior" or foto['etiqueta'] == "externa"):
                    posible_foto = (foto['id'], elemento['id'])
                    encontrada_exterior = 1
                    break
    if not encontrada_exterior:
        posible_foto = (None, elemento['id'])
    return posible_foto

@app.route("/busca_fallos_fotos_inspecciones")
@logeado
def busca_fallos_fotos_inspecciones(usuario):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM inspecciones")
    inspecciones = cur.fetchall()
    cur.execute("SELECT * FROM fotos")
    fotos = cur.fetchall()
    contador = 0
    fotos_corregidas = []
    for inspeccion in inspecciones:
        posible_foto = ()
        foto_erronea = 0
        for foto in fotos:
            if foto['id'] == inspeccion['foto_principal'] and foto['id_tabla'] != inspeccion['id'] and foto['tabla'] == "red" :
                foto_erronea = 1
                contador += 1
            if not posible_foto and foto['id_tabla'] == inspeccion['id'] and foto['tabla'] == "red" and (foto['etiqueta'] == "Interior" or foto['etiqueta'] == "interna"):
                posible_foto = (foto['id'], inspeccion['id'])
        if posible_foto and foto_erronea:
            fotos_corregidas.append(posible_foto)
        elif foto_erronea and not posible_foto:
            fotos_corregidas.append((None, inspeccion['id']))
    cur.executemany("UPDATE inspecciones SET foto_principal = ? WHERE id = ?", fotos_corregidas)
    db.commit()
    return "encontradas " + str(contador)
