#!/usr/bin/env python3
"""
Experimento LFU - 10,000 preguntas reales del dataset
Parte 2 de 3 del experimento completo
"""

import asyncio
import aiohttp
import json
import time
import random
import numpy as np

# Configuración del experimento
TOTAL_QUESTIONS = 10000
POLICY = "LFU"
CACHE_SIZE = 100
TTL = 600
GEMINI_RPM = 10
REQUEST_INTERVAL = 6.5

async def get_dataset_questions(session, limit=10000):
    """Obtiene preguntas reales del dataset completo"""
    base_url = "http://localhost"
    storage_port = 8004
    storage_url = f"{base_url}:{storage_port}/popular_questions"
    
    try:
        async with session.get(f"{storage_url}?limit={limit}") as response:
            if response.status == 200:
                data = await response.json()
                if data and 'questions' in data:
                    return data['questions']
    except Exception as e:
        print(f"⚠️ Error obteniendo preguntas del dataset: {e}")
    
    return []

async def save_results_to_file(results, filename="lfu_results.json"):
    """Guarda los resultados en un archivo JSON"""
    try:
        # Crear directorio results si no existe
        import os
        os.makedirs("../results", exist_ok=True)
        filepath = f"../results/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Resultados guardados en {filepath}")
    except Exception as e:
        print(f"❌ Error guardando resultados: {e}")

async def test_lfu_cache_10k():
    """Experimento LFU con 10,000 preguntas reales"""
    
    base_url = "http://localhost"
    cache_port = 8001
    generator_port = 8000
    
    experiment_start = time.time()
    
    print(f"\n{'='*80}")
    print(f"🧪 EXPERIMENTO LFU - 10,000 PREGUNTAS REALES")
    print(f"{'='*80}")
    print(f"📊 Configuración:")
    print(f"  • Política: {POLICY}")
    print(f"  • Tamaño cache: {CACHE_SIZE}")
    print(f"  • TTL: {TTL}s")
    print(f"  • Rate limit Gemini: {GEMINI_RPM} RPM")
    print(f"  • Intervalo entre requests: {REQUEST_INTERVAL}s")
    
    estimated_time = TOTAL_QUESTIONS / GEMINI_RPM
    print(f"  • Tiempo estimado: {estimated_time:.1f} minutos ({estimated_time/60:.1f} horas)")
    print(f"  • Hora de inicio: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    async with aiohttp.ClientSession() as session:
        # Configurar caché
        config_url = f"{base_url}:{cache_port}/configure"
        config_data = {
            "policy": POLICY,
            "max_size": CACHE_SIZE,
            "ttl": TTL
        }
        
        try:
            async with session.post(config_url, json=config_data) as response:
                if response.status != 200:
                    print(f"❌ Error configurando caché: {response.status}")
                    return None
                print(f"✅ Caché configurado: {POLICY}")
        except Exception as e:
            print(f"❌ Error conectando con caché: {e}")
            return None
        
        # Resetear caché
        reset_url = f"{base_url}:{cache_port}/reset"
        try:
            async with session.post(reset_url) as response:
                if response.status == 200:
                    print("🔄 Caché reseteado")
        except:
            pass
        
        # Obtener 10,000 preguntas REALES del dataset
        print(f"\n🔍 Obteniendo {TOTAL_QUESTIONS} preguntas REALES del dataset...")
        dataset_questions = await get_dataset_questions(session, limit=TOTAL_QUESTIONS)
        
        if not dataset_questions:
            print("❌ No se pudieron obtener preguntas del dataset")
            return None
        
        if len(dataset_questions) < TOTAL_QUESTIONS:
            print(f"⚠️ Solo se obtuvieron {len(dataset_questions)} preguntas, repitiendo para llegar a {TOTAL_QUESTIONS}")
            multiplier = (TOTAL_QUESTIONS // len(dataset_questions)) + 1
            dataset_questions = (dataset_questions * multiplier)[:TOTAL_QUESTIONS]
        
        # Crear distribución realista basada en popularidad
        weights = []
        for q in dataset_questions:
            count = q.get('count', 1)
            weight = np.log(count + 1) ** 2
            weights.append(weight)
        
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]
        
        # Seleccionar 10,000 preguntas basado en distribución de popularidad
        selected_questions = np.random.choice(
            dataset_questions, 
            size=TOTAL_QUESTIONS, 
            p=weights,
            replace=True
        )
        
        print(f"✅ Seleccionadas {len(selected_questions)} preguntas REALES")
        print(f"  • Pregunta más popular: {selected_questions[0]['question'][:60]}...")
        
        # Procesar las 10,000 preguntas
        print(f"\n🚀 INICIANDO PROCESAMIENTO DE 10,000 PREGUNTAS REALES (LFU)")
        
        processed_requests = []
        start_time = time.time()
        
        for i, question_data in enumerate(selected_questions):
            question = question_data['question']
            
            # Enviar pregunta REAL al sistema
            custom_url = f"{base_url}:{generator_port}/generate/custom"
            payload = {"question": question}
            
            try:
                async with session.post(custom_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        processed_requests.append({
                            'id': result.get('id'),
                            'question': question,
                            'count': question_data.get('count', 1),
                            'index': i + 1
                        })
                    else:
                        print(f"  ⚠️ Error en pregunta {i+1}: HTTP {response.status}")
            
            except Exception as e:
                print(f"  ❌ Error enviando pregunta {i+1}: {e}")
            
            # Mostrar progreso cada 100 preguntas
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                remaining = (TOTAL_QUESTIONS - (i + 1)) * REQUEST_INTERVAL
                eta = time.strftime('%H:%M:%S', time.localtime(time.time() + remaining))
                
                try:
                    async with session.get(f"{base_url}:{cache_port}/stats") as stats_response:
                        if stats_response.status == 200:
                            stats = await stats_response.json()
                            print(f"    📊 {i+1:,}/{TOTAL_QUESTIONS:,} | "
                                  f"Hit Rate: {stats.get('hit_rate', 0):.2%} | "
                                  f"Hits: {stats.get('cache_hits', 0):,} | "
                                  f"Cache: {stats.get('current_size', 0)}/{CACHE_SIZE} | "
                                  f"Tiempo: {elapsed/60:.1f}min | "
                                  f"ETA: {eta}")
                except:
                    print(f"    📊 {i+1:,}/{TOTAL_QUESTIONS:,} | Tiempo: {elapsed/60:.1f}min | ETA: {eta}")
            
            # Respetar rate limit
            if i < TOTAL_QUESTIONS - 1:
                await asyncio.sleep(REQUEST_INTERVAL)
        
        # Esperar procesamiento final
        print(f"\n⏳ Esperando procesamiento final del sistema...")
        await asyncio.sleep(60)
        
        # Obtener estadísticas finales
        stats_url = f"{base_url}:{cache_port}/stats"
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    final_stats = await response.json()
                    experiment_duration = time.time() - experiment_start
                    
                    # Agregar metadatos del experimento
                    final_stats['experiment_metadata'] = {
                        'policy': POLICY,
                        'total_questions': TOTAL_QUESTIONS,
                        'cache_size': CACHE_SIZE,
                        'ttl': TTL,
                        'duration_minutes': experiment_duration / 60,
                        'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(experiment_start)),
                        'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'questions_processed': len(processed_requests)
                    }
                    
                    print(f"\n{'='*80}")
                    print(f"📈 RESULTADOS FINALES - LFU (10,000 PREGUNTAS REALES)")
                    print(f"{'='*80}")
                    print(f"  📊 Estadísticas de Cache:")
                    print(f"    • Total requests procesados: {final_stats.get('total_requests', 0):,}")
                    print(f"    • Cache hits: {final_stats.get('cache_hits', 0):,}")
                    print(f"    • Cache misses: {final_stats.get('cache_misses', 0):,}")
                    print(f"    • Hit rate: {final_stats.get('hit_rate', 0):.2%}")
                    print(f"    • Avg response time: {final_stats.get('avg_response_time', 0):.4f}s")
                    print(f"    • Evictions: {final_stats.get('evictions', 0):,}")
                    print(f"    • Current cache size: {final_stats.get('current_size', 0)}")
                    print(f"  ⏱️ Métricas de Experimento:")
                    print(f"    • Duración total: {experiment_duration/60:.1f} minutos")
                    print(f"    • Preguntas procesadas: {len(processed_requests):,}")
                    print(f"    • Throughput: {final_stats.get('total_requests', 0)/(experiment_duration/60):.1f} req/min")
                    print(f"    • Eficiencia del LFU cache: {final_stats.get('cache_hits', 0)/max(final_stats.get('total_requests', 1), 1)*100:.1f}%")
                    
                    # Guardar resultados
                    await save_results_to_file(final_stats, "lfu_results.json")
                    
                    print(f"\n🎯 EXPERIMENTO LFU COMPLETADO")
                    print(f"📁 Resultados guardados en '../results/lfu_results.json'")
                    print(f"📤 Comparte este archivo con tus compañeros para la comparación final")
                    
                    return final_stats
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas finales: {e}")
        
        return None

def main():
    print("🚀 EXPERIMENTO LFU - PARTE 2 DE 3")
    print(f"⚙️ Este experimento tomará aproximadamente {TOTAL_QUESTIONS/GEMINI_RPM/60:.1f} horas")
    print(f"📋 Instrucciones para el equipo:")
    print(f"  1. Compañero 1 ejecuta 'experiment_lru.py' (LRU)")
    print(f"  2. Ejecuta este script (LFU)")
    print(f"  3. Compañero 3 ejecuta 'experiment_fifo.py' (FIFO)")
    print(f"  4. Al final, unan los 3 archivos JSON para comparar resultados")
    
    asyncio.run(test_lfu_cache_10k())

if __name__ == "__main__":
    main()