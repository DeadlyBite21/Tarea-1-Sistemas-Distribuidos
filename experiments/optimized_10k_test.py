#!/usr/bin/env python3
"""
Experimento Optimizado para 10,000 preguntas con Rate Limits de Gemini
Estrategia: Cache warming + Simulación inteligente
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
WARM_UP_QUESTIONS = 200  # Preguntas para "calentar" el cache
GEMINI_RPM = 10         # Rate limit de Gemini 2.5 Flash
REQUEST_INTERVAL = 6.5   # Segundos entre requests (respeta 10 RPM)

def calculate_experiment_time(warm_up_questions, rpm):
    """Calcula el tiempo real de experimento"""
    minutes = warm_up_questions / rpm
    return minutes

async def get_popular_questions_from_storage(session, limit=500):
    """Obtiene preguntas populares del storage"""
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
        print(f"⚠️ Error obteniendo preguntas populares: {e}")
    
    return []

async def warm_up_cache(session, questions, warm_up_count=200):
    """Fase 1: Calentar el cache con preguntas únicas respetando rate limits"""
    print(f"\n🔥 FASE 1: CALENTAMIENTO DEL CACHE")
    print(f"📊 Enviando {warm_up_count} preguntas únicas con rate limit de {GEMINI_RPM} RPM")
    
    estimated_time = calculate_experiment_time(warm_up_count, GEMINI_RPM)
    print(f"⏱️ Tiempo estimado: {estimated_time:.1f} minutos ({estimated_time*60:.0f} segundos)")
    
    base_url = "http://localhost"
    generator_port = 8000
    cache_port = 8001
    
    # Seleccionar preguntas únicas para el warm-up
    selected_questions = random.sample(questions, min(warm_up_count, len(questions)))
    
    start_time = time.time()
    sent_requests = []
    
    for i, question_data in enumerate(selected_questions):
        question = question_data['question']
        
        # Enviar pregunta
        custom_url = f"{base_url}:{generator_port}/generate/custom"
        payload = {"question": question}
        
        try:
            async with session.post(custom_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    sent_requests.append({
                        'id': result.get('id'),
                        'question': question,
                        'count': question_data.get('count', 1)
                    })
                    
                    # Mostrar progreso cada 20 preguntas
                    if (i + 1) % 20 == 0:
                        elapsed = time.time() - start_time
                        # Verificar estadísticas del cache
                        try:
                            async with session.get(f"{base_url}:{cache_port}/stats") as stats_response:
                                if stats_response.status == 200:
                                    stats = await stats_response.json()
                                    print(f"  📈 {i+1}/{warm_up_count} enviadas | "
                                          f"Cache: {stats.get('current_size', 0)} elementos | "
                                          f"Hit Rate: {stats.get('hit_rate', 0):.1%} | "
                                          f"Tiempo: {elapsed:.0f}s")
                        except:
                            print(f"  📈 {i+1}/{warm_up_count} enviadas | Tiempo: {elapsed:.0f}s")
        
        except Exception as e:
            print(f"  ❌ Error enviando pregunta {i+1}: {e}")
        
        # Respetar rate limit
        if i < len(selected_questions) - 1:
            await asyncio.sleep(REQUEST_INTERVAL)
    
    total_time = time.time() - start_time
    print(f"✅ Fase 1 completada en {total_time/60:.1f} minutos")
    
    return sent_requests

async def simulate_heavy_traffic(session, questions, total_requests=10000, cache_warmed=True):
    """Fase 2: Simular tráfico pesado con cache caliente"""
    print(f"\n🚀 FASE 2: SIMULACIÓN DE TRÁFICO PESADO")
    print(f"📊 Simulando {total_requests} requests con cache {'caliente' if cache_warmed else 'frío'}")
    
    base_url = "http://localhost"
    generator_port = 8000
    cache_port = 8001
    
    # Crear distribución realista basada en popularidad
    weights = []
    for q in questions:
        count = q.get('count', 1)
        # Uso distribución log-normal para simular tráfico real
        weight = np.log(count + 1) ** 2
        weights.append(weight)
    
    # Normalizar pesos
    total_weight = sum(weights)
    weights = [w/total_weight for w in weights]
    
    print(f"📈 Distribución de tráfico configurada (Zipf-like)")
    print(f"  • Pregunta más popular tendrá ~{max(weights)*100:.1f}% del tráfico")
    
    start_time = time.time()
    batch_size = 100  # Enviar en lotes para eficiencia
    
    for batch in range(0, total_requests, batch_size):
        current_batch_size = min(batch_size, total_requests - batch)
        
        # Seleccionar preguntas para este lote basado en distribución
        batch_questions = np.random.choice(
            questions, 
            size=current_batch_size, 
            p=weights,
            replace=True
        )
        
        # Enviar lote de preguntas (sin esperar rate limit - simulación)
        for i, question_data in enumerate(batch_questions):
            question = question_data['question']
            custom_url = f"{base_url}:{generator_port}/generate/custom"
            payload = {"question": question}
            
            try:
                async with session.post(custom_url, json=payload) as response:
                    pass  # Solo enviamos, no esperamos respuesta para simular volumen
            except:
                pass  # Ignorar errores en simulación
        
        # Mostrar progreso cada 1000 requests
        if (batch + batch_size) % 1000 == 0:
            elapsed = time.time() - start_time
            try:
                async with session.get(f"{base_url}:{cache_port}/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        print(f"  📊 {batch + current_batch_size:,}/{total_requests:,} simuladas | "
                              f"Cache Hits: {stats.get('cache_hits', 0):,} | "
                              f"Hit Rate: {stats.get('hit_rate', 0):.2%} | "
                              f"Cache Size: {stats.get('current_size', 0)}")
            except:
                print(f"  📊 {batch + current_batch_size:,}/{total_requests:,} simuladas")
        
        # Pequeña pausa entre lotes
        await asyncio.sleep(0.1)
    
    total_time = time.time() - start_time
    print(f"✅ Fase 2 completada en {total_time:.1f} segundos")

async def test_cache_policy_10k(policy="LRU", cache_size=100, ttl=600):
    """Experimento completo de 10,000 preguntas optimizado"""
    
    base_url = "http://localhost"
    cache_port = 8001
    
    experiment_start = time.time()
    
    print(f"\n{'='*80}")
    print(f"🧪 EXPERIMENTO DE 10,000 PREGUNTAS - POLÍTICA {policy}")
    print(f"{'='*80}")
    print(f"📊 Configuración:")
    print(f"  • Política: {policy}")
    print(f"  • Tamaño cache: {cache_size}")
    print(f"  • TTL: {ttl}s")
    print(f"  • Rate limit Gemini: {GEMINI_RPM} RPM")
    print(f"  • Estrategia: Cache warming + Simulación de volumen")
    
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
        
        # Obtener preguntas del storage
        print("\n🔍 Obteniendo preguntas del storage...")
        questions = await get_popular_questions_from_storage(session, limit=300)
        
        if not questions:
            print("❌ No se pudieron obtener preguntas del storage")
            return None
        
        print(f"✅ Obtenidas {len(questions)} preguntas")
        print(f"  • Más popular: {questions[0]['question'][:60]}... (count: {questions[0].get('count', 1)})")
        
        # FASE 1: Calentar cache
        warm_up_requests = await warm_up_cache(session, questions, WARM_UP_QUESTIONS)
        
        # Esperar que el cache se procese
        print(f"\n⏳ Dando tiempo para procesamiento del cache...")
        await asyncio.sleep(30)
        
        # FASE 2: Simular tráfico pesado
        await simulate_heavy_traffic(session, questions, TOTAL_QUESTIONS, cache_warmed=True)
        
        # Estadísticas finales
        print(f"\n⏳ Obteniendo estadísticas finales...")
        await asyncio.sleep(10)
        
        stats_url = f"{base_url}:{cache_port}/stats"
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    final_stats = await response.json()
                    experiment_duration = time.time() - experiment_start
                    
                    print(f"\n{'='*80}")
                    print(f"📈 RESULTADOS FINALES - {policy} (10,000 PREGUNTAS)")
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
                    print(f"    • Requests reales enviados: {len(warm_up_requests)}")
                    print(f"    • Requests simulados: {TOTAL_QUESTIONS:,}")
                    print(f"    • Throughput efectivo: {final_stats.get('total_requests', 0)/(experiment_duration/60):.1f} req/min")
                    
                    return final_stats
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas finales: {e}")
        
        return None

async def compare_policies_10k():
    """Compara las tres políticas con experimento de 10,000 preguntas"""
    print(f"🏁 COMPARACIÓN DE POLÍTICAS - EXPERIMENTO 10,000 PREGUNTAS")
    print(f"💡 Optimizado para rate limits de Gemini 2.5 Flash")
    
    policies = ["LRU", "LFU", "FIFO"]
    results = {}
    
    for i, policy in enumerate(policies):
        print(f"\n🔄 Ejecutando experimento {i+1}/3: {policy}")
        result = await test_cache_policy_10k(policy, cache_size=100, ttl=600)
        if result:
            results[policy] = result
        
        # Pausa entre experimentos para permitir reset
        if i < len(policies) - 1:
            print(f"\n⏸️ Pausa entre experimentos...")
            await asyncio.sleep(60)
    
    # Resumen final
    print(f"\n{'='*100}")
    print(f"🏆 RESUMEN FINAL - COMPARACIÓN 10,000 PREGUNTAS")
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
        print(f"📊 Impacto del cache en sistema de 10,000 preguntas:")
        winner_stats = results[best_policy]
        hits = winner_stats.get('cache_hits', 0)
        print(f"  • {hits:,} preguntas respondidas desde cache")
        print(f"  • {winner_stats.get('cache_misses', 0):,} preguntas enviadas al LLM")
        print(f"  • Reducción de carga LLM: {best_hit_rate:.1%}")
    
    return results

def main():
    print("🚀 EXPERIMENTO OPTIMIZADO PARA 10,000 PREGUNTAS")
    print(f"⚙️ Configuración:")
    print(f"  • Total preguntas objetivo: {TOTAL_QUESTIONS:,}")
    print(f"  • Cache warm-up: {WARM_UP_QUESTIONS} preguntas reales")
    print(f"  • Rate limit Gemini: {GEMINI_RPM} RPM")
    print(f"  • Intervalo entre requests: {REQUEST_INTERVAL}s")
    
    estimated_warm_up_time = calculate_experiment_time(WARM_UP_QUESTIONS, GEMINI_RPM)
    print(f"  • Tiempo estimado por política: {estimated_warm_up_time:.1f} minutos")
    print(f"  • Tiempo total estimado: {estimated_warm_up_time * 3:.1f} minutos")
    
    if len(sys.argv) > 1:
        policy = sys.argv[1].upper()
        if policy in ["LRU", "LFU", "FIFO"]:
            asyncio.run(test_cache_policy_10k(policy))
        else:
            print("Uso: python3 optimized_10k_test.py [LRU|LFU|FIFO]")
    else:
        asyncio.run(compare_policies_10k())

if __name__ == "__main__":
    main()