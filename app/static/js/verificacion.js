function editaInput(valor, indice, esto, id, hacerScroll) {
  $("#valor"+ id +"-"+indice).val(valor).addClass("editado");
  $("#etiqueta"+ id +"-"+indice).addClass("editado");
  $(".boton_upload"+id).removeClass('invisible');
  $(".boton"+ id +"-"+indice).removeClass("pulsado").removeClass("editado");
  $(esto).addClass("editado").parent().addClass('visible');

  setTimeout(function () {alargaMenu();}, 300);
  if (!mq.matches && hacerScroll) {
    $('html, body').animate( { scrollTop : $("#etiqueta-"+(parseInt(indice) + 1)).offset()['top']}, 300 );
  };
};

function anadeInput(indice, esto) {
  pulsarFeedBack(esto)
  $(".boton.aceptar, .boton.finalizar").removeClass("invisible");
  $("#valor-"+indice).addClass("editado").val($("#valor-"+indice).val() + $(esto).html());
}

function editaInputSeparador(valor, indice, esto, id) {
  var valores_actuales =  $("#valor"+ id +"-"+indice).val().split("|");
  $(".boton_upload"+id).removeClass('invisible');
  if (!valores_actuales.includes(valor)) {
    $("#valor"+ id +"-"+indice).val($("#valor"+ id +"-"+indice).val() + "|" + valor).addClass("editado");
    $("#etiqueta"+ id +"-"+indice).addClass("editado");
    // $(".boton"+ id +"-"+indice).removeClass("pulsado").removeClass("editado");
    $(esto).addClass("editado");
  } else {
    $(esto).removeClass("editado");
    var valores_nuevos = arrayRemove(valores_actuales, valor);
    $("#valor"+ id +"-"+indice).val(valores_nuevos.join("|"));
  }
  setTimeout(function () {alargaMenu();}, 300);
}

function pulsarFeedBack(esto) {
  $(esto).addClass("pulsado");
  window.navigator.vibrate(50, 0);
  setTimeout(function() {
    $(esto).removeClass("pulsado");
    window.navigator.vibrate(0);
  }, 100)
}

function nuevaVerificacion(ajuste, sinTabla) {
  var id_tabla = {0: "verificaciones", 1: "ajustes"}
  $.post('/_nueva_verificacion', {
    token: token,
    ajuste: ajuste
  }, function(data) {
    if (!sinTabla){
      var actualiza_tabla = [data.id_verificacion, data.fecha, '-', '-', '-', '-']
      var tabla = document.getElementById("tabla_"+id_tabla[ajuste])
      var fila = tabla.insertRow(1);
      fila.setAttribute("onclick", "window.open('/verificacion-" + data.id_verificacion + "', '_self')");
      fila.setAttribute("id", "fila_" + id_tabla[ajuste][0] + data.id_verificacion);
      for (var i = 0; i < 6; i++) {
        var celda = fila.insertCell();
        celda.innerHTML = actualiza_tabla[i];
      }
    }
    window.open(data.url, '_self');
  }).fail(function (data) {
    if (typeof data.responseJSON != "undefined") {var error = data.responseJSON.error;} else {var error = "Erro no servidor. "};
    alert(error + " Se o problema persiste contacte co administrador.");
  });
}

function ocultaOtrosPatrones(id, indice, esto) {
  $(".boton-"+indice).addClass("invisible");
  $(".patron"+id).addClass("invisible");
  $(esto).removeClass("invisible");
}

function muestraPatrones(patron) {
  $(".boton.aceptar").removeClass("invisible");
  $(".linea.patrones").removeClass("invisible")
  $(".patrones").removeClass("invisible").children("div").addClass("invisible");
  $(".patrones>div."+patron).removeClass("invisible");
  $(".boton-2, .boton-5").removeClass("editado");
  $("#valor-2").val("");
  $("#datos_sondas").removeClass("invisible");
  $(".sonda").addClass("invisible").removeClass("editado");
  $(".sonda"+patron).removeClass("invisible").addClass("editado"); //cuando haya más de una sonda, hay que cambiar esta línea
  $("input#valor-1b").val($(".sonda"+patron).attr("id").split("sonda")[1]).addClass("editado")
  if (patron != 'pH') {
    $(".temperatura").addClass("invisible");
  } else {
    $(".temperatura").removeClass("invisible");
  }
};

var numero_patrones_necesarios = 0;

function muestraContadorPatrones(numero) {
  numero_patrones_necesarios = numero;
  actualizaContadorPatrones();
};

function actualizaContadorPatrones() {
  $(".requisitos_sonda").addClass("invisible")
  var patrones_marcados = $("#valor-2").val().split("|").length - 1;
  $("#patrones_marcados").html(patrones_marcados);
  $("#patrones_necesarios").html(numero_patrones_necesarios);
  if (patrones_marcados < numero_patrones_necesarios) {
    $("#contador_patrones").removeClass("incorrecto correcto").addClass("editado");
    visibilidadRequisitos(0);
  } else if (patrones_marcados == numero_patrones_necesarios) {
    $("#contador_patrones").removeClass("incorrecto editado").addClass("correcto");
    visibilidadRequisitos(1);
  } else {
    $("#contador_patrones").removeClass("correcto editado").addClass("incorrecto");
    visibilidadRequisitos(0);
  }
};

function visibilidadRequisitos(visible) {
  var id_sonda = $(".sonda.editado").attr("id").split("sonda")[1];
  if (visible) {$(".requisitos_sonda"+id_sonda).removeClass("invisible")}
}

function muestraPatronesAjuste() {
  $(".patron_ajuste").toggleClass("invisible2");
  alargaMenu();
};

function actualizaVerificacion(id_verificacion, es_ajuste, finalizar) {
  $(".boton.aceptar, .boton.finalizar").addClass("invisible");
  $.post('/_actualiza_verificacion', {
    id_verificacion: id_verificacion,
    // valores: $("#formulario > :input.editado ").serialize(),
    valores: $("input").serialize(),
    finalizar: finalizar,
    es_ajuste: es_ajuste,
    token: token
  }, function(data) {
    if (finalizar) {
      if (data.valido == 1) {
        $(".grid_botonera3").addClass('invisible');
        $(".editado").removeClass("editado");
        $("#opciones_finalizado").removeClass("invisible");
        $("input").prop('disabled', true);
        $(".boton").not('.opciones').attr('onclick', '');
        $("#ver_informe").attr('onclick', `window.open('`+data.url+`', '_blank').focus();`)
        alargaMenu();
      } else {
        if (es_ajuste) {
          alert("O axuste é NON APTO");
        } else {
          alert("A verificación é NON APTA");
        }
      }

    } else {
      $(".boton.editado").addClass("pulsado");
      $(".editado").removeClass("editado");
    }
  }).fail(function (data) {
    $(".boton.aceptar, .boton.finalizar").removeClass("invisible");
    if (typeof data.responseJSON != "undefined") {var error = data.responseJSON.error;} else {var error = "Erro no servidor. "};
    alert(error + " Se o problema persiste contacte co administrador.");
  });
};

function borrarVerificacion(id_verificacion, es_ajuste){
  if (es_ajuste == 1 ) { var tipo = "a" } else { var tipo = "v"}
  $("#fila_" + tipo + id_verificacion).addClass("resaltado");
  asegurar = confirm("Seguro que desexa borrar esta verificación da base de datos?");
  if (asegurar) {
    $.post('/_eliminar_verificacion', {
      id_verificacion: id_verificacion,
      es_ajuste: es_ajuste,
      token: token
    }, function(data) {
      $("#fila_" + tipo + id_verificacion).hide();
    }).fail(function (data) {
      if (typeof data.responseJSON != "undefined") {var error = data.responseJSON.error;} else {var error = "Erro no servidor. "};
      alert(error + " Se o problema persiste contacte co administrador.");
      $(".confirmar"+id).removeClass('invisible');
    });
  };
  $("#fila_" + tipo + id_verificacion).removeClass("resaltado");
};

function arrayRemove(arr, value) {
    return arr.filter(function(ele){
        return ele != value;
    });
};

function cargaMasFilas(ajuste) {
  var verif_ajuste = ['verificacion', 'ajuste'];
  var i = 0;
  $(".antigua."+verif_ajuste[ajuste]).each( function() {
    if (i < 5) {
      $(this).removeClass('antigua');
      i++;
    };
  });
  if ($(".antigua."+verif_ajuste[ajuste]).length == 0) {
    $("#carga_mas_"+verif_ajuste[ajuste]).addClass('invisible');
  }
  alargaMenu();
}

function retirarPatron(id_patron) {
  asegurar = confirm("Seguro que desexa retirar este patrón? (só un administrador pode reverter os cambios)");
  if (asegurar) {
    $.post('/_retirar_patron', {
      id_patron: id_patron,
      token: token
    }, function(data) {
      $(".patron" + id_patron).remove();
    }).fail(function (data) {
      if (typeof data.responseJSON != "undefined") {var error = data.responseJSON.error;} else {var error = "Erro no servidor. "};
      alert(error + " Se o problema persiste contacte co administrador.");
      $(".confirmar"+id).removeClass('invisible');
    });
  };
}