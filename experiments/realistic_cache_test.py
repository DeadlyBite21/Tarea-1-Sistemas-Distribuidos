#!/usr/bin/env python3
"""
Experimento realista de caché que simula tráfico basado en popularidad
"""

import asyncio
import aiohttp
import json
import time
import sys
import random

async def get_popular_questions_from_storage(session, limit=100):
    """Obtiene las preguntas más populares del storage (simulando tráfico real)"""
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

async def simulate_realistic_traffic(session, questions, num_requests=100):
    """Simula tráfico realista basado en la popularidad de las preguntas"""
    generator_port = 8000
    base_url = "http://localhost"
    
    if not questions:
        print("❌ No hay preguntas disponibles")
        return
    
    # Crear distribución de probabilidades basada en popularidad
    # Las preguntas más populares (mayor count) tienen mayor probabilidad
    weights = []
    for q in questions:
        count = q.get('count', 1)
        # Usar raíz cuadrada para suavizar la distribución
        weight = count ** 0.5
        weights.append(weight)
    
    print(f"📊 Distribución de tráfico:")
    print(f"  • Pregunta más popular: {questions[0]['question'][:50]}... (count: {questions[0].get('count', 1)})")
    print(f"  • Total preguntas disponibles: {len(questions)}")
    
    # Simular requests
    for i in range(num_requests):
        # Seleccionar pregunta basada en popularidad
        question_data = random.choices(questions, weights=weights, k=1)[0]
        question = question_data['question']
        
        # Enviar pregunta al generador (que consultará el caché)
        custom_url = f"{base_url}:{generator_port}/generate/custom"
        payload = {"question": question}
        
        try:
            async with session.post(custom_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if i % 500 == 0:  # Log cada 500 requests
                        print(f"  📝 Request {i+1}: {question[:50]}... (count: {question_data.get('count', 1)})")
        except Exception as e:
            if i % 500 == 0:
                print(f"  ❌ Error en request {i+1}: {e}")
        
        # Pausa entre requests (simular tráfico real) - más rápido para 10k requests
        await asyncio.sleep(0.01)

async def test_cache_policy_realistic(policy="LRU", cache_size=100, ttl=300, num_requests=10000):
    """Prueba una política de caché con tráfico realista"""
    
    base_url = "http://localhost"
    cache_port = 8001
    
    print(f"\n🧪 Probando política {policy} con tráfico realista (tamaño={cache_size}, TTL={ttl}s)")
    
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
        
        # Obtener estadísticas iniciales
        stats_url = f"{base_url}:{cache_port}/stats"
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    initial_stats = await response.json()
                    print(f"📊 Estadísticas iniciales: Hit rate={initial_stats.get('hit_rate', 0):.1%}")
        except:
            print("⚠️ No se pudieron obtener estadísticas iniciales")
        
        # Obtener preguntas populares del storage
        print("🔍 Obteniendo preguntas populares del storage...")
        popular_questions = await get_popular_questions_from_storage(session, limit=200)
        
        if not popular_questions:
            print("❌ No se pudieron obtener preguntas del storage")
            return None
        
        print(f"✅ Obtenidas {len(popular_questions)} preguntas populares")
        
        # Simular tráfico realista
        print(f"🚀 Simulando {num_requests} requests con distribución realista...")
        await simulate_realistic_traffic(session, popular_questions, num_requests)
        
        # Esperar procesamiento
        print("⏳ Esperando procesamiento final...")
        await asyncio.sleep(15)
        
        # Estadísticas finales
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    final_stats = await response.json()
                    
                    print(f"\n📈 Resultados para {policy}:")
                    print(f"  • Total requests: {final_stats.get('total_requests', 0)}")
                    print(f"  • Cache hits: {final_stats.get('cache_hits', 0)}")
                    print(f"  • Cache misses: {final_stats.get('cache_misses', 0)}")
                    print(f"  • Hit rate: {final_stats.get('hit_rate', 0):.2%}")
                    print(f"  • Avg response time: {final_stats.get('avg_response_time', 0):.3f}s")
                    print(f"  • Evictions: {final_stats.get('evictions', 0)}")
                    print(f"  • Current size: {final_stats.get('current_size', 0)}")
                    
                    return final_stats
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas finales: {e}")
        
        return None

async def compare_policies_realistic():
    """Compara las tres políticas de caché con tráfico realista"""
    print("🏁 Iniciando comparación realista de políticas de caché")
    print("💡 Usando distribución basada en popularidad del storage")
    
    policies = ["LRU", "LFU", "FIFO"]
    results = {}
    
    for policy in policies:
        result = await test_cache_policy_realistic(policy, cache_size=50, ttl=300, num_requests=1000)
        if result:
            results[policy] = result
        
        # Pausa entre políticas
        await asyncio.sleep(5)
    
    # Resumen comparativo
    print("\n" + "="*60)
    print("📊 RESUMEN COMPARATIVO - TRÁFICO REALISTA")
    print("="*60)
    
    for policy, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        avg_time = stats.get('avg_response_time', 0)
        evictions = stats.get('evictions', 0)
        
        print(f"{policy:>6}: Hit Rate={hit_rate:>6.1%} | "
              f"Avg Time={avg_time:>6.3f}s | "
              f"Evictions={evictions:>3}")
    
    # Determinar la mejor política
    best_policy = None
    best_hit_rate = 0
    
    for policy, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        if hit_rate > best_hit_rate:
            best_hit_rate = hit_rate
            best_policy = policy
    
    if best_policy:
        print(f"\n🏆 Mejor política para tráfico realista: {best_policy} con {best_hit_rate:.1%} hit rate")
    
    return results

async def test_cache_sizes_realistic():
    """Prueba diferentes tamaños de caché con tráfico realista"""
    print("\n🔍 Probando diferentes tamaños de caché con tráfico realista (LRU)")
    
    sizes = [10, 20, 30, 50]
    results = {}
    
    for size in sizes:
        print(f"\n📏 Probando tamaño: {size}")
        result = await test_cache_policy_realistic("LRU", cache_size=size, ttl=300, num_requests=1000)
        if result:
            results[size] = result
        await asyncio.sleep(5)
    
    # Resumen de tamaños
    print("\n" + "="*50)
    print("📏 ANÁLISIS DE TAMAÑOS - TRÁFICO REALISTA")
    print("="*50)
    
    for size, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        evictions = stats.get('evictions', 0)
        print(f"Tamaño {size:>2}: Hit Rate={hit_rate:>6.1%} | Evictions={evictions:>3}")
    
    return results

def main():
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "policies":
            asyncio.run(compare_policies_realistic())
        elif test_type == "sizes":
            asyncio.run(test_cache_sizes_realistic())
        elif test_type in ["LRU", "LFU", "FIFO"]:
            asyncio.run(test_cache_policy_realistic(test_type))
        else:
            print("Uso: python realistic_cache_test.py [policies|sizes|LRU|LFU|FIFO]")
    else:
        # Ejecutar prueba completa
        async def full_test():
            await compare_policies_realistic()
            await test_cache_sizes_realistic()
        
        asyncio.run(full_test())

if __name__ == "__main__":
    main()