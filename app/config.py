# -*- coding: utf-8 -*-

import configparser

class Config(object):
    config = configparser.ConfigParser()
    config.read('redes.conf')
    SECRET_KEY=config['configuracion']['clave_secreta']
    SESSION_COOKIE_SECURE=config.getboolean('configuracion', 'cookie_secure')
    SESSION_COOKIE_SAMESITE=config['configuracion']['cookie_samesite']
    SESSION_COOKIE_HTTPONLY=config.getboolean('configuracion', 'cookie_httponly')
    MAX_CONTENT_LENGTH = int(config['configuracion']['max_content_length'])
    PERMANENT_SESSION_LIFETIME = int(config['configuracion']['duracion_sesion'])
