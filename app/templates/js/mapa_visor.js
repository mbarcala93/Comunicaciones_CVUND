var posicion = L.layerGroup();
var userMarker=L.marker([42.88043950138168, -8.545687906444074], {icon: greenIcon})
.addTo(posicion);

var mymap = L.map('mapid',{
  layers: [{{resultados.capa_base}}, posicion, {% if resultados.mapa == 'red' %}grupoElementos{% elif resultados.mapa == 'censo' %}grupoIndustrias{% endif %}],
  minZoom: 7,
  zoomControl: false,
  tap: false
}).{% if resultados.latitud and resultados.longitud %}setView([{{resultados.latitud}}, {{resultados.longitud}}],{{resultados.zoom}}){% elif concello %}fitBounds({{concello.geometria}}){% else %}fitBounds([[41.9, -9],[43.7, -7]]){% endif %}
  .on("moveend", function(event) {
    actualizarURL();
  })
  .on("baselayerchange", function(e){
    capa_base = baseLayers[e.name].options.nombre;
    actualizarURL();
  })
  .on("overlayadd", function(e) {
    var nombre_capa = e.name.split(" <span id=")[0].split("> ")[1];
    obtenerGeoJSON('{{resultados.cod_edar}}', nombre_capa);
  });

var cod_edar_URL = '{{resultados.cod_edar}}';
var globo_abierto = '{{resultados.globo_abierto}}';
var capa_base = '{{resultados.capa_base}}';

if (window["e"+globo_abierto]) {
  setTimeout(function(){window["e"+globo_abierto].openPopup();}, 300);
}

function actualizarURL() {
  var latlng_actual = mymap.getCenter();
  var zoom_actual = mymap.getZoom();
  window.history.pushState("", "", {% if resultados.mapa == 'red' %}"/rede-"{% elif resultados.mapa == 'censo' and resultados.concello == 0 %}"/censo-"{% elif resultados.mapa == 'censo' and resultados.concello == 1 %}"/censoConcello-"{% endif %}+ cod_edar_URL + "-"+ globo_abierto + "," + capa_base + "," + latlng_actual['lat'] + "," + latlng_actual['lng'] +","+ zoom_actual )
};

var baseLayers = {
"Mapa base": OpenStreetMap,
"Ortofoto" : WMSlayer,
"OpenTopoMap": OpenTopoMap
};

var overlayMaps = {
  {% if concello.provincia == "27" %}"EIEL LU rede": redWMS_Lu_r,
  "EIEL LU colectores": redWMS_Lu_c,{%endif%}
  {% if resultados.mapa == 'red' %}
	"<img src='static/images/mapas/negro_circulo.png' style='height: 10px' /> Elementos": grupoElementos,
  {% elif resultados.mapa == 'censo' %}
  "<img src='static/images/mapas/gris_circulo.png' style='height: 10px' /> Industrias": grupoIndustrias,
  {% endif %}
  "<img src='static/images/mapas/green.png' style='height: 20px; vertical-align:top;' /> Usuario": posicion,
  {% for capa in geoJSON | sort(attribute="nombre") %}
    {% if capa.color != "#222" %}"<svg height='10' width='10'><line x1='0' y1='5' x2='10' y2='5' style='stroke:{{capa.color}};stroke-width:2'/>-</svg> {{capa.nombre}} <span id='{{capa.nombre}}' class='material-icons leyenda'>get_app</span>": {{capa.nombre}}g{% if not loop.last %},{% endif %}
    {% else %}"<img src='{{capa.url_icono}}' style='height: 10px;' /> {{capa.nombre}} <span id='{{capa.nombre}}' class='material-icons leyenda'>get_app</span>": {{capa.nombre}}g {% if not loop.last %},{% endif %}
  {% endif %}{% endfor %}
};

var colapsado = true
if (mq.matches) {colapsado = true}
var leyenda = L.control.layers(baseLayers, overlayMaps, {hideSingleBase:true, collapsed:colapsado, position: {% if resultados.diestro %}'topright'{% else %}'topleft'{% endif %} })
.addTo(mymap);
{% if resultados.imprimir %}mymap.removeControl(leyenda);{% endif %}

function centrarMapa(geometria) {
  if (geometria[0].length == 2) {
    mymap.fitBounds(geometria);
  } else {
    mymap.setView([geometria[0], geometria[1]], 15)
  }
};

function centrarObjeto(id) {
  mymap.setView(window["e"+id]._latlng, 15);
  window["e"+id].openPopup()
};

var interiorPopup = "";
var latlng;
