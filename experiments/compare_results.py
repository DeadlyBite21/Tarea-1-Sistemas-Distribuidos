#!/usr/bin/env python3
"""
Comparador de Resultados - Experimentos de Cache
Une y compara los resultados de LRU, LFU y FIFO
"""

import json
import sys
import os
from datetime import datetime

def load_results(filename):
    """Carga resultados desde archivo JSON"""
    try:
        # Buscar en directorio results primero
        results_path = f"results/{filename}"
        if os.path.exists(results_path):
            filepath = results_path
        else:
            filepath = filename
            
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Archivo {filename} no encontrado en results/ ni en directorio actual")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error leyendo archivo {filename}")
        return None

def format_duration(minutes):
    """Formatea duración en formato legible"""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

def compare_results():
    """Compara los resultados de los tres experimentos"""
    
    print("🔄 CARGANDO RESULTADOS DE EXPERIMENTOS...")
    
    # Cargar resultados
    lru_results = load_results("lru_results.json")
    lfu_results = load_results("lfu_results.json")
    fifo_results = load_results("fifo_results.json")
    
    results = {}
    if lru_results:
        results["LRU"] = lru_results
        print("✅ Resultados LRU cargados")
    if lfu_results:
        results["LFU"] = lfu_results
        print("✅ Resultados LFU cargados")
    if fifo_results:
        results["FIFO"] = fifo_results
        print("✅ Resultados FIFO cargados")
    
    if not results:
        print("❌ No se encontraron archivos de resultados")
        print("📋 Asegúrate de que existan:")
        print("   • lru_results.json")
        print("   • lfu_results.json")
        print("   • fifo_results.json")
        return
    
    print(f"\n{'='*100}")
    print(f"🏆 COMPARACIÓN FINAL - EXPERIMENTOS DE CACHE 10,000 PREGUNTAS")
    print(f"{'='*100}")
    
    # Tabla de comparación
    print(f"\n📊 RESUMEN COMPARATIVO:")
    print(f"{'Política':<8} {'Hit Rate':<10} {'Hits':<8} {'Misses':<8} {'Evictions':<10} {'Cache Size':<10} {'Duración':<12}")
    print(f"{'-'*80}")
    
    best_policy = None
    best_hit_rate = 0
    
    for policy, stats in results.items():
        hit_rate = stats.get('hit_rate', 0)
        hits = stats.get('cache_hits', 0)
        misses = stats.get('cache_misses', 0)
        evictions = stats.get('evictions', 0)
        cache_size = stats.get('current_size', 0)
        
        # Obtener duración desde metadata si existe
        duration = "N/A"
        if 'experiment_metadata' in stats:
            duration_min = stats['experiment_metadata'].get('duration_minutes', 0)
            duration = format_duration(duration_min)
        
        print(f"{policy:<8} {hit_rate:<9.2%} {hits:<8,} {misses:<8,} {evictions:<10,} {cache_size:<10} {duration:<12}")
        
        if hit_rate > best_hit_rate:
            best_hit_rate = hit_rate
            best_policy = policy
    
    # Ganador
    if best_policy:
        print(f"\n🥇 POLÍTICA GANADORA: {best_policy}")
        winner_stats = results[best_policy]
        print(f"   • Hit Rate: {best_hit_rate:.2%}")
        print(f"   • Cache Hits: {winner_stats.get('cache_hits', 0):,}")
        print(f"   • Evictions: {winner_stats.get('evictions', 0):,}")
        
        if 'experiment_metadata' in winner_stats:
            metadata = winner_stats['experiment_metadata']
            print(f"   • Preguntas procesadas: {metadata.get('questions_processed', 0):,}")
            print(f"   • Tiempo total: {format_duration(metadata.get('duration_minutes', 0))}")
    
    # Análisis detallado
    print(f"\n📈 ANÁLISIS DETALLADO:")
    
    for policy, stats in results.items():
        print(f"\n🔍 {policy}:")
        print(f"   📊 Métricas de Rendimiento:")
        print(f"      • Total requests: {stats.get('total_requests', 0):,}")
        print(f"      • Hit rate: {stats.get('hit_rate', 0):.3%}")
        print(f"      • Avg response time: {stats.get('avg_response_time', 0):.4f}s")
        print(f"      • Memory usage: {stats.get('memory_usage', 0)}")
        
        if 'experiment_metadata' in stats:
            metadata = stats['experiment_metadata']
            print(f"   ⏱️ Información del Experimento:")
            print(f"      • Inicio: {metadata.get('start_time', 'N/A')}")
            print(f"      • Fin: {metadata.get('end_time', 'N/A')}")
            print(f"      • Duración: {format_duration(metadata.get('duration_minutes', 0))}")
            print(f"      • Cache size configurado: {metadata.get('cache_size', 0)}")
            print(f"      • TTL: {metadata.get('ttl', 0)}s")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    
    if len(results) >= 3:
        lru_hit = results.get("LRU", {}).get('hit_rate', 0)
        lfu_hit = results.get("LFU", {}).get('hit_rate', 0)
        fifo_hit = results.get("FIFO", {}).get('hit_rate', 0)
        
        if lfu_hit > lru_hit and lfu_hit > fifo_hit:
            print("   🎯 LFU es la mejor opción para este dataset")
            print("   📋 Razón: Aprovecha mejor la frecuencia de acceso de preguntas populares")
        elif lru_hit > lfu_hit and lru_hit > fifo_hit:
            print("   🎯 LRU es la mejor opción para este dataset")
            print("   📋 Razón: Buen balance entre recencia y frecuencia")
        elif fifo_hit > 0:
            print("   🎯 FIFO muestra rendimiento básico")
            print("   📋 Razón: Simple pero menos eficiente para patrones de acceso")
        else:
            print("   ⚠️ Todas las políticas muestran hit rates bajos")
            print("   📋 Considerar: Mayor tamaño de cache o ajuste de TTL")
    
    # Guardar reporte comparativo
    comparison_report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'best_policy': best_policy,
            'best_hit_rate': best_hit_rate,
            'total_experiments': len(results)
        },
        'detailed_results': results
    }
    
    try:
        os.makedirs("results", exist_ok=True)
        report_path = "results/comparison_report.json"
        with open(report_path, 'w') as f:
            json.dump(comparison_report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Reporte completo guardado en '{report_path}'")
    except Exception as e:
        print(f"❌ Error guardando reporte: {e}")
    
    print(f"\n🎉 ANÁLISIS COMPLETADO")

def main():
    print("🔍 COMPARADOR DE RESULTADOS - EXPERIMENTOS DE CACHE")
    print("📋 Este script compara los resultados de LRU, LFU y FIFO")
    print("📁 Busca archivos: lru_results.json, lfu_results.json, fifo_results.json")
    
    compare_results()

if __name__ == "__main__":
    main()