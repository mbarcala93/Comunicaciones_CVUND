var grupoIndustrias = L.layerGroup();

{% if industrias %}
{% for industria in industrias %}{% if industria.latitud != None and industria.longitud != None %}var e{{industria.id}} = L.marker([{{industria.latitud}}, {{industria.longitud}}],{icon: fucsiaCircleIcon })
.bindPopup(generaPopUpIndustria({{industria.id}}, {{resultados.permiso}}, '{{industria.ref}}', '{{industria.nome_industria | replace("'", "\\'")}}', {{industria.latitud}}, {{industria.longitud}}, '{{industria.actividade | replace("\n", "<br>")}}'))
.addTo(grupoIndustrias)
.on('popupopen', function() {globo_abierto = {{industria.id}};actualizarURL()})
.on('popupclose', function() {globo_abierto = 'no';actualizarURL()});
{% endif %}{% endfor %}{% endif %}

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
