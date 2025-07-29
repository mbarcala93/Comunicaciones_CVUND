from flask import Flask
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

from app import login
from app import menu
from app import rede
from app import censo
from app import verificacion
from app import auditoria
from app import laboratorio
from app import usuarios

#Configuramos app para que al final de la request cierre la conexión a la BBDD
from app.auxiliar import init_app
init_app(app)
