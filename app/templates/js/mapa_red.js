var grupoElementos = L.layerGroup();
var iconos_elemento = [brownCircleIcon, blueCircleIcon, orangeCircleIcon, blackCircleIcon, blackCircleIcon];

{% if elementos %}
var {% for elemento in elementos %} e{{elemento.id}} = L.marker({{elemento.geometria}},{icon: {% if elemento.tipo_agua_residual == 0 %}brownCircleIcon{% elif elemento.tipo_agua_residual == 1 %}czCircleIcon{% elif elemento.tipo_agua_residual == 2 %}orangeCircleIcon{% else %}blackCircleIcon{% endif %} })
.bindPopup(generaPopUpElemento({{elemento.id}}, {{resultados.permiso}}, '{{elemento.tipo_elemento}}', '{{elemento.geometria}}'))
.addTo(grupoElementos)
.on('popupopen', function() {globo_abierto = {{elemento.id}};actualizarURL()})
.on('popupclose', function() {globo_abierto = 'no';actualizarURL()}) {{ "," if not loop.last }}
{% endfor %}{% endif %}

{% if resultados.diestro %}
$(".menu_lateral").removeClass("zurdo").addClass("diestro");
$("#todo").removeClass("zurdo").addClass("diestro");
{% endif %}

function onEachFeatureClosure(nombre) {
  return function onEachFeature(feature, layer) {
    popup = "<b>" + nombre + "</b>"
    for (var [key, value] of Object.entries(feature.properties)) {
      popup += "<br>" + key + " - " + value
    }
    layer.bindPopup(popup);
  }
}
{% if geoJSON %}
{% for capa in geoJSON | sort(attribute="nombre") %}
var {{capa.nombre}}g = L.layerGroup();
var {{capa.nombre}}c = {"type": "FeatureCollection","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": []}
var {{capa.nombre}}pl = L.geoJSON({{capa.nombre}}c, {
  color: "{{capa.color}}",
  onEachFeature: onEachFeatureClosure('{{capa.nombre}}'),
  pointToLayer: function (feature, latlng) {
      return L.marker(latlng, {icon: {{capa.icono}} })
  }
}).addTo({{capa.nombre}}g);
{% endfor %}
{% endif %}

var elementos = {"c": {"icono": gris_green, "capa": grupoElementos}, "a": {"icono": azul_green, "capa": grupoElementos}}
