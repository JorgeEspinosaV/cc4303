Actividad 03: Sockets orientados a conexión con Stop & Wait

1. Introducción

En esta actividad implementé una clase SocketTCP que permite simular una comunicación orientada a conexión utilizando sockets UDP. Para lograrlo, construí sobre UDP mecanismos propios de una conexión confiable: establecimiento de conexión mediante 3-way handshake, envío confiable mediante Stop & Wait, manejo de ACKs, timeouts, retransmisiones, detección de duplicados y cierre de conexión.

La implementación se organizó en tres archivos principales:

* SocketTCP.py: contiene la clase SocketTCP y toda la lógica del protocolo.
* cliente.py: lee un archivo desde entrada estándar y lo envía usando SocketTCP.
* servidor.py: recibe el archivo usando SocketTCP y lo escribe por salida estándar.

La ejecución final del cliente se realiza de la forma solicitada:

python3 cliente.py localhost 8000 < archivo.txt

⸻

2. Diseño general de la solución

La solución utiliza sockets UDP como mecanismo de transporte base. Sobre ellos implementé una capa propia que simula algunas funciones de TCP:

1. Establecimiento de conexión mediante 3-way handshake.
2. Segmentos con encabezado propio.
3. Números de secuencia.
4. Confirmaciones mediante ACK.
5. Timeout fijo y retransmisión.
6. Manejo de duplicados.
7. Recepción parcial mediante recv(buff_size).
8. Cierre de conexión mediante FIN y ACK.
9. Manejo de pérdidas artificiales.

El socket UDP interno se crea dentro de la clase SocketTCP, por lo que el usuario de la clase no interactúa directamente con UDP.

⸻

3. Formato de segmentos

Para los segmentos definí un encabezado textual simple, separado por |||, siguiendo la estructura sugerida en el enunciado:

SYN|||ACK|||FIN|||SEQ|||DATOS

Los campos utilizados son:

* SYN: indica inicio de conexión.
* ACK: indica confirmación.
* FIN: indica cierre de conexión.
* SEQ: número de secuencia.
* DATOS: contenido del segmento.

Ejemplo de segmento SYN:

1|||0|||0|||21|||

Ejemplo de segmento SYN-ACK:

1|||1|||0|||72|||

Ejemplo de segmento de datos:

0|||0|||0|||80|||Hola, este es un

Ejemplo de ACK:

0|||1|||0|||96|||

En la clase SocketTCP implementé dos funciones estáticas:

create_segment(syn, ack, fin, seq, data)
parse_segment(segment)

La función create_segment() construye un segmento a partir de sus campos, mientras que parse_segment() recibe un segmento en bytes y retorna una estructura tipo diccionario con los campos separados.

⸻

4. Constructor de la clase SocketTCP

La clase SocketTCP se inicializa sin parámetros, como pide el enunciado:

mi_socket = SocketTCP()

En el constructor se inicializan los recursos necesarios para la comunicación:

* socket UDP interno;
* dirección local;
* dirección de destino;
* número de secuencia inicial aleatorio;
* número de secuencia esperado;
* datos pendientes para recv(buff_size);
* segmentos pendientes para resolver casos borde del handshake.

El número de secuencia inicial se elige aleatoriamente entre 0 y 100.

⸻

5. 3-way handshake

El establecimiento de conexión se implementa mediante las funciones:

bind(address)
connect(address)
accept()

5.1. Función bind(address)

La función bind(address) asocia el socket UDP interno a una dirección local. Es utilizada por el servidor para escuchar conexiones entrantes.

Ejemplo:

server_socketTCP.bind(("127.0.0.1", 8000))

5.2. Función connect(address)

La función connect(address) implementa el lado cliente del handshake. El cliente envía un segmento SYN, espera un SYN-ACK y luego responde con un ACK.

5.3. Función accept()

La función accept() implementa el lado servidor. El servidor espera un SYN, crea un nuevo objeto SocketTCP asociado a un puerto distinto y responde desde ese nuevo socket con un SYN-ACK. Luego espera el ACK final del cliente.

Esto permite que el socket principal siga representando el socket de escucha, mientras que el nuevo socket representa la conexión establecida.

5.4. Diagrama del 3-way handshake

Cliente                                      Servidor
connect(address)                            accept()
     |                                          |
     | -------- SYN=1, seq=x -----------------> |
     |                                          |
     | <------- SYN=1, ACK=1, seq=y ----------- |
     |                                          |
     | -------- ACK=1, seq=x+1 ---------------> |
     |                                          |
Conexión establecida                   Conexión establecida

⸻

6. Stop & Wait

El envío confiable de datos se implementó con Stop & Wait mediante las funciones:

send(message)
recv(buff_size)

6.1. Función send(message)

La función send(message) primero envía el largo total del mensaje como un segmento independiente:

message_length = len(message)

Luego divide el mensaje en trozos de máximo 16 bytes y envía cada trozo dentro de un segmento con encabezado.

Por cada segmento enviado, el emisor espera un ACK. Si el ACK no llega dentro del timeout definido, retransmite el mismo segmento.

La lógica general es:

enviar segmento
esperar ACK
si llega ACK correcto:
    avanzar al siguiente segmento
si ocurre timeout:
    retransmitir el mismo segmento

6.2. Función recv(buff_size)

La función recv(buff_size) recibe primero el largo del mensaje. Luego comienza a recibir segmentos hasta retornar como máximo buff_size bytes.

El parámetro buff_size afecta solamente la cantidad de datos que retorna recv(), no el tamaño del buffer UDP interno. El buffer UDP interno se mantiene fijo.

Si el mensaje completo es más grande que buff_size, la función puede ser llamada varias veces para recibir el resto del mensaje.

Para resolver este caso implementé dos variables internas:

self.pending_data
self.remaining_message_length

* pending_data: guarda bytes que ya fueron recibidos, pero que no pudieron ser retornados porque excedían el buff_size.
* remaining_message_length: guarda cuántos bytes faltan por entregar del mensaje actual.

Esto permite que no se pierdan datos cuando recv(buff_size) retorna solo una parte del mensaje.

⸻

7. Manejo de duplicados

Cuando el receptor recibe un segmento, compara su número de secuencia con el valor esperado:

* Si seq == expected_seq, el segmento es el esperado, se agrega al mensaje y se responde con ACK.
* Si seq < expected_seq, el segmento es duplicado. En ese caso no se vuelve a agregar al mensaje y solo se reenvía el último ACK.
* Si seq > expected_seq, el segmento está fuera de orden y se reenvía el último ACK válido.

Esto evita duplicar datos cuando se pierde un ACK y el emisor retransmite el mismo segmento.

⸻

8. Manejo de pérdidas

Como el desarrollo se realizó en macOS, no utilicé netem. En su lugar implementé pérdida manual mediante una constante global:

LOSS_PROBABILITY = 0.2

La pérdida se simula en la función interna _sendto(). Si se genera una pérdida artificial, el segmento no se envía. Como todos los envíos pasan por _sendto(), las pérdidas pueden ocurrir en ambos sentidos: cliente a servidor y servidor a cliente.

También agregué un modo debug mediante:

DEBUG_LOSS = True

Durante las pruebas, el debug permitió observar mensajes como:

[LOSS] Paquete perdido artificialmente...
[SEND] Timeout. Retransmitiendo segmento...
[RECV] Segmento duplicado. Reenviando ACK.

Esto permitió verificar que el protocolo efectivamente detectaba pérdidas, retransmitía segmentos y manejaba duplicados.

⸻

9. Caso borde: pérdida del último ACK del handshake

Durante el manejo de pérdidas aparece un caso borde importante: puede perderse el último ACK del handshake.

En ese caso, el cliente cree que la conexión ya está establecida y comienza a enviar datos, pero el servidor sigue esperando el ACK final.

Diagrama del caso borde

Cliente                                      Servidor
connect(address)                            accept()
     |                                          |
     | -------- SYN=1, seq=x -----------------> |
     |                                          |
     | <------- SYN=1, ACK=1, seq=y ----------- |
     |                                          |
     | -------- ACK=1, seq=x+1 ----X            |
     |                                          |
Cliente cree conexión establecida       Servidor sigue esperando ACK
     |                                          |
     | -------- DATA, seq=x+1 ----------------> |
     |                                          |
Servidor recibe DATA con el SEQ esperado.
Concluye que el ACK final se perdió,
acepta la conexión y guarda ese segmento
para que recv() lo procese después.

Solución implementada

Para resolver este caso, en accept() agregué una condición especial. Si el servidor está esperando el ACK final, pero recibe un segmento de datos con el número de secuencia esperado, asume que el ACK final se perdió.

En ese caso:

1. acepta la conexión;
2. guarda el segmento recibido en pending_segments;
3. retorna el nuevo socket de conexión;
4. luego recv() procesa ese segmento guardado.

Esto evita perder el primer segmento de datos enviado por el cliente.

⸻

10. Cierre de conexión

El cierre de conexión se implementó mediante:

close()
recv_close()

La función close() representa el lado que inicia el cierre, y recv_close() representa el lado que recibe la solicitud de cierre.

Diagrama del cierre

Host A                                      Host B
close()                                    recv_close()
   |                                           |
   | ------------ FIN -----------------------> |
   |                                           |
   | <----------- ACK ------------------------ |
   |                                           |
   | <----------- FIN ------------------------ |
   |                                           |
   | ------------ ACK -----------------------> |
   |                                           |
socket cerrado                         socket cerrado

Cierre con pérdidas

Para tolerar pérdidas, implementé las siguientes reglas:

* Si close() no recibe los mensajes esperados después de un timeout, reenvía el FIN.
* close() espera hasta 3 timeouts.
* Si después de 3 timeouts no recibe respuesta, asume que la contraparte cerró.
* Si recibe correctamente ACK y FIN, envía el último ACK tres veces.
* Entre cada envío del ACK final espera un tiempo equivalente al timeout.

En recv_close():

* espera el FIN del otro host;
* responde ACK;
* envía su propio FIN;
* espera el ACK final hasta 3 timeouts;
* si no llega, asume que la contraparte cerró.

⸻

11. Pruebas realizadas

11.1. Cliente y servidor UDP provisorios

Primero implementé un cliente y servidor UDP simples. El cliente leía un archivo, lo dividía en trozos de máximo 16 bytes y lo enviaba al servidor.

Sin pérdida artificial, el servidor recibió el mensaje completo.

Luego se simuló pérdida manual y se observó que el mensaje llegaba incompleto, demostrando que UDP no garantiza confiabilidad por sí solo.

⸻

11.2. Prueba de creación y parseo de segmentos

Probé create_segment() y parse_segment() con un segmento de ejemplo:

b'1|||0|||0|||25|||Mensaje de prueba'

El resultado parseado fue:

{
    'SYN': 1,
    'ACK': 0,
    'FIN': 0,
    'SEQ': 25,
    'DATA': b'Mensaje de prueba'
}

Esto confirmó que el encabezado se estaba construyendo y leyendo correctamente.

⸻

11.3. Prueba de handshake sin pérdidas

Probé el 3-way handshake ejecutando:

Servidor:

server_socketTCP = SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()

Cliente:

client_socketTCP = SocketTCP()
client_socketTCP.connect(address)

Durante la prueba se observó que:

* el cliente envió SYN;
* el servidor respondió SYN-ACK desde un nuevo socket;
* el cliente respondió ACK;
* el servidor aceptó la conexión.

También se verificó que la dirección del nuevo socket era distinta a la del socket principal del servidor.

⸻

11.4. Prueba de send() y recv() sin pérdidas

Se ejecutaron los tests sugeridos en el enunciado:

Test 1: mensaje de largo 16
Test 2: mensaje de largo 19
Test 3: mensaje de largo 19 recibido con recv(14) en dos llamadas

Resultados obtenidos:

Test 1: Passed
Test 2: Passed
Test 3: Passed

El Test 3 permitió verificar que recv(buff_size) funciona correctamente cuando buff_size < message_length.

⸻

11.5. Prueba de Stop & Wait con pérdidas

Se configuró:

LOSS_PROBABILITY = 0.2

Durante la prueba se observaron pérdidas de:

* SYN;
* SYN-ACK;
* último ACK del handshake;
* segmentos de datos;
* ACKs.

El protocolo retransmitió segmentos cuando ocurrió timeout y el receptor manejó duplicados reenviando el último ACK válido.

El mensaje largo fue recibido íntegramente:

Test con pérdidas: Passed

⸻

11.6. Prueba de cierre con pérdidas

Se probó el cierre de conexión con pérdida manual activa.

Durante la prueba se observó que:

* close() envió FIN;
* recibió ACK y FIN;
* reenvió el ACK final tres veces;
* recv_close() esperó el ACK final;
* si hubo timeout, siguió esperando hasta el límite definido;
* ambos lados cerraron correctamente.

Resultado:

Cliente: conexión cerrada
Servidor: conexión cerrada

⸻

11.7. Prueba final con archivo

Finalmente probé el cliente y servidor finales usando el formato solicitado:

python3 servidor.py 8000 > recibido.txt
python3 cliente.py localhost 8000 < archivo.txt

Luego comparé el archivo enviado y el recibido:

diff archivo.txt recibido.txt

El comando diff no mostró diferencias.

También verifiqué el tamaño de ambos archivos:

wc -c archivo.txt recibido.txt

Resultado:

154 archivo.txt
154 recibido.txt

Esto confirma que el archivo fue transmitido íntegramente.

⸻

12. Decisiones de diseño

Uso de encabezado textual

Decidí usar un encabezado textual separado por ||| porque facilita la depuración y permite visualizar claramente los valores de SYN, ACK, FIN y SEQ.

Uso del campo SEQ como confirmación en ACK

En los segmentos ACK utilicé el campo SEQ como número de confirmación. Es decir, el ACK indica el siguiente byte esperado por el receptor.

Envío del largo del mensaje

Cada llamada a send(message) envía primero el largo del mensaje como un segmento independiente. Esto permite que recv(buff_size) sepa cuántos bytes debe recibir y evita que el receptor espere indefinidamente.

Manejo de recv(buff_size)

Para permitir que recv(buff_size) retorne como máximo buff_size bytes sin perder datos, implementé pending_data y remaining_message_length.

Manejo del último ACK perdido en handshake

Para resolver el caso donde se pierde el último ACK del handshake, implementé pending_segments. Si el servidor recibe datos mientras espera el ACK final, guarda ese segmento y luego lo entrega a recv().

Simulación de pérdidas

Como no usé netem, implementé pérdida manual con LOSS_PROBABILITY. Esta solución permite controlar la tasa de pérdida desde el código y probar pérdidas en ambos sentidos de la comunicación.

⸻

13. Situaciones borde consideradas

Durante la implementación consideré las siguientes situaciones:

* pérdida de SYN;
* pérdida de SYN-ACK;
* pérdida del último ACK del handshake;
* pérdida de segmentos de datos;
* pérdida de ACKs;
* recepción de segmentos duplicados;
* recv(buff_size) menor que el largo del mensaje;
* pérdida de mensajes durante el cierre;
* pérdida del ACK final del cierre.

En cada caso se implementaron retransmisiones, reenvío de ACKs o almacenamiento temporal de datos para evitar pérdida de información.

⸻

14. Conclusión

La clase SocketTCP implementa una comunicación orientada a conexión usando UDP como transporte base. La solución incorpora handshake, Stop & Wait, números de secuencia, ACKs, timeouts, retransmisión, manejo de duplicados, recepción parcial y cierre de conexión.

Las pruebas realizadas muestran que el protocolo permite transmitir información íntegramente, incluso cuando se inducen pérdidas artificiales. Además, el cliente final puede ejecutarse en el formato solicitado:

python3 cliente.py localhost 8000 < archivo.txt

y el servidor puede recibir el archivo y escribirlo correctamente por salida estándar.
