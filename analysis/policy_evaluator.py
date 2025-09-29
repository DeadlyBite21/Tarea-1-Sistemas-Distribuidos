"""
Evaluador de Políticas de Caché
Implementa y compara diferentes políticas de remoción (LRU, LFU, FIFO)
"""

import asyncio
import aiohttp
import json
import time
import random
from collections import OrderedDict, defaultdict, deque
from abc import ABC, abstractmethod
import statistics

class CachePolicy(ABC):
    """Clase base para políticas de caché"""
    
    def __init__(self, max_size=50):
        self.max_size = max_size
        self.cache = {}
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
    
    @abstractmethod
    def get(self, key):
        """Obtener valor del caché"""
        pass
    
    @abstractmethod
    def put(self, key, value):
        """Insertar valor en el caché"""
        pass
    
    def get_stats(self):
        """Obtener estadísticas del caché"""
        hit_rate = self.hits / self.total_requests if self.total_requests > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': self.total_requests,
            'hit_rate': hit_rate,
            'miss_rate': 1 - hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size
        }
    
    def clear_stats(self):
        """Limpiar estadísticas"""
        self.hits = 0
        self.misses = 0
        self.total_requests = 0

class LRUCache(CachePolicy):
    """Least Recently Used Cache"""
    
    def __init__(self, max_size=50):
        super().__init__(max_size)
        self.cache = OrderedDict()
    
    def get(self, key):
        self.total_requests += 1
        if key in self.cache:
            # Mover al final (más reciente)
            value = self.cache.pop(key)
            self.cache[key] = value
            self.hits += 1
            return value
        else:
            self.misses += 1
            return None
    
    def put(self, key, value):
        if key in self.cache:
            # Actualizar y mover al final
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Remover el menos reciente (primero)
            self.cache.popitem(last=False)
        
        self.cache[key] = value

class LFUCache(CachePolicy):
    """Least Frequently Used Cache"""
    
    def __init__(self, max_size=50):
        super().__init__(max_size)
        self.cache = {}
        self.frequencies = defaultdict(int)
        self.frequency_buckets = defaultdict(OrderedDict)
        self.min_frequency = 0
    
    def get(self, key):
        self.total_requests += 1
        if key in self.cache:
            self._update_frequency(key)
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def put(self, key, value):
        if self.max_size <= 0:
            return
        
        if key in self.cache:
            self.cache[key] = value
            self._update_frequency(key)
            return
        
        if len(self.cache) >= self.max_size:
            self._evict()
        
        self.cache[key] = value
        self.frequencies[key] = 1
        self.frequency_buckets[1][key] = True
        self.min_frequency = 1
    
    def _update_frequency(self, key):
        freq = self.frequencies[key]
        self.frequencies[key] = freq + 1
        
        # Remover de bucket actual
        del self.frequency_buckets[freq][key]
        
        # Si este era el último elemento del min_frequency bucket
        if self.min_frequency == freq and not self.frequency_buckets[freq]:
            self.min_frequency += 1
        
        # Añadir al nuevo bucket
        self.frequency_buckets[freq + 1][key] = True
    
    def _evict(self):
        # Remover el menos frecuente, en caso de empate el más antiguo
        key_to_evict = next(iter(self.frequency_buckets[self.min_frequency]))
        del self.frequency_buckets[self.min_frequency][key_to_evict]
        del self.cache[key_to_evict]
        del self.frequencies[key_to_evict]

class FIFOCache(CachePolicy):
    """First In First Out Cache"""
    
    def __init__(self, max_size=50):
        super().__init__(max_size)
        self.cache = {}
        self.insertion_order = deque()
    
    def get(self, key):
        self.total_requests += 1
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def put(self, key, value):
        if key in self.cache:
            self.cache[key] = value
            return
        
        if len(self.cache) >= self.max_size:
            # Remover el primero que entró
            oldest_key = self.insertion_order.popleft()
            del self.cache[oldest_key]
        
        self.cache[key] = value
        self.insertion_order.append(key)

class CachePolicyEvaluator:
    """Evaluador de políticas de caché"""
    
    def __init__(self):
        self.questions_pool = []
        self.mock_responses = {}
        self.storage_url = "http://localhost:8004"

    def load_real_questions(self, limit=100):
        """Cargar preguntas reales de la base de datos"""
        import requests
        try:
            response = requests.get(f"{self.storage_url}/questions?limit={limit}&random=true")
            if response.status_code == 200:
                data = response.json()
                questions = data.get('questions', [])
                self.questions_pool = [q['question'] for q in questions if q['question']]
                # Crear respuestas mock basadas en preguntas reales
                self.mock_responses = {q: f"Respuesta simulada para: {q[:50]}..." for q in self.questions_pool}
                print(f"✅ Cargadas {len(self.questions_pool)} preguntas reales")
            else:
                print(f"❌ Error obteniendo preguntas: {response.status_code}")
                self._load_fallback_questions()
        except Exception as e:
            print(f"❌ Error cargando preguntas reales: {e}")
            self._load_fallback_questions()

    def _load_fallback_questions(self):
        """Cargar preguntas de respaldo si falla la conexión"""
        self.questions_pool = [
            "¿Qué es Python y para qué se usa?",
            "¿Cómo funciona Docker?",
            "¿Qué es DevOps?",
            "¿Qué es machine learning?",
            "¿Qué son las APIs REST?",
            "¿Cómo funciona Kubernetes?",
            "¿Qué es la computación en la nube?",
            "¿Qué son las bases de datos NoSQL?",
            "¿Qué es el Big Data?",
            "¿Qué es la inteligencia artificial?",
            "¿Cómo funcionan los microservicios?",
            "¿Qué es GraphQL?",
            "¿Qué es blockchain?",
            "¿Cómo funciona Git?",
            "¿Qué es la programación funcional?",
            "¿Qué es TDD?",
            "¿Cómo funcionan las redes neuronales?",
            "¿Qué es la criptografía?",
            "¿Qué son los algoritmos de ordenamiento?",
            "¿Cómo funciona el protocolo HTTP?"
        ]
        self.mock_responses = {q: f"Respuesta simulada para: {q}" for q in self.questions_pool}

    def generate_zipf_requests(self, num_requests=200, alpha=1.2):
        """Generar requests siguiendo distribución Zipf"""
        import numpy as np
        zipf_indices = np.random.zipf(alpha, num_requests) - 1
        zipf_indices = zipf_indices % len(self.questions_pool)
        return [self.questions_pool[i] for i in zipf_indices]

    def generate_hotspot_requests(self, num_requests=200, hotspot_ratio=0.8):
        """Generar requests con patrón hotspot (80/20)"""
        hot_questions = self.questions_pool[:4]  # 20% de preguntas
        cold_questions = self.questions_pool[4:]  # 80% de preguntas
        
        requests = []
        for _ in range(num_requests):
            if random.random() < hotspot_ratio:
                requests.append(random.choice(hot_questions))
            else:
                requests.append(random.choice(cold_questions))
        return requests

    def simulate_cache_behavior(self, cache_policy, requests):
        """Simular comportamiento del caché con una política específica"""
        cache_policy.clear_stats()
        response_times = []
        
        for request in requests:
            start_time = time.time()
            
            # Intentar obtener del caché
            cached_response = cache_policy.get(request)
            
            if cached_response is None:
                # Cache miss - simular obtener respuesta del LLM
                response = self.mock_responses.get(request, "Respuesta por defecto")
                cache_policy.put(request, response)
                # Simular latencia del LLM (100-300ms)
                response_time = random.uniform(0.1, 0.3)
            else:
                # Cache hit - respuesta rápida
                # Simular latencia del cache (1-5ms)
                response_time = random.uniform(0.001, 0.005)
            
            response_times.append(response_time)
        
        stats = cache_policy.get_stats()
        stats['avg_response_time'] = statistics.mean(response_times)
        stats['response_times'] = response_times
        
        return stats

    def evaluate_cache_sizes(self, cache_sizes=[10, 25, 50, 100, 200]):
        """Evaluar diferentes tamaños de caché"""
        print("\n🔬 EVALUANDO TAMAÑOS DE CACHÉ")
        print("=" * 50)
        
        # Cargar preguntas reales
        self.load_real_questions(limit=150)
        
        # Generar requests de prueba
        test_requests = self.generate_zipf_requests(300)
        
        results = {}
        
        for size in cache_sizes:
            print(f"\nProbando tamaño: {size}")
            
            # Probar cada política con este tamaño
            lru_cache = LRUCache(max_size=size)
            lfu_cache = LFUCache(max_size=size)
            fifo_cache = FIFOCache(max_size=size)
            
            lru_stats = self.simulate_cache_behavior(lru_cache, test_requests)
            lfu_stats = self.simulate_cache_behavior(lfu_cache, test_requests)
            fifo_stats = self.simulate_cache_behavior(fifo_cache, test_requests)
            
            results[size] = {
                'LRU': lru_stats,
                'LFU': lfu_stats,
                'FIFO': fifo_stats
            }
            
            print(f"  LRU Hit Rate: {lru_stats['hit_rate']:.2%}")
            print(f"  LFU Hit Rate: {lfu_stats['hit_rate']:.2%}")
            print(f"  FIFO Hit Rate: {fifo_stats['hit_rate']:.2%}")
        
        return results

    def evaluate_policies_detailed(self):
        """Evaluación detallada de políticas con diferentes patrones"""
        print("\n🔬 EVALUACIÓN DETALLADA DE POLÍTICAS")
        print("=" * 50)
        
        # Cargar preguntas reales
        self.load_real_questions(limit=100)
        
        test_scenarios = [
            ("Distribución Zipf", self.generate_zipf_requests(200)),
            ("Patrón Hotspot", self.generate_hotspot_requests(200)),
            ("Distribución Uniforme", random.choices(self.questions_pool, k=200))
        ]
        
        detailed_results = {}
        
        for scenario_name, requests in test_scenarios:
            print(f"\n📊 Escenario: {scenario_name}")
            print("-" * 30)
            
            # Crear caches con tamaño estándar
            lru_cache = LRUCache(max_size=50)
            lfu_cache = LFUCache(max_size=50)
            fifo_cache = FIFOCache(max_size=50)
            
            # Simular comportamiento
            lru_stats = self.simulate_cache_behavior(lru_cache, requests)
            lfu_stats = self.simulate_cache_behavior(lfu_cache, requests)
            fifo_stats = self.simulate_cache_behavior(fifo_cache, requests)
            
            detailed_results[scenario_name] = {
                'LRU': lru_stats,
                'LFU': lfu_stats,
                'FIFO': fifo_stats
            }
            
            print(f"LRU  - Hit Rate: {lru_stats['hit_rate']:.2%}, "
                  f"Avg Time: {lru_stats['avg_response_time']:.3f}s")
            print(f"LFU  - Hit Rate: {lfu_stats['hit_rate']:.2%}, "
                  f"Avg Time: {lfu_stats['avg_response_time']:.3f}s")
            print(f"FIFO - Hit Rate: {fifo_stats['hit_rate']:.2%}, "
                  f"Avg Time: {fifo_stats['avg_response_time']:.3f}s")
        
        return detailed_results

    def generate_comprehensive_report(self):
        """Generar reporte comprensivo del análisis"""
        print("\n" + "=" * 80)
        print("📊 ANÁLISIS COMPRENSIVO DE POLÍTICAS DE CACHÉ")
        print("=" * 80)
        
        # Evaluación de tamaños
        size_results = self.evaluate_cache_sizes()
        
        # Evaluación detallada de políticas
        policy_results = self.evaluate_policies_detailed()
        
        # Análisis de resultados
        self.analyze_size_impact(size_results)
        self.analyze_policy_performance(policy_results)
        self.generate_recommendations()

    def analyze_size_impact(self, size_results):
        """Analizar el impacto del tamaño del caché"""
        print("\n📈 ANÁLISIS DEL IMPACTO DEL TAMAÑO")
        print("-" * 40)
        
        print(f"{'Tamaño':<8} {'LRU Hit%':<10} {'LFU Hit%':<10} {'FIFO Hit%':<10}")
        print("-" * 40)
        
        for size, results in size_results.items():
            lru_hit = results['LRU']['hit_rate'] * 100
            lfu_hit = results['LFU']['hit_rate'] * 100
            fifo_hit = results['FIFO']['hit_rate'] * 100
            
            print(f"{size:<8} {lru_hit:<10.1f} {lfu_hit:<10.1f} {fifo_hit:<10.1f}")
        
        # Encontrar punto óptimo
        best_size_lru = max(size_results.keys(), 
                           key=lambda x: size_results[x]['LRU']['hit_rate'])
        
        print(f"\n💡 OBSERVACIONES:")
        print(f"• Tamaño óptimo para LRU: {best_size_lru}")
        print(f"• Rendimiento mejora hasta cierto punto, luego se estabiliza")
        print(f"• Balance entre memoria usada y hit rate es crucial")

    def analyze_policy_performance(self, policy_results):
        """Analizar rendimiento de políticas"""
        print("\n🏆 ANÁLISIS DE RENDIMIENTO POR POLÍTICA")
        print("-" * 50)
        
        policy_wins = {'LRU': 0, 'LFU': 0, 'FIFO': 0}
        
        for scenario, results in policy_results.items():
            best_policy = max(results.keys(), key=lambda x: results[x]['hit_rate'])
            policy_wins[best_policy] += 1
            
            print(f"\n📊 {scenario}:")
            for policy, stats in results.items():
                marker = "🥇" if policy == best_policy else "  "
                print(f"  {marker} {policy}: {stats['hit_rate']:.2%} hit rate, "
                      f"{stats['avg_response_time']:.3f}s avg time")
        
        print(f"\n🏆 GANADOR GENERAL:")
        overall_winner = max(policy_wins.keys(), key=lambda x: policy_wins[x])
        print(f"• {overall_winner} ganó en {policy_wins[overall_winner]} de 3 escenarios")

    def generate_recommendations(self):
        """Generar recomendaciones finales"""
        print("\n" + "=" * 60)
        print("💡 RECOMENDACIONES FINALES")
        print("=" * 60)
        
        print("""
🎯 ELECCIÓN DE POLÍTICA:
• LRU: Mejor para patrones temporales claros (acceso reciente importante)
• LFU: Ideal para patrones estables con consultas muy frecuentes
• FIFO: Simple pero menos eficiente, útil cuando memoria es limitada

📊 TAMAÑO DE CACHÉ:
• Punto dulce típicamente entre 50-100 entradas para este workload
• Más allá de cierto punto, beneficios marginales decrecen
• Considerar memoria disponible vs mejora en hit rate

🚀 IMPLEMENTACIÓN RECOMENDADA:
• Usar LRU como política por defecto (balance eficiencia/simplicidad)
• Tamaño inicial: 50-75 entradas
• Monitorear hit rate y ajustar según patrones reales
• Considerar TTL para datos que pueden volverse obsoletos

⚡ OPTIMIZACIONES ADICIONALES:
• Pre-warming con consultas más frecuentes
• Cache multicapa (L1: memoria, L2: disco)
• Compresión de valores para optimizar memoria
• Métricas en tiempo real para ajuste dinámico
        """)

def main():
    """Función principal"""
    try:
        import numpy as np
    except ImportError:
        print("Instalando numpy...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np
    
    evaluator = CachePolicyEvaluator()
    evaluator.generate_comprehensive_report()
    
    print("\n✅ Análisis de políticas completado!")
    print("Este análisis proporciona base empírica para justificar decisiones de diseño.")

if __name__ == "__main__":
    main()