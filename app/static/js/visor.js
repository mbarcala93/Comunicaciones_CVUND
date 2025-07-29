var mapa_reducido_elemento = 0;
var mapa_reducido_inspeccion = 0;

function reduceMapa(ficha_elemento) {
  $(".grid_tabla").removeClass("tabla_alargada");
  if (ficha_elemento) {mapa_reducido_elemento = 1;}
  else {mapa_reducido_inspeccion = 1;}
  $("#contenedor_ficha_inspecciones").addClass("grid23").removeClass("grid13R");
  if (mapa_reducido_elemento + mapa_reducido_inspeccion == 1) {
    $("#todo").addClass("grid_encogido").removeClass("grid_encogido2");
    $(".visor").addClass("visor_encogido").removeClass("visor_encogido2");
    $(".grid_tabla").removeClass("tabla_encogida");
  } else {
    $("#todo").addClass("grid_encogido2").removeClass("grid_encogido");
    $(".visor").addClass("visor_encogido2").removeClass("visor_encogido");
    $(".grid_tabla").addClass("tabla_encogida");
  };
  if (!mq.matches) {
    $(".visor").removeClass("mapa_mediano");
    $("#amplia_mapa").removeClass('invisible');
    $("#reduce_mapa").addClass('invisible');
  };
  setTimeout(function(){mymap.invalidateSize(true)}, 100);
};

function ampliaMapa(ficha) {
  $(".grid_tabla").removeClass("tabla_encogida");
  if (ficha == "elemento") {
    mapa_reducido_elemento = 0;
    $("#contenedor_ficha_inspecciones").removeClass("grid23").addClass("grid13R");
  }
  else {mapa_reducido_inspeccion = 0;}
  if (mapa_reducido_elemento == 0 && mapa_reducido_inspeccion == 0) {
    $("#todo").removeClass("grid_encogido");
    $(".visor").removeClass("visor_encogido").removeClass("mapa_mediano");
    $(".boton_amplia_mapa").addClass('invisible');
    $(".grid_tabla").addClass("tabla_alargada");
  } else if (mapa_reducido_elemento + mapa_reducido_inspeccion == 1) {
    $("#todo").addClass("grid_encogido").removeClass("grid_encogido2");
    $(".visor").addClass("visor_encogido").removeClass("visor_encogido2").removeClass("mapa_mediano");
  };
  if (!mq.matches) {
    $("#contenedor_ficha_inspecciones").removeClass("grid13R");
  };
  setTimeout(function(){mymap.invalidateSize(true)}, 100);
};

function boton_amplia_mapa(amplia) {
  $(".boton_amplia_mapa").toggleClass("invisible");
  $(".visor").toggleClass("mapa_mediano");
  setTimeout(function(){mymap.invalidateSize(true); alargaMenu()}, 250);
};

function muestraTabla() {
  $(".visor").addClass("visor_achatado");
  $("#todo").addClass("grid_achatado");
  $(".grid_tabla").removeClass("invisible")
  setTimeout(function(){mymap.invalidateSize(true)}, 100);
  setTimeout(function () {alargaMenu();}, 600);
};

function ocultaTabla() {
  $(".visor").removeClass("visor_achatado");
  $("#todo").removeClass("grid_achatado");
  $(".grid_tabla").addClass("invisible")
  setTimeout(function(){mymap.invalidateSize(true)}, 100);
  setTimeout(function () {alargaMenu();}, 600);
};

function ampliaImagen(ruta) {
  if (mq.matches) {
    window.open('static_p/fotos/' + ruta, '_blank');
  };
};

function modoEdicionVisor(id_elemento) {
  $(".editar"+id_elemento).toggleClass("invisible");
  $("#boton_upload").hide();
  setTimeout(function(){alargaMenu();}, 600);
}

function ocultaFicha(ficha, id) {
  if ($(".ficha.inspeccion").length > 1 && id) {
    $("#ficha"+id).removeClass("inspeccion").hide(300);
    setTimeout(function(){$("#ficha"+id).remove();}, 300);
  } else {
    $("#contenedor_ficha_"+ficha).html("");
    ampliaMapa(ficha);
    setTimeout(function(){alargaMenu();}, 350);
  };
};

function cargar_(input, id) {
  $("#carga_" + input+id).toggle();
  $("#file64_" + input+id).val("");
  $("#subir_" + input + "_icon"+id).hide()
  setTimeout(function () {alargaMenu();}, 200);
}

// const compress = new Compress();

function comprimir(input, id) {
  $("#subir_" + input + "_icon"+id).hide();
  $("#cargando_"+ input+id).html("Comprimindo foto...").show();
  var files = [...$("#file64_" + input+id)[0].files]
  var compress = new Compress();
  compress.compress(files, {
    size: 1, // the max size in MB, defaults to 2MB
    quality: 0.75, // the quality of the image, max is 1,
    maxWidth: 1920, // the max width of the output image, defaults to 1920px
    maxHeight: 1920, // the max height of the output image, defaults to 1920px
    resize: true // defaults to true, set false if you do not want to resize the image width and height
  }).then((data) => {
    // returns an array of compressed images
    $("#string64_" + input+id).val(data[0]["data"]).addClass("hayFoto");
    $("#cargando_"+ input+id).hide();
    $("#subir_" + input + "_icon"+id).show();
    if (input != "foto") {
      $("."+input+id).addClass("editado").parent().addClass('visible');
      $(".etiqueta_fotos").addClass('editado')
      $(".boton_upload").show();
    }
  })
  setTimeout(function () {alargaMenu();}, 300);
  setTimeout(function () {alargaMenu();}, 1000);
};

function generaDivFoto(ruta, num_foto, id_foto, etiqueta, id_inspeccion, tipo_visor) {
  var texto_establece_principal = ""
  if (tipo_visor == 'ind') {
    texto_establece_principal = "<span onclick='establecePrincipal(&quot;" + ruta + "&quot;, " + id_foto + ")'><span class='material-icons'>photo</span> Foto principal da industria</span><br>"
  } else {
    texto_establece_principal = "<span onclick='establecePrincipal(&quot;" + ruta + "&quot;, " + id_foto + ", 1)'><span class='material-icons'>photo</span> Foto principal do elemento</span><br>"+
    "<span onclick='establecePrincipal(&quot;" + ruta + "&quot;, " + id_foto + ", 0)'><span class='material-icons'>photo</span> Foto principal da inspección</span></div>"
  }
  return  foto = "<div class='interior_panel rotable"+ num_foto + "_" + id_inspeccion +"' onclick='rota(" + num_foto + ", " + id_inspeccion + ")'>"+
    "<div class='frontal_panel foto'><img src='/static_p/fotos/"+ruta+"'></div>"+
    "<div class='trasero_panel foto'>"+
    "<b><span class='material-icons'>local_offer</span> "+ etiqueta +"</b><br><br>"+
    "<span onclick='borraFoto(&quot;" + ruta + "&quot;, &quot;" + num_foto + "&quot;, &quot;" + id_inspeccion + "&quot;)'><span class='material-icons'>delete</span> Borrar foto</span><br>"+
    texto_establece_principal +
  "</div>"
};

function borraFoto(ruta, num_foto, id_inspeccion) {
  if (confirm("Seguro que desexa eliminar esta foto?")) {
    confirmarBorrarFoto(ruta, num_foto, id_inspeccion);
  };
};

function rota(num_foto, id_inspeccion) {
  $(".rotable"+num_foto+"_"+id_inspeccion).toggleClass("rota");
}

function editarInput(esto, id_elemento, edita_hermanos) {
  if (!boton_actualizar_pulsado) {
    $(".boton_upload"+id_elemento).show();
    alargaMenu();
    var indice = esto.id.split("-")[1];
    $("#etiqueta"+id_elemento+"-"+indice).addClass("editado");
    $(esto).addClass("editado");
    if (edita_hermanos) {
      var indice_hermano = esto.id.split("-")[2]
      $(".hermano"+indice_hermano).addClass("editado");
      $(esto).parent().siblings(".etiqueta.hermano").addClass("editado")
    }
  }
}

var boton_actualizar_pulsado = 0;

function actualizaElemento(id) {
  if (!boton_actualizar_pulsado) {
    boton_actualizar_pulsado = 1;
    $("span.editar"+id).hide();
    $("#boton_editar"+id).hide();
    $(".etiq"+id+":not(.editado)").hide();
    $(".t_ficha"+id+".titulo_ficha:not(.confirma)").hide();
    $(".input"+id+".ficha:not(.editado)").hide();
    $(".bot"+id+":not(.editado)").hide();
    $(".val"+id+":not(.editado)").hide();
    $(".valor"+id+":not(.editado)").hide();
    $(".boton_upload"+id).hide();
    $(".grbot"+id+":not(.visible)").hide();
    for(let elem of $(".apartado_parametros")){
      if($(`#${elem.id}`).children().find('.editado').length == 0){
        $(`#${elem.id}`).hide();
      }
    }
    for(let elem of $(".elem_parametro")){
      if($(`#${elem.id}`).find('.editado').length == 0){
        $(`#${elem.id}`).hide();
      }
    }
    $(".confirmar"+id).show();
    var posicion_boton = $("#boton_confirmar"+id).offset()['top'];
    if (window.innerHeight >= posicion_boton) {
      var posicion = 0;
    } else {
      var posicion = posicion_boton - window.innerHeight + 100;
    }
    $('html, body').animate( { scrollTop :  posicion  }, 800 );
  }
}

var antiguoPopupMover = "";
var modoCrearPuntos = 0;
var interiorPopup_crear = "";

function moverElemento(id) {
  if (geoposactivado) {getPosition()};
  modoCrearPuntos = 1;
  antiguoPopupMover = window["e"+id]._popup._content;
  window["e"+id].bindPopup("Sinale a nova localización.<br><span onclick='cancelaMueveElemento(&quot;"+id + "&quot;)'><span class='material-icons subir' >cancel</span> Cancelar</span>");
  interiorPopup_crear = "<span class='clicable' onclick='confirmaMoverElemento(&quot;"+id+"&quot;)'><span class='material-icons subir' >check</span> Confirmar localización</span>"+
                  "<br><span class='clicable' onclick='cancelaMueveElemento(&quot;"+id + "&quot;)'><span class='material-icons subir' >cancel</span> Cancelar</span>";

  userMarker.bindPopup(interiorPopup_crear);
};

function cancelaMueveElemento(id) {
  window["e"+id].closePopup().bindPopup(antiguoPopupMover);
  interiorPopup_crear = "";
  modoCrearPuntos = 0;
}

proj4.defs("EPSG:25829","+proj=utm +zone=29 +ellps=GRS80 +units=m +no_defs");
var sourceProj = new proj4.Proj('WGS84');
var destProj = new proj4.Proj('EPSG:25829');

function latlng2xy(latlng) {
   xy = proj4(sourceProj,destProj,[latlng['lng'],latlng['lat']]);
   resultado = "<div>x: "+ numeroConPuntos(xy[0].toFixed(0)) + "<br>y: " + numeroConPuntos(xy[1].toFixed(0)) + "</div>"
   return resultado
};

function toggleOpcionesEditar() {
  $(".opciones_editar").toggle();
};

function eliminarElemento(id) {
  if (confirm("Seguro que desexa eliminar este elemento? Borraranse as inspeccións, fotos e medicións asociadas.")) {
    confirmarEliminarElemento(id)
  };
};

function eliminarInspeccion(id_insp) {
  if (confirm("Seguro que desexa eliminar esta inspección? Borraranse as fotos e medicións asociadas.")) {
    confirmarEliminarInspeccion(id_insp)
  };
};

function outros(elemento, cod) {
  if (cod == 1) {
    $("."+ elemento +"-outros").show();
    alargaMenu();
  } else {
    $("."+ elemento +"-outros").hide().val("");
  };
};

function editaInput(valor, indice, esto, id, hacerScroll) {
  if (!boton_actualizar_pulsado) {
    $("#valor"+ id +"-"+indice).val(valor).addClass("editado");
    $("#etiqueta"+ id +"-"+indice).addClass("editado");
    $(".boton_upload"+id).show();
    $(".boton"+ id +"-"+indice).removeClass("pulsado").removeClass("editado");
    $(esto).addClass("editado").parent().addClass('visible');

    setTimeout(function () {alargaMenu();}, 300);
    if (!mq.matches && hacerScroll) {
      $('html, body').animate( { scrollTop : $("#etiqueta-"+(parseInt(indice) + 1)).offset()['top']}, 300 );
    };
  }
};

function engadeInput(valor, indice, esto, id, hacerScroll) {
  if (!boton_actualizar_pulsado) {
    $("#valor"+ id +"-"+indice).val($("#valor"+ id +"-"+indice).val() + valor).addClass("editado");
    $("#etiqueta"+ id +"-"+indice).addClass("editado");
    $(".boton_upload"+id).show();
    $(".boton"+ id +"-"+indice).removeClass("editado").removeClass("pulsado");
    $(esto).addClass("editado").parent().addClass('visible');
    setTimeout(function () {$(esto).removeClass("editado");}, 100);
    setTimeout(function () {alargaMenu();}, 300);
    if (!mq.matches && hacerScroll) {
      $('html, body').animate( { scrollTop : $("#etiqueta-"+(parseInt(indice) + 1)).offset()['top']}, 300 );
    };
  }
};

function seleccionaInput(valor, separador, indice, esto, id, hacerScroll) {
  if (!boton_actualizar_pulsado) {
    let valor_input = $("#valor"+ id +"-"+indice).val().split(separador);
    if(valor_input.includes(valor.toString())){
      valor_input.splice(valor_input.indexOf(valor.toString()),1);

    }else{
      valor_input.push(valor.toString());

    }
    valor_input = valor_input.filter((v)=>v!='')
    $("#valor"+ id +"-"+indice).val(valor_input.join(separador));
    $("#valor"+ id +"-"+indice).addClass("editado");
    $("#etiqueta"+ id +"-"+indice).addClass("editado");
    $(".boton_upload"+id).show();
    $(".boton"+ id +"-"+indice).removeClass("editado").removeClass("pulsado");
    $(esto).addClass("editado").parent().addClass('visible');
    setTimeout(function () {alargaMenu();}, 300);
    if (!mq.matches && hacerScroll) {
      $('html, body').animate( { scrollTop : $("#etiqueta-"+(parseInt(indice) + 1)).offset()['top']}, 300 );
    };
  }
};

function alternaInput(valor, indice, esto, id) {
  if ($(esto).hasClass("correcto")) {
    $("#valor"+ id +"-"+indice)
    .val(valor)
    // .attr('name', $("#valor"+ id +"-"+indice).attr('name') + "!")
    .removeClass("correcto")
    .addClass("incorrecto");;
    $(esto).removeClass("correcto")
    .addClass("incorrecto");
  } else if ($(esto).hasClass("incorrecto")) {
    $("#valor"+ id +"-"+indice)
      .val("")
      // .attr('name', $("#valor"+ id +"-"+indice).attr('name').split("!")[0])
      .removeClass("incorrecto");
      $(esto).removeClass("incorrecto");
  } else {
    $("#valor"+ id +"-"+indice)
      .val(valor)
      .addClass("correcto");
      $(esto).addClass("correcto");
  }
};

var alterna_datos_marea = ["actual", "maxima", "tiempo_maxima", "porcentaje"];
var indice_alterna_datos_marea = 1;
function alternaMarea() {
  $(".marea").hide();
  $("#" + alterna_datos_marea[indice_alterna_datos_marea]).show()
  CopyToClipboard(alterna_datos_marea[indice_alterna_datos_marea])
  if (indice_alterna_datos_marea < 3) {
    indice_alterna_datos_marea += 1;
  } else {
    indice_alterna_datos_marea = 0;
  }
}

function CopyToClipboard(id)
{
var r = document.createRange();
r.selectNode(document.getElementById(id));
window.getSelection().removeAllRanges();
window.getSelection().addRange(r);
document.execCommand('copy');
window.getSelection().removeAllRanges();
}

function expandir(indice) {
  $(".expande"+indice).toggle(300);
  setTimeout(function(){alargaMenu();}, 400);
}

function minimizaActividades() {
  if (!$(".expandeActiv.grid_container").hasClass("invisible2")) {expandir_invisible('Activ')}
}

function expandir_invisible(indice) {
  $(".expande"+indice).toggleClass("invisible2");
  setTimeout(function(){alargaMenu();}, 400);
}

function centraIndustria(id) {
  mymap.flyTo(window["e"+id].getLatLng());
  window["e"+id].openPopup();
}

function obtenerGeoJSON(edar, capa) {
  $("span.leyenda#"+capa).html("hourglass_empty");
  if (!window[capa + 'pl'].getLayers().length) {
    $.getJSON('/_obtener_geoJSON', {
      edar: edar,
      capa: capa,
      token: token
    }, function(data) {
      window[capa + 'pl'].addData(data.features)
      $("span.leyenda#"+capa).addClass("invisible");
    }).fail(function(data) {
      $("span.leyenda#"+capa).html("get_app");
      if (typeof data.responseJSON != "undefined") {var error = data.responseJSON.error;} else {var error = "Erro no servidor. "};
      alert(error + " Se o problema persiste contacte co administrador.");
    });
  }
}

function registrarUsuario(){
  let nombre = prompt('Nome:');

  $.post('/_registra_usuario', {
    nombre: nombre,
    token: token
  }, function(data) {
    let option= document.createElement('option');
    option.setAttribute('name',`${nombre}`);
    option.setAttribute('valor',`${data.id_usuario}`);
    option.innerHTML = `${nombre}`;
    $('#usuarios').append(option);
    setTimeout(() => {
      alert('Usuario rexistrado con exito');
    }, 100);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function marcaInSitu(id_elemento,id_parametro){
  if($(`#valorActual${id_elemento}-24-${id_parametro}vinculado`).hasClass('editado')){
    editaInput(1, `23-${id_parametro}`, $(`#valor${id_elemento}-23-${id_parametro}`), `${id_elemento}`);
  }else{
    editaInput(0, `23-${id_parametro}`, $(`#valor${id_elemento}-23-${id_parametro}`), `${id_elemento}`);
  }
}