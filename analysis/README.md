# Análisis del Comportamiento de la Caché

Este directorio contiene herramientas comprensivas para el análisis experimental del sistema de caché distribuido, incluyendo evaluación de políticas, patrones de tráfico y métricas de rendimiento.

## 📁 Archivos del Análisis

### `cache_analyzer.py`
Analizador principal que evalúa el comportamiento de la caché bajo diferentes distribuciones de tráfico:
- **Distribución Uniforme**: Todas las preguntas tienen igual probabilidad
- **Distribución Zipf**: Simula patrones reales donde pocas preguntas son muy frecuentes
- **Patrón Hotspot**: Concentración extrema en consultas populares (regla 80/20)
- **Patrón Burst**: Ráfagas intensas de consultas similares

### `policy_evaluator.py`
Evaluador de políticas de caché que implementa y compara:
- **LRU (Least Recently Used)**: Remueve elementos menos recientemente usados
- **LFU (Least Frequently Used)**: Remueve elementos menos frecuentemente usados
- **FIFO (First In First Out)**: Remueve elementos en orden de llegada

### `run_complete_analysis.py`
Script principal que ejecuta todos los análisis y genera reportes comprensivos.

## 🚀 Cómo Ejecutar el Análisis

### Prerequisitos
1. Asegúrate de que todos los servicios estén ejecutándose:
```bash
docker-compose up -d
```

2. Verifica que los servicios respondan:
```bash
curl http://localhost:8000/health  # Generator
curl http://localhost:8001/health  # Cache
curl http://localhost:8003/health  # LLM
curl http://localhost:8002/health  # Score
curl http://localhost:8004/health  # Storage
```

### Ejecutar Análisis Completo
```bash
cd analysis
python3 run_complete_analysis.py
```

Este script:
1. ✅ Instala dependencias automáticamente (numpy, matplotlib, pandas, etc.)
2. 🔍 Verifica que todos los servicios estén ejecutándose
3. 📊 Recolecta métricas del sistema en tiempo real
4. ⚡ Ejecuta pruebas de rendimiento
5. 🔬 Analiza comportamiento bajo diferentes patrones de tráfico **usando preguntas reales** de la base de datos
6. 🏆 Evalúa políticas de caché (LRU, LFU, FIFO) con **datos reales**
7. 📈 **Genera gráficos** con visualizaciones profesionales
8. 📋 Genera reporte final comprensivo

### Ejecutar Análisis Individuales

#### Solo análisis de comportamiento con gráficos:
```bash
python3 cache_analyzer.py
```

#### Solo evaluación de políticas con datos reales:
```bash
python3 policy_evaluator.py
```

## 📊 Tipos de Experimentos

### 1. Análisis de Distribuciones de Tráfico
- **Objetivo**: Entender cómo diferentes patrones de consultas afectan el rendimiento
- **Métricas**: Hit rate, miss rate, tiempo de respuesta promedio
- **Distribuciones probadas**:
  - Uniforme: Baseline para comparación
  - Zipf: Refleja uso real de sistemas
  - Hotspot: Concentración en consultas populares
  - Burst: Picos de tráfico intenso

### 2. Evaluación de Políticas de Caché
- **Objetivo**: Determinar la mejor estrategia de remoción de elementos
- **Políticas comparadas**:
  - **LRU**: Óptima para localidad temporal
  - **LFU**: Ideal para patrones estables
  - **FIFO**: Simple pero menos eficiente
- **Métricas**: Hit rate por política y patrón de tráfico

### 3. Análisis de Tamaños de Caché
- **Objetivo**: Encontrar el balance óptimo memoria vs rendimiento
- **Tamaños evaluados**: 10, 25, 50, 100, 200 entradas
- **Métricas**: Hit rate vs tamaño de caché para cada política

### 4. Pruebas de Rendimiento en Tiempo Real
- **Objetivo**: Validar el rendimiento del sistema completo
- **Métricas**: Latencia end-to-end, throughput, cache hit rate estimado

## 📈 Métricas Recolectadas

### Métricas de Caché
- **Hit Rate**: Porcentaje de consultas servidas desde caché
- **Miss Rate**: Porcentaje de consultas que requieren LLM
- **Tiempo de Respuesta Promedio**: Latencia media de todas las consultas
- **Utilización de Memoria**: Porcentaje del caché ocupado

### Métricas del Sistema
- **Total de Registros**: Consultas almacenadas en base de datos
- **Preguntas Únicas**: Diversidad de consultas procesadas
- **Score Promedio**: Calidad promedio de respuestas generadas
- **Throughput**: Consultas procesadas por segundo

## 🎯 Resultados Esperados

### Patrones de Rendimiento
1. **Distribución Zipf** muestra mayor hit rate que uniforme
2. **Patrón Hotspot** maximiza beneficios del caché
3. **LRU** generalmente supera a FIFO y LFU en workloads variados
4. **Tamaño óptimo** típicamente entre 50-100 entradas

### Recomendaciones Derivadas
- **Política recomendada**: LRU para balance eficiencia/simplicidad
- **Tamaño inicial**: 50-75 entradas
- **TTL sugerido**: 1 hora para consultas generales
- **Monitoreo**: Hit rate >80% objetivo en producción

## � Reportes Generados

El análisis genera varios outputs:

### 1. Reporte de Consola
Análisis en tiempo real con resultados inmediatos y visualizaciones ASCII.

### 2. **🆕 Gráficos Profesionales** (directorio `analysis_graphs/`)
- **`hit_rates_by_distribution.png`**: Gráfico de barras comparativo de hit rates por distribución de tráfico
- **`response_times_distribution.png`**: Histogramas de tiempos de respuesta por patrón de tráfico
- **`request_patterns.png`**: Visualización de patrones de distribución de requests
- **`summary_comparison.png`**: Resumen comparativo general con tres métricas clave

### 3. Reporte Final (archivo .txt)
Documento comprensivo con:
- Resumen ejecutivo
- Métricas del sistema
- Análisis de rendimiento
- Evaluación de políticas
- **Referencias a gráficos generados**
- Recomendaciones de implementación
- Conclusiones y próximos pasos

### 4. **🆕 Datos Reales**
- Todas las pruebas utilizan **preguntas reales** extraídas de la base de datos del sistema
- Más de **1.4 millones de registros** disponibles para análisis
- Distribuciones realistas basadas en patrones de uso actual

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# Ajustar timeouts
export CACHE_TIMEOUT=30
export LLM_TIMEOUT=60

# Configurar tamaños de prueba
export CACHE_SIZES="10,25,50,100"
export TEST_REQUESTS=500
```

### Personalización de Experimentos
Modifica las variables en los scripts para ajustar:
- Número de requests por experimento
- Distribuciones de tráfico custom
- Tamaños de caché específicos
- Métricas adicionales

## 🐛 Troubleshooting

### Servicios no responden
```bash
# Verificar logs
docker-compose logs cache
docker-compose logs llm

# Reiniciar servicios
docker-compose restart
```

### Dependencias faltantes
```bash
# Instalar manualmente
pip install numpy matplotlib pandas aiohttp requests

# O usar requirements.txt
pip install -r requirements.txt
```

### Errores de conexión
- Verificar que los puertos no estén ocupados
- Confirmar que Kafka esté completamente inicializado
- Esperar ~30 segundos después de `docker-compose up`

## 📚 Base Científica

Este análisis proporciona:
- **Validación empírica** de decisiones de diseño
- **Datos cuantitativos** sobre rendimiento del sistema
- **Comparación objetiva** entre políticas de caché
- **Recomendaciones basadas en evidencia** para optimización

Los resultados sustentan las elecciones arquitectónicas y proporcionan métricas para monitoreo en producción.