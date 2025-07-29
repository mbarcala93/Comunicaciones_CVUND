function editaEquipo(esto){
  $(".subirCambiosEquipo").removeClass("invisible");
  $(esto).addClass("editado");
  prevenirSalir();
}

function actualizaDatosEquipo(id_equipo){
  $(".subirCambiosEquipo").addClass("invisible");
  $.post('/_actualiza_datos_equipo', {
    cambios: $("input.editarEquipo.editado").serialize(),
    id_equipo: id_equipo,
    token: token
  }, function(data) {  
    finalizaActualizaDatosEquipo(id_equipo);
  }).fail(function(data) {
    $(".subirCambiosEquipo").removeClass("invisible");
      mensaxeErroAJAX(data);
  });
}

function finalizaActualizaDatosEquipo() {
  $("input.editarEquipo.editado").not(".titulo").each(function() {
    let nombre = $(this).attr("name");
    let valor = $(this).val()
    $(`#${nombre}`).text(valor)
  });
  let valor = `${$("#denominacion").val()} ${$("#tipo").val()}`
  $(`#denominacion_tipo`).text(valor);
  $(`#denominacion`).attr("bbdd", `${$("#denominacion").val()}`);
  $(`#tipo`).attr("bbdd", `${$("#tipo").val()}`);
  modoVisualizacion();
};

function cancelaActualizaDatosEquipo() {
  $("input.editarEquipo.editado").not(".titulo").each(function() {
    let nombre = $(this).attr("name");
    let valor = $(`#${nombre}`).text()
    $(this).val(valor)
  });
  $(`#denominacion`).val($(`#denominacion`).attr("bbdd"));
  $(`#tipo`).val($(`#tipo`).attr("bbdd"));
  modoVisualizacion();
};

function modoVisualizacion() {
  $("input.editarEquipo.editado").removeClass("editado");
  modoEdicion("Equipo");
  $(".subirCambiosEquipo").addClass("invisible");
  prevenirSalir();
}

var coloresEstadoRevision = {0: "#ffeea0", 1: "#8cd586", 2: "#fe93a3", 3: "#cfcfcf"};

var cambios = {};

function verRevisiones(id_elemento, elemento) {
  $(`#revisiones_${id_elemento}${elemento}`).toggleClass("invisible");
  obten_auditoria();
  setTimeout(function () {alargaMenu();}, 300)
};

function estadoRevision(id, elemento="", id_elemento="") {
  hay_Cambio(elemento, id_elemento)
  var estado = parseInt($(`#revision${id}`).attr("estado"));
  if (estado < 3) {
    var nuevo_estado = estado + 1;
  } else {
    var nuevo_estado = 0;
  }
  $("#revision" + id)
    .css("background-color", coloresEstadoRevision[nuevo_estado])
    .attr("estado", nuevo_estado)
    .attr("hayCambio", 1);
  cambios[id] = nuevo_estado;
};

function hay_Cambio(elemento="", id_elemento='') {
  $(`#guardar${elemento}${id_elemento}`).removeClass('invisible');
  prevenirSalir();
}

function guardaCambios(id_equipo) {
  var observaciones = {}
  $(`.observacion${id_equipo}`).each(function() {
    let valor = $(this).val();
    let id_observacion = $(this).attr("id").split("observacion")[1];
    observaciones[id_observacion] = valor;
  });

  $(".guardar").addClass('invisible');
  $.post('/_actualiza_equipo', {
    cambios: JSON.stringify(cambios),
    observaciones: JSON.stringify(observaciones),
    marca: $("#marca").val(),
    modelo: $("#modelo").val(),
    num_serie: $("#num_serie").val(),
    criticidad: $("#criticidad").val(),
    mediciones: $("input.revisiones_medicion").serialize(),
    id_equipo: id_equipo,
    token: token
  }, function(data) {  
    $("#check").removeClass('invisible');
    setTimeout(function(){
        $("#check").addClass('invisible')
    }, 3000);
    for (id in cambios) {
    $("#revision_fecha" + id).html(data.fecha);
    $("#revision_inspector" + id).html(data.id_inspector)
    };
    prevenirSalir();
  }).fail(function(data) {
      $(".guardar").removeClass('invisible')
      mensaxeErroAJAX(data);
  });
};

function cargar_fotos(id_equipo) {
    $(".boton_carga_fotos").toggleClass('invisible');
    $("#mas_fotos").toggleClass('invisible');
    $(".revisiones").toggleClass("bajo");
    if(!$("#mas_fotos").hasClass('invisible')) {
      $.getJSON('/_ver_fotos_equipo', {
        id_equipo: id_equipo
      }, function(data) {
        $("#mas_fotos .matriz_fotos").html(data.fotos);
        avisa_no_hay_fotos();
        setTimeout(function () {alargaMenu();}, 300);
      }).fail(function(data) {
          $(".boton_carga_fotos").toggleClass('invisible');
          $("#mas_fotos").toggleClass('invisible');
          mensaxeErroAJAX(data);
          $(".revisiones").toggleClass("bajo");
      });
    }
    setTimeout(function () {alargaMenu();}, 300);
};

function avisa_no_hay_fotos() {
  $("#sin_fotos").addClass("invisible")
  setTimeout(function() {
    if ($("#mas_fotos .matriz_fotos .interior_panel:visible").length == 0) {
      $("#sin_fotos").removeClass("invisible")
    } else {
      $("#sin_fotos").addClass("invisible")
    }
  }, 100)
}
  
function cargar_subir_fotos(elemento="", id_elemento="") {
    $(`#panel_subir_fotos${elemento}${id_elemento}`).toggleClass("invisible");
    $(`.boton_subir_foto${elemento}${id_elemento}`).toggleClass("invisible");
    setTimeout(function () {
        alargaMenu();
    }, 300);
};

function rota(num_foto) {
    $(".rotable"+num_foto).toggleClass("rota");
}

function cambiaTipo(id_foto, tipo, elemento) {
    $.post('/_cambia_tipo', {
        id_foto: id_foto,
        tipo: tipo,
        elemento: elemento,
        token: token
    }, function(data) {
        if (tipo == 1 && elemento == 'equipos') {
          $("#foto_principal img").attr("src", `/static_p/fotos_audit/${data.ruta}`);
        }
        cargar_fotos(data.id_equipo);
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
};

function comprimirFoto(id_tabla, esto, elemento) {
    $(`#cargando_foto${id_tabla}${elemento}`)
        .removeClass("invisible")
        .text('Comprimindo foto...');
    var max_width = 1920;
    var max_height = 1920;  
    for (let index = 0; index <  $(esto).prop("files").length; index++) {
        const file =  $(esto).prop("files")[index];
        if (!file) {
          return;
        }
        new Compressor(file, {
          maxWidth: max_width,
          maxHeight: max_height,
          success(result) {
            const formData = new FormData();
            formData.append("foto", result, result.name);
            if (elemento == undefined) {
              subirFoto(id_tabla, formData);
            } else if (elemento == "Motor") {
              subirFotoMotor(id_tabla, formData);
            }
          },
          error(err) {
            const data = {
              error:
                "Error comprimindo o ficheiro. Recargue a páxina e comprobe que se trata dunha imaxe.",
            };
            mensaxeErroAJAX(data);
            $(`#cargando_foto${id_tabla}${elemento}`).addClass("invisible");
          },
        });
    } 
    // const file = $(esto).prop("files")[0];
}

function subirFoto(id_equipo, formData) {
    formData.append("id_equipo", id_equipo);
    formData.append("token", token);
    
    $(`#cargando_foto${id_equipo}`)
      .html("Subindo foto...")
      .removeClass("invisible");
    
    $.ajax({
      url: "/_subir_foto_equipo",
      data: formData,
      processData: false,
      contentType: false,
      type: "POST",
      success: function (data) {
        if ($("#foto_principal img.primeraFoto").attr("src") == "/static_p/fotos_audit/sin_foto.png") {
          $("#foto_principal img.primeraFoto").attr("src", `/static_p/fotos_audit/${data.ruta}`)
        }
        if (!$("#mas_fotos").hasClass('invisible')) {
            cargar_fotos(id_equipo);
        }
        cargar_fotos(id_equipo);
        $(`#check_foto${id_equipo}`).removeClass("invisible");
        $(`#cargando_foto${id_equipo}`).html("Foto subida correctamente");
        setTimeout(function() {
            $(`#check_foto${id_equipo}`).addClass("invisible");
            $(`#cargando_foto${id_equipo}`).addClass("invisible");
            alargaMenu();
        }, 2500)
      },
      error: function (data) {
        mensaxeErroAJAX(data);
        $(`#cargando_foto${id_equipo}`).addClass('invisible');
      },
    });
  }

function borraFoto(id_foto, elemento) {
    if (!confirm("Seguro que desexa borrar esta foto?")) {
        return undefined
    }
    $.post('/_borra_foto_elem_audit', {
        id_foto: id_foto,
        elemento: elemento,
        token: token
    }, function(data) {
        $(`#foto${id_foto}`).remove();
    }).fail(function(data) {
        mensaxeErroAJAX(data);
    });
}

function prevenirSalir() {
  if ($(".guardar:visible").length > 0) {
    window.onbeforeunload = function() {return 0;}
  } else {
    window.onbeforeunload = null;
  }
}

function obten_auditoria() {
  if ($(".filtros_auditoria.pulsado").length < 1) {
    var id_auditoria = parseInt($("#lista_auditorias").children(":last").attr("auditoria"));
    cambiaFiltroAuditoria(id_auditoria);
  } else {
    var id_auditoria = parseInt($(".filtros_auditoria.pulsado").attr("auditoria"))
  }
  return id_auditoria
}

function verRevisionesDisponibles(id_elemento, elemento) {
  $(`#botones_rev_asig_${id_elemento}${elemento}`).addClass("invisible");
  $(`#verRevisiones_${id_elemento}${elemento}`).addClass("invisible");
  obten_auditoria();
  $.getJSON('/_ver_revisiones_disponibles', {
	id_elemento: id_elemento,
	elemento: elemento
  }, function(data) {
    $(`#revisiones_disponibles_${id_elemento}${elemento}`).removeClass("invisible");
    $(`#botones_rev_disp_${id_elemento}${elemento}`).html(data.boton_rev_disp);
    // boton_nueva_rev_disp = `<span class="material-icons boton panel alineado" onclick="nuevaRevisionDisponible(${id_elemento}, '${elemento}')">add_circle_outline</span>`
    // $(`#botones_rev_disp_${id_elemento}${elemento}`).append(boton_nueva_rev_disp);
    $(`#muestra_rev_ocultas_${id_elemento}${elemento}`).removeClass("invisible");
    $(`#botones_rev_disp_oc_${id_elemento}${elemento}`).html(data.boton_rev_disp_oc_);
    $(`#botones_grupo_rev${id_elemento}${elemento}`).html(data.boton_grupo_rev);
    setTimeout(function () {alargaMenu();}, 300)
    
  }).fail(function(data) {
      mensaxeErroAJAX(data);
      $(`#verRevisiones_${id_elemento}${elemento}`).removeClass("invisible");
  });
};

function muestraRevOcultas(id_equipo) {
  $(`.oculta_rev_disp${id_equipo}`).toggleClass('invisible');
  setTimeout(function () {alargaMenu();}, 100)
}

function seleccionaGrupoRevisionDisponible(ids_rev_disp, sufijo, esto) {
  let lista_id = ids_rev_disp.split(",");
  if ($(esto).hasClass("pulsado")) {
    $(esto).removeClass("pulsado");
    for (const id_revision_disponible of lista_id) {
      let color = $(`#revDisp${sufijo}_${id_revision_disponible}`).attr("color")
      $(`#revDisp${sufijo}_${id_revision_disponible}`)
        .removeClass("editado")
        .attr("style", `background-color: ${color}`);

    }
  } else {
    $(`.grupoRevDisp${sufijo}.pulsado`).click();
    $(esto).addClass("pulsado");
    for (const id_revision_disponible of lista_id) {
      $(`#revDisp${sufijo}_${id_revision_disponible}`)
        .addClass("editado")
        .attr("style", "");
    }
  }
  setTimeout(function () {alargaMenu();}, 300)
}

function seleccionaRevisionDisponible(id_revision_disponible, sufijo) {
  if ($(`#revDisp${sufijo}_${id_revision_disponible}`).hasClass("pulsado")) {
    $(`#revDisp${sufijo}_${id_revision_disponible}`)
      .addClass("incorrecto")
      .attr("style", ``)
      .removeClass("pulsado");
      
  } else if ($(`#revDisp${sufijo}_${id_revision_disponible}`).hasClass("incorrecto")) {
    $(`#revDisp${sufijo}_${id_revision_disponible}`)
      .removeClass("incorrecto")
      .addClass("pulsado");
  } else {
    let color = $(`#revDisp${sufijo}_${id_revision_disponible}`).attr("color")
    $(`#revDisp${sufijo}_${id_revision_disponible}`).toggleClass("editado");
    $(`#revDisp${sufijo}_${id_revision_disponible}`).not(".editado").attr("style", `background-color: ${color}`);
    $(`#revDisp${sufijo}_${id_revision_disponible}.editado`).attr("style", ``);
  }
  setTimeout(function () {alargaMenu();}, 300)
}

function asignaRevisiones(id_equipo) {
  var nuevas_revisiones = []
  $(`.revDisp${id_equipo}.editado`).each(function(){
    nuevas_revisiones.push($(this).attr("revision_id"));
  })
  var eliminar_revisiones = []
  $(`.revDisp${id_equipo}.incorrecto`).each(function(){
    let id_rev_disp = $(this).attr("revision_id");
    eliminar_revisiones.push(id_rev_disp);
  })
  let id_auditoria = $(".filtros_auditoria.pulsado").attr("auditoria");
  $.post('/_asigna_revisiones', {
    id_equipo: id_equipo,
    id_auditoria: id_auditoria,
    nuevas_revisiones: nuevas_revisiones,
    eliminar_revisiones: eliminar_revisiones,
    token: token
  }, function(data) {
    $(`#revisiones_disponibles_${id_equipo}`)
      .addClass("invisible");
    $(`#botones_rev_asig_${id_equipo}`)
      .removeClass("invisible")
      .html("")
      .append(data.boton);
    $(`#muestra_rev_ocultas_${id_equipo}`).addClass("invisible");
    $(`#medicionesMotor${id_equipo}`).html(data.input_medicion);
    $(`#verRevisiones_${id_equipo}`).removeClass("invisible");
    setTimeout(() => {
      alargaMenu();
    }, 300);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
}

function cancelaAsignaRevisiones(id_equipo) {
  $(`#revisiones_disponibles_${id_equipo}`)
      .addClass("invisible");
  $(`#botones_rev_asig_${id_equipo}`).removeClass("invisible");
  $(`#verRevisiones_${id_equipo}`).removeClass("invisible");
  $(`#muestra_rev_ocultas_${id_elemento}`).addClass("invisible");
}

function navegaEquipo(id_equipo, id_tratamiento, siguiente) {
  $.getJSON('/_navega_equipo', {
    id_equipo: id_equipo,
    id_tratamiento: id_tratamiento,
    siguiente: siguiente
  }, function(data) {
    if (data.url) {
      window.location.href = data.url
    } else {
      $(`#navega${siguiente}`).addClass("invisible");
    }
  }).fail(function(data) {
      mensaxeErroAJAX(data);
  }); 
}