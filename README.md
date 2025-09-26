# Tarea-1-Sistemas-Distribuidos
Repositorio completo de tarea 1 de sistemas distribuidos

## Instrucciones para levantar y probar el sistema completo

### 1. Requisitos previos
- Docker y Docker Compose instalados
- Archivo `.env` configurado con las variables necesarias (ver ejemplo en la tarea)

### 2. Construir y levantar todos los servicios

```bash
docker compose up -d --build
```

Esto levantará:
- PostgreSQL (db)
- Zookeeper y Kafka
- api-gateway (FastAPI)
- responder-llm (servicio LLM)
- scorer (servicio de métricas)
- cache (servicio de caché)
- traffic-gen (generador de tráfico)

Puedes ver el estado de los servicios con:
```bash
docker compose ps
```

### 3. Ver logs de los servicios
Para ver los logs de un servicio específico:
```bash
docker compose logs --tail=40 <servicio>
# Ejemplo:
docker compose logs --tail=40 traffic-gen
docker compose logs --tail=40 cache
docker compose logs --tail=40 responder-llm
docker compose logs --tail=40 scorer
docker compose logs --tail=40 api-gateway
```

### 4. Probar el flujo end-to-end
- El generador de tráfico (`traffic-gen`) enviará preguntas automáticamente al topic `questions` de Kafka.
- El servicio `cache` recibirá las preguntas, responderá si están en caché o las delegará al pipeline.
- `responder-llm` generará respuestas usando el LLM configurado.
- `scorer` calculará la métrica de calidad.
- `api-gateway` expone endpoints HTTP para interactuar con el sistema.

Puedes probar el API Gateway accediendo a:
```
http://localhost:8000/docs
```
o usando curl/postman para enviar preguntas manualmente:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "¿Cuál es la capital de Francia?"}'
```

### 5. Limpiar el entorno
Para detener y eliminar todos los contenedores, redes y volúmenes:
```bash
docker compose down -v
```

### 6. Notas y troubleshooting
- Si algún servicio no arranca, revisa los logs con `docker compose logs <servicio>`.
- Asegúrate de que el broker Kafka esté accesible como `kafka:9092` desde todos los servicios.
- Si cambiaste el código fuente, vuelve a construir con `docker compose up -d --build`.

---
Para dudas o problemas, revisa los logs y la configuración de variables de entorno.
