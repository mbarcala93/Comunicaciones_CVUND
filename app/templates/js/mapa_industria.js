

var mymap = L.map('mapid',{
  layers: [OpenStreetMap],
  minZoom: 7,
  zoomControl: false,
  // dragging: false,
  // scrollWheelZoom: false,
  tap: false
}).setView([{{industria.latitud}}, {{industria.longitud}}],15)

var industria = L.marker([{{industria.latitud}}, {{industria.longitud}}],{icon: fucsiaCircleIcon }).addTo(mymap)
