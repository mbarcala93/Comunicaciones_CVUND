function generaPopUpElemento(id, permiso, tipo, geometria) {
  var geometria_array = JSON.parse(geometria);
  var latlng_elem = {'lat': geometria_array[0], 'lng': geometria_array[1]};
  if (permiso > 0) {
    var escritura_desplegable = "<span onclick='nuevaInspeccion("+id+")'><span class='material-icons subir' >add_circle_outline</span></span> Nova inspección"+
                          "<div class='invisible opciones_editar'><span class='clicable' onclick='moverElemento("+ id +")'><span class='material-icons'>location_on</span> Mover</span>"+
                          "<br><span class='clicable' onclick='eliminarElemento("+ id +")'><span class='material-icons'>delete</span> Eliminar</span><div style='margin:10px 0 0 10px'>" + latlng2xy(latlng_elem) + "</div></div>";
  } else {
    var escritura_desplegable = "<div class='invisible opciones_editar'>"+
                             "<div style='margin:10px 0 0 10px'>" + latlng2xy(latlng_elem) + "</div></div>";
  }
  ;

  var resultado =  "<span class='material-icons derecha opciones_editar' onclick='toggleOpcionesEditar()'>expand_more</span><span class='material-icons derecha opciones_editar invisible' onclick='toggleOpcionesEditar()'>expand_less</span>"  +
                    "<b>"+tipo + "</b> " + id  +"<div class='clicable' onclick='muestraFichaElemento("+id+")'><span class='material-icons'>visibility</span> Ficha</div>" + escritura_desplegable;
  return resultado;
};

function muestraFichaElemento(id) {
  boton_actualizar_pulsado = 0;
  $.getJSON('/_muestra_ficha_elemento', {
    id: id,
    token: token
  }, function(data) {
    reduceMapa(1);
    setTimeout(function(){$("#contenedor_ficha_elemento").html(data.valor);}, 200);
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function muestraFichaInspeccion(id, todas, individual) {
  boton_actualizar_pulsado = 0;
  if (individual) {
    ocultaFicha('inspecciones', id)
  }
  else {
    $("#contenedor_ficha_inspecciones").html("");
  }
  $.getJSON('/_muestra_ficha_inspeccion', {
    todas: todas,
    id: id,
    token: token
  }, function(data) {
    reduceMapa(0);
    setTimeout(function(){$("#contenedor_ficha_inspecciones").prepend(data.valor).addClass("grid23").remove("grid13R");}, 200);
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
  if (!mq.matches) {
    setTimeout(function () {$('html, body').animate( { scrollTop : $("#contenedor_ficha_inspecciones").position()['top'] }, 800 );}, 600);

  };
};

function subirFoto(id, tipo) {
  $(".etiqueta_fotos.etiq.editado").css("color", "black");
  $("#subir_" + tipo + "_icon"+id).hide();
  $("#cargando_"+ tipo+id).html("Subindo foto...").show();
  $.post('/_subir_foto', {
    foto: $("#string64_"+tipo+id).val(),
    id: id,
    etiqueta: $("#valor_"+tipo+"-"+id).val(),
    token: token
  }, function(data) {
    $("#cargando_"+ tipo+id).hide();
    $(".boton."+tipo+id).css("background-color", "rgb(130, 200, 20)");
    $("#check_upload_"+tipo+id).show();
    if (data.exito == 1 && tipo == "foto") {
      $("#carga_"+tipo+id).hide();
      if (data.principal_inspeccion) {
        $("div#foto_principal"+ id +" > img").attr("src", "/static_p/fotos/"+ data.ruta)
      }
      setTimeout(function(){$("#check_upload_"+tipo+id).hide();}, 3000);

        cargaMasFotos(id, 1);

      setTimeout(function () {alargaMenu();}, 300);
      setTimeout(function () {alargaMenu();}, 600);
    } else if (data.exito == 1) {
      $("."+tipo+id).html(tipo + " <span class='material-icons'>check_circle</span>");
      window["subida_"+tipo] = 1;
      if (subida_auxiliar+subida_exterior+subida_interior == 3) {
        setTimeout(function(){
          ocultaFicha("elemento");
        }, 3000);
        subida_interior = 0;
        subida_exterior = 0;
        subida_auxiliar = 0;
      }
    }
  }).fail(function(data) {
    mensaxeErroAJAX(data);
    $("#subir_" + tipo + "_icon"+id).show();
    $("#cargando_"+ tipo+id).hide();
  });
};

function confirmarBorrarFoto(ruta, num_foto, id_inspeccion) {
  var foto_principal_inspeccion = $("div#foto_principal"+ id_inspeccion +" > img").attr("src").split("/static_p/fotos/")[1]
  var foto_principal_elemento = $("div#foto_principal > img").attr("src").split("/static_p/fotos/")[1]
  $.post('/_borra_foto', {
    ruta: ruta,
    foto_principal_inspeccion: foto_principal_inspeccion,
    foto_principal_elemento: foto_principal_elemento,
    token: token
  }, function(data) {
    $(".rotable" + num_foto + "_" + id_inspeccion).html("");
    if (data.nueva_ruta_elemento) {
      $("div#foto_principal > img").attr("src", "/static_p/fotos/" + data.nueva_ruta_elemento);
    }
    if (data.nueva_ruta_inspeccion) {
      $("div#foto_principal"+ id_inspeccion +" > img").attr("src", "/static_p/fotos/" + data.nueva_ruta_inspeccion);
    }
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function establecePrincipal(ruta, id, foto_elemento) {
  $.post('/_establece_principal', {
    id: id,
    token: token,
    foto_elemento: foto_elemento
  }, function(data) {
      $("div#foto_principal"+ data.id_actualizar +" > img").attr("src", "/static_p/fotos/"+ruta);
      cargaMasFotos(data.id_inspeccion, 1);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function cargaMasFotos(id, fotos_desplegadas) {
  if (fotos_desplegadas == 0) {
    $.getJSON('/_carga_mas_fotos', {
      id: id,
      token: token
    }, function(data) {
      $("#foto_principal"+id).hide();
      $("#mas_fotos"+id).html(`<span onclick="cargaMasFotos('`+ id +`', 1)" class="clicable">Ocultar <span class="material-icons negro">keyboard_arrow_up</span></span>`)
      var i;
      if (data.rutas.length == 0) {
        $("#mas_fotos"+id).html($("#mas_fotos"+id).html() + "<br>Non se atoparon fotos")
      } else {
        for (i = 0; i < data.rutas.length; i++) {
          $("#mas_fotos"+id).html($("#mas_fotos"+id).html() + generaDivFoto(data.rutas[i], i, data.ids[i], data.etiquetas[i], id))
        }
      }
    }).fail(function(data) {
      mensaxeErroAJAX(data);
    });
  } else {
    $("#foto_principal"+id).show();
    $("#mas_fotos"+id).html(`<span onclick="cargaMasFotos('`+ id +`', 0)" class="clicable"><span class="material-icons negro">collections</span> Fotos</span>`)
  };
  setTimeout(function () {alargaMenu();}, 300);
  setTimeout(function () {alargaMenu();}, 600);
};

var subida_interior = 0;
var subida_exterior = 0;
var subida_auxiliar = 0;

function ConfirmaActualizaElemento(elemento, id) {
  var elemento_id = "";
  if (elemento == "inspecciones") {elemento_id = id;}
  $(".confirmar"+elemento_id).hide();
  $.post('/_actualiza_elem', {
    id: id,
    elemento: elemento,
    valores: $("#formulario"+ elemento_id +" :input.editado ").serialize(),
    token: token
  }, function(data) {
    $(".check_upload"+elemento_id).show();
    $(".boton_upload"+elemento_id).hide();

    if (elemento == "inspecciones") {
      setTimeout(function(){muestraFichaInspeccion(id, 0)}, 3000)
      $("#boton_inspeccion"+id).html(fechaBonita(data.datos_popUp.fecha) + " " + data.datos_popUp.hora)
    } else {
      window["e"+id].setIcon(iconos_elemento[data.datos_popUp.tipo_agua_residual])
      setTimeout(function(){muestraFichaElemento(id);}, 3000)
    };
    boton_actualizar_pulsado = 0;
  }).fail(function(data) {
    mensaxeErroAJAX(data);
    $(".confirmar"+elemento_id).show();
  });
};

function ConfirmaActualizaNuevoElemento(id_elem, id_insp) {
  boton_actualizar_pulsado = 0;
  $('html, body').animate( { scrollTop : $(".ficha"+id_elem).offset()['top']}, 300 );
  $(".confirmar").hide();
  if ($("#formulario_elemento>.etiqueta.editado").length > 0) {
    $.post('/_actualiza_elem', {
      id: id_elem,
      elemento: "elementos",
      valores: $("#formulario_elemento :input.editado ").serialize(),
      token: token
    }, function(data) {
      if (data.exito == 1) {
        $("#formulario_elemento").html("Datos elemento <span class='material-icons check'>check_circle</span>");
        if (data.tipo_agua_residual) {
          window["e"+id_elem].setIcon(iconos_elemento[data.tipo_agua_residual])
        };
      };
    })
    .fail(function () {
      alert("Erro modificando os datos do elemento. Cancele e inténteo de novo. Se o problema persiste, contacte co administrador");
      $(".confirmar").show()
    });
  };
  if ($("#formulario_inspeccion>.etiqueta.editado").length > 0 || $("#formulario_inspeccion>.visible").length){
    $.post('/_actualiza_elem', {
      id: id_insp,
      elemento: "inspecciones",
      valores: $("#formulario_inspeccion :input.editado ").serialize(),
      token: token
    }, function(data) {
      if (data.exito == 1) {
        $("#formulario_inspeccion").html("<br>Datos inspección <span class='material-icons check'>check_circle</span>");
      }
    })
    .fail(function () {
      alert("Erro modificando os datos do elemento. Cancele e inténteo de novo. Se o problema persiste, contacte co administrador");
      $(".confirmar").show()
    });
  };
  subida_interior = 0;
  subida_exterior = 0;
  subida_auxiliar = 0;
  if ($("#string64_exterior"+id_insp).val() != "") {
    subirFoto(id_insp, 'exterior');
  } else {subida_exterior = 1;};
  if ($("#string64_interior"+id_insp).val() != "") {
    subirFoto(id_insp, 'interior');
  } else {subida_interior = 1;};
  if ($("#string64_auxiliar"+id_insp).val() != "") {
    subirFoto(id_insp, 'auxiliar');
  } else {subida_auxiliar = 1};
  if (subida_auxiliar+subida_exterior+subida_interior == 3) {
    setTimeout(function(){
      ocultaFicha("elemento");
    }, 3000);
    subida_interior = 0;
    subida_exterior = 0;
    subida_auxiliar = 0;
  }
};

var numNuevMedic = 0
var unidades = {"Condutividade": "µS/cm", "Temperatura": "ºC", "Turbidez": "NTU" }

function nuevaMedicion(id) {
  var html =  '<div class="grid_container grbot'+ id +' grid_botonera2">' +
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_etiqueta" onclick="editaInput(&quot;Condutividade&quot;, &quot;8_'+ numNuevMedic +'_etiqueta&quot;, this, &quot;'+ id +'&quot;);$(&quot;#valor-8_'+ numNuevMedic +'_etiqueta&quot;).hide();editaInput(&quot;µS/cm&quot;, &quot;8_'+ numNuevMedic +'_unidades&quot;, &quot;&quot;, &quot;'+ id +'&quot;);">Condutividade</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_etiqueta" onclick="editaInput(&quot;Temperatura&quot;, &quot;8_'+ numNuevMedic +'_etiqueta&quot;, this, &quot;'+ id +'&quot;);$(&quot;#valor-8_'+ numNuevMedic +'_etiqueta&quot;).hide();editaInput(&quot;ºC&quot;, &quot;8_'+ numNuevMedic +'_unidades&quot;, &quot;&quot;, &quot;'+ id +'&quot;);">Temperatura</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_etiqueta" onclick="editaInput(&quot;Turbidez&quot;, &quot;8_'+ numNuevMedic +'_etiqueta&quot;, this, &quot;'+ id +'&quot;);$(&quot;#valor-8_'+ numNuevMedic +'_etiqueta&quot;).hide();editaInput(&quot;NTU&quot;, &quot;8_'+ numNuevMedic +'_unidades&quot;, &quot;&quot;, &quot;'+ id +'&quot;);">Turbidez</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_etiqueta" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_etiqueta&quot;).val(&quot&quot;).toggle();$(&quot;.boton'+ id +'-8_'+ numNuevMedic +'_etiqueta&quot;).removeClass(&quot;editado&quot;);editaInput(&quot;&quot;, &quot;8_'+ numNuevMedic +'_unidades&quot;, &quot;&quot;, &quot;'+ id +'&quot;);"><span class="material-icons">edit</span></div>'+
              '</div>'+
              '<input id="valor'+ id +'-8_'+ numNuevMedic +'_etiqueta" type="text" class="ficha_ medicion'+ id +' val'+ id +' valor editar'+ id +' invisible" name="medicionnueva|'+ numNuevMedic +'|etiqueta" value=""><br class="val'+ id +' valor invisible">'+
              '<div class="grid_container grbot'+ id +' grid_botonera3">'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 1).addClass(&quot;editado&quot;);">1</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 2).addClass(&quot;editado&quot;);">2</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 3).addClass(&quot;editado&quot;);">3</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 4).addClass(&quot;editado&quot;);">4</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 5).addClass(&quot;editado&quot;);">5</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 6).addClass(&quot;editado&quot;);">6</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 7).addClass(&quot;editado&quot;);">7</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 8).addClass(&quot;editado&quot;);">8</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 9).addClass(&quot;editado&quot;);">9</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + 0).addClass(&quot;editado&quot;);">0</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val() + &quot;.&quot;).addClass(&quot;editado&quot;);">.</div>'+
                '<div class="boton panel bot'+ id +' boton'+ id +'-8_'+ numNuevMedic +'_valor" onclick="$(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val($(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val().substring(0, $(&quot;#valor'+ id +'-8_'+ numNuevMedic +'_valor&quot;).val().length-1));"><span class="material-icons">backspace</span></div>'+
              '</div>'+
              '<input id="valor'+ id +'-8_'+ numNuevMedic +'_valor" type="text" class="ficha_ medicion'+ id +' val'+ id +' valor editar'+ id +'" name="medicionnueva|'+ numNuevMedic +'|valor" value=""><br class="val'+ id +' valor">'+
              '<input id="valor'+ id +'-8_'+ numNuevMedic +'_unidades" type="text" class="ficha_ medicion'+ id +' val'+ id +' valor editar'+ id +'" name="medicionnueva|'+ numNuevMedic +'|unidades" value=""><br class="val'+ id +' valor">';
  $("#mediciones"+id).append(html);
  alargaMenu();
  numNuevMedic += 1;
}

function confirmaMoverElemento(id) {
  $.post('/_mueve_elemento', {
    id: id,
    lat: latlng["lat"],
    lon: latlng["lng"],
    token: token
  }, function(data) {
      window["e"+id].setLatLng(latlng).bindPopup(antiguoPopupMover);
      interiorPopup_crear = "";
      modoCrearPuntos = 0;
      userMarker.closePopup();
      getPosition();
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function crearElemento(cod_edar) {
  if (geoposactivado == 1) {
    getPosition();
    alert("Non se poden crear lementos co GPS activado. Pulse a localización do elemento no mapa.")
  } else {
    $.post('/_crea_elemento', {
      lat: latlng["lat"],
      lon: latlng["lng"],
      cod_edar: cod_edar,
      token: token
    }, function(data) {
      ocultaFicha("inspecciones");
      ocultaFicha("elemento");
      reduceMapa(1);
      setTimeout(function(){$("#contenedor_ficha_elemento").html(data.ficha_renderizada);}, 200);
      mymap.setView(latlng);
      window["e"+data.id_elem] = L.marker([latlng["lat"], latlng["lng"]],{icon: blackCircleIcon})
      .bindPopup(generaPopUpElemento(data.id_elem, data.permiso, "Novo elemento", "[" + latlng["lat"] + ", " + latlng["lng"] + "]"))
      .addTo(grupoElementos)
      window["e"+data.id_elem].openPopup()
      setTimeout(function () {
        if (!mq.matches) {
          $('html, body').animate( { scrollTop : $("#etiqueta-3").offset()['top']}, 300 );
        };
        alargaMenu();
      }, 200);
      setTimeout(function(){alargaMenu();}, 600);
    }).fail(function(data) {
      mensaxeErroAJAX(data);
    });
  }
};

function nuevaInspeccion(id_elem) {
  $.post('/_nueva_inspeccion', {
    id_elem: id_elem,
    token: token
  }, function(data) {
    html = '<div class="boton panel bot" onclick="muestraFichaInspeccion(' + data.id_insp + ', 0)">' + data.fecha.substring(6,8) + '/' + data.fecha.substring(4,6) + '/' + data.fecha.substring(0,4) + ' ' + data.hora + '</div>';
    $("#botones_fichas" + id_elem).append(html);
    muestraFichaElemento(id_elem);

    $("#contenedor_ficha_inspecciones").html("");
    reduceMapa(0);
    setTimeout(function(){$("#contenedor_ficha_inspecciones").prepend(data.ficha_renderizada).addClass("grid23").remove("grid13R");}, 200);
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);
    if (!mq.matches) {
      setTimeout(function () {$('html, body').animate( { scrollTop : $("#contenedor_ficha_inspecciones").position()['top'] }, 800 );}, 600);
    };
    muestraFichaInspeccion(data.id_insp, 0);
    setTimeout(function() {modoEdicionVisor(data.id_insp)}, 400);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function confirmarEliminarElemento(id) {
  $.post('/_eliminar_elemento', {
    id: id,
    token: token
  }, function(data) {
    window['e'+id].removeFrom(mymap);
    ocultaFicha("elemento", id);
    $("#contenedor_ficha_inspecciones").html("");
    ocultaFicha();
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function confirmarEliminarInspeccion(id_insp) {
  $.post('/_eliminar_inspeccion', {
    id_insp: id_insp,
    token: token
  }, function(data) {
    $("#boton_inspeccion" + id_insp).hide();
    ocultaFicha("inspecciones", id_insp);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function buscaConcello(id) {
  $.getJSON('/_que_concello', {
    id: id
  }, function(data) {
    if (data.exito == 1) {
      $('#valor-4').val(data.cod_ine + " - " + data.denominacion).addClass('editado');
      $('#etiqueta-4').addClass('editado');
      $(".boton_upload").show();
      setTimeout(function () {alargaMenu();}, 300);
    } else {
      alert("Houbo un erro buscando o Concello. Recoméndase introducilo en manual: faga click no mapa e aparecerá un globo co código e nome do concello.")
    }
  });
};

function muestraFiltros(cod_edar) {
  $.getJSON('/_muestra_ficha_filtro', {
    cod_edar: cod_edar,
  }, function(data) {
    reduceMapa(1);
    setTimeout(function(){$("#contenedor_ficha_elemento").html(data.valor);}, 200);
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);

  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function filtra(cod_edar) {
  $.getJSON('/_filtra_elementos', {
    cod_edar: cod_edar,
    token: token,
    valores: $("#formulario > div :input.correcto ").serialize(),
    valores_not: $("#formulario > div :input.incorrecto ").serialize()
  }, function(data) {
    grupoElementos.eachLayer(function(layer) { grupoElementos.removeLayer(layer);});
    for ( id in data.listado_id) {
      // console.log("window['e"+data.listado_id[id]+"'].addTo(grupoIndustrias)");
      window["e"+data.listado_id[id]].addTo(grupoElementos);
    };

  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}
