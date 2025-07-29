# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta
import requests
from app.auxiliar import interpola

def obtenMarea(coordenadas):
    """Compone una URL con la clave de la API, la fecha actual y las coordenadas. La
    busca en el servidor de meteogalicia y obtiene un JSON. Extrae los datos de
    marea interpolados de la hora actual.
    La entrada es una lista de la forma [lat, long]. P.ej. obtenMarea([43.45,-8.637])
    La salida es un diccionario de la forma:
    {marea actual interpolada, minutos marea alta cercana, metros marea alta}
    minutos marea alta cercana: positivos si la marea alta más próxima ya pasó,
    negativos si aún no pasó.
    """
    resultado = {}
    API_meteoGalicia = "GTTp4hc9KfIWz1aSCg55H64kT98aHi3Ni97nLwD9j8zPwgzQ1min0Bugr7syiGCA "
    coordenadas = str(coordenadas[1]) + "," + str(coordenadas[0])
    fcruda = datetime.now()
    # fcruda = datetime(2021, 10, 8, 12, 42, 0, 0)
    fecha = fcruda.strftime("%Y-%m-%dT%H:%M:%S")
    url = "https://servizos.meteogalicia.gal/apiv4/getTidesInfo?coords={}&startTime={}&endTime={}&API_KEY={}".format(coordenadas, fecha, fecha, API_meteoGalicia)
    r = requests.get(url)
    # f=open("./app/marea.json", "r")
    # texto = json.loads(f.read())
    # f.close()
    texto =  json.loads(r.text)
    # Iteramos en los intervalos de 30 minutos de mareas
    valores = texto["features"][0]["properties"]["days"][0]["variables"][0]["values"]
    for variable in valores:
        if fecha.split("T")[1].split(":")[0] == variable["timeInstant"].split("T")[1].split(":")[0]:
            if fcruda.minute < 30:
                mueveIndice = 0
                x0 = 0
                x1 = 30
            else:
                mueveIndice = 1
                x0 = 30
                x1 = 60
            y0 = valores[valores.index(variable)+mueveIndice]["height"]
            y1 = valores[valores.index(variable)+mueveIndice+1]["height"]
            resultado['actual'] = round(interpola(x0, y0, x1, y1, fcruda.minute) - 1.7, 2)
            break
    # Iteramos en las mareas mínimas y máximas
    valores = texto["features"][0]["properties"]["days"][0]["variables"][0]["summary"]
    tiempoMareaCercana = timedelta(seconds=25000) # segundos de más de 6 horas, redondeado a número bonito
    for variable in valores:
        if variable["state"] == "High tides":
            listaFechaMarea = variable["timeInstant"].split("T")
            mareaDatetime = datetime(int(listaFechaMarea[0][:4]), int(listaFechaMarea[0][5:7]), int(listaFechaMarea[0][9:11]), int(listaFechaMarea[1][:2]), int(listaFechaMarea[1][3:5]))
            tiempoMarea = fcruda - mareaDatetime
            if abs(tiempoMarea) < abs(tiempoMareaCercana):
                tiempoMareaCercana = tiempoMarea
                mareaMax = variable["height"]
    resultado['tiempo_maxima'] = int((tiempoMareaCercana.seconds + tiempoMareaCercana.days*3600*24)/60)
    resultado['maxima'] = round(mareaMax - 1.7, 2)
    resultado['porcentaje'] = int((resultado['actual']+1.7)/(resultado['maxima']+1.7)*100)
    return resultado

if __name__ == "__main__":
    print(obtenMarea([43.45,-8.637]))
