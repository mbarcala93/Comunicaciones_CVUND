function formularioSubirEquipos() {
    $("#panel_importaciones").toggleClass('invisible');
}

function mostrarFilas() {
    $(".filaOculta").toggleClass("invisible");
    $(".filaOculta").addClass("resaltado");
    setTimeout(function(){
        $(".filaOculta").removeClass("resaltado");
    }, 600);
};

function cargaEquipos(cod_edar) {
    let formData = new FormData();
    formData.append("cod_edar", cod_edar);
    formData.append("token", token);
    formData.append("file", $("#archivo_datos")[0].files[0]);
    $.ajax({
        url: '/_carga_equipos', 
        data: formData,
        processData: false,
        contentType: false,
        type: 'POST',
        success: function(data){
            $(`#equipos_check`).removeClass('invisible');
            setTimeout(function() {
                $(`#equipos_check`).addClass('invisible');},
                2500);
            formularioSubirEquipos();
        },
        error: function(data) {
        mensaxeErroAJAX(data);
        }
    });
};