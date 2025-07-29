function editarInput(esto, id_elemento, edita_hermanos) {
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

function nuevoUsuario() {
  $.post('/_crea_usuario', {
    token: token
  }, function(data) {
    $('#lista_usuarios').prepend(data.html);
    modoEdicion(data.id_usuario);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
  });
};

function ConfirmaActualizaUsuario(id) {
  $(".confirmar"+id).hide();
  $.post('/_actualiza_usuario', {
    id_usuario: id,
    valores: $("#formulario"+ id +" :input.editado ").serialize(),
    token: token
  }, function(data) {
    $(".check_upload"+id).show();
    $(".boton_upload"+id).hide();
    finalizaEdicion(id, 'usuario')
    setTimeout(function () {
      $(`.check_upload${id}`).hide();
      modoEdicion(id);
    }, 2000);
  }).fail(function(data) {
    mensaxeErroAJAX(data);
    $(".boton_upload"+id).show();
  });
};

function eliminaUsuario(id) {
  $(`#formulario${id}`).addClass('incorrecto');
  $(`#formulario${id} input`).addClass('incorrecto');
  setTimeout(function () {
    if(confirm("¿Seguro que desea eliminar este usuario?")){
      $.post('/_borra_usuario', {
        id_usuario: id,
        token: token
      }, function(data) {
        $(`#formulario${id}`).remove();
      }).fail(function(data) {
        mensaxeErroAJAX(data);
      });
    }else{
      $(`#formulario${id}`).removeClass('incorrecto');
      $(`#formulario${id} input`).removeClass('incorrecto');
    }
  }, 100);
};