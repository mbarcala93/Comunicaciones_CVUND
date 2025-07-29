function numeroConPuntos(x) {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
};

function sustituyeNumero(esto) {
  var val = parseInt($(esto).text());
  val = numeroConPuntos(val);
  $(esto).text(val);
};

$(document).ready(function() {
  $( ".numero" ).each(sustituyeNumero(this));

  alargaMenu();
  if (!mq.matches) {
    $("#nome_paxina").html($("#nome_paxina").attr("alt"))
    $("#nome_sesion").html($("#nome_sesion").attr("alt"))
    $("#texto_manual").html($("#texto_manual").attr("alt"))
    var a = $("#nome_paxina").width();
    var c = $("#logoutUsuario").width();
    var w = $(window).width();
    if (w < a + c && w >= a ) {
      $("#logoutUsuario").removeClass('derecha').css('text-align', 'right').css('marginRight', '10px')
    }
  }
  setTimeout(function(){alargaMenu();}, 600);
});

const mq = window.matchMedia( "(min-width: 968px)" );

$(window).resize(function() {
  alargaMenu();
});

var bloquea_menu = 0;

function abreMenu() {
  bloquea_menu = 1;
  $(".menu_lateral").addClass("width", 300);
  $("#boton_cerrar").css("display", "inline-block");
  $("#boton_abrir").css("display", "none");
};

function cierraMenu() {
  bloquea_menu = 0;
  $(".menu_lateral").removeClass("width", 300);
  $("#boton_abrir").css("display", "inline-block");
  $("#boton_cerrar").css("display", "none");
};

function alargaMenu() {
  var largo_todo = parseInt($("#todo").css("height").split("px")[0]) + 25
  var largo_ventana = window.innerHeight - 60
  if (largo_todo > largo_ventana) {
    var largo = (largo_todo+15)+"px"
  } else {var largo = (largo_ventana)+"px";}
  $("aside.menu_lateral").css("height",largo)
};

function modoEdicion(sufijo="") {
  $(".editar" + sufijo).toggleClass("invisible");
  setTimeout(function(){alargaMenu();}, 300);
};

function mensaxeErroAJAX(data) {
  if (typeof data.responseJSON != "undefined") {var error = data.responseJSON.error;} else {var error = "Erro no servidor. "};
  alert(error + " Se o problema persiste contacte co administrador.");
};

function fechaBonita(fecha) {
  var fecha_str = String(fecha)
  var fecha_bonita = fecha_str.substr(6,2) + "/" + fecha_str.substr(4,2) + "/" + fecha_str.substr(0,4)
  return fecha_bonita
}

function sustituyePuntoDecimal(esto) {
  var valor = $(esto).val();
  var valor_corregido = valor.replace(",", ".");
  valor_corregido = valor_corregido.replace("..", ".");
  valor_corregido = valor_corregido.replace(/[a-zA-Z ]/g, "");
  $(esto).val(valor_corregido);
}

function letraDNI(input_DNI) {
  var letras = ["T", "R", "W", "A", "G", "M", "Y", "F", "P", "D", "X", "B", "N", "J", "Z", "S", "Q", "V", "H", "L", "C", "K", "E"]
  var resto = input_DNI%23;
  var letra = letras[resto];
  if (letra == undefined) {letra = "-comprobe números-"}
  return letra
};

function compruebaDNI(esto, id) {
  var input_DNI = $(esto).val();
  if (input_DNI.length == 8) {
    $(esto).val(input_DNI + letraDNI(input_DNI))
    if (letraDNI(input_DNI).length > 9) {
      $("#DNI_correcto"+id).addClass("invisible");
      $("#DNI_incorrecto"+id).removeClass("invisible");
    } else {
      $("#DNI_incorrecto"+id).addClass("invisible");
      $("#DNI_correcto"+id).removeClass("invisible");
    }
  } else if (input_DNI.length == 9) {
    var numeros_DNI = input_DNI.substr(0, 8);
    var letra_DNI = input_DNI.substr(8, 1);
    if  (letra_DNI != letraDNI(numeros_DNI)) {
      $("#DNI_correcto"+id).addClass("invisible");
      $("#DNI_incorrecto"+id).removeClass("invisible");
    } else {
      $("#DNI_incorrecto"+id).addClass("invisible");
      $("#DNI_correcto"+id).removeClass("invisible");
    }
  } else if (input_DNI.length < 8) {
    $(".checkeo_DNI"+id).addClass("invisible");
  } else if (input_DNI.length > 9) {
    $("#DNI_correcto"+id).addClass("invisible");
    $("#DNI_incorrecto"+id).removeClass("invisible");
  }
}

function extreaeId(sufijo) {
  // if (sufijo.split("-").length > 2) {
  //   return sufijo.split("-")[1];
  // } else {
    return sufijo.split("-")[0];
  // }
};

function editaInputLista(esto) {
  let sufijo = $(esto).attr('id').split("seleccion")[1];
  let id = extreaeId(sufijo);
  let lista =`#${$(esto).attr('list')}`;
  let id_btn = id.replace('Actual','');

  let valor = $(esto).val();
  if(valor == ''){
    $(esto).removeClass("incorrecto")
      .removeClass("editado");
      $(`#valor${sufijo}vinculado`)
      .removeClass("editado").removeClass("incorrecto")
      .val('');
  } else if($(lista)[0].options.namedItem(valor)) {
    $(esto).removeClass("incorrecto")
      .addClass("editado");
    $(`#valor${sufijo}vinculado`)
      .addClass("editado")
      .val($(lista)[0].options[valor].getAttribute("valor"));
    $(`#etiqueta${sufijo}`).addClass("editado");
    $(`.boton_upload${id_btn}`).removeClass('invisible');
  }else {
    $(esto)
      .addClass("incorrecto")
      .removeClass("editado");
    $(`#valor${sufijo}vinculado`)
      .removeClass("editado")
      .val("");
    $(`#etiqueta${sufijo}`).removeClass("editado");
    $(`.boton_upload${id_btn}`).removeClass('invisible');
  }
}

function eliminarVacios(obj){
  for(elem in obj){
      if(typeof obj[`${elem}`] === 'object'){
          if(Object.keys(obj[`${elem}`]).length == 0){
              delete obj[`${elem}`];
          }else{
              eliminarVacios(obj[`${elem}`]);
          }
      }
  }
}

function finalizaEdicion(epigrafe, contenedor) {
  console.log("." + contenedor + epigrafe + " .valor.editado ");
  $("." + contenedor + epigrafe + " .valor.editado ").each(function () {
    var indice = $(this).attr("id").split("-")[1];
    if ($(".editado.boton" + epigrafe + "-" + indice).length > 0) {
      var nuevo_valor = $(".editado.boton" + epigrafe + "-" + indice)
        .removeClass("editado")
        .addClass("pulsado")
        .text();
    } else {
      var nuevo_valor = $(this).val();
    }
    $("#texto" + epigrafe + "-" + indice).text(nuevo_valor);
    $("#texto_modal" + epigrafe + "-" + indice).text(nuevo_valor);
    $("#etiqueta" + epigrafe + "-" + indice).removeClass("editado");
    
    $("#textoActual" + epigrafe + "-" + indice).text(nuevo_valor);
    $("#etiquetaActual" + epigrafe + "-" + indice).removeClass("editado");
    $("#valorActual" + epigrafe + "-" + indice).removeClass("editado");
    $("#seleccion" + epigrafe + "-" + indice).removeClass("editado");
    
    $(this).removeClass("editado");
    $(".boton_upload" + epigrafe).addClass("invisible");
  });
}

//FILTRO

//Función que añade una PROPIEDAD(valores del campo de la bbdd que se corresponde con la clave del objeto* que lo contiene) a un OBJETO o si este ya la tiene le añade valores al ARRAY que contiene como valor || *Estructura del objeto: objeto{campo_bbdd:{PROPIEDAD:[valor1,valor2...valorn]}}
function añadirDato(objeto, campo, clave, valor) {
  if (campo != "None") {
    if(!objeto.hasOwnProperty(`${campo}`)){
      objeto[`${campo}`]={};
    }else if(!objeto[`${campo}`].hasOwnProperty(`${clave}`)){
      objeto[`${campo}`][`${clave}`] = [valor];
    }else{
      objeto[`${campo}`][`${clave}`].push(valor);
    }
  }
}

//variable para saber en que filtro nos encontramos
let filtro_disponible = 0;

/*
Función que filtra por cualquier campo habilitado para ello con el valor escrito en el input
Parametros:
  - esto: input en el que se escribe el filtro(this)
  - contenedor: elemento HTML que contiene los elementos a filtrar
  - str_elementos: el XXXX de los elementos a mostrar(id: XXXXid_bbdd)
  - objeto: objeto js que contiene los filtros, generado en otro js
            (Estructura objeto={nombre_campo_bbdd:{valor1:[id1,id2...idn]}})
  - sufijo: str que posterior al id del elemento[opcional]
*/
function filtrarRegistros(esto, contenedor, str_elementos, objeto, sufijo='') {
  filtro_disponible = 0;
  let filtro = $(esto).val();
  var texto = RegExp(".*" + filtro + ".*", "i");
  let lista_registros_mostrar = [];

  //Recorremos el objeto con estructura CAMPO_BBDD:Objecto
  for (let [key, value1] of Object.entries(objeto)) {
    //Recorremos el objeto con estructura VALOR:[id1,id2...,idn]
    for (let [key, value] of Object.entries(value1)) {
      //Si VALOR coincide con la expresión regular añadimos a una lista los ids que no figuren ya en ella
      if (key.match(texto) && filtro != "") {
        let lista_ids_registros = value;
        for (let id of lista_ids_registros) {
          if (!lista_registros_mostrar.includes(id)) {
            lista_registros_mostrar.push(id);
          }
        }
      }
    }
  }

  if (filtro != "" && filtro_disponible == 0) {
    //Ocultamos todos los registros
    $("#filtrado").removeClass("invisible");
    $(`#${contenedor}`).children().addClass("invisible");

    //Volvemos a hacer visibles los registros que cumplen el filtro
    for (let id of lista_registros_mostrar) {
      $(`#${str_elementos}${id}${sufijo}`).removeClass("invisible");
    }
  } else {
    eliminarFiltros(contenedor);
  }
}

/*
Función que aplica los filtros habilitados con el valor de cada input a su campo correspondiente
Parametros:
  - objeto: objeto js que contiene los filtros, generado en otro js
            (Estructura objeto={nombre_campo_bbdd:{valor1:[id1,id2...idn]}})
  - contenedor_filtros: elemento HTML que contiene los inputs de filtro
  - contenedor_datos: elemento HTML que contiene los elementos a filtrar
  - str_elementos: el XXXX de los elementos a mostrar(id: XXXXid_bbdd)
  - lista_datos: listado de ids que existen, generado en otro js
  - sufijo: str que posterior al id del elemento[opcional]
*/
function filtrarRegistrosAvanzado(
  objeto,
  contenedor_filtros,
  contenedor_datos,
  str_elementos,
  lista_datos,
  sufijo=''
) {
  filtro_disponible = 1;
  //Se hace un COPIA COMPLETA del listado de ids de usuarios
  let lista_registros_mostrar = JSON.parse(JSON.stringify(lista_datos));

  let ids_filtro = [];
  //Recorremos todos los inputs de filtro que haya en el contenedor pasado como parametro
  for (let filtro of $(`#${contenedor_filtros}`).children()) {
    //Omitimos el filtro simple (nos quedamos solo con los de clase 'filtro_compuesto')
    if (`${filtro.id}` != "filtro_general") {
      //Recuperamos un listados de ids que cumplen el filtro aplicado para el campo correspondiente
      ids_filtro = Array.from(
        filtrarInputsRelacionados(
          `${filtro.id}`,
          objeto[`${filtro.id.replace("filtro_", "")}`],
          lista_datos
        )
      );

      //Recorremos la lista que contiene todos los ids
      for (let id of lista_registros_mostrar) {
        // ""Eliminamos"" los ids que no cumplieran el filtro para no mostrarlos
        if (!ids_filtro.includes(id)) {
          lista_registros_mostrar[lista_registros_mostrar.indexOf(id)] = "NULL";
        }
      }
    }
  }

  if (filtro_disponible == 1) {
    //Ocultamos todos los registros
    $("#filtrado").removeClass("invisible");
    $(`#${contenedor_datos}`).children().addClass("invisible");

    //Volvemos a hacer visibles los registros que cumplen el filtro
    for (let id of lista_registros_mostrar) {
      $(`#${str_elementos}${id}${sufijo}`).removeClass("invisible");
    }
  } else {
    eliminarFiltros(contenedor_datos);
  }
}

/*
Función que devuleve un listado de ids que cumplan el filtro aplicado o todos si este filtro está vacío
Parametros:
  - input: id del input de filtro (filtro_[nombre_campo_bbdd])
  - objeto: objeto js que contiene los filtros, generado en otro js
            (Estructura: objeto:{valor1:[id1,id2...idn]})
  - lista_datos: listado de ids que existen, generado en otro js
*/
function filtrarInputsRelacionados(input, objeto, lista_datos) {
  let filtro = $(`#${input}`).val();
  var texto = RegExp(".*" + filtro + ".*", "i");
  let lista_registros_filtrados = [];

  //Recorremos el objeto con estructura VALOR:[id1,id2...,idn]
  for (let [key, value] of Object.entries(objeto)) {
    if (filtro != "") {
      //Si VALOR coincide con la expresión regular añadimos a una lista los ids que no figuren ya en ella
      if (key.match(texto)) {
        let lista_ids_registros = value;
        for (let id of lista_ids_registros) {
          if (!lista_registros_filtrados.includes(id)) {
            lista_registros_filtrados.push(id);
          }
        }
      }
    } else {
      //Si no hay un filtro aplicado se devuelven todos los ids disponibles
      lista_registros_filtrados = JSON.parse(JSON.stringify(lista_datos));
    }
  }
  return lista_registros_filtrados;
}

/*
Función que elimina los filtros aplicados
Parametros:
  - contenedor_datos: elemento HTML contenedor de lso elementos a filtrar
*/
function eliminarFiltros(contenedor_datos) {
  $("#filtros").children().val("");
  $(`#${contenedor_datos}`).children().removeClass("invisible");
  $("#filtrado").addClass("invisible");
}

//Función que lterna entre el tipo de filtro y vacia todos los inputs de filtros
function cambioFiltro(contenedor_datos) {
  $(".filtro_general").toggleClass("invisible");
  $(".filtro_combinado").toggleClass("invisible");
  filtro_disponible = filtro_disponible ? 0 : 1;
  eliminarFiltros(contenedor_datos);
}

//FIN FILTRO