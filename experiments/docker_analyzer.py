#!/usr/bin/env python3
"""
📊 ANALIZADOR DE LOGS DOCKERIZADOS
Extrae y visualiza métricas de los logs de Docker en tiempo real
"""

import subprocess
import re
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import os

def extract_docker_metrics():
    """Extrae métricas de todos los servicios"""
    services = ['cache', 'generator', 'llm', 'storage', 'score']
    all_metrics = {}
    
    for service in services:
        print(f"🔍 Analizando logs de {service}...")
        try:
            # Obtener logs recientes
            result = subprocess.run(
                ["docker-compose", "logs", "--tail", "500", service],
                capture_output=True,
                text=True,
                check=True
            )
            
            metrics = parse_service_logs(service, result.stdout)
            all_metrics[service] = metrics
            
        except subprocess.CalledProcessError:
            print(f"⚠️ No se pudieron obtener logs de {service}")
            all_metrics[service] = {}
    
    return all_metrics

def parse_service_logs(service, logs):
    """Parsea logs específicos por servicio"""
    metrics = {
        'total_lines': 0,
        'events': [],
        'errors': 0,
        'info_messages': 0,
        'warnings': 0
    }
    
    cache_hits = 0
    cache_misses = 0
    questions_sent = 0
    responses_received = 0
    
    for line in logs.split('\\n'):
        if not line.strip():
            continue
            
        metrics['total_lines'] += 1
        
        # Contar tipos de mensajes
        if 'ERROR' in line:
            metrics['errors'] += 1
        elif 'INFO' in line:
            metrics['info_messages'] += 1
        elif 'WARN' in line:
            metrics['warnings'] += 1
        
        # Análisis específico por servicio
        if service == 'cache':
            if 'Cache hit para pregunta' in line:
                cache_hits += 1
            elif 'Pregunta no encontrada en cache' in line:
                cache_misses += 1
            elif 'Respuesta cacheada' in line:
                responses_received += 1
                
        elif service == 'generator':
            if 'Pregunta personalizada enviada' in line or 'Pregunta enviada' in line:
                questions_sent += 1
                
        elif service == 'llm':
            if 'Procesando pregunta' in line:
                responses_received += 1
    
    # Métricas específicas
    if service == 'cache':
        total_cache_requests = cache_hits + cache_misses
        hit_rate = (cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        metrics.update({
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'total_cache_requests': total_cache_requests,
            'hit_rate': hit_rate
        })
    
    elif service == 'generator':
        metrics.update({
            'questions_sent': questions_sent
        })
        
    elif service == 'llm':
        metrics.update({
            'responses_generated': responses_received
        })
    
    return metrics

def create_service_analysis_plot(all_metrics, output_dir='plots'):
    """Crea análisis visual de todos los servicios"""
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Docker Services Analysis - Real-time Metrics', fontsize=16, fontweight='bold')
    
    # 1. Actividad por servicio
    ax1 = axes[0, 0]
    services = list(all_metrics.keys())
    activity_counts = [all_metrics[s].get('total_lines', 0) for s in services]
    
    bars1 = ax1.bar(services, activity_counts, color=['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6'])
    ax1.set_title('Log Activity by Service')
    ax1.set_ylabel('Number of Log Lines')
    
    for bar, count in zip(bars1, activity_counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(activity_counts)*0.01,
                f'{count:,}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Cache Performance (si disponible)
    ax2 = axes[0, 1]
    if 'cache' in all_metrics and all_metrics['cache'].get('total_cache_requests', 0) > 0:
        cache_data = all_metrics['cache']
        hits = cache_data.get('cache_hits', 0)
        misses = cache_data.get('cache_misses', 0)
        
        labels = ['Cache Hits', 'Cache Misses']
        sizes = [hits, misses]
        colors = ['#2ecc71', '#e74c3c']
        
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors, 
                                          autopct='%1.1f%%', startangle=90)
        ax2.set_title(f'Cache Performance\\nHit Rate: {cache_data.get("hit_rate", 0):.1f}%')
    else:
        ax2.text(0.5, 0.5, 'No Cache Data\\nAvailable', ha='center', va='center',
                transform=ax2.transAxes, fontsize=14)
        ax2.set_title('Cache Performance')
    
    # 3. Error Analysis
    ax3 = axes[0, 2]
    error_counts = [all_metrics[s].get('errors', 0) for s in services]
    warning_counts = [all_metrics[s].get('warnings', 0) for s in services]
    
    x = np.arange(len(services))
    width = 0.35
    
    bars3a = ax3.bar(x - width/2, error_counts, width, label='Errors', color='#e74c3c', alpha=0.8)
    bars3b = ax3.bar(x + width/2, warning_counts, width, label='Warnings', color='#f39c12', alpha=0.8)
    
    ax3.set_title('Errors and Warnings by Service')
    ax3.set_ylabel('Count')
    ax3.set_xticks(x)
    ax3.set_xticklabels(services, rotation=45)
    ax3.legend()
    
    # 4. Request Flow
    ax4 = axes[1, 0]
    
    # Simular flujo de requests basado en datos disponibles
    generator_questions = all_metrics.get('generator', {}).get('questions_sent', 0)
    cache_requests = all_metrics.get('cache', {}).get('total_cache_requests', 0)
    llm_responses = all_metrics.get('llm', {}).get('responses_generated', 0)
    
    flow_data = {
        'Questions\\nGenerated': generator_questions,
        'Cache\\nRequests': cache_requests,
        'LLM\\nResponses': llm_responses
    }
    
    flow_labels = list(flow_data.keys())
    flow_values = list(flow_data.values())
    
    bars4 = ax4.bar(flow_labels, flow_values, color=['#3498db', '#e67e22', '#9b59b6'], alpha=0.7)
    ax4.set_title('Request Flow Through System')
    ax4.set_ylabel('Number of Requests')
    
    for bar, value in zip(bars4, flow_values):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(flow_values)*0.01,
                f'{value:,}', ha='center', va='bottom', fontweight='bold')
    
    # 5. System Health
    ax5 = axes[1, 1]
    
    # Calcular "health score" basado en actividad y errores
    health_scores = []
    for service in services:
        metrics = all_metrics[service]
        activity = metrics.get('total_lines', 0)
        errors = metrics.get('errors', 0)
        
        if activity > 0:
            error_rate = errors / activity
            health_score = max(0, 100 - (error_rate * 100))
        else:
            health_score = 50  # Neutral si no hay actividad
        
        health_scores.append(health_score)
    
    colors_health = ['#2ecc71' if score > 80 else '#f39c12' if score > 60 else '#e74c3c' 
                     for score in health_scores]
    
    bars5 = ax5.bar(services, health_scores, color=colors_health, alpha=0.8)
    ax5.set_title('Service Health Score')
    ax5.set_ylabel('Health Score (%)')
    ax5.set_ylim(0, 100)
    
    for bar, score in zip(bars5, health_scores):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{score:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 6. Timeline Activity (simulado)
    ax6 = axes[1, 2]
    
    # Crear timeline simulado basado en métricas
    time_points = range(0, 24)  # 24 horas
    cache_activity = [np.random.poisson(all_metrics.get('cache', {}).get('total_lines', 0) / 24) 
                     for _ in time_points]
    generator_activity = [np.random.poisson(all_metrics.get('generator', {}).get('total_lines', 0) / 24) 
                         for _ in time_points]
    
    ax6.plot(time_points, cache_activity, label='Cache Activity', linewidth=2, color='#e67e22')
    ax6.plot(time_points, generator_activity, label='Generator Activity', linewidth=2, color='#3498db')
    ax6.fill_between(time_points, cache_activity, alpha=0.3, color='#e67e22')
    ax6.fill_between(time_points, generator_activity, alpha=0.3, color='#3498db')
    
    ax6.set_title('Simulated Activity Timeline')
    ax6.set_xlabel('Hour of Day')
    ax6.set_ylabel('Activity Level')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar
    plot_path = os.path.join(output_dir, 'docker_services_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Análisis de servicios Docker guardado en: {plot_path}")
    
    return plot_path

def generate_metrics_summary(all_metrics):
    """Genera resumen de métricas"""
    print("\\n" + "="*60)
    print("📊 RESUMEN DE MÉTRICAS DE SERVICIOS DOCKER")
    print("="*60)
    
    for service, metrics in all_metrics.items():
        print(f"\\n🔧 {service.upper()}:")
        print(f"   📝 Total log lines: {metrics.get('total_lines', 0):,}")
        print(f"   ❌ Errors: {metrics.get('errors', 0)}")
        print(f"   ⚠️ Warnings: {metrics.get('warnings', 0)}")
        print(f"   ℹ️ Info messages: {metrics.get('info_messages', 0):,}")
        
        # Métricas específicas
        if service == 'cache':
            print(f"   🎯 Cache hits: {metrics.get('cache_hits', 0):,}")
            print(f"   ❌ Cache misses: {metrics.get('cache_misses', 0):,}")
            print(f"   📊 Hit rate: {metrics.get('hit_rate', 0):.2f}%")
        elif service == 'generator':
            print(f"   📤 Questions sent: {metrics.get('questions_sent', 0):,}")
        elif service == 'llm':
            print(f"   🤖 Responses generated: {metrics.get('responses_generated', 0):,}")

def main():
    print("🐳 ANALIZADOR DE LOGS DOCKERIZADOS")
    print("=" * 50)
    
    # Extraer métricas
    print("🔍 Extrayendo métricas de todos los servicios...")
    all_metrics = extract_docker_metrics()
    
    # Generar resumen
    generate_metrics_summary(all_metrics)
    
    # Crear visualizaciones
    print("\\n🎨 Generando visualizaciones...")
    create_service_analysis_plot(all_metrics)
    
    print("\\n✅ Análisis completado!")
    print("📁 Gráfico disponible en: plots/docker_services_analysis.png")

if __name__ == "__main__":
    main()