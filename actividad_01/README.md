Actividad: construir un proxy
En esta actividad vamos a construir un proxy para filtrar contenido web. La actividad se divide en 2 partes para mantener el orden, sin embargo la parte 1 es más corta que la parte 2 y solo se entrega la versión final de la parte 2.

A continuación veremos algunos de los conceptos que necesitaremos saber para realizar esta actividad. Para esta actividad además necesitará del material provisto en el video: HTTP  y el material de la sección Mensajes HTTP.

Puntaje: 4.5 pts código + 1.5 pts informe

El desglose de puntaje por funcionalidad del código es el siguiente (Si su código pasa las pruebas debería cumplir con los puntos mencionados aquí):

(+0.5) El cliente recibe una respuesta
(+1.0) El proxy bloquea correctamente los sitios prohibidos
(+1.2) Se reemplazan correctamente las palabras según el json utilizado
(+0.5) Se modifican correctamente los headers.
(+1.3) Se manejan correctamente mensajes más grandes que el buffer del socket.
¿Qué es un proxy?
Un proxy es cualquier dispositivo intermedio entre un cliente y servidor, comúnmente utilizado para realizar las consultas a nombre del cliente y luego reenviárselas. Un proxy necesita ser capaz de recibir consultas como lo haría un servidor y luego (re)enviarlas como lo haría un cliente. Un ejemplo de uso de proxy es acceder desde sus casas a artículos científicos usando el proxy del DCC. Artículos a los que ustedes no tienen acceso, pero la Universidad sí. Esto funciona pues al utilizar el proxy del DCC para solicitar un artículo a una biblioteca a la cual la Universidad tiene acceso, el proxy del DCC reenvía su petición desde la red del DCC la cual es parte de la red de la Universidad. Luego desde la biblioteca ven que la Universidad está solicitando un artículo y como esta tiene acceso a la biblioteca, le entregan el artículo sin problemas. Finalmente el artículo es recibido por el proxy del DCC y quien reenvía el artículo a ustedes en sus casas.

Antes de comenzar
Maquina virtual: A la hora de ejecutar nuestro proxy, lo echaremos a correr en una máquina virtual y anclaremos el mismo a la IP de dicha máquina.
Tipo de socket usado por HTTP: El protocolo HTTP utiliza sockets orientados a conexión, por lo que los clientes deben invocar a la función connect para conectarse al servidor, mientras que los servidores deben llamar a accept para aceptar peticiones de clientes.
Comando curl: El comando curl funciona como cliente HTTP para texto permitiéndonos crear de forma fácil y rápida clientes para probar servidores HTTP.  Para esta actividad utilizaremos curl con la opción -I , la que sirve para traer solo los headers a través de una petición de tipo HEAD. También les puede servir la opción -L la cual entrega información siguiendo las redirecciones. Otra opción corresponde a utilizar -i la cual entrega el detalle del HEAD y el BODY con el cuál responde el servidor. El detalle de las opciones posibles lo pueden encontrar usando la línea de comando curl -h. La opción -x [dirección]:[puerto] le permite indicarle a curl que use el proxy ubicado en la dirección y puerto especificados.
Mensajes HTTP: Los mensajes HTTP se caracterizan por tener headers HTTP bastante amigables con el humano. La sección de headers se puede ver como un gran string que contiene la información necesaria para establecer la comunicación mediante HTTP. La primera línea de esta sección indica el protocolo HTTP en uso, el estado de la comunicación y el tipo de request si es que hay alguna (GET, POST), mientras que el resto de las líneas contiene un header cada una. Cada header tiene el formato "Nombre-del-header: contenido del header". Cada una de las líneas dentro de la sección de headers está separada por un salto de línea del tipo "\r\n", y con un doble salto de línea "\r\n\r\n" se marca el fin de la sección de headers y el inicio de la sección de datos.

Para comunicarse con un browser es necesario que los headers indiquen el 'Content-Type' que indica el tipo de datos que lleva el paquete y el 'Content-Length' que indica el largo de los datos que lleva el paquete. Para enviar texto plano puede usar 'Content-Type: text/html'. Para más información puede visitar https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers.
Puerto default HTTP: En conexiones HTTP, salvo que se indique lo contrario, nos vamos a conectar al puerto 80. De esta forma si un mensaje HTTP no especifica el puerto al que se desea conectar y solo indica el nombre del host, se asume que la conexión debe hacerse a la dirección (host, 80). Si en cambio el mensaje especifica tanto el nombre del host como un puerto con el formato 'host:puerto', se asume que la conexión debe hacerse a la dirección (host, puerto).  El puerto 80 se encuentra dentro de los llamados puertos reservados, los cuales se reservan para uso del sistema operativo o para protocolos conocidos como lo es el protocolo HTTP.
Archivos JSON: Los archivos JSON nos permiten almacenar e intercambiar datos usando un formato legible para el humano. La sintaxis de archivos JSON es relativamente similar a la sintaxis de diccionarios en Python. Estos archivos nos permiten almacenar datos en archivos .json y consultarlos a través de nuestro código. En la sección Material e indicaciones para la actividad (más abajo) puede encontrar un ejemplo de uso. 
Actividad
Parte 1 (No es necesario entregarla, es para comenzar en orden)
Partiremos creando y probando un servidor HTTP. Para construir su servidor puede usar como guía* el ejemplo de comunicación orientada a conexión  tcp_socket_server.py  visto en el modulo 1. Recuerde que para que un servidor sea en efecto un servidor HTTP, debe ser capaz de recibir mensajes HTTP, es decir, debe ser capaz de leer e interpretar HEAD + BODY HTTP.

(*): 'Cómo guía' significa que no es llegar y copiar, la idea es que lean y ejecuten el código de ejemplo, luego extraigan lo que les sea útil y descarten lo que no >:c

En esta primera parte realizaremos algunas pruebas para que se familiarice con el funcionamiento de mensajes HTTP. El código creado en esta parte será modificado y reutilizado en la parte 2.

Veamos los pasos:

Para esta a actividad ejecutaremos los códigos a desarrollar en una máquina virtual y asociaremos los respectivos sockets a la IP de dicha máquina a la cuál nos referiremos como IP_VM por IP Virtual Machine.  Respecto a la máquina virtual, puede ejecutar una máquina virtual tal como lo hizo en el curso anterior de Sistemas Operativos. Como primer paso cree su máquina virtual en caso de no tener una del curso anterior, y revise cuál es la IP de la misma, esta será su IP_VM.
Como primer paso a nivel de código encárguese de que su servidor pueda leer, interpretar y crear mensajes HTTP. Para ello cree la función parse_HTTP_message(http_message) que tome un mensaje HTTP y lo transfiera a una estructura de datos que le permita acceder fácilmente a la información del mensaje. Además cree la función create_HTTP_message que sea capaz de tomar la estructura de datos entregada por parse_HTTP y la convierta en un mensaje HTTP. Para saber qué información debería extraer, revise el material sobre mensajes HTTP, evalúe qué debería extraer su función parse y anótelo en su informe.
Test: Utilice su navegador para obtener un 'request' y use dicho request para probar que las funciones que acaba de programar funcionen como corresponde. Para obtener la request cree un socket servidor que escuche en (IP_VM, 8000) en su máquina virtual, e intente acceder a  http://IP_VM:8000 desde un navegador en su máquina local. Al hacer esto su socket recibirá la 'request' HTTP que está haciendo el navegador a su socket servidor. Para ver la request imprima lo que recibió su socket en pantalla usando print antes de invocar a decode. Utilice esta request para probar el correcto funcionamiento de sus funciones parse_HTTP_message y create_HTTP_message . (Note que en este punto su código no le responde nada al navegador, por lo que su navegador no va a mostrar nada).
Ahora, abra una consola (terminal) y utilice curl para obtener una 'response' o respuesta a una petición GET. Para ello ejecute el siguiente comando en consola (recuerde remover el '%'):
 % curl -i cc4303.bachmann.cl
Al ejecutar este comando, verá la respuesta a la request o petición GET hecha por curl. Note que en esta respuesta usted ve los saltos de línea sin mayor detalle, sin embargo cada salto de línea tiene la forma "\r\n". Utilice esta response o respuesta HTTP como guía para crear su propia response a la petición que estaba recibiendo en el paso (1). Para ello deberá crear un pequeño HTML que pueda mostrarse en su navegador y sus headers deberán ser consistentes con el largo y tipo de contenido de su mensaje HTTP. Utilice la respuesta que acaba de crear para responder la petición que le hizo el navegador en el paso (1).
Test: Haga que su código (corriendo en su máquina virtual) le responda al navegador con la respuesta que acaba de crear y verifique que el navegador logra mostrarla. Luego utilice curl desde su máquina local como se muestra a continuación y verifique que curl también recibe una respuesta satisfactoria.
 % curl -i IP_VM:8000
Modifique su servidor para que al momento de responder le agregue el header X-ElQuePregunta con su nombre como valor. (Esto nos va a servir en la parte 2, no cambie el nombre del header).
Test: pruebe que se agrega de forma correcta el header utilizando curl como se muestra a continuación.
 % curl IP_VM:[puerto_server_http] -i
Modifique su servidor para que pueda leer archivos JSON o archivos de configuración. Haga que el nombre y ubicación del archivo JSON pueda ser recibido como argumento al ejecutar su código. Estos archivos serán necesarios más adelante en la parte 2 para darle ciertas instrucciones a nuestro servidor.  Por mientras úselo para dejar en una variable su nombre, así el servidor quedará con un usuario parametrizable. Puede encontrar un ejemplo de uso de JSON en la sección Material e indicaciones para la actividad (más abajo).
Test: Pruebe que su servidor puede tomar su nombre desde su archivo JSON y lo puede utilizar para añadir el header X-ElQuePregunta.
Parte 2 (sí se entrega)
Ahora que ya tenemos listo nuestro servidor HTTP vamos a modificarlo para convertirlo en un proxy. Nuestro proxy tendrá dos funcionalidades principales:

Bloquear tráfico hacia páginas no permitidas (como un control parental)
Reemplazar contenido inadecuado (reemplazo el  string A  con el  string B)
Antes de comenzar a modificar su código haga dibuje un diagrama del flujo de funcionamiento de un proxy e identifique cuáles y cuántos sockets necesitará utilizar. Adjunte su diagrama en su informe junto a una breve explicación.

Una vez haya hecho su diagrama de proxy, proceda a modificar su código siguiendo los siguientes pasos:

Modifique su servidor para que sea un proxy que esté entre un cliente y un servidor, pero que no modifique el mensaje, esto es: recibe un requerimiento, se lo envía al servidor de forma íntegra, recibe la respuesta y se la envía al cliente sin modificarla. Para crear esta modificación a su código siga el diagrama que acaba de realizar. Note que para lograr esto necesitará poder comunicarse con el cliente y el servidor al mismo tiempo.
Test: Use curl para ver que su proxy logra transferir mensajes de forma exitosa. Para ello verifique que pedir la página example.com con curl sin usar proxy, entrega lo mismo que al usar curl con su código como proxy. Para probar esto ejecute los siguientes comandos:
 %%%%% petición SIN proxy:
 % curl example.com
 %%%%% petición CON proxy:
 % curl example.com -x IP_VM:8000
Modifique su proxy para que al recibir la URI (protocolo + dirección; por ejemplo http://www.example.com)  del servidor, chequee si la dirección está bloqueada. De ser así devuelva el código de error 403 junto a un HTML que muestre una imagen almacenada localmente por usted, para ello puede utilizar la etiqueta <img src=[file_path]> (se sugiere usar gatos). Para saber qué direcciones están bloqueadas utilice el archivo JSON de la sección Material e indicaciones para la actividad que sale más abajo.
Test: Utilizando su proxy con curl intente acceder a una página prohibida y verifique que este retorna error 403 junto al código HTML que usted implementó. Verifique que al ingresar a páginas que no están prohibidas, como cc4303.bachmann.cl, su código sigue funcionando como antes.
En caso de que la dirección del servidor final no sea una dirección prohibida, agregue a la request que va desde el proxy al servidor el header X-ElQuePregunta con su nombre.
Test: Utilizando curl, pruebe acceder al dominio cc4303.bachmann.cl a través de su proxy y verifique que el mensaje de bienvenida mostrado por la página cambia al pasar por su proxy, versus el mensaje mostrado al usar curl sin pasar por su proxy.
Configure su proxy para que reemplace contenido inadecuado. Para esto busque las palabras prohibidas (marcado como forbidden_words en el JSON mostrado en la sección Material e indicaciones para la actividad más abajo) y reemplace dichas palabras (reemplazo el string A con el string B).
Test: Utilizando curl pruebe acceder a cc4303.bachmann.cl/replace a través de su proxy y verifique que las palabras son reemplazadas y que no hay errores en el contenido.
Finalmente modifique su código para que pueda recibir mensajes utilizando sockets cuyo buffer de recepción sea más pequeño que el tamaño del mensaje a recibir. Para ello puede usar/modificar las funciones provistas en los códigos de ejemplo de la semana 1 (sockets). Para implementar esta parte deberá responder las siguientes preguntas ¿Cómo sé si llegó el mensaje completo? ¿Qué pasa si los headers no caben en mi buffer? ¿Cómo sé que el HEAD llegó completo?¿Y el BODY?. Al documentar su código en el informe, responda explícitamente estas preguntas.
Test: Pruebe que su proxy sigue funcionando cuando el tamaño del buffer de recepción es pequeño (ejemplo: recv_buffer = 50).
Pruebas
How to: La sección de pruebas contiene las pruebas que debe superar su código para considerarse correcto. Esta sección además puede contener experimentos que se le pedirá incluir en su informe/README. No olvide que en su informe además de las observaciones solicitadas en la parte de pruebas ud. debe documentar el funcionamiento de su código y sus decisiones de diseño.

Para probar el proxy recién implementado utilizaremos http://IP_VM:8000 como proxy del sistema de forma de que podamos probarlo utilizando un browser. Antes de configurar el proxy verifique que puede ver correctamente los siguientes sitios a través de su browser:

Usted puede ver el sitio http://cc4303.bachmann.cl/
Usted puede ver el sitio http://cc4303.bachmann.cl/replace
Usted puede ver el sitio http://cc4303.bachmann.cl/secret
Una vez haya confirmado que dichos sitios se muestran sin problemas configure su proxy para utilizarlo a través de su browser y proceda a hacer las pruebas. Para configurar el proxy puede seguir estas instrucciones https://es.ccm.net/faq/25993-como-configurar-un-proxy-en-tu-navegador-web .

Pruebe que su código es capaz de hacer lo siguiente al probarlo con el browser y anote sus observaciones en su informe:

Verifique que ya NO puede ver el sitio http://cc4303.bachmann.cl/secret, si no que recibe un error 403.
Verifique que al acceder al sitio http://cc4303.bachmann.cl/ el contenido de este se modifica según los cambios introducidos al área de headers.
Verifique que puede ver los sitios http://cc4303.bachmann.cl/ y http://cc4303.bachmann.cl/replace, pero las palabras prohibidas han sido modificadas. Verifique que el texto mostrado sea el mismo solo que con las palabras prohibidas censuradas.
Pruebe que su proxy funciona en los siguientes casos: (1) El tamaño del buffer de recepción del socket es más pequeño que el tamaño del mensaje, pero más grande que el tamaño del área de headers, y (2) el tamaño del buffer es más pequeño que el tamaño del área de headers, pero más grande que la start line. Anote el resultado de sus pruebas en el informe.
Material e indicaciones para la actividad
Ejemplo JSON: En el siguiente ejemplo vemos cómo calcular la cantidad total de artículos de oficina en un inventario. Para ello tenemos el archivo inventario.json:
 
 {
   "oficina": [
     {
       "nombre": "lapiz_pasta",
       "cantidad_total": 10,
       "colores": ["rojo","negro","azul"],
       "rojo": 2,
       "azul": 5,
       "negro": 3

     },
     {
       "nombre": "lapiz_mina",
       "cantidad_total": 5,
       "colores": ["grafito"],
       "grafito": 5
     }
   ]
 }
Usando el archivo inventario.json podemos calcular la cantidad total de artículos de oficina usando el siguiente código en Python ¿Cómo modificarían este código para que entregue sólo la cantidad de lápices de colores?
 
 import json
 
 # abrimos el archivo del inventario
 with open("inventario.json") as file:
     # usamos json para manejar los datos
     data = json.load(file)
     # calculamos la cantidad total de artículos de oficina en el inventario
     total_articulos_de_oficina = 0
     for articulo in data['oficina']:
         cantidad_articulo = articulo['cantidad_total']
         total_articulos_de_oficina += cantidad_articulo
 
 # imprimimos un mensaje indicando la cantidad total de artículos de oficina
 print("Hay un total de " + str(total_articulos_de_oficina) + " de artículos de oficina")
Probar proxy con curl: Puede realizar las pruebas iniciales de su proxy usando el comando curl con el flag -x para indicar el uso de proxy de la siguiente manera:
 % curl [domain] -x localhost:8000
JSON páginas bloqueadas y palabras prohibidas: Las páginas bloqueadas y las palabras prohibidas puede encontrarlas en el siguiente JSON: 
{ 
  "user": "--su email--",
  "blocked": ["http://www.dcc.uchile.cl/", "http://cc4303.bachmann.cl/secret"],
  "forbidden_words": [{"proxy": "[REDACTED]"}, {"DCC": "[FORBIDDEN]"}, {"biblioteca": "[???]"}]
}
Note que su proxy debe funcionar con páginas HTTP, pero es perfectamente posible que no funcione para HTTPS (http secure). Las páginas http://www.example.cl y http://cc4303.bachmann.cl se comunican a través de http y puede usarlas para probar su proxy.

