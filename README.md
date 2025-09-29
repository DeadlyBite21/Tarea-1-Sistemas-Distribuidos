# Tarea-1-Sistemas-Distribuidos
Repositorio completo de tarea 1 de sistemas distribuidos

## Instrucciones para levantar y probar el sistema

### 1. Requisitos previos
- Docker y Docker Compose instalados

### 2. Configuración de variables de entorno

El servicio `score` requiere la variable de entorno `GEMINI_API_KEY` (ya está configurada en el `docker-compose.yml`). Si quieres cambiar el modelo, puedes agregar la variable `GEMINI_MODEL` (por defecto usa `gemini-2.0-flash`).

### 3. Construir y levantar todos los servicios

```bash
docker compose up --build
```

Esto levantará los siguientes servicios:
- generator (generador de tráfico)
- cache (servicio de caché)
- score (servicio de generación de respuestas LLM)
- storage (servicio de almacenamiento)

### 4. Probar el sistema

Puedes probar el sistema de las siguientes formas:

#### Probar el servicio de score directamente

```bash
curl -X POST http://localhost:5003/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cómo funciona la inteligencia artificial?"}'
```

Deberías recibir una respuesta generada por el modelo Gemini.

#### Ver el modelo configurado

```bash
curl http://localhost:5003/model
```

#### Probar el flujo completo

Puedes interactuar con los otros servicios (generator, cache, storage) según la lógica de tu aplicación. Por ejemplo, puedes enviar preguntas al generator o cache si tienes endpoints expuestos.

### 5. Ver logs de los servicios

```bash
docker compose logs --tail=40 <servicio>
# Ejemplo:
docker compose logs --tail=40 score
```

### 6. Detener y limpiar el entorno

```bash
docker compose down -v
```

---

Si tienes dudas o errores, revisa los logs de cada servicio y asegúrate de que la API key de Gemini sea válida.
