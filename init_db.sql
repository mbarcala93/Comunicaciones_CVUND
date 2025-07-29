CREATE TABLE cambios (id INTEGER PRIMARY KEY, usuario VARCHAR(255), fecha VARCHAR(30), elemento VACHAR(5), id_elemento INTEGER, tipo_cambio VARCHAR(30), cambio VARCHAR(30), geometria VARCHAR(30));

DROP TABLE concellos;
ATTACH DATABASE "cruces.sqlite" as cruces;
CREATE TABLE concellos (id INTEGER PRIMARY KEY, 'cod_ine' VARCHAR(255), 'denominacion' VARCHAR(255), comentarios VARCHAR(500), contacto VARCHAR (500), geometria TEXT, adyacentes TEXT, centroides VARCHAR(20));
INSERT INTO concellos (cod_ine, denominacion, comentarios, contacto, geometria, adyacentes, centroides) SELECT cod_ine, denominacion, comentarios, contacto, geometria, adyacentes, centroides FROM cruces.concellos;

ATTACH DATABASE "edar.sqlite" as labs;
DROP TABLE usuarios;
CREATE TABLE usuarios (id INTEGER PRIMARY KEY, usuario VARCHAR(254), pass VARCHAR(254), bloqueado INTEGER, ambito VARCHAR(254), permiso INTEGER, diestro INTEGER, mareas INTEGER, edicion_industrias INTEGER, auditorias VARCHAR(254));
INSERT INTO usuarios (usuario, pass, bloqueado, ambito, permiso, diestro, mareas) SELECT nombre, pass, 0, 'admin', 2, 0, 0 FROM labs.usuarios;

DROP TABLE edar;
CREATE TABLE edar (id INTEGER PRIMARY KEY, provincia VARCHAR(254), municipio VARCHAR(254), cod_depu VARCHAR(254), habitantes INTEGER, cod_edar VARCHAR(254), latitud INTEGER, longitud INTEGER, nombre VARCHAR(254), asis_tecnica integer, EU_cod_edar varchar(45));
INSERT INTO edar (provincia, municipio, cod_depu, habitantes, cod_edar, latitud, longitud, nombre, asis_tecnica, EU_cod_edar) SELECT provincia, municipio, cod_depu, habitantes, cod_edar, latitud, longitud, nombre, asis_tecnica, EU_cod_edar FROM labs.edar;
update edar set provincia = "32" WHERE cod_edar = 'TRIV';
update edar set provincia = "32" WHERE cod_edar = 'SCIB';

ATTACH DATABASE "edar.sqlite" as labs;
DROP TABLE fotos;
CREATE TABLE fotos (id INTEGER PRIMARY KEY, id_inspeccion  INTEGER, ruta VARCHAR(255), etiqueta VARCHAR(254));
INSERT INTO fotos (id_inspeccion, ruta, etiqueta) SELECT substr(COD_INSPECCION, 3, 4), NOMBRE_FOTO, TIPO_FOTO FROM labs.fotos2;

DROP TABLE elementos;
CREATE TABLE elementos (id INTEGER PRIMARY KEY, prioridad INTEGER, geometria TEXT, altura FLOAT, cota_z_terreno FLOAT, fecha VARCHAR(10), inspector VARCHAR(10), cod_edar VARCHAR(20), tipo_elemento VARCHAR(254), tipo_agua_residual INTEGER, permiso INTEGER, foto_principal INTEGER);
DELETE FROM labs.pozos WHERE cod_pozo = "PO00000000";
DELETE FROM labs.pozos WHERE rowid > 2060 AND rowid < 2065;
INSERT INTO elementos (id, prioridad, geometria, altura, cota_z_terreno, fecha, inspector, cod_edar, tipo_elemento, tipo_agua_residual, permiso) SELECT substr(cod_pozo, 3,4), PRIORIDAD_CONTROL, "["||LATITUD||", "||LONGITUD||"]", H_POZO, COTA_Z_TERRENO, FECHA_ANADIDO, ANADIDO_POR, COD_EDAR, "Pozo", TIPO_POZO, 1 FROM labs.pozos WHERE fuente_dato = 'INSPECTOR REDES';
UPDATE elementos SET foto_principal = (SELECT f.id FROM fotos f LEFT JOIN inspecciones i ON f.id_inspeccion = i.id WHERE i.id_elemento = elementos.id AND substr(f.ruta, 18, 1) = "e");

DROP TABLE inspecciones;
CREATE TABLE inspecciones (id INTEGER PRIMARY KEY, id_elemento INTEGER, fecha VARCHAR(10), hora VARCHAR(5), estado INTEGER, comentarios TEXT, inspector VARCHAR(10), foto_principal INTEGER, insp_con_camara INTEGER);
DELETE FROM labs.inspecciones WHERE rowid = 205 or rowid = 206;
INSERT INTO inspecciones (id, id_elemento, fecha, hora, estado, comentarios, inspector) SELECT substr(COD_INSPECCION, 3, 4), substr(cod_elemento, 3,4), substr(COD_VISITA, 1,8), HORA, ESTADO, COMENTARIOS, ANADIDO_POR FROM labs.inspecciones;
UPDATE inspecciones SET foto_principal = (SELECT f.id FROM fotos f WHERE f.id_inspeccion = inspecciones.id AND substr(f.ruta, 18, 1) = "i");

DROP TABLE mediciones;
CREATE TABLE mediciones (id INTEGER PRIMARY KEY, id_inspeccion INTEGER, valor FLOAT, etiqueta VARCHAR(254), unidades VARCHAR(254));
INSERT INTO mediciones (id_inspeccion, valor, etiqueta, unidades) SELECT substr(COD_INSPECCION, 3, 4), MEDIDA_CONDUCTIVIDAD, 'Condutividade', 'µS/cm' FROM labs.inspecciones WHERE MEDIDA_CONDUCTIVIDAD != "";
INSERT INTO mediciones (id_inspeccion, valor, etiqueta, unidades) SELECT substr(COD_INSPECCION, 3, 4), MEDIDA_PH, 'pH' , '' FROM labs.inspecciones WHERE MEDIDA_PH != "";
INSERT INTO mediciones (id_inspeccion, valor, etiqueta, unidades) SELECT substr(COD_INSPECCION, 3, 4), MEDIDA_TURBIDEZ, 'Turbidez', 'NTU' FROM labs.inspecciones WHERE MEDIDA_TURBIDEZ != "";
INSERT INTO mediciones (id_inspeccion, valor, etiqueta, unidades) SELECT substr(COD_INSPECCION, 3, 4), MEDIDA_TEMPERATURA, 'Temperatura', 'ºC' FROM labs.inspecciones WHERE MEDIDA_TEMPERATURA != "";

alter table usuarios add diestro INTEGER;
update usuarios set diestro = 0;
update usuarios set diestro = 1 WHERE id = 6;

alter table usuarios add mareas INTEGER;
update usuarios set mareas = 0;
update usuarios set mareas = 1 WHERE id = 2;

--Preguntarle a JLG para eliminar inspecciones en ramales: DELETE FROM labs.inspecciones WHERE substr(cod_elemento, 1,2) != 'PO';

"""CODIGO PARA RESCATAR LOS ELEMENTOS DE PLANES DE SANEAMIENTO Y OTRAS FUENTES QUE TENÍAN
INSPECCIÓN EN LABS. TAMBIÉN REDIRECCIONA LAS FOTOS."""
ATTACH DATABASE "edar.sqlite" as labs;
INSERT INTO elementos (id, prioridad, geometria, altura, cota_z_terreno, fecha, inspector, cod_edar, tipo_elemento, tipo_agua_residual, permiso) SELECT DISTINCT substr(p.cod_pozo, 3,4), p.PRIORIDAD_CONTROL, "["||p.LATITUD||", "||p.LONGITUD||"]", p.H_POZO, p.COTA_Z_TERRENO, p.FECHA_ANADIDO, p.ANADIDO_POR, p.COD_EDAR, "Pozo", p.TIPO_POZO, 8 FROM labs.pozos p LEFT JOIN labs.inspecciones i ON i.cod_elemento = p.cod_pozo WHERE p.fuente_dato != 'INSPECTOR REDES' AND i.anadido_por not null;
UPDATE elementos SET foto_principal = (SELECT f.id FROM fotos f LEFT JOIN inspecciones i ON f.id_inspeccion = i.id WHERE i.id_elemento = elementos.id AND substr(f.ruta, 18, 1) = "e"), permiso = 1 WHERE permiso = 8;

"""Empieza el milestone de censo"""
CREATE TABLE censo (id INTEGER PRIMARY KEY, cod_industria VARCHAR(3), nome_industria VARCHAR(254), razon_social VARCHAR(254), cif VARCHAR(9), direccion VARCHAR(254), cod_concello INTEGER, telefono_1 VARCHAR(25), telefono_2 VARCHAR(25), email VARCHAR(254), web VARCHAR(254), nome_interlocutor VARCHAR(254), cargo VARCHAR(254), dni VARCHAR(9), latitud INTEGER, longitud INTEGER, concello_PV INTEGER, latitud_PV INTEGER, longitud_PV INTEGER, outras_entidades_admin VARCHAR(254), sistema VARCHAR(4), cod_concello_sistema INTEGER, actividade TEXT, cnae VARCHAR(20), solicitude_permiso INTEGER, informe_augas INTEGER, per_con INTEGER, observacions_pv TEXT, aai INTEGER, data_censo_prelim VARCHAR(20), inspector_censo_prelim VARCHAR(3), comentario_prior_censo_prelim TEXT, prioridade_censo_prelim INTEGER, recomendase_contacto_inicial INTEGER, ruta_AAI VARCHAR(254), consumo_auga INTEGER, require_PV INTEGER, foto_principal INTEGER, ruta_PV VARCHAR(254), tratamiento VARCHAR(254), id_doc_normativo INTEGER, prioridade INTEGER, recomendase_inspeccion_inicial INTEGER, observaciones TEXT, recomendase_control INTEGER);

CREATE TABLE censo_temp (id INTEGER PRIMARY KEY, cod_industria VARCHAR(3), nome_industria VARCHAR(254), razon_social VARCHAR(254), cif VARCHAR(9), direccion VARCHAR(254), cod_concello INTEGER, telefono_1 VARCHAR(25), telefono_2 VARCHAR(25), email VARCHAR(254), web VARCHAR(254), nome_interlocutor VARCHAR(254), cargo VARCHAR(254), dni VARCHAR(9), latitud INTEGER, longitud INTEGER, concello_PV INTEGER, latitud_PV INTEGER, longitud_PV INTEGER, outras_entidades_admin VARCHAR(254), sistema VARCHAR(4), cod_concello_sistema INTEGER, actividade TEXT, cnae VARCHAR(20), solicitude_permiso INTEGER, informe_augas INTEGER, per_con INTEGER, observacions_pv TEXT, aai INTEGER, data_censo_prelim VARCHAR(20), inspector_censo_prelim VARCHAR(3), comentario_prior_censo_prelim TEXT, prioridade_censo_prelim INTEGER, recomendase_contacto_inicial INTEGER, ruta_AAI VARCHAR(254), consumo_auga INTEGER, require_PV INTEGER, foto_principal INTEGER, ruta_PV VARCHAR(254), tratamiento VARCHAR(254), id_doc_normativo INTEGER, prioridade INTEGER, recomendase_inspeccion_inicial INTEGER, observaciones TEXT, recomendase_control INTEGER);

INSERT INTO censo_temp (id, cod_industria , nome_industria , razon_social , cif , direccion , cod_concello , telefono_1 , telefono_2 , email , web , nome_interlocutor , cargo , dni , latitud , longitud , concello_PV , latitud_PV , longitud_PV , outras_entidades_admin , sistema , cod_concello_sistema , actividade , cnae , solicitude_permiso , informe_augas , per_con , observacions_pv , aai , data_censo_prelim , inspector_censo_prelim , comentario_prior_censo_prelim, prioridade_censo_prelim , recomendase_contacto_inicial , ruta_AAI , consumo_auga , require_PV , foto_principal , ruta_PV , tratamiento , id_doc_normativo , prioridade , recomendase_inspeccion_inicial , observaciones , recomendase_control ) SELECT id, cod_industria , nome_industria , razon_social , cif , direccion , cod_concello , telefono_1 , telefono_2 , email , web , nome_interlocutor , cargo , dni , latitud , longitud , concello_PV , latitud_PV , longitud_PV , outras_entidades_admin , sistema , cod_concello_sistema , actividade , cnae , solicitude_permiso , informe_augas , per_con , observacions_pv , aai , data_censo_prelim , inspector_censo_prelim , comentario_prior_censo_prelim, prioridade_censo_prelim , recomendase_contacto_inicial , ruta_AAI , consumo_auga , require_PV , foto_principal , ruta_PV , tratamiento , id_doc_normativo , prioridade , recomendase_inspeccion_inicial , observaciones , recomendase_control FROM censo ;

DROP TABLE censo;
CREATE TABLE censo (id INTEGER PRIMARY KEY, cod_industria VARCHAR(3), nome_industria VARCHAR(254), razon_social VARCHAR(254), cif VARCHAR(9), direccion VARCHAR(254), cod_concello INTEGER, telefono_1 VARCHAR(25), telefono_2 VARCHAR(25), email VARCHAR(254), web VARCHAR(254), nome_interlocutor VARCHAR(254), cargo VARCHAR(254), dni VARCHAR(9), latitud INTEGER, longitud INTEGER, concello_PV INTEGER, latitud_PV INTEGER, longitud_PV INTEGER, outras_entidades_admin VARCHAR(254), sistema VARCHAR(4), cod_concello_sistema INTEGER, actividade TEXT, cnae VARCHAR(20), solicitude_permiso INTEGER, informe_augas INTEGER, per_con INTEGER, observacions_pv TEXT, aai INTEGER, data_censo_prelim VARCHAR(20), inspector_censo_prelim VARCHAR(3), comentario_prior_censo_prelim TEXT, prioridade_censo_prelim INTEGER, recomendase_contacto_inicial INTEGER, ruta_AAI VARCHAR(254), consumo_auga INTEGER, require_PV INTEGER, foto_principal INTEGER, ruta_PV VARCHAR(254), tratamiento VARCHAR(254), id_doc_normativo INTEGER, prioridade INTEGER, recomendase_inspeccion_inicial INTEGER, observaciones TEXT, recomendase_control INTEGER);

INSERT INTO censo (id, cod_industria , nome_industria , razon_social , cif , direccion , cod_concello , telefono_1 , telefono_2 , email , web , nome_interlocutor , cargo , dni , latitud , longitud , concello_PV , latitud_PV , longitud_PV , outras_entidades_admin , sistema , cod_concello_sistema , actividade , cnae , solicitude_permiso , informe_augas , per_con , observacions_pv , aai , data_censo_prelim , inspector_censo_prelim , comentario_prior_censo_prelim, prioridade_censo_prelim , recomendase_contacto_inicial , ruta_AAI , consumo_auga , require_PV , foto_principal , ruta_PV , tratamiento , id_doc_normativo , prioridade , recomendase_inspeccion_inicial , observaciones , recomendase_control ) SELECT id, cod_industria , nome_industria , razon_social , cif , direccion , cod_concello , telefono_1 , telefono_2 , email , web , nome_interlocutor , cargo , dni , latitud , longitud , concello_PV , latitud_PV , longitud_PV , outras_entidades_admin , sistema , cod_concello_sistema , actividade , cnae , solicitude_permiso , informe_augas , per_con , observacions_pv , aai , data_censo_prelim , inspector_censo_prelim , comentario_prior_censo_prelim, prioridade_censo_prelim , recomendase_contacto_inicial , ruta_AAI , consumo_auga , require_PV , foto_principal , ruta_PV , tratamiento , id_doc_normativo , prioridade , recomendase_inspeccion_inicial , observaciones , recomendase_control FROM censo_temp ;

DROP TABLE censo_temp;

ALTER TABLE censo ADD COLUMN tratamiento VARCHAR(254);
ALTER TABLE censo ADD COLUMN id_doc_normativo INTEGER;
ALTER TABLE censo ADD COLUMN prioridade INTEGER;
ALTER TABLE censo ADD COLUMN recomendase_inspeccion_inicial INTEGER;
ALTER TABLE censo ADD COLUMN recomendase_control INTEGER;
ALTER TABLE censo ADD COLUMN observaciones TEXT;

CREATE TABLE fotos_temp (id INTEGER PRIMARY KEY, id_inspeccion  INTEGER, ruta VARCHAR(255), etiqueta VARCHAR(254));
INSERT INTO fotos_temp (id_inspeccion, ruta, etiqueta) SELECT id_inspeccion, ruta, etiqueta FROM fotos;
DROP TABLE fotos;
CREATE TABLE fotos (id INTEGER PRIMARY KEY, id_tabla  INTEGER, ruta VARCHAR(255), etiqueta VARCHAR(254), tabla VARCHAR(25));
INSERT INTO fotos (id_tabla, ruta, etiqueta, tabla) SELECT id_inspeccion, ruta, etiqueta, "red" FROM fotos_temp;
DROP TABLE fotos_temp;

CREATE TABLE censo_temp (cod_industria VARCHAR(3), nome_industria VARCHAR(254), razon_social VARCHAR(254), cif VARCHAR(9), direccion VARCHAR(254), cod_concello INTEGER, telefono_1 VARCHAR(25), telefono_2 VARCHAR(25), email VARCHAR(254), web VARCHAR(254), nome_interlocutor VARCHAR(254), cargo VARCHAR(254), dni VARCHAR(9), coord_x INTEGER, coord_y INTEGER, concello_PV INTEGER, coord_x_PV INTEGER, coord_y_PV INTEGER, outras_entidades_admin VARCHAR(254), sistema VARCHAR(4), cod_concello_sistema INTEGER, actividade TEXT, cnae INTEGER, solicitude_permiso INTEGER, informe_augas INTEGER, per_con INTEGER, observacions_pv TEXT, aai INTEGER, data_censo_prelim VARCHAR(20), inspector_censo_prelim VARCHAR(3), comentario_prior_censo_prelim TEXT, prioridade_censo_prelim INTEGER, recomendase_contacto_inicial INTEGER);

.mode tabs
.import "ctr_ind_exp.tab" censo_temp

INSERT INTO censo (cod_industria, nome_industria, razon_social, cif, direccion, cod_concello, telefono_1, telefono_2, email, web, nome_interlocutor, cargo, dni, latitud, longitud, concello_PV, latitud_PV, longitud_PV, outras_entidades_admin, sistema, cod_concello_sistema, actividade, cnae, solicitude_permiso, informe_augas, per_con, observacions_pv, aai, data_censo_prelim, inspector_censo_prelim, comentario_prior_censo_prelim, prioridade_censo_prelim, recomendase_contacto_inicial) SELECT * FROM censo_temp;

update censo set latitud = replace(latitud, ".",""), longitud = replace(longitud, ".",""), latitud_PV = replace(latitud_PV, ".",""), longitud_PV = replace(longitud_PV, ".","");
update censo set latitud = null where latitud = '';
update censo set longitud = null where longitud = '';
update censo set latitud_PV = null where latitud_PV = '';
update censo set longitud_PV = null where longitud_PV = '';
update censo set latitud = latitud || "0"  where length(latitud) = 5;
update censo set latitud = latitud || "00"  where length(latitud) = 4;
update censo set latitud = latitud || "000"  where length(latitud) = 3;
update censo set longitud = 4698492 where longitud = 514103;
update censo set longitud = 4695418 where longitud = 533703;
update censo set longitud_PV = 4695418 where longitud_PV = 533703;
update censo set longitud_PV = 4694263 where longitud_PV = 529643;
update censo set latitud_PV = latitud_PV || "0"  where length(latitud_PV) = 5;
update censo set latitud_PV = latitud_PV || "00"  where length(latitud_PV) = 4;
update censo set latitud_PV = latitud_PV || "000"  where length(latitud_PV) = 3;

UPDATE censo SET nome_industria = REPLACE(nome_industria, "'", "");
UPDATE censo SET nome_industria = REPLACE(nome_industria, CHAR(10), " ");

ALTER TABLE usuarios ADD edicion_industrias INTEGER;

"""Empieza el milestone de inspecciones"""
CREATE TABLE inspecciones_ind (id INTEGER PRIMARY KEY, id_industria INTEGER, tipo_inspeccion INTEGER, inspector VARCHAR(3), fecha VARCHAR(10), hora VARCHAR(10), consideraciones_previas TEXT, cod_inspeccion VARCHAR(20), persona_presente VARCHAR(100), cargo_persona_presente VARCHAR(50), DNI_persona_presente VARCHAR(10), observado_inspector TEXT,  produccion_habitual VARCHAR(254), produccion_inspeccion VARCHAR(254),	manifestado_inspeccionado TEXT, comentarios_adicionales	TEXT, cond_meteorologicas VARCHAR(254), acepta_muestra INTEGER, motivos_no_entrega TEXT, naturaleza_AR VARCHAR(20), q_estimado VARCHAR(20), otros TEXT, turbidez INTEGER, identificacion_insp INTEGER, com_objeto_insp INTEGER, obstaculiz_insp INTEGER, presencia_titular INTEGER, niega_firma INTEGER, entrega_copia INTEGER, fecha_evaluacion VARCHAR(10), comentarios_evaluacion TEXT, conforme INTEGER, evaluacion_afeccion_sistema INTEGER, evaluacion_gestion_vertido INTEGER, recomendacion_canon INTEGER, recomendacion_envio_concello INTEGER, fecha_envio_AG VARCHAR(10), fecha_envio_canon VARCHAR(10), fecha_registro_AG VARCHAR(10), ref_registro_envio VARCHAR(100), fecha_acuse_recibo VARCHAR(10), comentarios_comunicacion TEXT);

CREATE TABLE muestras (id INTEGER PRIMARY KEY, id_inspecciones_ind INTEGER, cod_muestra VARCHAR(20), TIPO VARCHAR(20), latitud_TM FLOAT, longitud_TM FLOAT, material VARCHAR(254), volumen FLOAT, conservacion VARCHAR(20), fecha_resultados VARCHAR(10), observaciones TEXT);
CREATE TABLE analiticas (id INTEGER PRIMARY KEY, in_situ INTEGER, id_muestra INTEGER, valor FLOAT, etiqueta VARCHAR(254), unidades VARCHAR(254), incertidumbre FLOAT);

CREATE TABLE doc_normativos (id INTEGER PRIMARY KEY, cod_concello VARCHAR(254), titulo VARCHAR(254), publicacion VARCHAR(254), fecha_publicacion VARCHAR(10), evaluado INTEGER, fecha_evaluacion VARCHAR(10), comentarios_evaluacion TEXT);
CREATE TABLE parametros_DN (id INTEGER PRIMARY KEY, id_DN INTEGER, valor_limite VARCHAR(30), etiqueta VARCHAR(254), unidades VARCHAR(254));

ATTACH DATABASE "redes_insp.sqlite" as labs;

INSERT INTO inspecciones_ind (id, id_industria , tipo_inspeccion, inspector, fecha, hora, consideraciones_previas, cod_inspeccion, persona_presente, cargo_persona_presente, DNI_persona_presente, observado_inspector, produccion_habitual, produccion_inspeccion,	manifestado_inspeccionado, comentarios_adicionales, cond_meteorologicas, acepta_muestra, motivos_no_entrega, naturaleza_AR, q_estimado, otros, turbidez, identificacion_insp, com_objeto_insp, obstaculiz_insp, presencia_titular, niega_firma, entrega_copia, fecha_evaluacion, comentarios_evaluacion, conforme, evaluacion_afeccion_sistema, evaluacion_gestion_vertido, recomendacion_canon, recomendacion_envio_concello, fecha_envio_AG, fecha_envio_canon, fecha_registro_AG, ref_registro_envio, fecha_acuse_recibo, comentarios_comunicacion) SELECT id, id_industria , tipo_inspeccion, inspector, fecha, hora, consideraciones_previas, cod_inspeccion, persona_presente, cargo_persona_presente, DNI_persona_presente, observado_inspector, produccion_habitual, produccion_inspeccion,	manifestado_inspeccionado, comentarios_adicionales, cond_meteorologicas, acepta_muestra, motivos_no_entrega, naturaleza_AR, q_estimado, otros, turbidez, identificacion_insp, com_objeto_insp, obstaculiz_insp, presencia_titular, niega_firma, entrega_copia, fecha_evaluacion, comentarios_evaluacion, conforme, evaluacion_afeccion_sistema, evaluacion_gestion_vertido, recomendacion_canon, recomendacion_envio_concello, fecha_envio_AG, fecha_envio_canon, fecha_registro_AG, ref_registro_envio, fecha_acuse_recibo, comentarios_comunicacion FROM labs.inspecciones_ind;

INSERT INTO muestras (id, id_inspecciones_ind, cod_muestra, TIPO, latitud_TM, longitud_TM, material, volumen, conservacion, fecha_resultados, observaciones) SELECT id, id_inspecciones_ind, cod_muestra, TIPO, latitud_TM, longitud_TM, material, volumen, conservacion, fecha_resultados, observaciones FROM labs.muestras;

INSERT INTO analiticas (id, in_situ, id_muestra, valor, etiqueta, unidades, incertidumbre) SELECT id, in_situ, id_muestra, valor, etiqueta, unidades, incertidumbre FROM labs.analiticas;

"""Empieza el milestone de verificación"""

CREATE TABLE patrones (id INTEGER PRIMARY KEY, parametro VARCHAR(30), unidades VARCHAR(30), valor_nominal FLOAT, valor TEXT, marca VARCHAR(30), modelo VARCHAR(30), lote VARCHAR(30), caducidad INTEGER, fecha_puesta_servicio INTEGER, fecha_retirada INTEGER, verificacion INTEGER);

CREATE TABLE sondas (id INTEGER PRIMARY KEY, parametro VARCHAR(30), codigo VARCHAR(30), n_serie VARCHAR(30), en_uso INTEGER, incertidumbre FLOAT, incertidumbre_porcentual INTEGER, requisitos_ajuste TEXT);

CREATE TABLE verificaciones (id INTEGER PRIMARY KEY, parametro VARCHAR(30), fecha_inicio INTEGER, fecha_fin INTEGER, medicion_1 FLOAT, medicion_2 FLOAT, temperatura_1 FLOAT, temperatura_2 FLOAT, id_patron_1 INTEGER, id_patron_2 INTEGER, inspector VARCHAR(30), id_sonda INTEGER, impresa INTEGER, observaciones TEXT);

CREATE TABLE ajustes (id INTEGER PRIMARY KEY, parametro VARCHAR(30), fecha_inicio INTEGER, fecha_fin INTEGER, id_patrones VARCHAR(254), inspector VARCHAR(30), id_sonda INTEGER, impresa INTEGER, resultado TEXT, observaciones TEXT);

INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("pH", "", "7.01", "", "HANNA", "HI5007", "4113", 1711922400, 1);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("pH", "", "7.00", "", "Scharlau", "SO10071000", "3389 BATCH 20369201", 1667257200, 0);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("pH", "", "4.01", "", "HACH", "LZW9463.99", "20280", 1667170800, 0);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("pH", "", "9.21", "", "HACH", "LZW9465.99", "20297", 1667170800, 0);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("condutividade", "µS/cm", "147", "", "HACH", "LZW9700.99", "20357", 1672441200, 1);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("condutividade", "µS/cm", "12880", "", "HACH", "LZW9720.99", "21110", 1682805600, 1);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("pH", "", "4.01", "", "XS Basic", "51100033", "22503103", 1711922400, 1);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("condutividade", "µS/cm", "1413", "", "HACH", "LZW9710.99", "21042", 1677538800, 0);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("condutividade", "µS/cm", "84", "", "HANNA", "HI7033L", "6624", 1717192800, 1);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("condutividade", "µS/cm", "12880", "", "HANNA", "HI7030L", "7096", 1790805600, 1);
INSERT INTO patrones (parametro, unidades, valor_nominal, valor, marca, modelo, lote, caducidad, verificacion) VALUES("pH", "", "10.00", "", "Scharlau", "SO20101000", "3071 BATCH 22208201", 1696111200, 1);

UPDATE patrones set valor = valor_nominal;
UPDATE patrones set valor = '{"0": 4.01, "5": 4, "10": 4, "15": 4, "20": 4, "25": 4.01, "30": 4.01, "35": 4.02, "40": 4.03, "45": 4.05, "50": 4.06, "55": 4.08, "60": 4.1}' where modelo = "51100033";
UPDATE patrones set valor = '{"0": 7.13, "5": 7.1, "10": 7.07, "15": 7.05, "20": 7.03, "25": 7.01, "30": 7, "35": 6.99, "40": 6.98, "45": 6.98, "50": 6.98, "55": 6.98, "60": 6.98, "65": 6.99, "70": 6.99, "75": 7, "80": 7.01, "85": 7.02, "90": 7.03, "95": 7.04}' where modelo = "HI5007";
UPDATE patrones set valor = '{"0": 10.25, "5": 10.18, "10": 10.12, "15": 10.06, "20": 10, "25": 9.97, "30": 9.93, "35": 9.91, "40": 9.89, "45": 9.83, "50": 9.78}' where modelo = "SO20101000";

INSERT INTO sondas (parametro, codigo, n_serie, en_uso, incertidumbre, incertidumbre_porcentual, requisitos_ajuste) VALUES ("pH", "S01", "183192567728", 1, 0.18, 0, '{"Pendente": [0.85, 1.05], "Offset": [-30, 30], "r²": [0.995, 1.005], "n_patrons": 3}');
INSERT INTO sondas (parametro, codigo, n_serie, en_uso, incertidumbre, incertidumbre_porcentual, requisitos_ajuste) VALUES ("condutividade", "S05", "210772582813", 1, 0.09, 1, '{"Constante de cela": [0.280, 0.600], "n_patrons": 1}');

####Parte de ficha industria###
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('1', 'DECRETO 141/2012, do 21 de xuño, polo que se aproba o Regulamento marco do Servizo Público de Saneamento e Depuración de Augas Residuais de Galicia','DOG','21/06/2012',1,'12/04/2019');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('15082', 'ORDENANZA municipal de Regulamento do servizo de saneamento do Concello de Teo (BOP 13/07/2015)','BOP A Coruña','13/07/2015',1,'01/10/2019');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36022', 'ORDENANZA DO SERVIZO DE SANEAMENTO E DEPURACIÓN DE AUGAS RESIDUAIS (BOP 08/07/2016). O Grove','BOP Pontevedra','08/07/2016',1,'15/10/2019');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36005', 'ORDENANZA MUNICIPAL DE VERTIDOS E USO DO SISTEMA PÚBLICO DE SANEAMENTO EN BAIXA DO CONCELLO DE CALDAS DE REIS (BOP 21/08/2014)','BOP Pontevedra','21/08/2014',1,'15/10/2019');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('27010', 'ORDENANZA REGULADORA DO SERVIZO DE SANEAMENTO E DEPURACIÓN DE AUGAS RESIDUAIS DO CONCELLO DE CASTRO DE REI (30/01/2015)','BOP Lugo','30/01/2015',1,'14/01/2019');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('27029', 'ORDENANZA DO SERVIZO DE SANEAMENTO E DEPURACIÓN DE AUGAS RESIDUAIS DO CONCELLO DE MEIRA (BOP 23/09/2014)','BOP Lugo','23/09/2014',1,'27/01/2019');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('15073', 'ORDENANZA DE VERTEDURAS E DO SERVIZO MUNICIPAL DE SANEAMENTO DO CONCELLO DE RIVEIRA','BOP A Coruña','30/11/2016',1,'30/01/2020');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('15033', 'Ordenanza municipal de vertidos e uso do sistema público de saneamento en baixa. Concello de Dodro (BOP A Coruña 18/9/14)','BOP A Coruña','18/09/2014',1,'17/06/2020');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36060, 36046, 36051, 36027, 36006, 36061', 'Regulamento servicio de vertidos á rede de sumidorios da Mancomunidade do Salnés (BOP Pontevedra 05/12/2013)','BOP Pontevedra','05/12/2013',1,'24/06/2020');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36041', 'Regulamento do servizo de verteduras á rede de sumidoiros de Poio, e uso da mesma texto refundido.  (BOP Pontevedra 04/10/2018)','BOP Pontevedra','04/10/2018',1,'07/09/2020');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36038', 'Regulamento do uso e verteduras á rede municipal de saneamento de Pontevedra (BOP Pontevedra 10/10/2017)','BOP Pontevedra','10/10/2017',1,'07/09/2020');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36029', 'Regulamento do servizo municipal de abastecemento de auga e saneamento. Moaña (BOP Pontevedra 28/11/2014)','BOP Pontevedra','28/11/2014',1,'29/06/2021');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('36045', 'Regulamento do servizo municipal de abastecemento, saneamento e depuración de augas residuais do concello de Redondela (BOP Pontevedra 15/10/2014)','BOP Pontevedra','15/10/2014',1,'08/09/2021');
INSERT INTO doc_normativos (cod_concello, titulo, publicacion,fecha_publicacion, evaluado, fecha_evaluacion) VALUES ('32019', 'Ordenanza do servizo de saneamento e depuración de augas residuais Carballiño (BOP Ourense 14/10/2014)','BOP Ourense','14/10/2014',1,'22/11/2021');

INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(1, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(2, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '1000', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '1500', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '50', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '1000', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '25', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(3, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '1000', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '1500', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '50', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '1000', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '25', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(4, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '1000', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '1500', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '50', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '1000', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '25', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(5, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '1000', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '1500', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '50', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '1000', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '25', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(6, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '300', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '700', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '50', 'NH4', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '1000', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '25', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(7, '25', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(8, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(9, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(10, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(11, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(12, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '500', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '1000', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '40', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '500', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '20', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(13, '40', 'PT', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '5.5-9', 'pH', '');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '5000', 'Condutividade', 'µS/cm');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '1000', 'DBO5', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '1500', 'DQO', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '50', 'NTK', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '1000', 'SS', 'mg/l');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '25', 'Toxicidade', 'U.T.');
INSERT INTO parametros_DN (id_DN, valor_limite, etiqueta, unidades) VALUES(14, '40', 'PT', 'mg/l');

UPDATE analiticas SET valor = replace(valor, ",", ".") where valor like "%,%";
UPDATE analiticas SET etiqueta = "Condutividade" WHERE etiqueta like "Conduti%";
UPDATE analiticas SET etiqueta = "DBO5" WHERE etiqueta = "DBO";

UPDATE analiticas set incertidumbre = 0.25 WHERE etiqueta = "DBO5" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.25 WHERE etiqueta = "DQO" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.15 WHERE etiqueta = "SS" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.16 WHERE etiqueta = "NTK" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.20 WHERE etiqueta = "PT" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.18 WHERE etiqueta = "pH" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.09 WHERE etiqueta = "Condutividade" and incertidumbre is null;
UPDATE analiticas set incertidumbre = 0.14 WHERE etiqueta = "Toxicidade" and incertidumbre is null;


-- Empieza integración AUTIDAPP
CREATE TABLE tratamientos (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(254),
    color VARCHAR(254),
    id_instalacion INTEGER,
    FOREIGN KEY (id_instalacion) REFERENCES instalaciones(id)
);

CREATE TABLE equipos (
    id INTEGER PRIMARY KEY,
    id_tipo_prueba INTEGER,
    cod_antiguo INTEGER,
    cod_equipo VARCHAR(254),
    denominacion VARCHAR(254),
    posicion VARCHAR(254),
    unid_servicio VARCHAR(254),
    marca VARCHAR(254),
    modelo VARCHAR(254),
    num_serie VARCHAR(254),
    data_fabricacion INTEGER,
    data_posta_marcha INTEGER,
    potencia FLOAT,
    criticidad VARCHAR(254),
    tipo VARCHAR(254),
    cod_equipo_instalacion VARCHAR(254),
    id_tratamiento INTEGER,
    fuera_servicio INTEGER,
    observaciones TEXT,
    sumario VARCHAR(254),
    FOREIGN KEY (id_tipo_prueba) REFERENCES tipos_pruebas(id),
    FOREIGN KEY (id_tratamiento) REFERENCES tratamientos(id)
    );

CREATE TABLE revisiones_disponibles (
    id INTEGER PRIMARY KEY,
    actividad VARCHAR(254),
    tiene_medicion INTEGER,
    orden FLOAT,
    oculta INTEGER,
    electrica INTEGER,
    color VARCHAR(15)
    );

CREATE TABLE revisiones_equipos (
    id INTEGER PRIMARY KEY,
    id_revision_disponible INTEGER,
    id_inspector INTEGER,
    id_auditoria INTEGER,
    fecha VARCHAR(254),
    id_equipo INTEGER,
    estado INTEGER,
    medicion FLOAT,
    FOREIGN KEY (id_revisi  on_disponible) REFERENCES revisiones_disponibles(id),
    FOREIGN KEY (id_equipo) REFERENCES equipos(id),
    FOREIGN KEY (id_auditoria) REFERENCES auditorias(id)
    );

CREATE TABLE tipos_pruebas (
    id INTEGER PRIMARY KEY,
    tipo_prueba VARCHAR(254),
    rotulo VARCHAR(254),
    titulo VARCHAR(254),
    obsoleta BOOLEAN
); 

-- Mejora Auditapp: EDAR, auditoría, instalación, tratamiento, equipo, motor
-- tabla de edar de redes, se mantiene
-- tabla de edar_auditadas pasa a ser auditorias

CREATE TABLE auditorias (
    id INTEGER PRIMARY KEY,
    id_edar INTEGER,
    fecha INTEGER,
    id_foto INTEGER,
    FOREIGN KEY (id_edar) REFERENCES edar(id)
);

CREATE TABLE fotos_equipos (
    id INTEGER PRIMARY KEY,
    id_equipo INTEGER,
    id_auditoria INTEGER,
    tipo INTEGER,
    ruta VARCHAR(254),
    portada INTEGER,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id),
    FOREIGN KEY (id_auditoria) REFERENCES auditorias(id)
    );


CREATE TABLE instalaciones (
    id INTEGER PRIMARY KEY,
    id_edar INTEGER,
    nombre VARCHAR(254),
    FOREIGN KEY (id_edar) REFERENCES edar(id)
);

CREATE TABLE motores (
    id INTEGER PRIMARY KEY,
    id_equipo INTEGER,
    potencia FLOAT,
    marca VARCHAR(254),
    modelo VARCHAR(254),
    denominacion VARCHAR(254),
    fuera_servicio INTEGER,
    cosfi FLOAT,
    int_nominal FLOAT,
    tension INTEGER,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id)
);

CREATE TABLE fotos_motores (
    id INTEGER PRIMARY KEY,
    id_motor INTEGER,
    id_auditoria INTEGER,
    tipo INTEGER,
    ruta VARCHAR(254),
    portada INTEGER,
    FOREIGN KEY (id_motor) REFERENCES motores(id),
    FOREIGN KEY (id_auditoria) REFERENCES auditorias(id)
    );

CREATE TABLE revisiones_motores (
    id INTEGER PRIMARY KEY,
    id_revision_disponible INTEGER,
    id_inspector INTEGER,
    id_auditoria INTEGER,
    fecha VARCHAR(254),
    id_motor INTEGER,
    estado INTEGER,
    medicion FLOAT,
    FOREIGN KEY (id_revision_disponible) REFERENCES revisiones_disponibles(id),
    FOREIGN KEY (id_motor) REFERENCES motores(id),
    FOREIGN KEY (id_auditoria) REFERENCES auditorias(id)
    ); 

CREATE TABLE observaciones_audit_equipo (
    id INTEGER PRIMARY KEY,
    id_equipo INTEGER,
    id_auditoria INTEGER,
    observacion TEXT,
    estado_equipo INTEGER DEFAULT 0,
    estado_motor INTEGER DEFAULT 0,
    hay_motor INTEGER DEFAULT 0,
    hay_fotos_equipo INTEGER DEFAULT 0,
    hay_fotos_motor INTEGER DEFAULT 0,
    FOREIGN KEY (id_equipo) REFERENCES equipos(id),
    FOREIGN KEY (id_auditoria) REFERENCES auditorias(id)
);

CREATE TABLE observaciones_audit_motor (
    id INTEGER PRIMARY KEY,
    id_motor INTEGER,
    id_auditoria INTEGER,
    observacion TEXT,
    FOREIGN KEY (id_motor) REFERENCES motores(id),
    FOREIGN KEY (id_auditoria) REFERENCES auditorias(id)
);

CREATE TABLE grupos_revisiones (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(40)
);

CREATE TABLE asocia_rev_disp_grupos (
    id INTEGER PRIMARY KEY,
    id_revision_disponible INTEGER,
    id_grupo_revision INTEGER,
    FOREIGN KEY (id_revision_disponible) REFERENCES revisiones_disponibles(id),
    FOREIGN KEY (id_grupo_revision) REFERENCES grupos_revisiones(id)
);

CREATE TABLE importaciones (
    id INTEGER PRIMARY KEY,
    id_usuario INTEGER,
    id_edar INTEGER,
    fecha INTEGER,
    ruta VARCHAR(254),
    finalizada INTEGER,
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY(id_edar) REFERENCES edar(id)
);
