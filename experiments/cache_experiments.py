#!/usr/bin/env python3
"""
Experimentos para evaluar políticas de caché y parámetros del sistema
"""

import asyncio
import aiohttp
import json
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import os

class CacheExperimentRunner:
    def __init__(self):
        self.base_url = "http://localhost"
        self.generator_port = 8000
        self.cache_port = 8001
        self.storage_port = 8004
        
        # Configuraciones a probar
        self.cache_policies = ["LRU", "LFU", "FIFO"]
        self.cache_sizes = [10, 25, 50, 100, 200]
        self.ttl_values = [30, 60, 120, 300, 600]  # segundos
        self.traffic_patterns = ["uniform", "zipf", "burst"]
        
        self.results = []
        
    async def configure_cache(self, session, policy, size, ttl):
        """Configura la política de caché"""
        config_url = f"{self.base_url}:{self.cache_port}/configure"
        config_data = {
            "policy": policy,
            "max_size": size,
            "ttl": ttl
        }
        
        try:
            async with session.post(config_url, json=config_data) as response:
                return response.status == 200
        except:
            return False
    
    async def reset_cache(self, session):
        """Resetea la caché"""
        reset_url = f"{self.base_url}:{self.cache_port}/reset"
        try:
            async with session.post(reset_url) as response:
                return response.status == 200
        except:
            return False
    
    async def get_cache_stats(self, session):
        """Obtiene estadísticas de la caché"""
        stats_url = f"{self.base_url}:{self.cache_port}/stats"
        try:
            async with session.get(stats_url) as response:
                if response.status == 200:
                    return await response.json()
        except:
            pass
        return None
    
    async def generate_traffic_pattern(self, session, pattern, num_questions=100):
        """Genera tráfico según el patrón especificado"""
        
        if pattern == "uniform":
            # Tráfico uniforme - preguntas aleatorias
            for _ in range(num_questions):
                await self.send_single_question(session)
                await asyncio.sleep(0.1)
                
        elif pattern == "zipf":
            # Distribución Zipf - algunas preguntas muy frecuentes
            popular_questions = [
                "What is Python?",
                "How to learn programming?",
                "Best practices in software development?",
                "What is machine learning?",
                "How to use Docker?"
            ]
            
            for _ in range(num_questions):
                # 80% de las veces usar preguntas populares
                if np.random.random() < 0.8:
                    question = np.random.choice(popular_questions)
                    await self.send_custom_question(session, question)
                else:
                    await self.send_single_question(session)
                await asyncio.sleep(0.1)
                
        elif pattern == "burst":
            # Tráfico en ráfagas
            burst_size = 20
            for burst in range(num_questions // burst_size):
                # Ráfaga rápida
                for _ in range(burst_size):
                    await self.send_single_question(session)
                    await asyncio.sleep(0.01)
                # Pausa entre ráfagas
                await asyncio.sleep(2)
    
    async def send_single_question(self, session):
        """Envía una pregunta aleatoria"""
        url = f"{self.base_url}:{self.generator_port}/generate"
        try:
            async with session.post(url) as response:
                return response.status == 200
        except:
            return False
    
    async def send_custom_question(self, session, question):
        """Envía una pregunta personalizada"""
        url = f"{self.base_url}:{self.generator_port}/generate/custom"
        data = {"question": question}
        try:
            async with session.post(url, json=data) as response:
                return response.status == 200
        except:
            return False
    
    async def run_experiment(self, policy, cache_size, ttl, traffic_pattern, duration=300):
        """Ejecuta un experimento individual"""
        print(f"🧪 Ejecutando experimento: {policy}, tamaño={cache_size}, TTL={ttl}s, patrón={traffic_pattern}")
        
        async with aiohttp.ClientSession() as session:
            # Configurar caché
            if not await self.configure_cache(session, policy, cache_size, ttl):
                print(f"❌ Error configurando caché")
                return None
            
            # Resetear caché
            await self.reset_cache(session)
            
            # Estadísticas iniciales
            initial_stats = await self.get_cache_stats(session)
            start_time = time.time()
            
            # Generar tráfico
            num_questions = duration // 2  # Aproximadamente una pregunta cada 2 segundos
            await self.generate_traffic_pattern(session, traffic_pattern, num_questions)
            
            # Estadísticas finales
            final_stats = await self.get_cache_stats(session)
            end_time = time.time()
            
            if not final_stats:
                print(f"❌ Error obteniendo estadísticas finales")
                return None
            
            # Calcular métricas
            experiment_result = {
                'timestamp': datetime.now().isoformat(),
                'policy': policy,
                'cache_size': cache_size,
                'ttl': ttl,
                'traffic_pattern': traffic_pattern,
                'duration': end_time - start_time,
                'total_requests': final_stats.get('total_requests', 0),
                'cache_hits': final_stats.get('cache_hits', 0),
                'cache_misses': final_stats.get('cache_misses', 0),
                'hit_rate': final_stats.get('hit_rate', 0),
                'avg_response_time': final_stats.get('avg_response_time', 0),
                'memory_usage': final_stats.get('memory_usage', 0),
                'evictions': final_stats.get('evictions', 0)
            }
            
            self.results.append(experiment_result)
            print(f"✅ Completado: Hit Rate={experiment_result['hit_rate']:.2%}, Resp Time={experiment_result['avg_response_time']:.3f}s")
            
            return experiment_result
    
    async def run_all_experiments(self):
        """Ejecuta todos los experimentos"""
        print("🚀 Iniciando suite completa de experimentos de caché")
        
        total_experiments = len(self.cache_policies) * len(self.cache_sizes) * len(self.ttl_values) * len(self.traffic_patterns)
        current_experiment = 0
        
        for policy in self.cache_policies:
            for cache_size in self.cache_sizes:
                for ttl in self.ttl_values:
                    for traffic_pattern in self.traffic_patterns:
                        current_experiment += 1
                        print(f"\n📊 Experimento {current_experiment}/{total_experiments}")
                        
                        result = await self.run_experiment(policy, cache_size, ttl, traffic_pattern)
                        
                        if result:
                            # Guardar resultados incrementalmente
                            self.save_results()
                            
                        # Pausa entre experimentos
                        await asyncio.sleep(5)
        
        print(f"\n🎉 Completados {len(self.results)} experimentos exitosos")
        
    def save_results(self):
        """Guarda los resultados en un archivo JSON"""
        results_file = f"experiments/cache_experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # También guardar como CSV para análisis
        if self.results:
            df = pd.DataFrame(self.results)
            csv_file = results_file.replace('.json', '.csv')
            df.to_csv(csv_file, index=False)
    
    def generate_analysis_report(self):
        """Genera gráficos y análisis de los resultados"""
        if not self.results:
            print("❌ No hay resultados para analizar")
            return
        
        df = pd.DataFrame(self.results)
        
        # Crear directorio para gráficos
        os.makedirs('experiments/plots', exist_ok=True)
        
        # 1. Hit Rate por política de caché
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        policy_hit_rates = df.groupby('policy')['hit_rate'].mean()
        policy_hit_rates.plot(kind='bar')
        plt.title('Hit Rate Promedio por Política de Caché')
        plt.ylabel('Hit Rate')
        plt.xticks(rotation=45)
        
        # 2. Hit Rate vs Tamaño de Caché
        plt.subplot(2, 2, 2)
        for policy in self.cache_policies:
            policy_data = df[df['policy'] == policy]
            size_hit_rates = policy_data.groupby('cache_size')['hit_rate'].mean()
            plt.plot(size_hit_rates.index, size_hit_rates.values, marker='o', label=policy)
        plt.title('Hit Rate vs Tamaño de Caché')
        plt.xlabel('Tamaño de Caché')
        plt.ylabel('Hit Rate')
        plt.legend()
        
        # 3. Tiempo de Respuesta vs TTL
        plt.subplot(2, 2, 3)
        for policy in self.cache_policies:
            policy_data = df[df['policy'] == policy]
            ttl_response_times = policy_data.groupby('ttl')['avg_response_time'].mean()
            plt.plot(ttl_response_times.index, ttl_response_times.values, marker='s', label=policy)
        plt.title('Tiempo de Respuesta vs TTL')
        plt.xlabel('TTL (segundos)')
        plt.ylabel('Tiempo de Respuesta (s)')
        plt.legend()
        
        # 4. Hit Rate por Patrón de Tráfico
        plt.subplot(2, 2, 4)
        traffic_hit_rates = df.groupby('traffic_pattern')['hit_rate'].mean()
        traffic_hit_rates.plot(kind='bar', color=['skyblue', 'orange', 'lightgreen'])
        plt.title('Hit Rate por Patrón de Tráfico')
        plt.ylabel('Hit Rate')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('experiments/plots/cache_analysis_overview.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Análisis detallado por política
        self.generate_detailed_analysis(df)
    
    def generate_detailed_analysis(self, df):
        """Genera análisis detallado por política"""
        
        for policy in self.cache_policies:
            policy_data = df[df['policy'] == policy]
            
            plt.figure(figsize=(15, 10))
            
            # Hit Rate heatmap por tamaño y TTL
            plt.subplot(2, 3, 1)
            pivot_hit_rate = policy_data.pivot_table(values='hit_rate', 
                                                   index='cache_size', 
                                                   columns='ttl', 
                                                   aggfunc='mean')
            plt.imshow(pivot_hit_rate.values, cmap='YlOrRd', aspect='auto')
            plt.colorbar(label='Hit Rate')
            plt.title(f'{policy} - Hit Rate\n(Tamaño vs TTL)')
            plt.xlabel('TTL')
            plt.ylabel('Tamaño de Caché')
            
            # Tiempo de respuesta heatmap
            plt.subplot(2, 3, 2)
            pivot_response_time = policy_data.pivot_table(values='avg_response_time', 
                                                        index='cache_size', 
                                                        columns='ttl', 
                                                        aggfunc='mean')
            plt.imshow(pivot_response_time.values, cmap='YlOrRd', aspect='auto')
            plt.colorbar(label='Response Time (s)')
            plt.title(f'{policy} - Tiempo de Respuesta\n(Tamaño vs TTL)')
            plt.xlabel('TTL')
            plt.ylabel('Tamaño de Caché')
            
            # Evictions por tamaño
            plt.subplot(2, 3, 3)
            evictions_by_size = policy_data.groupby('cache_size')['evictions'].mean()
            evictions_by_size.plot(kind='bar')
            plt.title(f'{policy} - Evictions por Tamaño')
            plt.xlabel('Tamaño de Caché')
            plt.ylabel('Evictions Promedio')
            
            # Hit rate por patrón de tráfico
            plt.subplot(2, 3, 4)
            traffic_analysis = policy_data.groupby('traffic_pattern')['hit_rate'].mean()
            traffic_analysis.plot(kind='bar', color=['lightblue', 'lightcoral', 'lightgreen'])
            plt.title(f'{policy} - Hit Rate por Patrón')
            plt.xlabel('Patrón de Tráfico')
            plt.ylabel('Hit Rate')
            plt.xticks(rotation=45)
            
            # Memoria vs Hit Rate
            plt.subplot(2, 3, 5)
            plt.scatter(policy_data['memory_usage'], policy_data['hit_rate'], alpha=0.6)
            plt.title(f'{policy} - Memoria vs Hit Rate')
            plt.xlabel('Uso de Memoria')
            plt.ylabel('Hit Rate')
            
            # Throughput analysis
            plt.subplot(2, 3, 6)
            policy_data['throughput'] = policy_data['total_requests'] / policy_data['duration']
            throughput_by_size = policy_data.groupby('cache_size')['throughput'].mean()
            throughput_by_size.plot(kind='line', marker='o')
            plt.title(f'{policy} - Throughput por Tamaño')
            plt.xlabel('Tamaño de Caché')
            plt.ylabel('Requests/segundo')
            
            plt.tight_layout()
            plt.savefig(f'experiments/plots/{policy.lower()}_detailed_analysis.png', 
                       dpi=300, bbox_inches='tight')
            plt.show()

async def main():
    """Función principal"""
    runner = CacheExperimentRunner()
    
    print("🎯 Iniciando experimentos de evaluación de caché")
    print(f"📊 Se ejecutarán {len(runner.cache_policies) * len(runner.cache_sizes) * len(runner.ttl_values) * len(runner.traffic_patterns)} experimentos")
    
    # Ejecutar experimentos
    await runner.run_all_experiments()
    
    # Generar análisis
    print("\n📈 Generando análisis y gráficos...")
    runner.generate_analysis_report()
    
    print("\n✅ Experimentos completados. Resultados guardados en experiments/")

if __name__ == "__main__":
    asyncio.run(main())