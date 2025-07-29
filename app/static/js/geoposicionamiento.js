mymap.on('click', function (e) {
	if (geoposactivado == 0) {
		latlng = L.latLng(e.latlng);
		userMarker.addTo(posicion)
    interiorPopup = "<b>WGS84</b> <div>" + latlng["lat"].toFixed(5) + "<br>" + latlng["lng"].toFixed(5) +
                    "</div><b>UTM</b> " + latlng2xy(latlng);
    if (modoCrearPuntos) {
      interiorPopup += "<br>" + interiorPopup_crear
    }
		userMarker.setLatLng (latlng).bindPopup(interiorPopup);
	};
});

var geoposactivado = 0;
var positionId;

function success (pos) {
    latlng = {"lat": pos.coords.latitude, "lng": pos.coords.longitude}
    interiorPopup = "<b>WGS84</b> <div>" + latlng["lat"].toFixed(5) + "<br>" + latlng["lng"].toFixed(5) +
                    "</div><b>UTM</b> " + latlng2xy(latlng);
    userMarker.setLatLng(latlng).bindPopup(interiorPopup);
}
function error (err) {
}

function getPosition() {

  if (geoposactivado == 1) {
      navigator.geolocation.clearWatch(positionId);
      geoposactivado=0;
      $(".activadoGPS").hide();
      $(".desactivadoGPS").css("display", "inline-block");
  }

  else if (geoposactivado == 0) {
      geoposactivado=1
      $(".desactivadoGPS").hide();
      $(".activadoGPS").css("display", "inline-block")
      //Toma la posición, la guarda en variables
      options = {enableHighAccuracy: true, timeout: 5000, maximumAge: 10000}
      if (navigator.geolocation) {
        positionId = navigator.geolocation.watchPosition (success, error, options);
      }
      else{
          console.log("Tu navegador no soporta la API de Geoposicionamiento.");
      }
  }
}

getPosition();
