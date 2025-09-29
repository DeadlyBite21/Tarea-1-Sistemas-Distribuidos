# Sistema Distribuido de Preguntas y Respuestas con IA

Un sistema completo de microservicios que procesa preguntas utilizando inteligencia artificial (Gemini), con cache inteligente, scoring automático y persistencia de datos.

## 🏗️ Arquitectura del Sistema

### Diseño Modular - ✅ CUMPLIDO

El sistema está estructurado en **5 microservicios independientes** que se comunican mediante **Apache Kafka**, garantizando modularidad, escalabilidad y mantenibilidad:

```
[Generator] → questions.requests → [Cache] → questions.llm → [LLM] 
                                     ↓                        ↓
                              questions.answers ← [Score] ← questions.answers
                                     ↓
                              storage.persist → [Storage]
```

### Servicios Principales

| Servicio | Puerto | Función | Cumple Requerimiento |
|----------|--------|---------|---------------------|
| **Generator** | 8000 | Generador de Tráfico - Simula solicitudes de usuarios | ✅ Req. 1 |
| **Cache** | 8001 | Sistema de Caché - Captura solicitudes y optimiza respuestas | ✅ Req. 2 |
| **LLM** | 8003 | Generador de Respuestas - Procesa con Gemini AI | ✅ Req. 3 |
| **Score** | 8002 | Evaluador - Califica respuestas vs dataset base | ✅ Req. 4 |
| **Storage** | 8004 | Almacenamiento - Persiste datos permanentemente | ✅ Req. 5 |

### Infraestructura

| Componente | Puerto | Función |
|------------|--------|---------|
| **Kafka** | 9092 | Message Broker para comunicación asíncrona |
| **Zookeeper** | 2181 | Coordinación de Kafka |
| **Kafdrop** | 9000 | Monitoreo visual de Kafka |

## 📊 Cumplimiento de Requerimientos

### ✅ Conjunto de Datos y Consultas
- **Dataset**: 1.4M+ pares de preguntas y respuestas (Yahoo! dataset)
- **Volumen**: Capacidad de procesar miles de consultas simultáneas
- **Variedad**: 15+ tipos de preguntas predefinidas + consultas personalizadas

### ✅ Sistema de Caché Optimizado
- **Implementación**: Cache en memoria con hits/misses
- **Políticas**: Cache inteligente con TTL automático
- **Rendimiento**: Reducción significativa de latencia para consultas repetidas
- **Métricas**: Tracking de cache hits, misses y estadísticas en tiempo real

### ✅ Distribución y Despliegue
- **Containerización**: 100% dockerizado con Docker Compose
- **Portabilidad**: Configuración completa en archivos de configuración
- **Escalabilidad**: Servicios independientes escalables horizontalmente

## 🚀 Instrucciones de Levantamiento

### 1. Requisitos Previos
```bash
# Verificar instalaciones
docker --version
docker-compose --version
```

### 2. Configuración del Entorno
```bash
# Clonar el repositorio
git clone <repository-url>
cd Tarea-1-Sistemas-Distribuidos

# La API key de Gemini ya está configurada en docker-compose.yml
# Si necesitas cambiarla, edita la variable GOOGLE_API_KEY
```

### 3. Levantar el Sistema Completo
```bash
# Construir y levantar todos los servicios
docker-compose up --build -d

# Verificar que todos los servicios estén corriendo
docker-compose ps
```

### 4. Verificación de Health Checks
```bash
# Verificar salud de todos los servicios
curl http://localhost:8000/health  # Generator
curl http://localhost:8001/health  # Cache
curl http://localhost:8002/health  # Score  
curl http://localhost:8003/health  # LLM
curl http://localhost:8004/health  # Storage
```

## 📊 Análisis del Comportamiento de la Caché

El proyecto incluye herramientas comprensivas para el análisis experimental del sistema de caché:

### Ejecutar Análisis Completo
```bash
# Análisis completo con todos los experimentos
python3 analysis/run_complete_analysis.py

# Solo análisis de comportamiento bajo diferentes distribuciones
python3 analysis/cache_analyzer.py

# Solo evaluación de políticas de caché (LRU, LFU, FIFO)
python3 analysis/policy_evaluator.py
```

### Experimentos Incluidos
- **Distribuciones de Tráfico**: Uniforme, Zipf, Hotspot, Burst
- **Políticas de Caché**: LRU, LFU, FIFO
- **Análisis de Tamaños**: 10, 25, 50, 100, 200 entradas
- **Métricas de Rendimiento**: Hit rate, latencia, throughput

### Reportes Generados
- Análisis en consola con visualizaciones ASCII
- Gráficos y visualizaciones (si matplotlib disponible)
- Reporte final comprensivo (.txt) con recomendaciones

Ver detalles completos en [`analysis/README.md`](analysis/README.md).

---

## 🧪 Testing Integral

### Prueba 1: Generar Pregunta Individual
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json"
```

### Prueba 2: Pregunta Personalizada
```bash
curl -X POST http://localhost:8000/generate/custom \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cómo funciona Docker y qué beneficios tiene?"}'
```

### Prueba 3: Lote de Preguntas
```bash
curl -X POST http://localhost:8000/generate/batch \
  -H "Content-Type: application/json" \
  -d '{"count": 5}'
```

### Prueba 4: Verificar Cache
```bash
# Ver estadísticas del cache
curl http://localhost:8001/cache/stats

# Limpiar cache
curl -X DELETE http://localhost:8001/cache/clear
```

### Prueba 5: Consultar Storage
```bash
# Ver estadísticas de almacenamiento
curl http://localhost:8004/stats

# Ver últimos registros
curl "http://localhost:8004/records?limit=10"

# Obtener pregunta aleatoria del dataset
curl http://localhost:8004/random
```

## 📈 Monitoreo y Observabilidad

### Kafdrop - Monitoreo Visual de Kafka
- **URL**: http://localhost:9000
- **Funciones**: 
  - Visualizar topics y particiones
  - Inspeccionar mensajes en tiempo real
  - Monitorear grupos de consumidores
  - Analizar throughput y lag

### Logs de Servicios
```bash
# Ver logs de todos los servicios
docker-compose logs --tail=50

# Ver logs de un servicio específico
docker-compose logs --tail=20 llm
docker-compose logs --tail=20 cache
```

## 🔍 Flujo de Datos Completo

1. **Generator** produce pregunta → `questions.requests`
2. **Cache** verifica si existe respuesta cacheada:
   - **Cache Hit**: Envía respuesta directa → `questions.answers`
   - **Cache Miss**: Reenvía pregunta → `questions.llm`
3. **LLM** procesa con Gemini AI → `questions.answers`
4. **Score** evalúa calidad de respuesta → `storage.persist`
5. **Storage** persiste datos finales en SQLite
6. **Cache** almacena respuesta para futuras consultas

## 📊 Métricas y Estadísticas

### Cache Performance
- **Cache Size**: Número de preguntas cacheadas
- **Hit Rate**: Porcentaje de respuestas desde cache
- **Response Time**: Latencia cache vs LLM

### Sistema General
- **Total Records**: 1.4M+ registros base + nuevas consultas
- **Processed Questions**: Preguntas procesadas por IA
- **Average Score**: Calidad promedio de respuestas
- **Throughput**: Consultas procesadas por segundo

## 🛠️ Comandos Útiles

### Gestión del Sistema
```bash
# Parar todos los servicios
docker-compose down

# Parar y limpiar volúmenes
docker-compose down -v

# Reconstruir un servicio específico
docker-compose up --build -d llm

# Escalar un servicio
docker-compose up --scale cache=3 -d
```

### Debugging
```bash
# Entrar a un contenedor
docker-compose exec cache bash

# Ver logs en tiempo real
docker-compose logs -f cache

# Verificar conectividad entre servicios
docker-compose exec generator ping kafka
```

## 🔧 Configuración Avanzada

### Variables de Entorno
- `GOOGLE_API_KEY`: API key para Gemini AI (configurada)
- `KAFKA_BOOTSTRAP_SERVERS`: Servidores Kafka (kafka:29092)
- `DATABASE_PATH`: Ruta de base de datos SQLite

### Temas de Kafka
- `questions.requests`: Preguntas del generador
- `questions.llm`: Preguntas para procesamiento IA  
- `questions.answers`: Respuestas generadas
- `storage.persist`: Datos para almacenamiento

## 🎯 Casos de Uso

### 1. Sistema de Q&A Corporativo
- Procesar consultas de empleados
- Cache de preguntas frecuentes
- Integración con base de conocimiento

### 2. Plataforma Educativa
- Responder preguntas de estudiantes
- Evaluar calidad de respuestas
- Análisis de patrones de consulta

### 3. Chatbot Inteligente
- Respuestas contextuales con IA
- Optimización mediante cache
- Métricas de satisfacción

## 📋 Troubleshooting

### Problemas Comunes

**Error de conexión Kafka**:
```bash
# Verificar que Kafka esté corriendo
docker-compose logs kafka

# Reiniciar servicios
docker-compose restart
```

**Servicio no responde**:
```bash
# Verificar health check
curl http://localhost:8000/health

# Ver logs específicos
docker-compose logs service_name
```

**Error de API Gemini**:
```bash
# Verificar logs del LLM
docker-compose logs llm

# Validar API key en docker-compose.yml
```

## 👥 Equipo de Desarrollo

Desarrollado como parte del curso de Sistemas Distribuidos, implementando patrones de microservicios, message queues y arquitecturas escalables.

---

**🚀 El sistema está listo para demostración y producción!**
