# 🧪 Experimentos de Cache - 10,000 Preguntas Reales

## � Estructura de Carpetas

```
experiments/
├── coordinator.py              # 🎮 Coordinador principal  
├── compare_results.py          # 📊 Comparador de resultados
├── individual_experiments/     # 📂 Experimentos individuales
│   ├── experiment_lru.py      #   🔵 Experimento LRU
│   ├── experiment_lfu.py      #   🟢 Experimento LFU  
│   └── experiment_fifo.py     #   🟡 Experimento FIFO
├── results/                   # 📂 Resultados generados
│   ├── lru_results.json      #   📄 Resultados LRU
│   ├── lfu_results.json      #   📄 Resultados LFU
│   ├── fifo_results.json     #   📄 Resultados FIFO
│   └── comparison_report.json #   📄 Reporte comparativo
└── README_EXPERIMENTOS.md    # 📖 Esta documentación
```

## 🚀 Uso Rápido con Coordinador

### **🔍 Verificar Sistema**
```bash
cd experiments
python3 coordinator.py check
```

### **👥 Ver Asignación del Equipo**
```bash
python3 coordinator.py team
```

### **🧪 Ejecutar Experimentos**
```bash
# Compañero 1 - LRU
python3 coordinator.py lru

# Compañero 2 - LFU  
python3 coordinator.py lfu

# Compañero 3 - FIFO
python3 coordinator.py fifo
```

### **📊 Verificar Progreso**
```bash
python3 coordinator.py results
```

### **📈 Comparar Resultados Final**
```bash
python3 coordinator.py compare
```

---

## 👥 Asignación de Experimentos

### 🔵 **Compañero 1: Experimento LRU**
```bash
cd experiments
python3 coordinator.py lru
# O directamente:
cd individual_experiments  
python3 experiment_lru.py
```
- **Archivo de salida**: `results/lru_results.json`
- **Política**: Least Recently Used
- **Duración estimada**: ~16.7 horas

### 🟢 **Compañero 2: Experimento LFU** 
```bash
cd experiments
python3 coordinator.py lfu
# O directamente:
cd individual_experiments
python3 experiment_lfu.py
```
- **Archivo de salida**: `results/lfu_results.json`
- **Política**: Least Frequently Used
- **Duración estimada**: ~16.7 horas

### 🟡 **Compañero 3: Experimento FIFO**
```bash
cd experiments
python3 coordinator.py fifo
# O directamente:
cd individual_experiments
python3 experiment_fifo.py
```
- **Archivo de salida**: `results/fifo_results.json`
- **Política**: First In, First Out
- **Duración estimada**: ~16.7 horas

---

## 🛠️ Preparación del Sistema

Antes de ejecutar cualquier experimento, **cada compañero debe**:

### 1. **Levantar el Sistema Completo**
```bash
# Desde el directorio raíz del proyecto
docker-compose down
docker-compose up -d

# Verificar que todos los servicios estén funcionando
docker-compose ps
```

### 2. **Verificar Servicios**
```bash
# Generator (Puerto 8000)
curl http://localhost:8000/health

# Cache (Puerto 8001) 
curl http://localhost:8001/health

# LLM (Puerto 8003)
curl http://localhost:8003/health

# Storage (Puerto 8004)
curl http://localhost:8004/health

# Score (Puerto 8002)
curl http://localhost:8002/health
```

### 3. **Verificar Dataset**
El storage debe tener **1.4M+ preguntas** disponibles.

---

## 🚀 Ejecución de Experimentos

### ⚠️ **Importante Antes de Ejecutar:**
1. ✅ **Sistema completamente levantado**
2. ✅ **Todos los servicios healthy**
3. ✅ **Clave de API Gemini válida**
4. ✅ **Conexión estable a internet**

### 📊 **Durante la Ejecución:**
- El script muestra progreso cada 100 preguntas
- Se guardan estadísticas en tiempo real
- ETA (tiempo estimado) se actualiza constantemente
- **NO interrumpir** el proceso una vez iniciado

### 📈 **Métricas que se Miden:**
- **Hit Rate**: % de preguntas respondidas desde cache
- **Cache Hits**: Número absoluto de hits
- **Cache Misses**: Preguntas que requirieron LLM
- **Evictions**: Elementos expulsados del cache
- **Response Time**: Tiempo promedio de respuesta
- **Memory Usage**: Uso de memoria del cache

---

## 📁 Unión de Resultados

Una vez que **todos los experimentos** hayan terminado:

### 1. **Reunir Archivos JSON**
Los archivos se guardan automáticamente en la carpeta `results/`:
- `results/lru_results.json` (Compañero 1)
- `results/lfu_results.json` (Compañero 2)  
- `results/fifo_results.json` (Compañero 3)

### 2. **Ejecutar Comparación**
```bash
cd experiments
python3 coordinator.py compare
# O directamente:
python3 compare_results.py
```

### 3. **Obtener Reporte Final**
El script generará:
- **Comparación en consola**: Tabla comparativa detallada
- **results/comparison_report.json**: Reporte completo para la tarea

---

## 📊 Estructura de Resultados

### **Archivo Individual** (ej: `lru_results.json`)
```json
{
  "total_requests": 10000,
  "cache_hits": 800,
  "cache_misses": 9200,
  "hit_rate": 0.08,
  "avg_response_time": 0.0025,
  "evictions": 1240,
  "current_size": 100,
  "experiment_metadata": {
    "policy": "LRU",
    "total_questions": 10000,
    "duration_minutes": 1000.5,
    "start_time": "2025-09-30 10:00:00",
    "end_time": "2025-09-30 26:40:30"
  }
}
```

### **Reporte de Comparación**
```json
{
  "summary": {
    "best_policy": "LFU",
    "best_hit_rate": 0.125,
    "total_experiments": 3
  },
  "detailed_results": {
    "LRU": { /* resultados completos */ },
    "LFU": { /* resultados completos */ },
    "FIFO": { /* resultados completos */ }
  }
}
```

---

## 🎯 Características del Experimento

### **✅ Validez Académica:**
- **10,000 preguntas REALES** del dataset por experimento
- **Distribución realista** basada en popularidad de preguntas
- **Rate limits respetados** (6.5s entre requests)
- **Métricas completas** para análisis científico

### **✅ Optimizaciones Técnicas:**
- **Cache warming progresivo** con datos reales
- **Monitoreo en tiempo real** de estadísticas
- **Manejo de errores** robusto
- **Guardado automático** de resultados

### **✅ Configuración Consistente:**
- **Cache size**: 100 elementos
- **TTL**: 600 segundos (10 minutos)
- **Request interval**: 6.5 segundos
- **Same dataset**: Preguntas del storage real

---

## 🔧 Solución de Problemas

### **❌ Error de Conexión**
```bash
# Reiniciar servicios
docker-compose restart

# Verificar logs
docker-compose logs [servicio]
```

### **❌ Rate Limit Excedido**
- El script respeta automáticamente los límites
- Si hay error, verificar clave API Gemini

### **❌ Experimento Interrumpido**
- Los resultados parciales se pierden
- Reiniciar desde el inicio
- Considerar ejecutar con `nohup` para sesiones largas

### **❌ Memoria Insuficiente**
```bash
# Verificar uso de memoria
docker stats

# Limpiar containers si es necesario
docker system prune
```

---

## 📞 Coordinación del Equipo

### **🔄 Durante la Ejecución:**
1. **Comunicar inicio** del experimento
2. **Reportar progreso** cada pocas horas
3. **Avisar si hay problemas** inmediatamente
4. **Confirmar finalización** exitosa

### **📋 Al Finalizar:**
1. **Verificar archivo JSON** generado
2. **Compartir resultados** con el equipo
3. **Ejecutar comparación** conjunta
4. **Revisar reporte final** antes de entregar

---

## 🏆 Entrega Final

El experimento generará:
- ✅ **3 archivos individuales** con resultados detallados
- ✅ **1 reporte comparativo** con análisis completo
- ✅ **Recomendación técnica** de la mejor política
- ✅ **Métricas científicas** válidas para evaluación académica

**¡Buena suerte con los experimentos! 🚀**