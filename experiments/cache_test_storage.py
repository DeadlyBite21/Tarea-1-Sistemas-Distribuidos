#!/usr/bin/env python3
"""
Script simplificado para probar las políticas de caché básicas con preguntas del storage
"""

import asyncio
import aiohttp
import json
import time
import sys

async def get_random_questions_from_storage(session, count=10):
    """Obtiene preguntas aleatorias del storage"""
    base_url = "http://localhost"
    storage_port = 8004
    storage_url = f"{base_url}:{storage_port}/questions"
    questions = []
    
    try:
        # Obtener múltiples preguntas del storage
        for _ in range(count):
            async with session.get(f"{storage_url}?limit=1&random=true") as response:
                if response.status == 200:
                    data = await response.json()
                    # El storage devuelve un objeto con 'questions' array
                    questions_array = data.get('questions', [])
                    if questions_array and len(questions_array) > 0:
                        question_text = questions_array[0].get('question', '').strip()
                        if question_text:
                            questions.append(question_text)
                            print(f"  📖 Pregunta obtenida: {question_text[:50]}...")
                else:
                    print(f"  ⚠️ Storage respondió con status: {response.status}")
                await asyncio.sleep(0.1)  # Pequeña pausa entre requests
    except Exception as e:
        print(f"⚠️ Error obteniendo preguntas del storage: {e}")
        # Fallback a preguntas predefinidas
        questions = [
            "What is Python?",
            "How to learn programming?",
            "What is machine learning?",
            "How to use Docker?",
            "What is artificial intelligence?"
        ]
    
    return questions if questions else ["What is programming?"]

async def test_cache_policy(policy="LRU", cache_size=50, ttl=300, num_requests=100):
    """Prueba una política de caché específica"""
    
    base_url = "http://localhost"
    cache_port = 8001
    generator_port = 8000
    storage_port = 8004
    
    print(f"\n🧪 Probando política {policy} (tamaño={cache_size}, TTL={ttl}s)")
    
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
        
        # Estadísticas iniciales
        stats_url = f"{base_url}:{cache_port}/stats"
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    initial_stats = await response.json()
                    print(f"📊 Estadísticas iniciales: {initial_stats}")
        except:
            print("⚠️ No se pudieron obtener estadísticas iniciales")
        
        # Generar tráfico de prueba
        print(f"🚀 Generando {num_requests} preguntas...")
        
        # Obtener preguntas reales del storage
        print("📚 Obteniendo preguntas del storage...")
        popular_questions = await get_random_questions_from_storage(session, count=10)
        print(f"✅ Obtenidas {len(popular_questions)} preguntas del storage")
        
        # Patrón mixto: algunas preguntas repetidas del storage, otras únicas
        for i in range(num_requests):
            # 60% preguntas populares del storage, 40% aleatorias del storage
            if i % 10 < 6 and popular_questions:
                # Usar pregunta del storage que se repetirá (para probar caché)
                question = popular_questions[i % len(popular_questions)]
                custom_url = f"{base_url}:{generator_port}/generate/custom"
                payload = {"question": question}
                
                try:
                    async with session.post(custom_url, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            if i % 20 == 0:  # Log cada 20 requests
                                print(f"  📝 Pregunta del storage enviada: {question[:50]}...")
                except Exception as e:
                    if i % 20 == 0:
                        print(f"  ❌ Error enviando pregunta del storage: {e}")
            else:
                # Pregunta completamente aleatoria del storage
                storage_questions = await get_random_questions_from_storage(session, count=1)
                if storage_questions:
                    question = storage_questions[0]
                    custom_url = f"{base_url}:{generator_port}/generate/custom"
                    payload = {"question": question}
                    
                    try:
                        async with session.post(custom_url, json=payload) as response:
                            if response.status == 200:
                                result = await response.json()
                                if i % 20 == 0:
                                    print(f"  🎲 Pregunta aleatoria del storage: {question[:50]}...")
                    except Exception as e:
                        if i % 20 == 0:
                            print(f"  ❌ Error enviando pregunta aleatoria: {e}")
                else:
                    # Fallback al generador normal si no hay preguntas del storage
                    random_url = f"{base_url}:{generator_port}/generate"
                    try:
                        async with session.post(random_url) as response:
                            if response.status == 200:
                                result = await response.json()
                                if i % 20 == 0:
                                    print(f"  🎲 Pregunta aleatoria generada")
                    except Exception as e:
                        if i % 20 == 0:
                            print(f"  ❌ Error enviando pregunta aleatoria: {e}")
            
            # Pequeña pausa entre requests
            await asyncio.sleep(0.1)
        
        # Esperar a que se procesen las respuestas
        print("⏳ Esperando procesamiento...")
        await asyncio.sleep(10)
        
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

async def compare_policies():
    """Compara las tres políticas de caché"""
    print("🏁 Iniciando comparación de políticas de caché")
    
    policies = ["LRU", "LFU", "FIFO"]
    results = {}
    
    for policy in policies:
        result = await test_cache_policy(policy, cache_size=25, ttl=300, num_requests=50)
        if result:
            results[policy] = result
        
        # Pausa entre políticas
        await asyncio.sleep(5)
    
    # Resumen comparativo
    print("\n" + "="*60)
    print("📊 RESUMEN COMPARATIVO")
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
        print(f"\n🏆 Mejor política: {best_policy} con {best_hit_rate:.1%} hit rate")
    
    return results

async def test_cache_sizes():
    """Prueba diferentes tamaños de caché"""
    print("\n🔍 Probando diferentes tamaños de caché (LRU)")
    
    sizes = [10, 25, 50, 100]
    results = {}
    
    for size in sizes:
        print(f"\n📏 Probando tamaño: {size}")
        result = await test_cache_policy("LRU", cache_size=size, ttl=300, num_requests=40)
        if result:
            results[size] = result
        await asyncio.sleep(3)
    
    # Resumen de tamaños
    print("\n" + "="*50)
    print("📏 ANÁLISIS DE TAMAÑOS")
    print("="*50)
    
    for size, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        evictions = stats.get('evictions', 0)
        print(f"Tamaño {size:>3}: Hit Rate={hit_rate:>6.1%} | Evictions={evictions:>3}")
    
    return results

async def test_ttl_effects():
    """Prueba diferentes valores de TTL"""
    print("\n⏰ Probando diferentes valores de TTL (LRU)")
    
    ttl_values = [30, 60, 120, 300]
    results = {}
    
    for ttl in ttl_values:
        print(f"\n⏱️ Probando TTL: {ttl}s")
        result = await test_cache_policy("LRU", cache_size=25, ttl=ttl, num_requests=30)
        if result:
            results[ttl] = result
        await asyncio.sleep(3)
    
    # Resumen de TTL
    print("\n" + "="*50)
    print("⏰ ANÁLISIS DE TTL")
    print("="*50)
    
    for ttl, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        evictions = stats.get('evictions', 0)
        print(f"TTL {ttl:>3}s: Hit Rate={hit_rate:>6.1%} | Evictions={evictions:>3}")
    
    return results

def main():
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "policies":
            asyncio.run(compare_policies())
        elif test_type == "sizes":
            asyncio.run(test_cache_sizes())
        elif test_type == "ttl":
            asyncio.run(test_ttl_effects())
        elif test_type in ["LRU", "LFU", "FIFO"]:
            asyncio.run(test_cache_policy(test_type))
        elif test_type == "all":
            async def full_experiments():
                await compare_policies()
                await test_cache_sizes()
                await test_ttl_effects()
            asyncio.run(full_experiments())
        else:
            print("Uso: python simple_cache_test.py [policies|sizes|ttl|all|LRU|LFU|FIFO]")
    else:
        # Ejecutar prueba completa
        async def full_test():
            await compare_policies()
            await test_cache_sizes()
        
        asyncio.run(full_test())

if __name__ == "__main__":
    main()