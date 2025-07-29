
var edar = L.layerGroup();
var objetoEDAR = {}
{% for edar in edars %}var  ed{{edar.id}} = L.marker([{{edar.latitud}}, {{edar.longitud}}],{icon: gris_orange} )
.bindPopup("<b style='font-size:110%'>EDAR {{edar.cod_edar}}</b><br>"+
           "<i style='font-size:90%'>{{edar.concello}}</i><br>"+
           "<a href='/rede-{{edar.cod_edar}}'>Rede saneamento</a><br>"+
           "<a href='/censo-{{edar.cod_edar}}'>Censo industrias</a>")
.addTo(edar)
objetoEDAR["{{edar.concello}} {{edar.cod_edar}}"] = '{{edar.id}}';
{% endfor %}

var mymap = L.map('mapid',{
layers: [OpenStreetMap, edar],
minZoom: 7,
{% if resultados.control_zoom %}scrollWheelZoom: false,{% endif %}
zoomControl: false,
tap: false
}).fitBounds({% if concello %}{{concello.geometria}}{% else %}[[41.9, -9],[43.7, -7]]{% endif %});
var baseLayers = {
// "Branco e negro": BWOpenStreetMap,
"Mapa base": OpenStreetMap,
"Ortofoto" : WMSlayer,
// "MapBox": MapBox,
"OpenTopoMap": OpenTopoMap
};

var overlayMaps = {


};
