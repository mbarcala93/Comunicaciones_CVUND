function seleccionarEDAR() {
  $(".seleccionar_EDAR").toggleClass("invisible");
  alargaMenu();
}


function nuevaAuditoria(id_edar) {
    $.post('/_nueva_auditoria', {
        id_edar: id_edar,
        token: token
      }, function(data) {  
          $(`#listado_auditorias`).prepend(data.boton_nueva_auditoria);
          seleccionarEDAR();
          setTimeout(() => {alargaMenu();}, 300);
      }).fail(function(data) {
          mensaxeErroAJAX(data);
      });
}

function nuevaInstalacion(cod_edar) {
  var nombre = prompt("Nome da instalación:");
  if (nombre == undefined) {return}
  $.post('/_nueva_instalacion', {
    nombre: nombre,
    cod_edar: cod_edar,
    token: token
    }, function(data) {  
      $(`#listado_instalaciones`).append(data.panel_nueva_instalacion);
      setTimeout(() => {alargaMenu();}, 300);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}

function nuevoTratamiento(id_instalacion) {
  var nombre = prompt("Nome do tratamento:");
  if (nombre == undefined) {return}
  $.post('/_nuevo_tratamiento', {
    nombre: nombre,
    id_instalacion: id_instalacion,
    token: token
    }, function(data) {  
      $(`#listado_tratamientos${id_instalacion}`).append(data.panel_nuevo_tratamiento);
      setTimeout(() => {alargaMenu();}, 300);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}

function nuevoEquipo(id_tratamiento) {
  var denominacion = prompt("Denominacion do equipo:");
  if (denominacion == undefined) {return}
  $.post('/_nuevo_equipo', {
    denominacion: denominacion,
    id_tratamiento: id_tratamiento,
    token: token
    }, function(data) {  
      $(`#listado_equipos`).append(data.boton_nuevo_equipo);
      setTimeout(() => {alargaMenu();}, 300);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}

function borraInstalacion(id_instalacion) {
  if (!confirm("Seguro que desexa borrar a instalación? Eliminaranse TODOS os tratementos, equipos, fotos, revisións e motores vinculados.")) {return undefined}
  $.post('/_borra_instalacion', {
    id_instalacion: id_instalacion,
    token: token
    }, function(data) {  
      $(`#instalacion${id_instalacion}`).remove();
      setTimeout(() => {alargaMenu();}, 300);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}

function borraTratamiento(id_tratamiento) {
  if (!confirm("Seguro que desexa borrar o tratamento? Eliminaranse TODOS os equipos, fotos, revisións e motores vinculados.")) {return undefined}
  $.post('/_borra_tratamiento', {
    id_tratamiento: id_tratamiento,
    token: token
    }, function(data) {  
      window.location.replace(data.redireccion);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}

function borraEquipo(id_equipo) {
  if (!confirm("Seguro que desexa borrar o equipo? Eliminaranse TODAS as fotos, revisións e motores vinculados.")) {return undefined}
  $.post('/_borra_equipo', {
    id_equipo: id_equipo,
    token: token
    }, function(data) {  
      window.location.replace(data.redireccion);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}



function muestraBuscados() {
  var texto = RegExp(".*" + $("#textoBuscar").val() + ".*", 'i');
  $(".equipo>div").each(function() {
    if ($(this).text().match(texto)){
      $(this).parent().parent().show()
    }
    else {
      $(this).parent().parent().hide()
    }
  });
  setTimeout(function(){alargaMenu();}, 200);
};

function muestraTiposPruebas() {
  $("#tipo_prueba").addClass("invisible");
  $("#tipos_pruebas").removeClass("invisible");
}

function cambiaTipoPrueba(id_equipo, id_tipo_prueba, esto) {
  $.post('/_cambia_tipo_prueba', {
      id_equipo: id_equipo,
      id_tipo_prueba: id_tipo_prueba,
      token: token
  }, function(data) {
    $(".prueba").removeClass('pulsado');
    $(esto).addClass('pulsado');
    $("#tipo_prueba").removeClass("invisible");
    $("#tipos_pruebas").addClass("invisible");
    $('#titulo_prueba').text($(esto).text());
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
}

function cambiaFiltroAuditoria(id_auditoria, hayFotos=0) {
  var visibles = $(`.revision${id_auditoria}`).not(".invisible").length;
  $.post('/_cambia_filtro_auditoria', {
    id_auditoria: id_auditoria,
    token: token
  }, function(data) {
    $(`.filtro_auditoria${id_auditoria}`).toggleClass("decorado pulsado");
    $(".filtros_auditoria")
      .not(`.filtro_auditoria${id_auditoria}`)
      .removeClass("decorado pulsado");
    $(".revision").addClass("invisible");
    if (hayFotos) {
      avisa_no_hay_fotos();
    }
    if (!visibles){
      $(`.revision${id_auditoria}`).removeClass("invisible");
    }
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
};

function filtraPendientes() {
  $(".botonEquipo").each(function(){
    if ($(this).find(".material-icons:visible").length == 0) {
      $(this).toggleClass("invisible")
    }
  })
}

function giraFoto(id_foto, elemento) {
  $.post('/_gira_foto', {
    id_foto: id_foto,
    elemento: elemento,
    token: token
  }, function(data) {
    d = new Date();
    $(`#foto${id_foto} img`).attr("src", `/static_p/fotos_audit/${data.ruta}?` + d.getTime());
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
}

function promocionaPortada(id_foto, elemento) {
  $.post('/_promociona_foto', {
    id_foto: id_foto,
    elemento: elemento,
    token: token
  }, function(data) {
    $(`#promocionaPortada${id_foto}`).toggleClass('correcto');
    $(`#promocionadaPortada${id_foto}`).toggleClass('invisible');
    $(`#promocionadaPortada2${id_foto}`).toggleClass('invisible');
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
}

function promocionaAuditoria(id_foto, elemento) {
  $.post('/_promociona_auditoria', {
    id_foto: id_foto,
    elemento: elemento,
    token: token
  }, function(data) {

  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
}