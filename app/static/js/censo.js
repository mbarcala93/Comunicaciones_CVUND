function revisaAvance(apartado, maxApartado) {
  if ($("."+apartado).length == maxApartado) {
    $("#"+apartado).html("check_circle");
  }
}

function generaPopUpIndustria(id, permiso, ref_industria, nome_industria, latitud, longitud, actividade) {
  var latlng = {'lat': latitud, 'lng': longitud};
  var acciones_escritura = "";
  if (permiso > 0) {
    acciones_escritura =  "<div class='invisible expande7'><span class='clicable' onclick='moverElemento("+ id +")'><span class='material-icons'>location_on</span> Mover</span>"+
                          "<br><span class='clicable' onclick='eliminarElemento("+ id +")'><span class='material-icons'>delete</span> Eliminar</span></div>";
  }
  var resultado =  "<span class='material-icons derecha expande7' onclick='expandir(7)'>expand_more</span><span class='material-icons derecha expande7 invisible' onclick='expandir(7)'>expand_less</span>"  +
                    "<b style='font-size:110%'>"+ nome_industria + "</b><br><i>" + ref_industria  + "</i><br>"+
                    "<span style='font-size:90%;display:inline-block;max-width:150px;'>" + actividade + "</span>"+
                    "<div class='invisible expande7' style='margin:10px 0 10px 0'>" + latlng2xy(latlng) + "</div>" +
                    "<div class='linea' style='margin:5px 0 5px 0'></div>"+
                    "<div class='clicable' onclick='muestraFichaIndustria("+id+")'><span class='material-icons'>visibility</span> Ver ficha industria</div>" +
                    "<a href='/ficha_industria-"+id+"' target='_blank' class='noDecorado'><div class='invisible expande7'><span class='clicable' onclick=''><span class='material-icons'>print</span> Imprimir ficha</span></a>" + acciones_escritura;
  return resultado
};

var listado_codigos = [];

function muestraFichaIndustria(id) {
  boton_actualizar_pulsado = 0;
  $.getJSON('/_muestra_ficha_industria', {
    id: id,
    token: token
  }, function(data) {
    reduceMapa(1);
    setTimeout(function(){$("#contenedor_ficha_elemento").html(data.valor);}, 200);
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);
    setTimeout(function(){
      for (i=1; i < 7; i++) {
        if (i != data.edicion_industrias) {
          expandir(i);
        }
      }
    }, 200);
    listado_codigos = data.listado_codigos;

  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function muestraFichaInspeccion(id, todas, individual) {
  boton_actualizar_pulsado = 0;
  if (individual) {
    $("#ficha"+id).remove();
  }
  else {
    $("#contenedor_ficha_inspecciones").html("");
  }
  $.getJSON('/_muestra_ficha_inspeccion_industria', {
    todas: todas,
    id: id,
    token: token
  }, function(data) {
    reduceMapa(0);

    setTimeout(function(){$("#contenedor_ficha_inspecciones").prepend(data.valor).addClass("grid23").remove("grid13R");}, 200);
    if (individual) {
      $("#ficha"+id).addClass("inspeccion").show(100);
    }
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
  if (!mq.matches) {
    setTimeout(function () {$('html, body').animate( { scrollTop : $("#contenedor_ficha_inspecciones").position()['top'] }, 800 );}, 600);
    setTimeout(function () {alargaMenu();}, 800);
  };
};

function cumpleInspeccion(id_inspeccion) {
  $.getJSON('/_cumple_inspeccion', {
    id_inspeccion: id_inspeccion,
    token: token
  }, function(data) {
    editaInput(data.cumple, 28, "#boton_conforme"+data.cumple, id_inspeccion);
    if (data.cumple == 0) {
      alert(data.texto);
    }
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function nuevaInspeccion(id_industria) {
  $.post('/_nueva_inspeccion_industria', {
    id_industria: id_industria,
    token: token
  }, function(data) {
    muestraFichaInspeccion(data.id_inspeccion, 0);
    html = '<div id="boton_inspeccion'+data.id_inspeccion+'" class="boton panel bot tipo0" onclick="muestraFichaInspeccion('+data.id_inspeccion+', 0)">'+data.fecha+'</div>'
    $("#botones_fichas"+id_industria).append(html);
    setTimeout(function(){
                modoEdicionVisor(data.id_inspeccion);
                expandir(`10_${data.id_inspeccion}`);
                expandir(`11_${data.id_inspeccion}`);
                expandir(`12_${data.id_inspeccion}`);
                expandir(`14_${data.id_inspeccion}`);
                expandir(`15_${data.id_inspeccion}`);
                $(`.grid_analiticas.grid${data.id_inspeccion}`).toggleClass('editar_analiticas');
                $(`.grid_analiticas_plani.grid${data.id_inspeccion}`).toggleClass('editar_analiticas');
                $(`.grid_envases.grid${data.id_inspeccion}`).toggleClass('editar_envases');
    }, 300);
    
  }).fail(function (data) {
    mensaxeErroAJAX(data);
  });
}

function proponCodigo() {
  var nombre = $("#valor-2").val();
  if (nombre.length > 2) {
    var sistema = $("#valor-31").val()
    var codigo = nombre.substr(0,3).toUpperCase();
    compruebaCodigo(codigo, sistema);
  }
}

function compruebaCodigo(codigo, sistema) {
  $("#valor-1").removeClass(["incorrecto", "imposible"])
  var coincidencia_codigo = 0;
  for (indice in listado_codigos) {
    var sistema_existente = listado_codigos[indice].split("_")[0]
    var codigo_existente = listado_codigos[indice].split("_")[1]
    if (sistema_existente == sistema && codigo_existente == codigo) {
      coincidencia_codigo = 2
      break;
    } else if (codigo_existente == codigo) {
      coincidencia_codigo = 1;
    }
  }
  if (coincidencia_codigo == 2) {
    $('#aviso_cod_industria').html("Coincidencia no mesmo sistema!");
    $("#valor-1").val(codigo).addClass("imposible");
  } else if (coincidencia_codigo == 1) {
    $('#aviso_cod_industria').html("Coincidencia noutro sistema");
    $("#valor-1").val(codigo).addClass("incorrecto");
  } else {
    $('#aviso_cod_industria').html("");
    $("#valor-1").val(codigo).addClass("editado");
  }
}

function subirFotoIndustria(id, tipo, dic_check) {
  $("."+tipo).html(tipo + " <span style='font-size:60%;'>Subindo...</span>")
  $.post('/_subir_foto_industria', {
    foto: $("#string64_"+tipo).val(),
    id: id,
    etiqueta: $("#valor_"+tipo).val(),
    token: token
  }, function(data) {
    $("."+tipo).html(tipo + " <span class='material-icons'>check_circle</span>").removeClass("editado").addClass("correcto");
    dic_check.fotos_subidas += 1;
    if (dic_check.fotos_subidas == dic_check.fotos_por_subir) {
      recargaFicha("industria", id);
    }
  }).fail(function(data) {
    mensaxeErroAJAX(data);
    $(".confirmar").show()
  });
  return dic_check
};

function otrasFotos() {
  var num = $(".stringFotos").length - 1;
  html_boton =  '<div class="boton panel bot botonSubirFoto outra'+num+'" onclick="document.getElementById(&quot;file64_outra'+num+'&quot;).click();">'+
                'Outra '+num+
                '<span id="cargando_outra'+num+'" class="invisible cargando" style="font-size:60%">Comprimindo...</span>' +
                '</div>'
  html_input = '<input id="file64_outra'+num+'" class="imagenComprimir invisible" onchange="comprimir(&quot;outra'+num+'&quot;,&quot;&quot;)" name="files64_outra'+num+'" type="file" value="Archivo" multiple="false" accept="image/*">'+
         '<input id="string64_outra'+num+'" class="stringFotos" type="text" name="string64_outra'+num+'" value="" style="display: none;">'+
         '<input id="valor_outra'+num+'" class="invisible" value="Outra'+num+'">'
  $("#botones_fotos").append(html_boton);
  $(".valores_fotos").append(html_input);
}

function confirmarBorrarFoto(ruta, num_foto, id_industria) {
  var foto_principal_borrar = $("div#foto_principal > img").attr("src").split("/static_p/fotos/")[1]
  $.post('/_borra_foto_industria', {
    ruta: ruta,
    foto_principal: foto_principal_borrar,
    token: token
  }, function(data) {
    $(".rotable" + num_foto + "_" + id_industria).html("");
    if (data.nueva_ruta) {
      $("div#foto_principal > img").attr("src", "/static_p/fotos/" + data.nueva_ruta);
    }
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function establecePrincipal(ruta, id) {
  $.post('/_establece_principal_industria', {
    id: id,
    token: token,
    ruta: ruta
  }, function(data) {
    $("div#foto_principal > img").attr("src", "/static_p/fotos/"+ruta);
    cargaMasFotos(data.id_industria);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function cargaMasFotos(id, fotos_desplegadas) {
  if (fotos_desplegadas == 0) {

    $.getJSON('/_carga_mas_fotos_industria', {
      id: id,
      token: token
    }, function(data) {
      $("#foto_principal").hide();
      $("#mas_fotos"+id).html(`<span onclick="cargaMasFotos('`+ id +`', 1)" class="clicable">Ocultar <span class="material-icons negro">keyboard_arrow_up</span></span>`)
      var i;
      if (data.rutas.length == 0) {
        $("#mas_fotos"+id).html($("#mas_fotos"+id).html() + "<br>Non se atoparon fotos")
      } else {
        for (i = 0; i < data.rutas.length; i++) {
          $("#mas_fotos"+id).html($("#mas_fotos"+id).html() + generaDivFoto(data.rutas[i], i, data.ids[i], data.etiquetas[i], id, "ind"))
        }
      }
    }).fail(function(data) {
      mensaxeErroAJAX(data);
    });
  } else {

    $("#foto_principal").show();
    $("#mas_fotos"+id).html(`<span onclick="cargaMasFotos('`+ id +`', 0)" class="clicable"><span class="material-icons negro">collections</span> Fotos</span>`)
  };
  setTimeout(function () {alargaMenu();}, 300);
  setTimeout(function () {alargaMenu();}, 600);
};

function completaActividad(actividad, comentario, prioridad, visita) {
  var campos_editar = {"16": actividad, "28": comentario, "28b": prioridad, "29": visita};
  var valores = {"28b": {1: "Alta", 2: "Medio", 3: "Baixa", 4: "Moi baixa", 5: "Descoñecida"},
                "29": {1: "Si", 0: "Non"}};
  expandir_invisible("Activ");
  for (i in campos_editar){
    if ($("#valor-"+i).val() == "") {
      $("#valor-"+i).val(campos_editar[i]).addClass("editado");
      $("#etiqueta-"+i).addClass("editado");
      if ($("div.boton-"+i).length != 0) {
        $("div.boton-"+i+":contains("+valores[i][campos_editar[i]]+")").addClass("editado").parent().addClass('visible');
      }
      $(".boton_upload").show();
    }
  }
};

function ConfirmaActualizaElemento(elemento, id) {
  var dic_check = {"fotos_subidas": 0, "fotos_por_subir": $(".botonSubirFoto.editado").length}
  var id_elemento = id;
  if (elemento == "industria") { id = ""; }
  $(".confirmar"+id).hide();
  datos_por_actualizar = 1;
  let obj_datos = {};
  valores_ind =  $("#formulario"+id+" > span .valor.editado.industria ");
  valores_insp =  $("#formulario"+id+" > span .valor.editado.inspeccion ");

  if(valores_ind.length > 0){
    obj_datos['censo'] = {};
    obj_datos['censo'][`${id_elemento}`] = valores_ind.serialize();
  }

  if(valores_insp.length > 0){
    obj_datos['inspecciones_ind'] = {};
    obj_datos['inspecciones_ind'][`${id_elemento}`]=valores_insp.serialize();
  }

  muestras =  $("#formulario"+id_elemento+" .apartado_muestras").children();
  if(muestras.length > 0){
    obj_datos['muestras'] = {};
    for(muestra of muestras){
      let id_muestra = muestra.id.replace('elem_muestra','');
      let valores_muestra =  $("#elem_muestra"+id_muestra+" .valor.editado.muestra ");
      if(valores_muestra.length > 0){
        obj_datos['muestras'][`${id_muestra}`] = valores_muestra.serialize();
      }
    }
  }

  parametros =  $("#formulario"+id_elemento+" .apartado_parametros").children();
  if(parametros.length > 0){
    obj_datos['analiticas'] = {};
    for(parametro of parametros){
      let id_parametro = parametro.id.replace('elem_parametro','');
      let valores_parametro =  $("#elem_parametro"+id_parametro+" .valor.editado.parametro ");
      if(valores_parametro.length > 0){
        obj_datos['analiticas'][`${id_parametro}`] = valores_parametro.serialize();
      }
    }
  }

  envases =  $("#formulario"+id_elemento+" .apartado_envases").children();
  if(envases.length > 0){
    obj_datos['envases'] = {};
    for(envase of envases){
      let id_envase = envase.id.replace('elem_envase','');
      let valores_envase =  $("#elem_envase"+id_envase+" .valor.editado.envase ");
      if(valores_envase.length > 0){
        obj_datos['envases'][`${id_envase}`] = valores_envase.serialize();
      }
    }
  }

  eliminarVacios(obj_datos)

  $.post('/_actualiza_datos', {
    datos: JSON.stringify(obj_datos),
    elemento: elemento,
    id: id_elemento,
    token: token
  }, function(data) {
    actualizacion = true;
    $(".boton_upload"+id).hide();
    $("#formulario"+id+" span .valor.editado ").removeClass("editado").addClass("correcto");
    $("#formulario"+id+" span span.editado ").removeClass("editado").addClass("correcto");
    $("#formulario"+id+" span > div > div.boton.editado").removeClass("editado").addClass("correcto");
    boton_actualizar_pulsado = 0;
    if (elemento == "industria") {
      if (data.sin_datos != 1) {
        $(".check_upload"+id).show();
        window["e"+id_elemento].bindPopup(generaPopUpIndustria(id_elemento, data.permiso, data.datos_popUp.sistema+"_"+data.datos_popUp.cod_industria, data.datos_popUp.nome_industria, data.datos_popUp.lat, data.datos_popUp.lng, data.datos_popUp.actividade ))
        if ($(".hayFoto").length == 0) {recargaFicha(elemento, id_elemento);}
      };
      $(".stringFotos").each(function(i, tipo_foto) {
        var tipo = tipo_foto.id.split("_")[1];
        if ($("#string64_"+tipo).val() != "") {
          dic_check = subirFotoIndustria(id_elemento, tipo, dic_check);
        }
      });
    } else {
      $(".check_upload"+id).show();
      var fecha_bonita = fechaBonita(data.datos_popUp.fecha)
      $("#boton_inspeccion"+id)
        .removeClass(["tipoNone", "tipo0", "tipo1", "tipo2"])
        .addClass("tipo"+data.datos_popUp.tipo_inspeccion)
        .html(fecha_bonita);
      $(".check_upload"+id).show();
      recargaFicha(elemento, id_elemento);
    }
  }).fail(function (data) {
    mensaxeErroAJAX(data);
    $(".confirmar"+id).show();
  });
};

function recargaFicha(elemento, id_elemento) {
  setTimeout(function(){
    if (elemento == "industria") {
      muestraFichaIndustria(id_elemento);
    } else {
      muestraFichaInspeccion(id_elemento,0,1);
    }
  }, 3000);
};

function confirmaMoverElemento(id) {
  $.post('/_mueve_industria', {
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
  boton_actualizar_pulsado = 0;
  if (geoposactivado == 1) {
    getPosition();
    alert("Non se poden crear industrias co GPS activado. Pulse a localización do elemento no mapa.")
  } else if (cod_edar == "None") {
    alert("Non se pode crear industrias na vista xeral de censo. Seleccione un concello.")
  } else {
    $.post('/_crea_industria', {
      lat: latlng["lat"],
      lon: latlng["lng"],
      cod_edar: cod_edar,
      token: token
    }, function(data) {
      listado_codigos = data.listado_codigos;
      ocultaFicha("elemento");
      reduceMapa(1);
      setTimeout(function(){$("#contenedor_ficha_elemento").html(data.ficha_renderizada);}, 200);
      mymap.setView(latlng);
      window["e"+data.id_elem] = L.marker([latlng["lat"], latlng["lng"]],{icon: fucsiaCircleIcon})
      .bindPopup(generaPopUpIndustria(data.id_elem, data.permiso, "Nova industria", "", latlng["lat"] , latlng["lng"] ), "")
      .addTo(grupoIndustrias)
      .openPopup()
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

function confirmarEliminarElemento(id) {
  $.post('/_eliminar_industria', {
    id: id,
    token: token
  }, function(data) {
    window['e'+id].removeFrom(mymap);
    ocultaFicha("elemento", id);
    $("#contenedor_ficha_elemento").html("");
    ocultaFicha();
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function eliminarInspeccion(id) {
  confirma = confirm("Seguro que desexa borrar esta inpección?")
  if (confirma) {
    confirmarEliminarInspeccion(id);
  }
}

function confirmarEliminarInspeccion(id) {
  $.post('/_eliminar_inspeccion_ind', {
    id_inspeccion: id,
    token: token
  }, function(data) {
    ocultaFicha("inspecciones", id);
    ampliaMapa("inspeccion");
    $("#boton_inspeccion"+id).remove();
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function coordenadasPV() {
  if (geoposactivado == 1) {
    getPosition();
    alert("Non se poden asignar coordenadas co GPS activado. Pulse a localización do elemento no mapa.")
  } else {
    $("#valor-39").val(latlng['lat']).addClass('editado');
    $("#valor-40").val(latlng['lng']).addClass('editado');
    $("#etiqueta-39").addClass('editado');
    $("#etiqueta-40").addClass('editado');
    $(".boton_upload").show();
    queConcello(latlng['lat'], latlng['lng'], "#valor-36");
    $("#coordenadas_PV_UTM").html("-recargar ficha-");
  }
}

function queConcello(lat, lon, input_editar) {
  $.getJSON('/_que_concello', {
    lat: lat,
    lon: lon
  }, function(data) {
    if (input_editar) {
        $(input_editar).val(data.cod_ine).addClass('editado');
    }
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function subirPerVer(id_industria) {
    var formData = new FormData();
    formData.append("id_industria", id_industria);
    formData.append("token", token);
    formData.append("perVer", $("#file_perVer")[0].files[0]);
    $.ajax({
        url: "/_subir_perVer",
        type: "post",
        dataType: "json",
        data: formData,
        cache: false,
        contentType: false,
        processData: false
  }).done( function (data) {
    $("#boton_subir_PV").html("Permiso de vertido subido").addClass("correcto").attr("onclick", "");
    $("#borraPerVert").removeClass("invisible");
  }
  ).fail(function (data) {
    mensaxeErroAJAX(data);
  });
};

function subirAAI(id_industria) {
    var formData = new FormData();
    formData.append("id_industria", id_industria);
    formData.append("token", token);
    formData.append("AAI", $("#file_AAI")[0].files[0]);
    $.ajax({
        url: "/_subir_aai",
        type: "post",
        dataType: "json",
        data: formData,
        cache: false,
        contentType: false,
        processData: false
  }).done( function (data) {
    $("#boton_subir_AAI").html("AAI subida").addClass("correcto").attr("onclick", "");
    $("#borraAAI").removeClass("invisible");
  }
  ).fail(function (data) {
    mensaxeErroAJAX(data);
  });
};

function nuevaMuestra(id_inspeccion) {
  $.post('/_nueva_muestra_inspeccion', {
    id_inspeccion: id_inspeccion,
    token: token
  }, function(data) {
    modoEdicionVisor(id_inspeccion);
    $(`.grid_analiticas.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    $(`.grid_analiticas_plani.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    $("#parametros"+id_inspeccion).append(data.html);
    modoEdicionVisor(id_inspeccion);
    $(`.grid_analiticas.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    $(`.grid_analiticas_plani.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    setTimeout(function () {
      alargaMenu();
    }, 200);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function nuevoParametro(id_inspeccion, id_muestra) {
  $.post('/_nueva_medicion_muestra', {
    id_muestra: id_muestra,
    token: token
  }, function(data) {
    modoEdicionVisor(id_inspeccion);
    $(`.grid_analiticas.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    $(`.grid_analiticas_plani.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    $("#analiticas"+id_muestra).append(data.html);
    modoEdicionVisor(id_inspeccion);
    $(`.grid_analiticas.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    $(`.grid_analiticas_plani.grid${id_inspeccion}`).toggleClass('editar_analiticas');
    setTimeout(function () {
      alargaMenu();
    }, 200);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function eliminaParametro(id_parametro, id_inspeccion) {
  id_inputs = [22, 23, 24, 25, "24bis"];
  for (i in id_inputs) {
    $("#valor"+id_inspeccion+"-"+id_inputs[i]+"-"+id_parametro).addClass("incorrecto");
  }
  asegurar = confirm("Seguro que desexa borrar este parámetro? A acción é irreversible");
  if (asegurar) {
    $.post('/_eliminar_parametro', {
      id_parametro: id_parametro,
      token: token
    }, function(data) {
      for (i in id_inputs) {
        $("#valor"+id_inspeccion+"-"+id_inputs[i]+"-"+id_parametro).remove();
      }
    }).fail(function (data) {
      mensaxeErroAJAX(data);
    });
  } else {
    for (i in id_inputs) {
      $("#valor"+id_inspeccion+"-"+id_inputs[i]+"-"+id_parametro).removeClass("incorrecto");
    }
  }
}

function nuevoEnvase(id_inspeccion, id_muestra ) {
  $.post('/_nuevo_envase_muestra', {
    id_muestra: id_muestra,
    token: token
  }, function(data) {
    modoEdicionVisor(id_inspeccion);
    $(`.grid_envases.grid${id_inspeccion}`).toggleClass('editar_envases');
    $("#envases"+id_muestra).append(data.html);
    modoEdicionVisor(id_inspeccion);
    $(`.grid_envases.grid${id_inspeccion}`).toggleClass('editar_envases');
    setTimeout(function () {
      alargaMenu();
    }, 200);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function eliminaEnvase(id_envase, id_inspeccion) {
  $(`#elem_envase${id_envase}`).children().addClass("incorrecto");
  asegurar = confirm("Seguro que desexa borrar este envase? A acción é irreversible");
  if (asegurar) {
    $.post('/_eliminar_envase', {
      id_envase: id_envase,
      token: token
    }, function(data) {
      $(`#elem_envase${id_envase}`).remove();
    }).fail(function (data) {
      mensaxeErroAJAX(data);
    });
  } else {
    $(`#elem_envase${id_envase}`).children().removeClass("incorrecto");
  }
}

function eliminaMuestra(id_muestra) {
  $(".muestra"+id_muestra).addClass("incorrecto");
  asegurar = confirm("Seguro que desexa borrar esta mostra e os seus parámetros?");
  if (asegurar) {
    $.post('/_eliminar_muestra', {
      id_muestra: id_muestra,
      token: token
    }, function(data) {
      $(".muestra"+id_muestra).remove();
    }).fail(function (data) {
      mensaxeErroAJAX(data);
    });
  } else {
    $(".muestra"+id_muestra).removeClass("incorrecto");
  }
  
}

function download(fileUrl, fileName) {
  var a = document.createElement("a");
  a.href = fileUrl;
  a.setAttribute("download", fileName);
  a.click();
}

function borrarPerVert(id_industria) {
  if (confirm("Seguro que desexa eliminar o permiso de vertido para esta industria?")) {
    confirmaBorrarPerVert(id_industria);
  };
}

function confirmaBorrarPerVert(id_industria) {
  $.post('/_borrar_per_vert', {
    id_industria: id_industria,
    token: token
  }, function(data) {
    $("#boton_subir_PV").html("Subir permiso de vertido").removeClass("correcto").attr("onclick", '$("#file_perVer").click()');
    $("#borraPerVert").addClass("invisible");
  }).fail(function (data) {
    mensaxeErroAJAX(data);
  });
}

function borrarAAI(id_industria) {
  if (confirm("Seguro que desexa eliminar a Autorización Ambiental Integrada para esta industria?")) {
    confirmaBorrarAAI(id_industria);
  };
}

function confirmaBorrarAAI(id_industria) {
  $.post('/_borrar_aai', {
    id_industria: id_industria,
    token: token
  }, function(data) {
    $("#boton_subir_AAI").html("Subir AAI").removeClass("correcto").attr("onclick", '$("#file_AAI").click()');
    $("#borraAAI").addClass("invisible");
  }).fail(function (data) {
    mensaxeErroAJAX(data);
  });
}

function muestraFiltros(sistema) {
  $.getJSON('/_muestra_ficha_filtro_censo', {
    sistema: sistema,
    diccionarios_filtro: diccionarios_filtro
  }, function(data) {
    reduceMapa(1);
    setTimeout(function(){$("#contenedor_ficha_elemento").html(data.valor);}, 200);
    setTimeout(function(){alargaMenu();}, 200);
    setTimeout(function () {alargaMenu();}, 600);

  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

var diccionarios_filtro = []

function filtra(sistema) {
  $.getJSON('/_filtra_censo', {
    sistema: sistema,
    token: token,
    valores: $("div :input.correcto.filtro ").serialize(),
    valores_not: $("div :input.incorrecto ").serialize()
  }, function(data) {
    $(".boton.inspeccion").addClass("invisible");
    grupoIndustrias.eachLayer(function(layer) { grupoIndustrias.removeLayer(layer);});
    for (id in data.listado_id_censo) {
      window["e"+data.listado_id_censo[id]].addTo(grupoIndustrias);
    };
    for (id in data.listado_id_inspecciones) {
      $(".boton.inspeccion.inspeccion"+data.listado_id_inspecciones[id]).removeClass("invisible");
    }
    diccionarios_filtro = data.diccionarios_filtro
    muestraTabla();
    $(".grid_tabla").html(data.tabla)
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function descargaFiltro(sistema) {
  $.getJSON('/_filtra_censo-1', {
    sistema: sistema,
    token: token,
    valores: $("div :input.correcto.filtro ").serialize(),
    valores_not: $("div :input.incorrecto ").serialize()
  }, function(data) {
    $('a#descargaCSV').attr({href: "/_descarga_CSV"});
    document.getElementById('descargaCSV').click()
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function muestraIndustriasBuscadas() {
  var texto = RegExp(".*" + $("#textoBuscar").val() + ".*", 'i');
  $("tr").each(function(){
    if ($(this).children().text().match(texto)) {
      $(this).removeClass("invisible");
    } else if ($(this).children().prop("tagName") == "TD") {
      $(this).addClass("invisible");
    }
  });
  var encontradas = $("tr:not(.invisible):not(.invisible2)").length - 1;
  $("#filtro_JS").html(encontradas + " empresas");
};

function muestraIndustriaTipoInspeccion(i, esto) {
  if ($(esto).hasClass("resaltado")) {
    $(esto).removeClass("resaltado");
    $("tr").each(function(){
      $(this).removeClass("invisible2");
    });
  } else {
    $(".filtra_tipo").removeClass("resaltado");
    $(esto).addClass("resaltado");
    $("tr").each(function(){
      if ($(this).children().children("span.tipo"+i).length != 0) {
        $(this).removeClass("invisible2");
      } else if ($(this).children().prop("tagName") == "TD") {
        $(this).addClass("invisible2");
      }
    });
  }
  var encontradas = $("tr:not(.invisible):not(.invisible2)").length - 1;
  $("#filtro_JS").html(encontradas + " empresas");
}

function cerrarPlanificacion(id_insp){
  $.post(`/_informe_planificacion`, {
    id_insp: id_insp,
    token: token
  }, function(data) {
    muestraFichaInspeccion(id_insp, 0);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}