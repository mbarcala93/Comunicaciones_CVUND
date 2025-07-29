function muestraBuscados() {
  var texto = RegExp(".*" + $("#textoBuscar").val() + ".*", 'i');
  encontrados = 0;
  mymap.closePopup();
  for (var [key, value] of Object.entries(objetoEDAR)) {
    if (key.match(texto) && $("#textoBuscar").val() != ""){
      window["ed"+value].setIcon(gris_green);
      encontrados++;
      if (encontrados == 1) {
        concello_encontrado = value;
      } else {
        concello_encontrado = null;
      }
    }
    else {
      window["ed"+value].setIcon(gris_orange);
    }
  }
  if (encontrados == 1) {
    window["ed"+concello_encontrado].openPopup();
    mymap.setView(window["ed"+concello_encontrado].getLatLng(),10);
  } else {mymap.fitBounds([[41.9, -9],[43.7, -7]]);}
};
