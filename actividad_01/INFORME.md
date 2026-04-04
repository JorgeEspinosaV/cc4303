# Informe: Construcción de un Proxy

## Información estudiantes


| Estudiante | Email  |
|------------|-------|
| Esperanza Cares | esperanza.cares@ug.uchile.cl |
| Jorge Espinosa | jorge.espinosa@ug.uchile.cl |

---


## 1. Diseño del Proxy

### 1.1 Diagrama de funcionamiento

**[INSERTAR DIAGRAMA AQUÍ]**

### 1.2 Explicación del diagrama

[Explicación breve del flujo de funcionamiento del proxy]

### 1.3 Sockets necesarios

- Cantidad de sockets: [X]
- Descripción:
  - Socket 1: [Descripción]
  - Socket 2: [Descripción]
  - [Agregar más si es necesario]

---

## 2. Parte 1: Servidor HTTP

### 2.1 Función `parse_HTTP_message`

**Información extraída del mensaje HTTP:**

- [Campo 1]
- [Campo 2]
- [Campo 3]
- [Agregar campos según implementación]

**Implementación:**

```python
# Código de la función parse_HTTP_message
def parse_HTTP_message(http_message):
    # Tu implementación aquí
    pass
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

### 2.2 Función `create_HTTP_message`

**Implementación:**

```python
# Código de la función create_HTTP_message
def create_HTTP_message(parsed_data):
    # Tu implementación aquí
    pass
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

### 2.3 Lectura de archivos JSON

**Implementación:**

```python
# Código para leer archivos JSON
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

---

## 3. Parte 2: Implementación del Proxy

### 3.1 Transferencia de mensajes (sin modificación)

**Implementación:**

```python
# Código para transferir mensajes sin modificar
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

### 3.2 Bloqueo de sitios prohibidos

**Implementación:**

```python
# Código para bloquear sitios prohibidos
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Cómo se verifica si un sitio está bloqueado]
- [Qué respuesta se envía cuando el sitio está bloqueado]

### 3.3 Modificación de headers

**Implementación:**

```python
# Código para modificar headers
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Qué headers se modifican]
- [Por qué se modifican]

### 3.4 Reemplazo de contenido

**Implementación:**

```python
# Código para reemplazar contenido prohibido
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Cómo se identifican las palabras prohibidas]
- [Cómo se realiza el reemplazo]

### 3.5 Manejo de mensajes grandes

**Preguntas:**

1. **¿Cómo sé si llegó el mensaje completo?**
   
   [Respuesta]

2. **¿Qué pasa si los headers no caben en mi buffer?**
   
   [Respuesta]

3. **¿Cómo sé que el HEAD llegó completo?**
   
   [Respuesta]

4. **¿Y el BODY?**
   
   [Respuesta]

**Implementación:**

```python
# Código para manejar mensajes grandes
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

---

## 4. Pruebas realizadas

### 4.1 Pruebas con navegador

#### Test 1: Sitio prohibido

- **URL probada:** http://cc4303.bachmann.cl/secret
- **Resultado esperado:** Error 403
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Test 2: Modificación de headers

- **URL probada:** http://cc4303.bachmann.cl/
- **Resultado esperado:** Contenido modificado según cambios en headers
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Test 3: Reemplazo de palabras

- **URL probada:** http://cc4303.bachmann.cl/replace
- **Resultado esperado:** Palabras prohibidas reemplazadas
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Test 4: Sitios normales

- **URL probada:** http://cc4303.bachmann.cl/
- **Resultado esperado:** Sitio accesible normalmente
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

### 4.2 Pruebas con buffer pequeño

#### Caso 1: Buffer más pequeño que el mensaje, más grande que headers

- **Tamaño del buffer:** [X]
- **Tamaño del mensaje:** [Y]
- **Tamaño de los headers:** [Z]
- **Resultado:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Caso 2: Buffer más pequeño que headers, más grande que start line

- **Tamaño del buffer:** [X]
- **Tamaño de los headers:** [Y]
- **Tamaño de la start line:** [Z]
- **Resultado:** [Describe el resultado]
- **Observaciones:** [Observaciones]

### 4.3 Pruebas con curl

#### Sin proxy

```bash
curl example.com
```

**Resultado:** [Describe el resultado]

#### Con proxy

```bash
curl example.com -x IP_VM:8000
```

**Resultado:** [Describe el resultado]

---

## 5. Dificultades encontradas

[Dificultad 1]

[Dificultad 2]

[Dificultad 3]

---

## 6. Conclusiones

[Conclusión 1]

[Conclusión 2]

[Conclusión 3]

---

## 7. Referencias

- [Referencia 1]
- [Referencia 2]
- [Referencia 3]
