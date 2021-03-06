# -*- coding: utf-8 -*-

from __future__ import division
from nltk.corpus import wordnet as wn #Importamos el lector del corpus de wordnet
import random
import operator

#########################################################################
## La función inicio crea la vista inicial que tendrá el usuario si no tiene
## ninguna lista pendiente para etiquetar, crea dos variables en apoyo a esto
## Vista relacionada: particular/inicio.html
#########################################################################
"""
Nombre de la función: inicio
Descripción: Crea dos variables, una para mostrar el nombre del usuario y la otra para listar los terminos
Versión: 1.0
Autor: Antonio Nuñez
Retorno: locals() - Las variables locales del programa, se usan en la vista
Vista relacionada: default/inicio.html
"""
@auth.requires_login()
def inicio():
    if (len(db((db.temporal.usuario_id == auth.user.id) & (db.temporal.modo == '1')).select()) == 0):
        usuario_nombre = auth.user.first_name
        termino = db().select(db.termino.id, db.termino.ter)
        if(request.vars.en == "1"):
            response.flash = 'Lista de definiciones terminada'
    else:
        redirect(URL('relacion?rd=1'))
    return locals()

#########################################################################
## La función importar lee si se subió un archivo, si es así lo importa a la
## base de datos.
#########################################################################
"""
Nombre de la función: importar
Descripción: Lee si hay un archivo, si es así lo importa a la base de datos
Versión: 2.1
Autor: Antonio Nuñez
Retorno: dict() - Un diccionario
Vista relacionada: default/importar.html
"""
@auth.requires_login()
def importar():
    if request.vars.csvfile != None:
        db.termino.insert(ter=request.vars.nombre)
        idTermino = db(db.termino.ter == request.vars.nombre).select(db.termino.id)
        table = db[request.vars.table]
        file = request.vars.csvfile.file
        table.import_from_csv_file(file)
        db(db.definicion.termino_id==1).update(termino_id=idTermino[0]['id'])
        users = db().select(db.auth_user.id)
        db.grupo.insert(grup='No informativo', termino_id=idTermino[0]['id'], tipo="Sistema", modo="1")
        db.grupo.insert(grup='No informativo', termino_id=idTermino[0]['id'], tipo="Sistema", modo="2")
        redirect(URL('inicio'))
    else:
        response.flash = 'Selecciona un archivo'
    return dict()

#########################################################################
## La función relacion crea la interfaz necesaria para que el etiquetador
## pueda relacionar definiciones con grupos. Primero crea la lista si no
## existe, posteriormente crea otras listas utiles para mostrar al etiquetador
#########################################################################
"""
Nombre de la función: relacion
Descripción: Crea la interfaz para la relacion
Versión: 2.8
Autor: Antonio Nuñez
Retorno: locals() - Las variables locales del programa, se usan en la vista
Vista relacionada: default/relacion.html
"""
@auth.requires_login()
def relacion():
    muestra = list()
    if(len(db((db.temporal.usuario_id == auth.user.id) & (db.temporal.modo == '1')).select()) == 0):
        muestra = getMuestra(db(db.definicion.termino_id==request.vars.termino).select())
        response.flash = 'Se ha creado una lista aleatoria'
    else:
        muestra = db((db.temporal.usuario_id == auth.user.id) & (db.temporal.modo == '1')).select()
        if(request.vars.rd == "1"):
            response.flash = 'Continua desde la última sesión'
    definicion = db(db.definicion.id==muestra[0]['definicion_id']).select()[0]
    termino = db(db.termino.id==definicion['termino_id']).select()[0]
    historial = getHistorialKeywords(db((db.relacion.definicion_id==definicion['id']) & (db.relacion.modo == "1")).select())
    grupos = db((db.grupo.termino_id == termino['id']) & (db.grupo.modo == '1')).select()
    if(request.vars.error == '0'):
        response.flash = 'Favor de llenar los campos'
    elif request.vars.error == '1':
        response.flash = 'Las palabras clave no se encuentran en la definición'
    total_usuarios = len(db(db.auth_user.id > 0).select())
    porcentaje = getPorcentajes(db((db.relacion.modo == "1")).select())
    return locals()

#########################################################################
## La función getMuestra crea una lista aleatoria y devuelve la consulta de
## la misma
#########################################################################
"""
Nombre de la función: getMuestra
Descripción: Crea la lista aleatoria
Versión: 1.1
Autor: Antonio Nuñez
Parametros: lista_definiciones - Las definiciones del término seleccionado
Retorno: La consulta de la muestra aleatoria que se acaba de crear
"""    
def getMuestra(lista_definiciones):
    i = 0
    muestra = list()
    max = 10
    if(len(lista_definiciones) < 10):
        max = len(lista_definiciones)
    while (i < max):
        definicion = int(random.uniform(0, len(lista_definiciones)))
        if noEnLista(lista_definiciones[definicion]['id'], muestra):
            muestra.append(lista_definiciones[definicion])
            i = i + 1
    registraLista(muestra)
    return db((db.temporal.usuario_id == auth.user.id) & (db.temporal.modo == '1')).select()

#########################################################################
## La función noEnLista coprueba que una definición no se repita en la lista
## aleatoria
#########################################################################
"""
Nombre de la función: noEnLista
Descripción: Valida que las definiciones no se repitan
Versión: 1.1
Autor: Antonio Nuñez
Parametros: idDefinicion - La definición que se quiere validar | muestra - La lista de definiciones
Retorno: flag - Si se repite
"""   
def noEnLista(idDefinicion, muestra):
    flag = True
    for definicion in muestra:
        if definicion['id'] == idDefinicion:
            flag = False
    return flag

#########################################################################
## La función registraLista crea el registro temporal en la base de datos
## de la lista aleatoria que se creo
#########################################################################
"""
Nombre de la función: registraLista
Descripción: Registra la lista aleatoria en la base de datos
Versión: 1.0
Autor: Antonio Nuñez
Parametros: muestra - La lista de definiciones
"""   
def registraLista(muestra):
    for definicion in muestra:
        db.temporal.insert(usuario_id=auth.user.id, definicion_id=definicion['id'], modo="1")

#########################################################################
## La función getHistorialKeywords busca las palabras que se han utilizado
## para un grupo y las cuenta, regresa un diccionario con las palabras clave
## y la cantidad de veces que se repitieron, esto se ordena de mayor a menor
#########################################################################
"""
Nombre de la función: getHistorialKeywords
Descripción: Regresa un diccionario con la cantidad de veces que una palabra clave se repitio
Versión: 2.0
Autor: Antonio Nuñez
Parametros: lista - La lista de registros
Retorno: ordena - Diccionario ordenado de las palabras clave y su cantidad de usos
"""   
def getHistorialKeywords(lista):
    frase_clave = []
    for registro in lista:
        aux = registro['keywords'].split(',')
        for frase in aux:
            if frase[0] == ' ':
                frase = frase[1:]
            frase_clave.append(frase)
    conteo_frase = {}
    for frase in frase_clave:
        if frase in conteo_frase:
            conteo_frase[frase] += 1
        else:
            conteo_frase[frase] = 1
    ordenado = sorted(conteo_frase.items(), key=operator.itemgetter(1), reverse=True)
    return ordenado
    
#########################################################################
## La función getPorcentajes suma la cantidad de veces que un grupo ha sido
## utilizado por un usuario y lo regresa.
#########################################################################
"""
Nombre de la función: getPorcentajes
Descripción: Regresa un diccionario con la cantidad de veces que un grupo ha sido utilizado
Versión: 2.0
Autor: Antonio Nuñez
Parametros: grupos - La lista de registros
Retorno: porcentaje - Diccionario con el numero de usuarios que han usado un grupo
"""   
def getPorcentajes(grupos):
    porcentaje = dict()
    for grupo in grupos:
        if grupo['grupo_id'] in porcentaje and grupo['usuario'] not in porcentaje:
            porcentaje[grupo['grupo_id']] += 1
        else:
            porcentaje[grupo['grupo_id']] = 1
            porcentaje["u" + str(grupo['usuario'])] = 1
    return porcentaje

#########################################################################
## La función vistaWordNet crea la cadena de grupos que son sugerencia de wordnet
#########################################################################
"""
Nombre de la función: vistaWordNet
Descripción: Crea la cadena de grupos sugerencia de wordnet
Versión: 1.0
Autor: Antonio Nuñez
Retorno: locals() - Las variables locales del programa, se usan en la vista
Vista relacionada: particular/vistaWordNet
"""   
def vistaWordNet():
    wordnet = crear_cadena(request.vars.ter, True)
    return locals()

#########################################################################
## La función crear_cadena lee el término y una bandera para consultar wordnet
## y agregar a la cadena los grupos que este devuelve. Tiene opción de recursividad
## hasta un nivel más
#########################################################################
"""
Nombre de la función: crear_cadena
Descripción: Regresa los grupos sugeridos en forma de cadena con formato html
Versión: 1.1
Autor: Antonio Nuñez
Parametros: termino - Lo que buscaremos en wordnet | flag - si buscará un nivel más | cadenas - el contenido que ya existe cuando es recursiva
Retorno: cadenas - los grupos en formato html
"""
def crear_cadena(termino, flag, cadenas=list()):
    lista = wordnet_termino(termino)
    if(len(db((db.grupo.grup == str(termino)) & (db.grupo.modo == "1")).select()) == 0):
        cadenas.append('<input type=\'checkbox\' name=\'grupo\' value=\''+ str(termino) + '\' />@' + str(termino)) #Cada término
        for synset in lista:
            if not busca_existencia(str(synset.definition()), cadenas): #Si el término no existe en la cadena
                lemmas = [str(lemma.name()) for lemma in synset.lemmas()]
                cadenas.append('<br><strong>Lemmas</strong>: ' + str(lemmas) + ', <br><strong>Definition:</strong> (' + synset.definition() + '),<br> <strong>Examples: </strong> ' + str(synset.examples()).replace("u'", "'").replace("[]", "No available"))
        cadenas.append('--------------------------------------------------')
    if flag: #Avanza un nivel más de búsqueda
        for synset in lista:
            lemmas = [str(lemma.name()) for lemma in synset.lemmas()]
            for aux in lemmas: #Por cada lemma
                if busca_existencia(str(aux), cadenas, '@'):
                    print 'Ya existe'
                else:
                    cadenas = crear_cadena(aux, False, cadenas)
    return cadenas

#########################################################################
## La función wordnet_termino devuelve los synsets de un termino
#########################################################################
"""
Nombre de la función: wordnet_termino
Descripción: Regresa los synsets de un termino
Versión: 1.0
Autor: Antonio Nuñez
Parametros: termino - Lo que buscaremos en wordnet
Retorno: Los synsets
"""      
def wordnet_termino(termino):
    return list(wn.synsets(str(termino)))

#########################################################################
## La función busca_existencia busca si algún synset ya está en la cadena
#########################################################################
"""
Nombre de la función: busca_existencia
Descripción: Busca si el synset ya existe
Versión: 1.0
Autor: Antonio Nuñez
Parametros: cadena - la cadena a buscar | cadenas - Donde buscaremos la cadena | identificador - algún adorno que hayamos agregado
Retorno: flag - Si existe en la cadena
"""    
def busca_existencia(cadena, cadenas, identificador=''):
    flag = False
    if identificador != '':
        cadena = str(identificador) + str(cadena)
    for aux in cadenas:
        if cadena.lower() in aux.lower():
            flag = True
    return flag

#########################################################################
## La función crearGrupo se encarga de crear el grupo y de generar una string con
## los grupos en la base de dados con el fin de hacer validaciones
#########################################################################
"""
Nombre de la función: crearGrupo
Descripción: Crea lo grupos personalizados
Versión: 1.6
Autor: Antonio Nuñez
Retorno: locals() - Las variables locales del programa, se usan en la vista
Vista relacionada: particular/crearGrupo
"""   
@auth.requires_login()
def crearGrupo():
    user = auth.user.id
    termino = request.vars.termino
    grupos = db((db.grupo.termino_id == termino) & (db.grupo.modo == "1")).select()
    cadena_grupos = ""
    for grupo in grupos:
        cadena_grupos += grupo['grup'] + " "
    if request.vars.nombre == '0':
        response.flash = 'Ingresa un grupo'
    elif request.vars.nombre != '':
        db.grupo.insert(grup = request.vars.nombre, termino_id = termino, tipo='Custom', modo='1')
    return locals()
    
#########################################################################
## La función DBGroup se encarga de crear los grupos sugeridos
#########################################################################
"""
Nombre de la función: DBGroup
Descripción: Crea lo grupos sugeridos
Versión: 1.0
Autor: Antonio Nuñez
Retorno: locals() - Las variables locales del programa, se usan en la vista
Vista relacionada: particular/vistaWordNet
"""
def DBGroup():
    if(request.vars.grupo != None):
        if  isinstance(request.vars.grupo, list):
            for grupo in request.vars.grupo:
                db.grupo.insert(grup = grupo, termino_id = request.vars.termino, tipo='wordnet', modo="1")
        else:
            db.grupo.insert(grup = request.vars.grupo, termino_id = request.vars.termino, tipo='wordnet', modo="1")
    validaOtro = False
    if request.vars.otro == '-1':
        validaOtro = True
    else:
        redirect(URL("crearGrupo?termino=" + request.vars.otro + "&nombre=0"))
    return locals()

#########################################################################
## La función getHistorialGrupos se encarga de crear el historial de definiciones
## usadas para un grupo o conjunto de grupos, lo mandamos a llamar con ajax
#########################################################################
"""
Nombre de la función: getHistorialGrupos
Descripción: Crea el historial de definiciones por grupo
Versión: 1.0
Autor: Antonio Nuñez
Retorno: respuestaHtml - la respuesta que ajax pondra en la vista
Vista relacionada: particular/relacion
"""
def getHistorialGrupos():
    respuestaHtml = ""
    user = request.vars.c
    if request.vars.grupos != None:
        if  isinstance(request.vars.grupos, list):
            for grupo in request.vars.grupos:
                historial = db((db.relacion.grupo_id == grupo) & (db.relacion.usuario == user) & (db.relacion.modo == "1")).select()
                grupoNombre = db((db.grupo.id == grupo) & (db.grupo.modo == "1")).select()[0]['grup']
                respuestaHtml += "<p><strong>Grupo:</strong> " + grupoNombre + "<br>"
                contador = 10
                aux = len(historial) - 1
                if (len(historial) < 10):
                    contador = len(historial)
                while(contador > 0):
                    respuestaHtml += "<strong>Definción: </strong>" + db(db.definicion.id == historial[aux]['definicion_id']).select()[0]['defi'] + "<br>"
                    contador -= 1
                    aux -= 1
                respuestaHtml += "</p>"
        else:
            historial = db((db.relacion.grupo_id == request.vars.grupos) & (db.relacion.usuario == user) & (db.relacion.modo == "1")).select()
            grupoNombre = db((db.grupo.id == request.vars.grupos) & (db.grupo.modo == "1")).select()[0]['grup']
            respuestaHtml += "<p><strong>Grupo:</strong> " + grupoNombre + "<br>"
            contador = 10
            aux = len(historial) - 1
            if (len(historial) < 10):
                contador = len(historial)
            while(contador > 0):
                respuestaHtml += "<strong>Definción: </strong>" + db(db.definicion.id == historial[aux]['definicion_id']).select()[0]['defi'] + "<br>"
                contador -= 1
                aux -= 1
            respuestaHtml += "</p>"
    else:
        respuestaHtml = "Selecciona un grupo"
    return respuestaHtml

#########################################################################
## La función unir toma los datos mandados desde relacion y los introduce
## en la base de datos
#########################################################################
"""
Nombre de la función: unir
Descripción: Crea la relacion en la base de datos
Versión: 1.0
Autor: Antonio Nuñez
Retorno: locals() - Las variables locales del programa, se usan en la vista
Vista relacionada: particular/relacion
"""
@auth.requires_login()
def unir():
    if(request.vars.keyword == '' or request.vars.grupo == None): #Validación de campos vacios
        redirect(URL('relacion?error=0'))
    else:
        if  isinstance(request.vars.grupo, list):
            request.vars.grado = [x for x in request.vars.grado if x != '']
            i = 0
            while i < len(request.vars.grupo):
                db.relacion.insert(keywords=request.vars.keyword, grado=request.vars.grado[i], grupo_id=request.vars.grupo[i], definicion_id=request.vars.definicion, usuario=auth.user.id, modo="1")
                i = i + 1
        else:
            db.relacion.insert(keywords=request.vars.keyword, grado='100', grupo_id=request.vars.grupo, definicion_id=request.vars.definicion, usuario=auth.user.id, modo="1")
        db((db.temporal.usuario_id==auth.user.id) & (db.temporal.definicion_id == request.vars.definicion) & (db.temporal.modo == "1")).delete()
        if(len(db((db.temporal.usuario_id==auth.user.id) & (db.temporal.modo == "1")).select()) == 0):
            redirect(URL('inicio?en=1'))
        else:
            redirect(URL('relacion'))
    return locals()
