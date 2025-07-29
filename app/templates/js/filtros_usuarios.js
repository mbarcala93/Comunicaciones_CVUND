objetoFiltroUsuarios={}
listaIdsUsuarios = []

//Se recorre la lista de campos por los que se puede filtrar (especificados en el .py)
{% for campo in lista_campos %}
   //Se añade la propiedad al objeto
   objetoFiltroUsuarios[`{{campo}}`]={'':[]};
   //para cada registro procedente de la bbdd se comprueba si el objeto ya contiene su info y si no la tiene se añade
   {% for registro in datos_filtro  if registro[campo] != None %} 
      añadirDato(objetoFiltroUsuarios,`{{campo}}`,`{{registro[campo]}}`,{{registro.id}});
   {% endfor %}
{% endfor %}

//Lista de ids
{% for registro in usuarios %}
   listaIdsUsuarios.push({{registro.id}})
{% endfor %}