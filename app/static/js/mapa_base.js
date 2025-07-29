var OpenStreetMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
	maxZoom: 21,
	nombre: "OpenStreetMap",
	attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>'
}),

WMSlayer = L.tileLayer.wms('https://ideg.xunta.gal/servizos/services/Raster/PNOA_2017/MapServer/WmsServer?', {
		layers: '1',
		maxZoom: 21,
		nombre: "WMSlayer",
		attribution: '&copy; <a href="https://cmatv.xunta.gal/organizacion/c/CMAOT_Instituto_Estudos_Territorio">Instituto de Estudos do Territorio</a>'
}),
// BWOpenStreetMap = L.tileLayer('http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png', {
//   maxZoom: 18,
//   attribution: '&copy; <a href="http://maps.stamen.com/">stamen</a>'
// }),

// MapBox = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.pk.eyJ1Ijoic29sYWdvIiwiYSI6ImNraHl6cWE0NjF0azEyeXA1MmozcDhqZDIifQ.xJ8pY55wH3iZU_rt4-Jffw', {
// 	maxZoom: 18,
// 	attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
// 			'<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
// 			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',,
// 	id: 'mapbox.streets'
// }),

OpenTopoMap = L.tileLayer('http://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
  maxZoom: 21,
	nombre: "OpenTopoMap",
  attribution: '<a href="https://creativecommons.org/licenses/by-sa/3.0/es/">CC-BY-SA</a> <a href="https://opentopomap.org//">OpenTopoMap</a>'
});

redWMS_Lu_c = L.tileLayer.wms("https://eieldelugo.usc.es/qgisserver?SERVICE=WMS&VERSION=1.3.0", {
		layers: 'EIEL_2019_Colectores',
		minZoom: 14,
		maxZoom: 21,
    transparent: true,
    format: 'image/png',
		attribution: '&copy; <a href="https://eieldelugo.usc.es">EIEL Lugo</a>'
});

redWMS_Lu_r = L.tileLayer.wms("https://eieldelugo.usc.es/qgisserver?SERVICE=WMS&VERSION=1.3.0", {
		layers: 'EIEL_2019_Redes de saneamiento',
		minZoom: 14,
		maxZoom: 21,
    transparent: true,
    format: 'image/png',
		attribution: '&copy; <a href="https://eieldelugo.usc.es">EIEL Lugo</a>'
});

var gris_green = L.icon({
		iconUrl: 'static/images/mapas/gris_verde.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var gris_orange = L.icon({
		iconUrl: 'static/images/mapas/gris_naranja.png',
		iconSize:     [20, 32.8],
		iconAnchor:   [10, 32.8],
		popupAnchor:  [0, -24],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var gris_red = L.icon({
		iconUrl: 'static/images/mapas/gris_rojo.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var azul_green = L.icon({
		iconUrl: 'static/images/mapas/azul_verde.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var azul_orange = L.icon({
		iconUrl: 'static/images/mapas/azul_naranja.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var azul_red = L.icon({
		iconUrl: 'static/images/mapas/azul_rojo.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var pk_icon = L.icon({
		iconUrl: 'static/images/mapas/pk.svg',
		iconSize:     [10, 10],
		iconAnchor:   [5, 5],
		popupAnchor:  [0, 0]
});

var ocre_verdeIcon = L.icon({
		iconUrl: 'static/images/mapas/ocre_verde.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var ocre_naranjaIcon = L.icon({
		iconUrl: 'static/images/mapas/ocre_naranja.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var ocre_rojoIcon = L.icon({
		iconUrl: 'static/images/mapas/ocre_rojo.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var umbrella = L.icon({
		iconUrl: 'static/images/mapas/umbrella.svg',
		iconColor: "#822",
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		// shadowUrl: 'static/images/mapas/rojo_s.png'
});

var greenIcon = L.icon({
		iconUrl: 'static/images/mapas/green.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});
var blueIcon = L.icon({
		iconUrl: 'static/images/mapas/azul.png',
		iconSize:     [25, 41],
		iconAnchor:   [12.5, 41],
		popupAnchor:  [0, -30],
		shadowUrl: 'static/images/mapas/rojo_s.png'
});

var blackCircleIcon = L.icon({
    iconUrl: 'static/images/mapas/negro_circulo.png',
    iconSize:     [10, 10],
		iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var brownCircleIcon = L.icon({
    iconUrl: 'static/images/mapas/marron_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var blueCircleIcon = L.icon({
    iconUrl: 'static/images/mapas/azul_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var orangeCircleIcon = L.icon({
    iconUrl: 'static/images/mapas/naranja_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var greenCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/verde_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var czCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/CZ_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var lilaCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/rosa_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var fucsiaCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/fucsia_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var turquesaCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/turquesa_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var limaCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/lima_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var grisCircleIcon = L.icon({
	iconUrl: 'static/images/mapas/gris_circulo.png',
    iconSize:     [10, 10],
    iconAnchor:   [5, 5],
    popupAnchor:  [0, 0]
});

var zoom_inic;
if (mq.matches) {zoom_inic = 8;}
else {zoom_inic = 7;}
