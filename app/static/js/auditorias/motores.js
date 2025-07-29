function nuevoMotor(id_equipo) {
  $.post('/_nuevo_motor', {
    id_equipo: id_equipo,
    token: token
  }, function(data) {
    $("#motores").append(data.panel);
    $("#botones_motores").append(data.boton);
    setTimeout(() => {
      alargaMenu();
    }, 300);
    $(`#boton_motor${data.id_motor}`).addClass("pulsado");
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
}
  
function muestraFichaMotor(id_motor) {
  if ($(`#boton_motor${id_motor}`).hasClass("pulsado")) {
    if (!$(`#guardarMotor${id_motor}`).hasClass("invisible")) {
      var nombre_motor = $(`#nombreMotor${id_motor}`).text();
      if (!confirm(`Hai datos sen gardar no motor ${nombre_motor}. Está seguro de que desexa pechar o panel?`)) {
        return undefined
      }
    }
    $(`#panel_motor${id_motor}`).remove()
    prevenirSalir()
  } else {
    $.getJSON('/_muestra_ficha_motor', {
      id_motor: id_motor
    }, function(data) {
      $("#motores").append(data.panel);
    }).fail(function(data) {
      mensaxeErroAJAX(data);
    });
  }
  $(`#boton_motor${id_motor}`).toggleClass("pulsado");
  setTimeout(function () {alargaMenu();}, 300)
}

function editaMotor(esto){
  let id_motor =  $(esto).attr("id").split("Motor")[1];
  $(`.subirCambiosMotor${id_motor}`).removeClass("invisible");
  $(esto).addClass("editado");
  prevenirSalir();
}

function actualizaDatosMotor(id_motor){
  $(`.subirCambiosMotor${id_motor}`).addClass("invisible");
  $.post('/_actualiza_datos_motor', {
    cambios: $(`input.editarMotor${id_motor}.editado`).serialize(),
    id_motor: id_motor,
    token: token
  }, function(data) {  
    finalizaActualizaDatosMotor(id_motor);
  }).fail(function(data) {
    $(".subirCambiosMotor").removeClass("invisible");
      mensaxeErroAJAX(data);
  });
}

function finalizaActualizaDatosMotor(id_motor) {
  $(`input.editarMotor${id_motor}.editado`).each(function() {
    let nombre = $(this).attr("name");
    let valor = $(this).val()
    $(`#${nombre}_label_Motor${id_motor}`).text(valor)
  });
  modoVisualizacionMotor(id_motor);
  let texto = $(`#denominacion_Motor${id_motor}`).val();
  $(`#boton_motor${id_motor}`).text(texto);
};

function cancelaActualizaDatosMotor(id_motor) {
  $(`input.editarMotor${id_motor}.editado`).each(function() {
    let nombre = $(this).attr("name");
    let valor = $(`#${nombre}_label_Motor${id_motor}`).text()
    $(this).val(valor)
  });
  modoVisualizacionMotor(id_motor);
};

function modoVisualizacionMotor(id_motor) {
  $(`input.editarMotor${id_motor}.editado`).removeClass("editado");
  modoEdicion(`Motor${id_motor}`);
  $(`.subirCambiosMotor${id_motor}`).addClass("invisible");
  prevenirSalir();
}

function guardaCambiosMotor(id_motor) {
  $(`#guardarMotor${id_motor}`).addClass('invisible');
  var estado_revisiones = {}
  $(`.revisionMotor${id_motor}`).each(function() {
    if ($(this).attr("hayCambio") == "1") {
      let estado = $(this).attr("estado");
      let id_revision = $(this).attr("id").split("revision")[1];
      estado_revisiones[id_revision] = estado;
    }
  });
  var observaciones = {}
  $(`.observacionMotor${id_motor}`).each(function() {
    let valor = $(this).val();
    let id_observacion = $(this).attr("id").split("observacionMotor")[1];
    observaciones[id_observacion] = valor;
  });

  $.post('/_actualiza_motor', {
    datos_motor: $(`input.datosMotor${id_motor}`).serialize(),
    id_motor: id_motor,
    estado_revisiones: JSON.stringify(estado_revisiones),
    observaciones: JSON.stringify(observaciones),
    mediciones: $(`input.revisiones_medicionMotor${id_motor}`).serialize(),
    token: token
  }, function(data) {  
    $(`.revisionMotor${id_motor}`).each(function() {
      for (let id_revision in data.revisiones_act) {
        let usuario = data.revisiones_act[id_revision].usuario;
        let fecha = data.revisiones_act[id_revision].fecha;
        $(`#revision_inspector${id_revision}`).text(usuario);
        $(`#revision_fecha${id_revision}`).text(fecha);
      }
    });
    $(`#checkMotor${id_motor}`).removeClass('invisible');
    setTimeout(function(){
        $(`#checkMotor${id_motor}`).addClass('invisible')
    }, 3000);
    prevenirSalir();
  }).fail(function(data) {
      $(`#guardarMotor${id_motor}`).removeClass('invisible');
      mensaxeErroAJAX(data);
  });
};
  
function borraMotor(id_motor) {
  if (!confirm("Seguro que desexa eliminar o motor? as revisións e fotos vinculadas tamén se eliminarán.")) {
    return undefined
  }
  $.post('/_borra_motor', {
    id_motor: id_motor,
    token: token
  }, function(data) {  
    $(`#panel_motor${id_motor}`).remove();
    $(`#boton_motor${id_motor}`).remove();
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  });
};
  
function subirFotoMotor(id_motor, formData) {
  var elemento = "Motor";
  var id_auditoria = obten_auditoria();

  formData.append("id_motor", id_motor);
  formData.append("id_auditoria", id_auditoria);
  formData.append("token", token);
  
  $(`#cargando_foto${id_motor}${elemento}`)
    .html("Subindo foto...")
    .removeClass("invisible");
  
  $.ajax({
    url: "/_subir_foto_motor",
    data: formData,
    processData: false,
    contentType: false,
    type: "POST",
    success: function (data) {
      if (!$(`#fotos_${id_motor}${elemento}`).hasClass('invisible')) {
          $(`#fotos_${id_motor}${elemento}`).html("").addClass('invisible');
          cargar_fotosMotor(id_motor);
      }
      $(`#check_foto${id_motor}${elemento}`).removeClass("invisible");
      $(`#cargando_foto${id_motor}${elemento}`).html("Foto subida correctamente");
      setTimeout(function() {
          $(`#check_foto${id_motor}${elemento}`).addClass("invisible");
          $(`#cargando_foto${id_motor}${elemento}`).addClass("invisible");
      }, 2500)
    },
    error: function (data) {
      mensaxeErroAJAX(data);
      $(`#cargando_foto${id_motor}${elemento}`).addClass('invisible');
    },
  });
}

function cargar_fotosMotor(id_motor) {
  var id_auditoria = obten_auditoria();
  var elemento = "Motor";
  $(`.boton_carga_fotos${id_motor}${elemento}`).toggleClass('invisible');
  $(`#fotos_${id_motor}${elemento}`).toggleClass('invisible');
  $.getJSON('/_ver_fotos_motor', {
    id_motor: id_motor,
    id_auditoria: id_auditoria
  }, function(data) {
      $(`#fotos_${id_motor}${elemento}`).html(data.fotos)
  }).fail(function(data) {
      $(`.boton_carga_fotos${id_motor}${elemento}`).toggleClass('invisible');
      $(`#fotos_${id_motor}${elemento}`).toggleClass('invisible');
      mensaxeErroAJAX(data);
  });
  setTimeout(function () {alargaMenu();}, 300)
};

function obten_auditoria() {
  if ($(".filtros_auditoria.pulsado").length < 1) {
    var id_auditoria = parseInt($("#lista_auditorias").children(":last").attr("auditoria"));
    cambiaFiltroAuditoria(id_auditoria);
  } else {
    var id_auditoria = parseInt($(".filtros_auditoria.pulsado").attr("auditoria"))
  }
  return id_auditoria
}

function asignaRevisionesMotor(id_motor) {
    var nuevas_revisiones = []
    $(`.revDisp${id_motor}Motor.editado`).each(function(){
      nuevas_revisiones.push($(this).attr("revision_id"));
    })
    var eliminar_revisiones = []
    $(`.revDisp${id_motor}Motor.incorrecto`).each(function(){
      let id_rev_disp = $(this).attr("revision_id");
      eliminar_revisiones.push(id_rev_disp);
    })
    
    $.post('/_asigna_revisiones_motor', {
      id_motor: id_motor,
      nuevas_revisiones: nuevas_revisiones,
      eliminar_revisiones: eliminar_revisiones,
      token: token
    }, function(data) {
      $(`#revisiones_disponibles_${id_motor}Motor`)
        .addClass("invisible");
      $(`#botones_rev_asig_${id_motor}Motor`)
        .removeClass("invisible")
        .html("")
        .append(data.boton);
      $(`#medicionesMotor${id_motor}`).html(data.input_medicion);
      $(`#verRevisiones_${id_motor}Motor`).removeClass("invisible");
      setTimeout(() => {
        alargaMenu();
      }, 300);
    }).fail(function(data) {
      mensaxeErroAJAX(data);
    });
  }
 
  function cancelaAsignaRevisionesMotor(id_motor) {
    $(`#revisiones_disponibles_${id_motor}Motor`)
        .addClass("invisible");
    $(`#botones_rev_asig_${id_motor}Motor`).removeClass("invisible");
    $(`#verRevisiones_${id_motor}Motor`).removeClass("invisible");
  }