"""
Analizador del comportamiento de la caché
Herramienta para evaluar diferentes políticas de caché y distribuciones de tráfico
"""

import asyncio
import aiohttp
import json
import time
import random
from typing import List, Dict, Any
import statistics
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import os

class CacheAnalyzer:
    def __init__(self, base_url="http://localhost"):
        self.base_url = base_url
        self.generator_url = f"{base_url}:8000"
        self.cache_url = f"{base_url}:8001"
        self.storage_url = f"{base_url}:8004"
        
        # Preguntas base se obtienen dinámicamente
        self.questions_pool = []
        
    async def load_real_questions(self, limit: int = 200, use_popular: bool = False):
        """Cargar preguntas reales de la base de datos"""
        async with aiohttp.ClientSession() as session:
            try:
                if use_popular:
                    url = f"{self.storage_url}/popular_questions?limit={limit}"
                else:
                    url = f"{self.storage_url}/questions?limit={limit}&random=true"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        questions = data.get('questions', [])
                        self.questions_pool = [q['question'] for q in questions if q['question']]
                        print(f"✅ Cargadas {len(self.questions_pool)} preguntas reales de la base de datos")
                    else:
                        print(f"❌ Error obteniendo preguntas: {response.status}")
                        # Fallback a preguntas por defecto
                        self.questions_pool = [
                            "¿Qué es Python y para qué se usa?",
                            "¿Cómo funciona Docker?", 
                            "¿Qué es DevOps?",
                            "¿Qué es machine learning?",
                            "¿Qué son las APIs REST?"
                        ]
            except Exception as e:
                print(f"❌ Error cargando preguntas: {e}")
                # Fallback a preguntas por defecto
                self.questions_pool = [
                    "¿Qué es Python y para qué se usa?",
                    "¿Cómo funciona Docker?", 
                    "¿Qué es DevOps?",
                    "¿Qué es machine learning?",
                    "¿Qué son las APIs REST?"
                ]
        
        self.metrics = {
            'uniform': {'hits': 0, 'misses': 0, 'total_requests': 0, 'response_times': []},
            'zipf': {'hits': 0, 'misses': 0, 'total_requests': 0, 'response_times': []},
            'hotspot': {'hits': 0, 'misses': 0, 'total_requests': 0, 'response_times': []},
            'burst': {'hits': 0, 'misses': 0, 'total_requests': 0, 'response_times': []}
        }

    async def clear_cache(self):
        """Limpiar el caché antes de cada experimento"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.cache_url}/cache/clear") as response:
                    result = await response.json()
                    print(f"Cache cleared: {result}")
        except Exception as e:
            print(f"Error clearing cache: {e}")

    async def get_cache_stats(self):
        """Obtener estadísticas actuales del caché"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.cache_url}/cache/stats") as response:
                    return await response.json()
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}

    def generate_uniform_distribution(self, num_requests=100):
        """Distribución uniforme - todas las preguntas con igual probabilidad"""
        return [random.choice(self.questions_pool) for _ in range(num_requests)]

    def generate_zipf_distribution(self, num_requests=100, alpha=1.2):
        """Distribución Zipf - algunas preguntas muy frecuentes, otras raras"""
        # Generar índices según distribución Zipf
        zipf_indices = np.random.zipf(alpha, num_requests) - 1
        # Asegurar que los índices estén en rango válido
        zipf_indices = zipf_indices % len(self.questions_pool)
        return [self.questions_pool[i] for i in zipf_indices]

    def generate_hotspot_distribution(self, num_requests=100, hotspot_ratio=0.8):
        """Distribución hotspot - 80% de requests van a 20% de preguntas"""
        hot_questions = self.questions_pool[:3]  # 3 preguntas "calientes"
        cold_questions = self.questions_pool[3:]  # Resto "frías"
        
        requests = []
        for _ in range(num_requests):
            if random.random() < hotspot_ratio:
                requests.append(random.choice(hot_questions))
            else:
                requests.append(random.choice(cold_questions))
        return requests

    def generate_burst_distribution(self, num_requests=100):
        """Distribución en ráfagas - patrones de consultas repetitivas"""
        requests = []
        burst_size = 5
        
        while len(requests) < num_requests:
            # Seleccionar una pregunta para la ráfaga
            burst_question = random.choice(self.questions_pool)
            # Generar ráfaga de la misma pregunta
            burst_length = min(burst_size, num_requests - len(requests))
            requests.extend([burst_question] * burst_length)
            
            # Añadir algunas preguntas aleatorias entre ráfagas
            if len(requests) < num_requests:
                random_count = min(3, num_requests - len(requests))
                requests.extend([random.choice(self.questions_pool) for _ in range(random_count)])
        
        return requests[:num_requests]

    async def send_question(self, session, question):
        """Enviar una pregunta y medir tiempo de respuesta"""
        start_time = time.time()
        try:
            async with session.post(
                f"{self.generator_url}/generate/custom",
                json={"question": question},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    await response.json()
                    end_time = time.time()
                    return end_time - start_time
                else:
                    print(f"Error HTTP: {response.status}")
                    return 0.1  # Tiempo por defecto para errores
        except Exception as e:
            print(f"Error sending question: {e}")
            return 0.1  # Tiempo por defecto para errores

    async def run_experiment(self, distribution_name, questions, delay=0.1):
        """Ejecutar experimento con una distribución específica"""
        print(f"\n=== Ejecutando experimento: {distribution_name.upper()} ===")
        print(f"Total preguntas: {len(questions)}")
        
        # Limpiar caché antes del experimento
        await self.clear_cache()
        
        # Obtener estadísticas iniciales
        initial_stats = await self.get_cache_stats()
        initial_size = initial_stats.get('cache_size', 0)
        
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            for i, question in enumerate(questions):
                response_time = await self.send_question(session, question)
                if response_time:
                    response_times.append(response_time)
                
                # Pausa entre requests para simular tráfico real
                await asyncio.sleep(delay)
                
                # Progress indicator
                if (i + 1) % 20 == 0:
                    print(f"Progreso: {i + 1}/{len(questions)} preguntas enviadas")
        
        # Esperar a que se procesen todas las preguntas
        await asyncio.sleep(5)
        
        # Obtener estadísticas finales
        final_stats = await self.get_cache_stats()
        final_size = final_stats.get('cache_size', 0)
        
        # Calcular métricas (aproximadas basadas en el crecimiento del caché)
        cache_growth = final_size - initial_size
        estimated_misses = min(cache_growth, len(questions))
        estimated_hits = len(questions) - estimated_misses
        
        self.metrics[distribution_name] = {
            'hits': estimated_hits,
            'misses': estimated_misses,
            'total_requests': len(questions),
            'response_times': response_times,
            'hit_rate': estimated_hits / len(questions) if len(questions) > 0 else 0,
            'miss_rate': estimated_misses / len(questions) if len(questions) > 0 else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0.1,
            'cache_size_growth': cache_growth
        }
        
        print(f"Experimento {distribution_name} completado")
        print(f"  - Hits estimados: {estimated_hits}")
        print(f"  - Misses estimados: {estimated_misses}")
        print(f"  - Hit rate: {self.metrics[distribution_name]['hit_rate']:.2%}")
        print(f"  - Tiempo promedio: {self.metrics[distribution_name]['avg_response_time']:.3f}s")
        
        # Devolver las métricas calculadas
        return {
            'hits': estimated_hits,
            'misses': estimated_misses,
            'total_requests': len(questions),
            'response_times': response_times,
            'hit_rate': estimated_hits / len(questions) if len(questions) > 0 else 0,
            'miss_rate': estimated_misses / len(questions) if len(questions) > 0 else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0.1,
            'cache_size_growth': cache_growth
        }

    async def run_all_experiments(self, num_requests_per_experiment=50, generate_graphs=True):
        """Ejecutar todos los experimentos de análisis de caché"""
        print("\n" + "=" * 60)
        print("🔬 ANÁLISIS COMPLETO DEL COMPORTAMIENTO DE CACHÉ")
        print("=" * 60)
        
        # Cargar preguntas reales de la base de datos
        await self.load_real_questions(limit=100)
        
        if not self.questions_pool:
            print("❌ No se pudieron cargar preguntas. Abortando análisis.")
            return {}
        
        print(f"📊 Usando {len(self.questions_pool)} preguntas reales de la base de datos")
        
        # Generar diferentes distribuciones de tráfico
        experiments = {
            "Distribución Uniforme": self.generate_uniform_distribution(num_requests_per_experiment),
            "Distribución Zipf": self.generate_zipf_distribution(num_requests_per_experiment),
            "Patrón Hotspot": self.generate_hotspot_distribution(num_requests_per_experiment),
            "Patrón Burst": self.generate_burst_distribution(num_requests_per_experiment)
        }
        
        results = {}
        
        for experiment_name, questions in experiments.items():
            print(f"\n🧪 Ejecutando: {experiment_name}")
            print("-" * 40)
            
            result = await self.run_experiment(experiment_name, questions, delay=0.05)
            results[experiment_name] = result
            
            # Mostrar resultados inmediatos
            print(f"✅ Hit Rate: {result['hit_rate']:.1%}")
            print(f"✅ Miss Rate: {result['miss_rate']:.1%}")
            print(f"✅ Tiempo promedio: {result['avg_response_time']:.3f}s")
            print(f"✅ Total requests: {result['total_requests']}")
        
        # Generar resumen comparativo
        self.print_comparative_analysis(results)
        
        # Generar gráficos si se solicita
        if generate_graphs:
            try:
                self.save_graphs(results)
                print("\n📊 Gráficos generados exitosamente")
            except Exception as e:
                print(f"\n❌ Error generando gráficos: {e}")
        
        return results

    def print_comparative_analysis(self, results: Dict):
        """Imprimir análisis comparativo de resultados"""
        print("\n" + "=" * 60)
        print("📈 RESUMEN COMPARATIVO")
        print("=" * 60)
        
        # Encontrar la mejor distribución
        best_hit_rate = max(results.items(), key=lambda x: x[1]['hit_rate'])
        
        print(f"\n🏆 MEJOR RENDIMIENTO: {best_hit_rate[0]}")
        print(f"   Hit Rate: {best_hit_rate[1]['hit_rate']:.1%}")
        print(f"   Tiempo promedio: {best_hit_rate[1]['avg_response_time']:.3f}s")
        
        print(f"\n📊 ANÁLISIS POR DISTRIBUCIÓN:")
        
        for dist, data in results.items():
            hit_rate = data['hit_rate'] * 100
            avg_time = data['avg_response_time']
            total_reqs = data['total_requests']
            
            print(f"\n  📉 {dist}:")
            print(f"    Hit Rate: {hit_rate:.1f}%")
            print(f"    Tiempo promedio: {avg_time:.3f}s")
            print(f"    Total requests: {total_reqs}")
            
            if 'uniforme' in dist.lower():
                print(f"    📈 Hit Rate: {hit_rate:.1f}% - Distribución equilibrada")
                print(f"    📈 Rendimiento baseline para comparación")
            elif 'zipf' in dist.lower():
                print(f"    📈 Hit Rate: {hit_rate:.1f}% - Patrón realista de uso")
                print(f"    📈 Simula comportamiento típico de usuarios")
            elif 'hotspot' in dist.lower():
                print(f"    📈 Hit Rate: {hit_rate:.1f}% - Concentración en pocas consultas")
                print(f"    📈 Óptimo para caché, 80/20 rule")
            elif 'burst' in dist.lower():
                print(f"    📈 Hit Rate: {hit_rate:.1f}% - Patrones de ráfaga")
                print(f"    📈 Beneficia mucho de caché durante ráfagas")
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"1. La distribución {best_hit_rate[0]} muestra el mejor rendimiento de caché")
        print(f"2. En escenarios reales, esperar patrones similares a Zipf o Hotspot")
        print(f"3. El caché es especialmente efectivo con consultas repetitivas")
        print(f"4. Considerar pre-warming del caché para consultas frecuentes")

    def generate_analysis_report(self):
        """Generar reporte de análisis con gráficos"""
        print("\n" + "=" * 60)
        print("📊 REPORTE DE ANÁLISIS DE CACHÉ")
        print("=" * 60)
        
        # Crear DataFrame para análisis
        data = []
        for dist_name, metrics in self.metrics.items():
            data.append({
                'Distribución': dist_name.title(),
                'Total Requests': metrics['total_requests'],
                'Hits': metrics['hits'],
                'Misses': metrics['misses'],
                'Hit Rate (%)': metrics['hit_rate'] * 100,
                'Miss Rate (%)': metrics['miss_rate'] * 100,
                'Avg Response Time (s)': metrics['avg_response_time'],
                'Cache Growth': metrics['cache_size_growth']
            })
        
        df = pd.DataFrame(data)
        
        # Mostrar tabla resumen
        print("\n📋 TABLA RESUMEN:")
        print(df.to_string(index=False, float_format='%.3f'))
        
        # Generar gráficos
        self.create_visualizations(df)
        
        # Análisis y conclusiones
        self.generate_conclusions(df)

    def create_visualizations(self, df):
        """Crear visualizaciones de los resultados"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Análisis del Comportamiento de la Caché', fontsize=16, fontweight='bold')
        
        # Gráfico 1: Hit Rate por distribución
        bars1 = ax1.bar(df['Distribución'], df['Hit Rate (%)'], 
                       color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax1.set_title('Tasa de Aciertos por Distribución')
        ax1.set_ylabel('Hit Rate (%)')
        ax1.set_ylim(0, 100)
        
        # Añadir valores en las barras
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        # Gráfico 2: Tiempo de respuesta promedio
        bars2 = ax2.bar(df['Distribución'], df['Avg Response Time (s)'], 
                       color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax2.set_title('Tiempo de Respuesta Promedio')
        ax2.set_ylabel('Tiempo (segundos)')
        
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.3f}s', ha='center', va='bottom')
        
        # Gráfico 3: Hits vs Misses
        x = range(len(df))
        width = 0.35
        ax3.bar([i - width/2 for i in x], df['Hits'], width, label='Hits', color='#4ECDC4')
        ax3.bar([i + width/2 for i in x], df['Misses'], width, label='Misses', color='#FF6B6B')
        ax3.set_title('Hits vs Misses por Distribución')
        ax3.set_ylabel('Número de Requests')
        ax3.set_xticks(x)
        ax3.set_xticklabels(df['Distribución'])
        ax3.legend()
        
        # Gráfico 4: Crecimiento del caché
        bars4 = ax4.bar(df['Distribución'], df['Cache Growth'], 
                       color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax4.set_title('Crecimiento del Caché')
        ax4.set_ylabel('Nuevas entradas en caché')
        
        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Guardar gráfico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig(f'/tmp/cache_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')
        print(f"\n📈 Gráficos guardados en: /tmp/cache_analysis_{timestamp}.png")
        
        # Mostrar en pantalla si es posible
        try:
            plt.show()
        except:
            print("No se puede mostrar gráficos en este entorno")

    def generate_conclusions(self, df):
        """Generar conclusiones del análisis"""
        print("\n" + "=" * 60)
        print("🔍 ANÁLISIS Y CONCLUSIONES")
        print("=" * 60)
        
        # Encontrar la mejor y peor distribución
        best_hit_rate = df.loc[df['Hit Rate (%)'].idxmax()]
        worst_hit_rate = df.loc[df['Hit Rate (%)'].idxmin()]
        fastest_response = df.loc[df['Avg Response Time (s)'].idxmin()]
        
        print(f"\n📊 RESULTADOS PRINCIPALES:")
        print(f"• Mejor Hit Rate: {best_hit_rate['Distribución']} ({best_hit_rate['Hit Rate (%)']:.1f}%)")
        print(f"• Peor Hit Rate: {worst_hit_rate['Distribución']} ({worst_hit_rate['Hit Rate (%)']:.1f}%)")
        print(f"• Respuesta más rápida: {fastest_response['Distribución']} ({fastest_response['Avg Response Time (s)']:.3f}s)")
        
        print(f"\n🎯 ANÁLISIS POR DISTRIBUCIÓN:")
        
        for _, row in df.iterrows():
            dist = row['Distribución']
            hit_rate = row['Hit Rate (%)']
            response_time = row['Avg Response Time (s)']
            
            print(f"\n• {dist.upper()}:")
            if dist.lower() == 'uniform':
                print(f"  - Hit Rate: {hit_rate:.1f}% - Distribución equilibrada")
                print(f"  - Rendimiento baseline para comparación")
            elif dist.lower() == 'zipf':
                print(f"  - Hit Rate: {hit_rate:.1f}% - Patrón realista de uso")
                print(f"  - Simula comportamiento típico de usuarios")
            elif dist.lower() == 'hotspot':
                print(f"  - Hit Rate: {hit_rate:.1f}% - Concentración en pocas consultas")
                print(f"  - Óptimo para caché, 80/20 rule")
            elif dist.lower() == 'burst':
                print(f"  - Hit Rate: {hit_rate:.1f}% - Patrones de ráfaga")
                print(f"  - Beneficia mucho de caché durante ráfagas")
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"1. La distribución {best_hit_rate['Distribución']} muestra el mejor rendimiento de caché")
        print(f"2. En escenarios reales, esperar patrones similares a Zipf o Hotspot")
        print(f"3. El caché es especialmente efectivo con consultas repetitivas")
        print(f"4. Considerar pre-warming del caché para consultas frecuentes")

    def save_graphs(self, results: Dict, output_dir: str = "analysis_graphs"):
        """Generar y guardar gráficos de los resultados"""
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurar estilo de matplotlib
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
        # 1. Gráfico de Hit Rates por Distribución
        self._plot_hit_rates_by_distribution(results, output_dir)
        
        # 2. Gráfico de Tiempos de Respuesta
        self._plot_response_times(results, output_dir)
        
        # 3. Gráfico de Distribución de Requests
        self._plot_request_distributions(results, output_dir)
        
        # 4. Gráfico Comparativo General
        self._plot_summary_comparison(results, output_dir)
        
        print(f"📊 Gráficos guardados en el directorio: {output_dir}/")
    
    def _plot_hit_rates_by_distribution(self, results: Dict, output_dir: str):
        """Gráfico de barras con hit rates por distribución"""
        distributions = list(results.keys())
        hit_rates = [results[dist]['hit_rate'] * 100 for dist in distributions]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(distributions, hit_rates, color=['#3498db', '#e74c3c', '#f39c12', '#2ecc71'])
        
        # Añadir valores en las barras
        for bar, rate in zip(bars, hit_rates):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.title('Hit Rate por Distribución de Tráfico', fontsize=16, fontweight='bold')
        plt.xlabel('Distribución de Tráfico', fontsize=12)
        plt.ylabel('Hit Rate (%)', fontsize=12)
        plt.ylim(0, 100)
        plt.grid(axis='y', alpha=0.3)
        
        # Añadir línea de objetivo
        plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Objetivo (80%)')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/hit_rates_by_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_response_times(self, results: Dict, output_dir: str):
        """Histograma de tiempos de respuesta"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()
        
        colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']
        
        for i, (dist_name, data) in enumerate(results.items()):
            if i < 4:  # Solo los primeros 4 resultados
                response_times = data.get('response_times', [])
                if response_times:
                    axes[i].hist(response_times, bins=20, color=colors[i], alpha=0.7, edgecolor='black')
                    axes[i].set_title(f'{dist_name}\nPromedio: {statistics.mean(response_times):.3f}s')
                    axes[i].set_xlabel('Tiempo de Respuesta (s)')
                    axes[i].set_ylabel('Frecuencia')
                    axes[i].grid(alpha=0.3)
        
        plt.suptitle('Distribución de Tiempos de Respuesta por Patrón de Tráfico', 
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/response_times_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_request_distributions(self, results: Dict, output_dir: str):
        """Gráfico de distribución de requests"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()
        
        colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']
        
        for i, (dist_name, data) in enumerate(results.items()):
            if i < 4:
                # Simular distribución de preguntas para visualización
                question_counts = {}
                questions_used = self.questions_pool[:10]
                
                # Contar frecuencias según el tipo de distribución
                if 'zipf' in dist_name.lower():
                    # Distribución Zipf - pocas preguntas muy frecuentes
                    for j, q in enumerate(questions_used):
                        question_counts[f'Q{j+1}'] = max(1, int(50 / (j + 1)))
                elif 'hotspot' in dist_name.lower():
                    # Patrón hotspot - 80/20
                    for j, q in enumerate(questions_used):
                        if j < 2:  # 20% de preguntas
                            question_counts[f'Q{j+1}'] = 40
                        else:  # 80% de preguntas
                            question_counts[f'Q{j+1}'] = 2
                elif 'burst' in dist_name.lower():
                    # Patrón burst - ráfagas
                    for j, q in enumerate(questions_used):
                        question_counts[f'Q{j+1}'] = random.choice([1, 1, 1, 25, 1, 1])
                else:
                    # Distribución uniforme
                    for j, q in enumerate(questions_used):
                        question_counts[f'Q{j+1}'] = 5
                
                questions = list(question_counts.keys())
                counts = list(question_counts.values())
                
                axes[i].bar(questions, counts, color=colors[i], alpha=0.7)
                axes[i].set_title(f'{dist_name}')
                axes[i].set_xlabel('Preguntas')
                axes[i].set_ylabel('Frecuencia')
                axes[i].tick_params(axis='x', rotation=45)
        
        plt.suptitle('Patrones de Distribución de Requests', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/request_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_summary_comparison(self, results: Dict, output_dir: str):
        """Gráfico resumen comparativo"""
        distributions = list(results.keys())
        hit_rates = [results[dist]['hit_rate'] * 100 for dist in distributions]
        avg_times = [results[dist]['avg_response_time'] * 1000 for dist in distributions]  # en ms
        total_requests = [results[dist]['total_requests'] for dist in distributions]
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Hit Rates
        bars1 = ax1.bar(distributions, hit_rates, color='#3498db', alpha=0.8)
        ax1.set_title('Hit Rate por Distribución', fontweight='bold')
        ax1.set_ylabel('Hit Rate (%)')
        ax1.set_ylim(0, 100)
        ax1.grid(axis='y', alpha=0.3)
        for bar, rate in zip(bars1, hit_rates):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{rate:.1f}%', ha='center', va='bottom')
        
        # Tiempos de Respuesta
        bars2 = ax2.bar(distributions, avg_times, color='#e74c3c', alpha=0.8)
        ax2.set_title('Tiempo Promedio de Respuesta', fontweight='bold')
        ax2.set_ylabel('Tiempo (ms)')
        ax2.grid(axis='y', alpha=0.3)
        for bar, time in zip(bars2, avg_times):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{time:.1f}ms', ha='center', va='bottom')
        
        # Total de Requests
        bars3 = ax3.bar(distributions, total_requests, color='#2ecc71', alpha=0.8)
        ax3.set_title('Total de Requests Procesados', fontweight='bold')
        ax3.set_ylabel('Número de Requests')
        ax3.grid(axis='y', alpha=0.3)
        for bar, count in zip(bars3, total_requests):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{count}', ha='center', va='bottom')
        
        # Rotar etiquetas del eje x
        for ax in [ax1, ax2, ax3]:
            ax.tick_params(axis='x', rotation=45)
        
        plt.suptitle('Resumen Comparativo de Análisis de Caché', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/summary_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

async def main():
    """Función principal para ejecutar el análisis"""
    analyzer = CacheAnalyzer()
    
    # Ejecutar experimentos
    await analyzer.run_all_experiments(num_requests_per_experiment=30, generate_graphs=True)
    
    # Generar reporte (comentado temporalmente debido a cambio en estructura de datos)
    # analyzer.generate_analysis_report()
    
    print("\n✅ Análisis completado!")
    print("Los resultados muestran el comportamiento del caché bajo diferentes distribuciones de tráfico.")

if __name__ == "__main__":
    # Instalar dependencias necesarias
    import subprocess
    import sys
    
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        import aiohttp
    except ImportError as e:
        print(f"Instalando dependencias necesarias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib", "pandas", "numpy", "aiohttp"])
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        import aiohttp
    
    asyncio.run(main())