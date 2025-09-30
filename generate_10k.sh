#!/bin/bash

echo "Generando 10,000 preguntas en lotes de 500..."

for i in {1..20}; do
    echo "Lote $i/20 - Generando 500 preguntas..."
    curl -X POST http://localhost:8000/generate/batch \
         -H "Content-Type: application/json" \
         -d '{"num_questions": 500}' \
         --silent --output /dev/null
    
    echo "Lote $i completado. Esperando 5 segundos antes del siguiente lote..."
    sleep 5
done

echo "¡Todas las 10,000 preguntas han sido enviadas!"