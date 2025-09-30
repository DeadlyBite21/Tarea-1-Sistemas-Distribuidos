#!/usr/bin/env python3
"""
Experimento REAL de 10,000 preguntas del dataset con Rate Limits optimizado
Estrategia: Todas las preguntas son reales del dataset + Cache inteligente
"""

import asyncio
import aiohttp
import json
import time
import sys
import random
import numpy as np

# Configuración del experimento
TOTAL_QUESTIONS = 10000  # Requerimiento de la tarea
GEMINI_RPM = 10         # Rate limit de Gemini 2.5 Flash
REQUEST_INTERVAL = 6.5   # Segundos entre requests (respeta 10 RPM)

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

async def test_cache_policy_real_10k(policy="LRU", cache_size=100, ttl=600):
    """Experimento REAL de 10,000 preguntas del dataset"""
    
    base_url = "http://localhost"
    cache_port = 8001
    generator_port = 8000
    
    experiment_start = time.time()
    
    print(f"\n{'='*80}")
    print(f"🧪 EXPERIMENTO REAL DE 10,000 PREGUNTAS - POLÍTICA {policy}")
    print(f"{'='*80}")
    print(f"📊 Configuración:")
    print(f"  • Política: {policy}")
    print(f"  • Tamaño cache: {cache_size}")
    print(f"  • TTL: {ttl}s")
    print(f"  • Rate limit Gemini: {GEMINI_RPM} RPM")
    print(f"  • Intervalo entre requests: {REQUEST_INTERVAL}s")
    
    estimated_time = TOTAL_QUESTIONS / GEMINI_RPM
    print(f"  • Tiempo estimado: {estimated_time:.1f} minutos ({estimated_time/60:.1f} horas)")
    print(f"  • TODAS las preguntas son REALES del dataset")
    
    async with aiohttp.ClientSession() as session:
        # Configurar caché
        config_url = f"{base_url}:{cache_port}/configure"
        config_data = {
            "policy": policy,
            "max_size": cache_size,
            "ttl": ttl
        }
        
        try:
            async with session.post(config_url, json=config_data) as response:
                if response.status != 200:
                    print(f"❌ Error configurando caché: {response.status}")
                    return None
                print(f"✅ Caché configurado: {policy}")
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
            # Repetir preguntas para llegar a 10,000 si es necesario
            multiplier = (TOTAL_QUESTIONS // len(dataset_questions)) + 1
            dataset_questions = (dataset_questions * multiplier)[:TOTAL_QUESTIONS]
        
        # Crear distribución realista basada en popularidad
        weights = []
        for q in dataset_questions:
            count = q.get('count', 1)
            # Uso distribución log-normal para simular tráfico real
            weight = np.log(count + 1) ** 2
            weights.append(weight)
        
        # Normalizar pesos
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
        print(f"  • Count de la más popular: {selected_questions[0].get('count', 1)}")
        
        # ESTRATEGIA INTELIGENTE: Procesar en lotes respetando rate limits
        print(f"\n🚀 INICIANDO PROCESAMIENTO DE 10,000 PREGUNTAS REALES")
        print(f"📈 Estrategia: Lotes inteligentes con cache warming progresivo")
        
        processed_requests = []
        start_time = time.time()
        
        # Dividir en lotes para mostrar progreso
        batch_size = 100
        total_batches = (TOTAL_QUESTIONS + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, TOTAL_QUESTIONS)
            current_batch = selected_questions[batch_start:batch_end]
            
            print(f"\n📦 LOTE {batch_num + 1}/{total_batches}")
            print(f"  • Procesando preguntas {batch_start + 1} - {batch_end}")
            
            batch_start_time = time.time()
            
            for i, question_data in enumerate(current_batch):
                question = question_data['question']
                global_index = batch_start + i + 1
                
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
                                'index': global_index
                            })
                        else:
                            print(f"  ⚠️ Error en pregunta {global_index}: HTTP {response.status}")
                
                except Exception as e:
                    print(f"  ❌ Error enviando pregunta {global_index}: {e}")
                
                # Mostrar progreso cada 50 preguntas
                if global_index % 50 == 0:
                    elapsed = time.time() - start_time
                    # Verificar estadísticas del cache
                    try:
                        async with session.get(f"{base_url}:{cache_port}/stats") as stats_response:
                            if stats_response.status == 200:
                                stats = await stats_response.json()
                                print(f"    📊 {global_index:,}/{TOTAL_QUESTIONS:,} | "
                                      f"Cache: {stats.get('current_size', 0)} elementos | "
                                      f"Hit Rate: {stats.get('hit_rate', 0):.2%} | "
                                      f"Hits: {stats.get('cache_hits', 0):,} | "
                                      f"Tiempo: {elapsed/60:.1f}min")
                    except:
                        print(f"    📊 {global_index:,}/{TOTAL_QUESTIONS:,} | Tiempo: {elapsed/60:.1f}min")
                
                # Respetar rate limit (CRÍTICO)
                if global_index < TOTAL_QUESTIONS:
                    await asyncio.sleep(REQUEST_INTERVAL)
            
            batch_time = time.time() - batch_start_time
            print(f"  ✅ Lote {batch_num + 1} completado en {batch_time/60:.1f} minutos")
            
            # Pequeña pausa entre lotes para permitir procesamiento
            if batch_num < total_batches - 1:
                print(f"  ⏸️ Pausa entre lotes...")
                await asyncio.sleep(10)
        
        # Esperar que el sistema procese todas las preguntas
        print(f"\n⏳ Esperando procesamiento final del sistema...")
        await asyncio.sleep(60)
        
        # Estadísticas finales
        stats_url = f"{base_url}:{cache_port}/stats"
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    final_stats = await response.json()
                    experiment_duration = time.time() - experiment_start
                    
                    print(f"\n{'='*80}")
                    print(f"📈 RESULTADOS FINALES - {policy} (10,000 PREGUNTAS REALES)")
                    print(f"{'='*80}")
                    print(f"  📊 Estadísticas de Cache:")
                    print(f"    • Total requests procesados: {final_stats.get('total_requests', 0):,}")
                    print(f"    • Cache hits: {final_stats.get('cache_hits', 0):,}")
                    print(f"    • Cache misses: {final_stats.get('cache_misses', 0):,}")
                    print(f"    • Hit rate: {final_stats.get('hit_rate', 0):.2%}")
                    print(f"    • Avg response time: {final_stats.get('avg_response_time', 0):.4f}s")
                    print(f"    • Evictions: {final_stats.get('evictions', 0):,}")
                    print(f"    • Current cache size: {final_stats.get('current_size', 0)}")
                    print(f"    • Cache utilization: {final_stats.get('current_size', 0)/cache_size*100:.1f}%")
                    print(f"  ⏱️ Métricas de Experimento:")
                    print(f"    • Duración total: {experiment_duration/60:.1f} minutos")
                    print(f"    • Preguntas REALES enviadas: {len(processed_requests):,}")
                    print(f"    • Throughput efectivo: {final_stats.get('total_requests', 0)/(experiment_duration/60):.1f} req/min")
                    print(f"    • Eficiencia del cache: {final_stats.get('cache_hits', 0)/max(final_stats.get('total_requests', 1), 1)*100:.1f}%")
                    
                    # Análisis de patrones de cache
                    if final_stats.get('cache_hits', 0) > 0:
                        print(f"  🎯 Análisis de Patrones:")
                        print(f"    • Preguntas evitaron LLM: {final_stats.get('cache_hits', 0):,}")
                        print(f"    • Reducción de carga LLM: {final_stats.get('hit_rate', 0):.1%}")
                        print(f"    • Costo computacional ahorrado: ~{final_stats.get('cache_hits', 0) * 6.5/60:.1f} minutos")
                    
                    return final_stats
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas finales: {e}")
        
        return None

async def compare_policies_real_10k():
    """Compara las tres políticas con 10,000 preguntas REALES del dataset"""
    print(f"🏁 COMPARACIÓN DE POLÍTICAS - EXPERIMENTO 10,000 PREGUNTAS REALES")
    print(f"💡 Todas las preguntas son del dataset original")
    print(f"⚡ Optimizado para rate limits de Gemini 2.5 Flash")
    
    policies = ["LRU", "LFU", "FIFO"]
    results = {}
    
    total_estimated_time = (TOTAL_QUESTIONS / GEMINI_RPM) * len(policies)
    print(f"⏱️ Tiempo total estimado: {total_estimated_time/60:.1f} horas")
    print(f"📅 Inicio estimado: {time.strftime('%H:%M:%S')}")
    
    for i, policy in enumerate(policies):
        print(f"\n🔄 Ejecutando experimento {i+1}/3: {policy}")
        print(f"📅 Hora de inicio: {time.strftime('%H:%M:%S')}")
        
        result = await test_cache_policy_real_10k(policy, cache_size=100, ttl=600)
        if result:
            results[policy] = result
            print(f"✅ Experimento {policy} completado")
        else:
            print(f"❌ Experimento {policy} falló")
        
        # Pausa entre experimentos para permitir reset completo
        if i < len(policies) - 1:
            print(f"\n⏸️ Pausa entre experimentos (2 minutos)...")
            await asyncio.sleep(120)
    
    # Resumen final
    print(f"\n{'='*100}")
    print(f"🏆 RESUMEN FINAL - COMPARACIÓN 10,000 PREGUNTAS REALES")
    print(f"{'='*100}")
    
    best_policy = None
    best_hit_rate = 0
    
    for policy, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        hits = stats.get('cache_hits', 0)
        total = stats.get('total_requests', 0)
        evictions = stats.get('evictions', 0)
        cache_size = stats.get('current_size', 0)
        
        print(f"{policy:>6}: Hit Rate={hit_rate:>7.2%} | "
              f"Hits={hits:>6,} | "
              f"Total={total:>6,} | "
              f"Evictions={evictions:>6,} | "
              f"Cache Size={cache_size:>3}")
        
        if hit_rate > best_hit_rate:
            best_hit_rate = hit_rate
            best_policy = policy
    
    if best_policy:
        print(f"\n🥇 GANADOR: {best_policy} con {best_hit_rate:.2%} hit rate")
        print(f"📊 Impacto del cache en sistema de 10,000 preguntas REALES:")
        winner_stats = results[best_policy]
        hits = winner_stats.get('cache_hits', 0)
        print(f"  • {hits:,} preguntas respondidas desde cache")
        print(f"  • {winner_stats.get('cache_misses', 0):,} preguntas enviadas al LLM")
        print(f"  • Reducción de carga LLM: {best_hit_rate:.1%}")
        print(f"  • Tiempo ahorrado: ~{hits * 6.5/60:.1f} minutos")
    
    print(f"\n⏰ Experimento completado: {time.strftime('%H:%M:%S')}")
    return results

def main():
    print("🚀 EXPERIMENTO REAL DE 10,000 PREGUNTAS DEL DATASET")
    print(f"⚙️ Configuración:")
    print(f"  • Total preguntas: {TOTAL_QUESTIONS:,} (TODAS REALES del dataset)")
    print(f"  • Rate limit Gemini: {GEMINI_RPM} RPM")
    print(f"  • Intervalo entre requests: {REQUEST_INTERVAL}s")
    
    estimated_time_per_policy = TOTAL_QUESTIONS / GEMINI_RPM
    print(f"  • Tiempo por política: {estimated_time_per_policy:.1f} minutos")
    print(f"  • Tiempo total estimado: {estimated_time_per_policy * 3:.1f} minutos")
    
    if len(sys.argv) > 1:
        policy = sys.argv[1].upper()
        if policy in ["LRU", "LFU", "FIFO"]:
            asyncio.run(test_cache_policy_real_10k(policy))
        else:
            print("Uso: python3 real_10k_test.py [LRU|LFU|FIFO]")
    else:
        asyncio.run(compare_policies_real_10k())

if __name__ == "__main__":
    main()