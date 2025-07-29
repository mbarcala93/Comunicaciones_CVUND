function cargaLaboratorio(esto) {
  let formData;
	const archivo = $(esto).prop("files")[0];
	if(archivo){
    $('#modalAdjunto').show();
    formData = new FormData();
    formData.append("token", token);
    formData.append("archivo",  archivo);
    $.ajax({
      url: '/_compara_muestras', 
      data: formData,
      processData: false,
      contentType: false,
      type: 'POST',
      success: function(data){
        $(`#comparacionMuestras`).html(data.comparacion);
        setTimeout(() => {
          alargaMenu();
        }, 300);
      },
      error: function(data) {
      mensaxeErroAJAX(data);
      }
    });
	}
}

function despliegaFichaMuestraCorrecta(esto) {
    $(esto).siblings("div, span").toggleClass("invisible");
    $(esto).siblings("h4").toggleClass("centrado");
    $(esto).toggleClass("invisible");
    alargaMenu();
}

function despliegaFichaMuestraActualiza(esto) {
    $(esto).siblings("div").children("span.correcto_actualiza").toggleClass("invisible");
    $(esto).siblings(".despliega_actualiza").toggleClass("invisible");
    $(esto).toggleClass("invisible");
    alargaMenu();
}

function despliegaFichaMuestraIncorrecta(esto) {
    $(esto).siblings("div").children("span.correcto_incorrecta").toggleClass("invisible");
    $(".despliega_incorrecta").toggleClass("invisible");
    alargaMenu();
}

function abreIndustria(cod_muestra) {
    $.getJSON('/_visor_industria', {
        cod_muestra: cod_muestra,
        token: token
      }, function(data) {
          window.open(data.url, '_blank').focus();
      }).fail(function(data) {
        mensaxeErroAJAX(data);
      });
}

function actualizaMuestra(cod_muestra) {
    $.post('/_actualiza_muestra', {
        cod_muestra: cod_muestra,
        token: token
      }, function(data) {
        if (data.cambios == 1) {
          $(`#${cod_muestra}`).html('<span class="material-icons check">check_circle</span> Resultados actualizados correctamente')
          setTimeout(() => {
            $(`#${cod_muestra}`).remove();
            alargaMenu();
          }, 2000);
        }
      }).fail(function (data) {
        mensaxeErroAJAX(data);
      });
}