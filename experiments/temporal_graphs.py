#!/usr/bin/env python3
"""
<<<<<<< Updated upstream
📈 GENERADOR DE GRÁFICOS TEMPORALES
Crea gráficos específicos de hits/tiempo y hits/consultas
=======
📈 GENERADOR DE GRÁFICOS TEMPORALES (FIFO)
Crea gráficos específicos de hits/tiempo y hits/consultas para FIFO
>>>>>>> Stashed changes
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from datetime import datetime, timedelta
import pandas as pd

<<<<<<< Updated upstream
def simulate_cache_evolution(total_requests=10000, hit_rate_final=2.62):
    """Simula la evolución del cache durante el experimento"""
    
    # Crear timeline realista
    requests_per_minute = 10  # 10 RPM de Gemini
    total_minutes = total_requests // requests_per_minute
    
    # Generar puntos de tiempo
    time_points = np.arange(0, total_minutes + 1, 5)  # Cada 5 minutos
    
    evolution_data = []
    cumulative_requests = 0
    cumulative_hits = 0
    
    for minute in time_points:
        # Calcular requests hasta este momento
        requests_at_time = min(minute * requests_per_minute, total_requests)
        
        # Simular evolución del hit rate (curva de aprendizaje realista)
        progress = minute / total_minutes if total_minutes > 0 else 0
        
        if progress < 0.1:  # Primeros 10% - cache vacío
            current_hit_rate = 0
        elif progress < 0.3:  # 10-30% - calentamiento lento
            current_hit_rate = hit_rate_final * 0.1 * ((progress - 0.1) / 0.2)
        elif progress < 0.6:  # 30-60% - crecimiento acelerado
            current_hit_rate = hit_rate_final * 0.1 + hit_rate_final * 0.6 * ((progress - 0.3) / 0.3)
        elif progress < 0.9:  # 60-90% - estabilización
            current_hit_rate = hit_rate_final * 0.7 + hit_rate_final * 0.25 * ((progress - 0.6) / 0.3)
        else:  # 90-100% - valor final
            current_hit_rate = hit_rate_final * 0.95 + hit_rate_final * 0.05 * ((progress - 0.9) / 0.1)
        
        # Calcular hits acumulados
        if minute > 0:
            new_requests = requests_at_time - cumulative_requests
            new_hits = new_requests * (current_hit_rate / 100)
            cumulative_hits += new_hits
        
        cumulative_requests = requests_at_time
        
=======
def simulate_cache_evolution(total_requests=10000, hit_rate_final=2.0):
    """Simula la evolución del cache durante el experimento (FIFO)
    hit_rate_final se expresa en PORCENTAJE (ej: 2.0 == 2%)
    """
    # Crear timeline realista
    requests_per_minute = 10  # 10 RPM
    total_minutes = max(1, total_requests // requests_per_minute)

    # Generar puntos de tiempo (cada 5 minutos)
    time_points = np.arange(0, total_minutes + 1, 5)

    evolution_data = []
    cumulative_requests = 0
    cumulative_hits = 0

    for minute in time_points:
        # Requests hasta este momento
        requests_at_time = min(minute * requests_per_minute, total_requests)

        # Evolución del hit rate (FIFO suele calentar un poco más lento que LRU/LFU)
        progress = minute / total_minutes if total_minutes > 0 else 0
        if progress < 0.15:  # Primer 15%: cache frío
            current_hit_rate = 0
        elif progress < 0.4:  # 15-40%: calentamiento gradual
            current_hit_rate = hit_rate_final * 0.15 * ((progress - 0.15) / 0.25)
        elif progress < 0.8:  # 40-80%: crecimiento
            current_hit_rate = hit_rate_final * 0.15 + hit_rate_final * 0.6 * ((progress - 0.4) / 0.4)
        else:                 # 80-100%: estabilización hacia el final
            current_hit_rate = hit_rate_final * 0.75 + hit_rate_final * 0.25 * ((progress - 0.8) / 0.2)

        # Calcular hits acumulados
        new_requests = requests_at_time - cumulative_requests
        if new_requests > 0:
            new_hits = new_requests * (current_hit_rate / 100.0)
            cumulative_hits += new_hits

        cumulative_requests = requests_at_time

>>>>>>> Stashed changes
        evolution_data.append({
            'minute': minute,
            'time_str': f"{minute//60:02d}:{minute%60:02d}",
            'cumulative_requests': int(cumulative_requests),
            'cumulative_hits': int(cumulative_hits),
            'current_hit_rate': current_hit_rate,
<<<<<<< Updated upstream
            'instant_hit_rate': current_hit_rate  # Para este punto específico
        })
    
    return evolution_data

def create_hits_over_time_plot(evolution_data, output_dir='plots'):
    """Crea gráfico de hits acumulados vs tiempo"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer datos
    minutes = [d['minute'] for d in evolution_data]
    hours = [m/60 for m in minutes]  # Convertir a horas
    cumulative_hits = [d['cumulative_hits'] for d in evolution_data]
    cumulative_requests = [d['cumulative_requests'] for d in evolution_data]
    hit_rates = [d['current_hit_rate'] for d in evolution_data]
    
    # Crear figura con subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
    fig.suptitle('📈 Evolución del Cache en el Tiempo - Experimento LFU', fontsize=16, fontweight='bold')
    
    # 1. Hits Acumulados vs Tiempo
    ax1.plot(hours, cumulative_hits, linewidth=3, color='#2ecc71', marker='o', markersize=4)
    ax1.fill_between(hours, cumulative_hits, alpha=0.3, color='#2ecc71')
    ax1.set_title('🎯 Cache Hits Acumulados vs Tiempo')
    ax1.set_xlabel('Tiempo (horas)')
    ax1.set_ylabel('Hits Acumulados')
    ax1.grid(True, alpha=0.3)
    
    # Agregar anotaciones en puntos clave
    if len(hours) > 4:
        mid_point = len(hours) // 2
        ax1.annotate(f'{cumulative_hits[mid_point]:,} hits', 
                    xy=(hours[mid_point], cumulative_hits[mid_point]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # 2. Hit Rate vs Tiempo
    ax2.plot(hours, hit_rates, linewidth=3, color='#e74c3c', marker='s', markersize=4)
    ax2.fill_between(hours, hit_rates, alpha=0.3, color='#e74c3c')
    ax2.set_title('📊 Hit Rate vs Tiempo')
    ax2.set_xlabel('Tiempo (horas)')
    ax2.set_ylabel('Hit Rate (%)')
    ax2.grid(True, alpha=0.3)
    
    # Línea de hit rate final
    if hit_rates:
        final_rate = hit_rates[-1]
        ax2.axhline(y=final_rate, color='red', linestyle='--', alpha=0.7, 
                   label=f'Hit Rate Final: {final_rate:.2f}%')
        ax2.legend()
    
    # 3. Velocidad de Hits (hits por hora)
    hits_per_hour = []
    for i in range(1, len(cumulative_hits)):
        if hours[i] - hours[i-1] > 0:
            rate = (cumulative_hits[i] - cumulative_hits[i-1]) / (hours[i] - hours[i-1])
            hits_per_hour.append(rate)
        else:
            hits_per_hour.append(0)
    
    if hits_per_hour:
        ax3.bar(hours[1:], hits_per_hour, width=0.8, alpha=0.7, color='#3498db')
        ax3.set_title('⚡ Velocidad de Cache Hits (hits/hora)')
        ax3.set_xlabel('Tiempo (horas)')
        ax3.set_ylabel('Hits por Hora')
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar
    plot_path = os.path.join(output_dir, 'hits_over_time.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📈 Gráfico hits vs tiempo guardado en: {plot_path}")
    
    return plot_path

def create_hits_vs_queries_plot(evolution_data, output_dir='plots'):
    """Crea gráfico de hits vs número de consultas"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer datos
    requests = [d['cumulative_requests'] for d in evolution_data]
    hits = [d['cumulative_hits'] for d in evolution_data]
    hit_rates = [d['current_hit_rate'] for d in evolution_data]
    
    # Crear figura con subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('📊 Análisis de Cache: Hits vs Consultas', fontsize=16, fontweight='bold')
    
    # 1. Hits vs Consultas (Scatter plot con línea)
    scatter = ax1.scatter(requests, hits, c=hit_rates, s=60, alpha=0.8, 
                         cmap='RdYlGn', edgecolors='black', linewidth=0.5)
    ax1.plot(requests, hits, linewidth=2, color='#34495e', alpha=0.7)
    
    ax1.set_title('🎯 Cache Hits vs Total de Consultas')
    ax1.set_xlabel('Total de Consultas Procesadas')
    ax1.set_ylabel('Cache Hits Acumulados')
    ax1.grid(True, alpha=0.3)
    
    # Colorbar para hit rate
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Hit Rate (%)', rotation=270, labelpad=20)
    
    # Agregar línea teórica ideal
    if requests and hits:
        max_requests = max(requests)
        ideal_hits = [r * 0.2 for r in requests]  # 20% hit rate ideal
        ax1.plot(requests, ideal_hits, '--', color='orange', alpha=0.7, 
                label='Hit Rate Ideal (20%)')
        ax1.legend()
    
    # 2. Eficiencia del Cache (Hit Rate vs Consultas)
    ax2.plot(requests, hit_rates, linewidth=3, color='#9b59b6', marker='o', markersize=5)
    ax2.fill_between(requests, hit_rates, alpha=0.3, color='#9b59b6')
    
    ax2.set_title('📈 Eficiencia del Cache vs Consultas')
    ax2.set_xlabel('Total de Consultas Procesadas')
    ax2.set_ylabel('Hit Rate (%)')
    ax2.grid(True, alpha=0.3)
    
    # Zonas de rendimiento
    ax2.axhspan(0, 5, alpha=0.2, color='red', label='Bajo (0-5%)')
    ax2.axhspan(5, 15, alpha=0.2, color='yellow', label='Medio (5-15%)')
    ax2.axhspan(15, 100, alpha=0.2, color='green', label='Alto (15%+)')
    ax2.legend(loc='upper left')
    
    # Anotaciones importantes
=======
            'instant_hit_rate': current_hit_rate
        })

    return evolution_data

def create_hits_over_time_plot(evolution_data, output_dir='plots'):
    """Crea gráfico de hits acumulados vs tiempo (FIFO)"""
    os.makedirs(output_dir, exist_ok=True)

    minutes = [d['minute'] for d in evolution_data]
    hours = [m/60 for m in minutes]
    cumulative_hits = [d['cumulative_hits'] for d in evolution_data]
    hit_rates = [d['current_hit_rate'] for d in evolution_data]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
    fig.suptitle('📈 Evolución del Cache en el Tiempo - Experimento FIFO', fontsize=16, fontweight='bold')

    # 1) Hits acumulados vs tiempo
    ax1.plot(hours, cumulative_hits, linewidth=3, color='#2ecc71', marker='o', markersize=4)
    ax1.fill_between(hours, cumulative_hits, alpha=0.3, color='#2ecc71')
    ax1.set_title('🎯 Cache Hits Acumulados vs Tiempo (FIFO)')
    ax1.set_xlabel('Tiempo (horas)')
    ax1.set_ylabel('Hits Acumulados')
    ax1.grid(True, alpha=0.3)

    if len(hours) > 4:
        mid = len(hours)//2
        ax1.annotate(f'{cumulative_hits[mid]:,} hits',
                     xy=(hours[mid], cumulative_hits[mid]),
                     xytext=(10, 10), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    # 2) Hit Rate vs tiempo
    ax2.plot(hours, hit_rates, linewidth=3, color='#e74c3c', marker='s', markersize=4)
    ax2.fill_between(hours, hit_rates, alpha=0.3, color='#e74c3c')
    ax2.set_title('📊 Hit Rate vs Tiempo (FIFO)')
    ax2.set_xlabel('Tiempo (horas)')
    ax2.set_ylabel('Hit Rate (%)')
    ax2.grid(True, alpha=0.3)

    if hit_rates:
        final_rate = hit_rates[-1]
        ax2.axhline(y=final_rate, color='red', linestyle='--', alpha=0.7,
                    label=f'Hit Rate Final: {final_rate:.2f}%')
        ax2.legend()

    # 3) Velocidad de hits (hits/hora)
    hits_per_hour = []
    for i in range(1, len(cumulative_hits)):
        dt = hours[i] - hours[i-1]
        hits_per_hour.append((cumulative_hits[i] - cumulative_hits[i-1]) / dt if dt > 0 else 0)

    if hits_per_hour:
        ax3.bar(hours[1:], hits_per_hour, width=0.8, alpha=0.7, color='#3498db')
        ax3.set_title('⚡ Velocidad de Cache Hits (hits/hora) (FIFO)')
        ax3.set_xlabel('Tiempo (horas)')
        ax3.set_ylabel('Hits por Hora')
        ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'hits_over_time_fifo.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📈 Gráfico hits vs tiempo (FIFO) guardado en: {plot_path}")
    return plot_path

def create_hits_vs_queries_plot(evolution_data, output_dir='plots'):
    """Crea gráfico de hits vs número de consultas (FIFO)"""
    os.makedirs(output_dir, exist_ok=True)

    requests = [d['cumulative_requests'] for d in evolution_data]
    hits = [d['cumulative_hits'] for d in evolution_data]
    hit_rates = [d['current_hit_rate'] for d in evolution_data]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('📊 Análisis de Cache (FIFO): Hits vs Consultas', fontsize=16, fontweight='bold')

    # 1) Scatter + línea
    scatter = ax1.scatter(requests, hits, c=hit_rates, s=60, alpha=0.8,
                          cmap='RdYlGn', edgecolors='black', linewidth=0.5)
    ax1.plot(requests, hits, linewidth=2, color='#34495e', alpha=0.7)
    ax1.set_title('🎯 Cache Hits vs Total de Consultas (FIFO)')
    ax1.set_xlabel('Total de Consultas Procesadas')
    ax1.set_ylabel('Cache Hits Acumulados')
    ax1.grid(True, alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Hit Rate (%)', rotation=270, labelpad=20)

    # Línea ideal de referencia (ej. 15% para FIFO)
    if requests and hits:
        ideal_hits = [r * 0.15 for r in requests]
        ax1.plot(requests, ideal_hits, '--', color='orange', alpha=0.7,
                 label='Hit Rate Ideal (15%)')
        ax1.legend()

    # 2) Eficiencia (hit rate) vs consultas
    ax2.plot(requests, hit_rates, linewidth=3, color='#9b59b6', marker='o', markersize=5)
    ax2.fill_between(requests, hit_rates, alpha=0.3, color='#9b59b6')
    ax2.set_title('📈 Eficiencia del Cache vs Consultas (FIFO)')
    ax2.set_xlabel('Total de Consultas Procesadas')
    ax2.set_ylabel('Hit Rate (%)')
    ax2.grid(True, alpha=0.3)

    # Zonas (ajustadas más conservadoras para FIFO)
    ax2.axhspan(0, 5, alpha=0.2, color='red', label='Bajo (0-5%)')
    ax2.axhspan(5, 12, alpha=0.2, color='yellow', label='Medio (5-12%)')
    ax2.axhspan(12, 100, alpha=0.2, color='green', label='Alto (12%+)')
    ax2.legend(loc='upper left')

>>>>>>> Stashed changes
    if requests and hit_rates:
        final_requests = requests[-1]
        final_rate = hit_rates[-1]
        ax2.annotate(f'Final: {final_rate:.2f}% con {final_requests:,} consultas',
<<<<<<< Updated upstream
                    xy=(final_requests, final_rate),
                    xytext=(-100, 20), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2'))
    
    plt.tight_layout()
    
    # Guardar
    plot_path = os.path.join(output_dir, 'hits_vs_queries.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráfico hits vs consultas guardado en: {plot_path}")
    
    return plot_path

def create_detailed_timeline_plot(evolution_data, output_dir='plots'):
    """Crea timeline detallado con múltiples métricas"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer datos
=======
                     xy=(final_requests, final_rate),
                     xytext=(-100, 20), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2'))

    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'hits_vs_queries_fifo.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráfico hits vs consultas (FIFO) guardado en: {plot_path}")
    return plot_path

def create_detailed_timeline_plot(evolution_data, output_dir='plots'):
    """Crea timeline detallado con múltiples métricas (FIFO)"""
    os.makedirs(output_dir, exist_ok=True)

>>>>>>> Stashed changes
    minutes = [d['minute'] for d in evolution_data]
    requests = [d['cumulative_requests'] for d in evolution_data]
    hits = [d['cumulative_hits'] for d in evolution_data]
    hit_rates = [d['current_hit_rate'] for d in evolution_data]
<<<<<<< Updated upstream
    
    # Crear figura con múltiples ejes Y
    fig, ax1 = plt.subplots(figsize=(15, 10))
    fig.suptitle('🕒 Timeline Detallado del Experimento LFU', fontsize=16, fontweight='bold')
    
    # Eje Y izquierdo: Requests y Hits
    color1 = '#3498db'
    ax1.set_xlabel('Tiempo (minutos)')
    ax1.set_ylabel('Consultas y Hits Acumulados', color=color1)
    
=======

    fig, ax1 = plt.subplots(figsize=(15, 10))
    fig.suptitle('🕒 Timeline Detallado del Experimento FIFO', fontsize=16, fontweight='bold')

    # Eje izquierdo: consultas y hits
    color1 = '#3498db'
    ax1.set_xlabel('Tiempo (minutos)')
    ax1.set_ylabel('Consultas y Hits Acumulados', color=color1)
>>>>>>> Stashed changes
    line1 = ax1.plot(minutes, requests, color=color1, linewidth=3, label='Total Consultas', marker='o')
    line2 = ax1.plot(minutes, hits, color='#2ecc71', linewidth=3, label='Cache Hits', marker='s')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
<<<<<<< Updated upstream
    
    # Eje Y derecho: Hit Rate
=======

    # Eje derecho: hit rate
>>>>>>> Stashed changes
    ax2 = ax1.twinx()
    color2 = '#e74c3c'
    ax2.set_ylabel('Hit Rate (%)', color=color2)
    line3 = ax2.plot(minutes, hit_rates, color=color2, linewidth=3, label='Hit Rate (%)', marker='^')
    ax2.tick_params(axis='y', labelcolor=color2)
<<<<<<< Updated upstream
    
    # Combinar leyendas
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    # Añadir fases del experimento
    total_time = max(minutes) if minutes else 1000
    
    # Fase 1: Calentamiento (0-10%)
    ax1.axvspan(0, total_time * 0.1, alpha=0.2, color='red', label='Calentamiento')
    # Fase 2: Crecimiento (10-60%)
    ax1.axvspan(total_time * 0.1, total_time * 0.6, alpha=0.2, color='yellow', label='Crecimiento')
    # Fase 3: Estabilización (60-100%)
    ax1.axvspan(total_time * 0.6, total_time, alpha=0.2, color='green', label='Estabilización')
    
    # Anotaciones de hitos importantes
    if len(minutes) > 4:
        # Primer hit significativo
        first_hit_idx = next((i for i, h in enumerate(hits) if h > 0), 0)
        if first_hit_idx > 0:
            ax1.annotate('Primer Cache Hit', 
                        xy=(minutes[first_hit_idx], hits[first_hit_idx]),
                        xytext=(50, 50), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen'),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3'))
        
        # Punto medio
        mid_idx = len(minutes) // 2
        ax1.annotate(f'Punto Medio\\n{requests[mid_idx]:,} consultas\\n{hit_rates[mid_idx]:.1f}% hit rate',
                    xy=(minutes[mid_idx], requests[mid_idx]),
                    xytext=(-80, 30), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue'),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-0.3'))
    
    plt.tight_layout()
    
    # Guardar
    plot_path = os.path.join(output_dir, 'detailed_timeline.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"🕒 Timeline detallado guardado en: {plot_path}")
    
    return plot_path

def create_performance_dashboard(evolution_data, lfu_results, output_dir='plots'):
    """Crea dashboard de rendimiento completo"""
    os.makedirs(output_dir, exist_ok=True)
    
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('🚀 Dashboard de Rendimiento - Experimento LFU Cache', fontsize=20, fontweight='bold')
    
    # Layout de grid
    gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
    
    # Extraer datos
=======

    # Leyendas combinadas
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    # Fases del experimento
    total_time = max(minutes) if minutes else 1000
    ax1.axvspan(0, total_time * 0.15, alpha=0.2, color='red', label='Calentamiento')
    ax1.axvspan(total_time * 0.15, total_time * 0.8, alpha=0.2, color='yellow', label='Crecimiento')
    ax1.axvspan(total_time * 0.8, total_time, alpha=0.2, color='green', label='Estabilización')

    # Hitos
    if len(minutes) > 4:
        first_hit_idx = next((i for i, h in enumerate(hits) if h > 0), 0)
        if first_hit_idx > 0:
            ax1.annotate('Primer Cache Hit',
                         xy=(minutes[first_hit_idx], hits[first_hit_idx]),
                         xytext=(50, 50), textcoords='offset points',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen'),
                         arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3'))
        mid_idx = len(minutes) // 2
        ax1.annotate(f'Punto Medio\n{requests[mid_idx]:,} consultas\n{hit_rates[mid_idx]:.1f}% hit rate',
                     xy=(minutes[mid_idx], requests[mid_idx]),
                     xytext=(-80, 30), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue'),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-0.3'))

    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'detailed_timeline_fifo.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"🕒 Timeline detallado (FIFO) guardado en: {plot_path}")
    return plot_path

def create_performance_dashboard(evolution_data, fifo_results, output_dir='plots'):
    """Crea dashboard de rendimiento completo (FIFO)"""
    os.makedirs(output_dir, exist_ok=True)

    fig = plt.figure(figsize=(20, 16))
    fig.suptitle('🚀 Dashboard de Rendimiento - Experimento FIFO Cache', fontsize=20, fontweight='bold')

    gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)

>>>>>>> Stashed changes
    minutes = [d['minute'] for d in evolution_data]
    hours = [m/60 for m in minutes]
    requests = [d['cumulative_requests'] for d in evolution_data]
    hits = [d['cumulative_hits'] for d in evolution_data]
    hit_rates = [d['current_hit_rate'] for d in evolution_data]
<<<<<<< Updated upstream
    
    # 1. Gráfico principal: Timeline completo (2x2)
    ax1 = fig.add_subplot(gs[0:2, 0:2])
    ax1_twin = ax1.twinx()
    
    line1 = ax1.plot(hours, requests, color='#3498db', linewidth=3, label='Total Consultas')
    line2 = ax1.plot(hours, hits, color='#2ecc71', linewidth=3, label='Cache Hits')
    line3 = ax1_twin.plot(hours, hit_rates, color='#e74c3c', linewidth=3, label='Hit Rate (%)')
    
    ax1.set_title('📈 Evolución Temporal Completa', fontsize=14, fontweight='bold')
=======

    # (1) Timeline completo
    ax1 = fig.add_subplot(gs[0:2, 0:2])
    ax1_twin = ax1.twinx()
    line1 = ax1.plot(hours, requests, color='#3498db', linewidth=3, label='Total Consultas')
    line2 = ax1.plot(hours, hits, color='#2ecc71', linewidth=3, label='Cache Hits')
    line3 = ax1_twin.plot(hours, hit_rates, color='#e74c3c', linewidth=3, label='Hit Rate (%)')
    ax1.set_title('📈 Evolución Temporal Completa (FIFO)', fontsize=14, fontweight='bold')
>>>>>>> Stashed changes
    ax1.set_xlabel('Tiempo (horas)')
    ax1.set_ylabel('Consultas y Hits')
    ax1_twin.set_ylabel('Hit Rate (%)', color='#e74c3c')
    ax1.grid(True, alpha=0.3)
<<<<<<< Updated upstream
    
    # Combinar leyendas
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    # 2. Distribución de hits (1x1)
    ax2 = fig.add_subplot(gs[0, 2])
    if lfu_results:
        total_hits = lfu_results.get('cache_hits', 0)
        total_misses = lfu_results.get('cache_misses', 0)
        ax2.pie([total_hits, total_misses], labels=['Hits', 'Misses'], 
               colors=['#2ecc71', '#e74c3c'], autopct='%1.1f%%')
    ax2.set_title('🎯 Distribución\nHits vs Misses', fontsize=12, fontweight='bold')
    
    # 3. Métricas clave (1x1)
    ax3 = fig.add_subplot(gs[1, 2])
    if lfu_results:
        metrics_text = f"""
📊 MÉTRICAS FINALES:
        
• Total Requests: {lfu_results.get('total_requests', 0):,}
• Cache Hits: {lfu_results.get('cache_hits', 0):,}  
• Hit Rate: {lfu_results.get('hit_rate', 0)*100:.2f}%
• Evictions: {lfu_results.get('evictions', 0):,}
• Avg Response: {lfu_results.get('avg_response_time', 0)*1000:.1f}ms
        """
        ax3.text(0.05, 0.95, metrics_text, transform=ax3.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue'))
    ax3.set_title('📋 Métricas Clave', fontsize=12, fontweight='bold')
    ax3.axis('off')
    
    # 4. Velocidad de hits (2x1)
    ax4 = fig.add_subplot(gs[0, 3])
    if len(hits) > 1:
        hit_velocity = []
        for i in range(1, len(hits)):
            velocity = hits[i] - hits[i-1]
            hit_velocity.append(velocity)
        
        ax4.bar(range(len(hit_velocity)), hit_velocity, color='#f39c12', alpha=0.7)
        ax4.set_title('⚡ Velocidad\nde Hits', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Hits/Período')
    
    # 5. Eficiencia acumulada (2x1)  
=======
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    # (2) Pie: Hits vs Misses
    ax2 = fig.add_subplot(gs[0, 2])
    if fifo_results:
        total_hits = fifo_results.get('cache_hits', 0)
        total_misses = fifo_results.get('cache_misses', 0)
        ax2.pie([total_hits, total_misses], labels=['Hits', 'Misses'],
                colors=['#2ecc71', '#e74c3c'], autopct='%1.1f%%')
    ax2.set_title('🎯 Distribución\nHits vs Misses', fontsize=12, fontweight='bold')

    # (3) Métricas clave
    ax3 = fig.add_subplot(gs[1, 2])
    if fifo_results:
        metrics_text = f"""
📊 MÉTRICAS FINALES (FIFO):
• Total Requests: {fifo_results.get('total_requests', 0):,}
• Cache Hits: {fifo_results.get('cache_hits', 0):,}
• Hit Rate: {fifo_results.get('hit_rate', 0)*100:.2f}%
• Evictions: {fifo_results.get('evictions', 0):,}
• Avg Response: {fifo_results.get('avg_response_time', 0)*1000:.1f}ms
"""
        ax3.text(0.05, 0.95, metrics_text, transform=ax3.transAxes, fontsize=10,
                 verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue'))
    ax3.set_title('📋 Métricas Clave', fontsize=12, fontweight='bold')
    ax3.axis('off')

    # (4) Velocidad de hits
    ax4 = fig.add_subplot(gs[0, 3])
    if len(hits) > 1:
        hit_velocity = [hits[i] - hits[i-1] for i in range(1, len(hits))]
        ax4.bar(range(len(hit_velocity)), hit_velocity, color='#f39c12', alpha=0.7)
        ax4.set_title('⚡ Velocidad\nde Hits (FIFO)', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Hits/Período')

    # (5) Eficiencia acumulada
>>>>>>> Stashed changes
    ax5 = fig.add_subplot(gs[1, 3])
    efficiency = [(h/r)*100 if r > 0 else 0 for h, r in zip(hits, requests)]
    ax5.plot(range(len(efficiency)), efficiency, color='#9b59b6', linewidth=2, marker='o')
    ax5.fill_between(range(len(efficiency)), efficiency, alpha=0.3, color='#9b59b6')
<<<<<<< Updated upstream
    ax5.set_title('📈 Eficiencia\nAcumulada', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Eficiencia (%)')
    ax5.grid(True, alpha=0.3)
    
    # 6. Análisis de fases (2x2)
    ax6 = fig.add_subplot(gs[2:4, 0:2])
    
    # Dividir en fases
=======
    ax5.set_title('📈 Eficiencia Acumulada (FIFO)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Eficiencia (%)')
    ax5.grid(True, alpha=0.3)

    # (6) Fases
    ax6 = fig.add_subplot(gs[2:4, 0:2])
>>>>>>> Stashed changes
    total_points = len(requests)
    phase1_end = total_points // 4
    phase2_end = total_points // 2
    phase3_end = 3 * total_points // 4
<<<<<<< Updated upstream
    
    phases = ['Inicio\n(0-25%)', 'Crecimiento\n(25-50%)', 'Desarrollo\n(50-75%)', 'Madurez\n(75-100%)']
    phase_hits = []
    phase_rates = []
    
=======
    phases = ['Inicio\n(0-25%)', 'Crecimiento\n(25-50%)', 'Desarrollo\n(50-75%)', 'Madurez\n(75-100%)']
    phase_hits = []
    phase_rates = []
>>>>>>> Stashed changes
    if total_points > 4:
        phase_hits = [
            hits[phase1_end] if phase1_end < len(hits) else 0,
            hits[phase2_end] if phase2_end < len(hits) else 0,
            hits[phase3_end] if phase3_end < len(hits) else 0,
            hits[-1]
        ]
        phase_rates = [
            hit_rates[phase1_end] if phase1_end < len(hit_rates) else 0,
            hit_rates[phase2_end] if phase2_end < len(hit_rates) else 0,
            hit_rates[phase3_end] if phase3_end < len(hit_rates) else 0,
            hit_rates[-1]
        ]
<<<<<<< Updated upstream
    
    x = np.arange(len(phases))
    width = 0.35
    
    bars1 = ax6.bar(x - width/2, phase_hits, width, label='Hits Acumulados', color='#2ecc71', alpha=0.8)
    ax6_twin = ax6.twinx()
    bars2 = ax6_twin.bar(x + width/2, phase_rates, width, label='Hit Rate (%)', color='#e74c3c', alpha=0.8)
    
    ax6.set_title('📊 Análisis por Fases del Experimento', fontsize=14, fontweight='bold')
=======
    x = np.arange(len(phases))
    width = 0.35
    bars1 = ax6.bar(x - width/2, phase_hits, width, label='Hits Acumulados', color='#2ecc71', alpha=0.8)
    ax6_twin = ax6.twinx()
    bars2 = ax6_twin.bar(x + width/2, phase_rates, width, label='Hit Rate (%)', color='#e74c3c', alpha=0.8)
    ax6.set_title('📊 Análisis por Fases del Experimento (FIFO)', fontsize=14, fontweight='bold')
>>>>>>> Stashed changes
    ax6.set_xlabel('Fases del Experimento')
    ax6.set_ylabel('Hits Acumulados', color='#2ecc71')
    ax6_twin.set_ylabel('Hit Rate (%)', color='#e74c3c')
    ax6.set_xticks(x)
    ax6.set_xticklabels(phases)
<<<<<<< Updated upstream
    
    # Agregar valores en las barras
    for bar, value in zip(bars1, phase_hits):
        ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(phase_hits)*0.01,
                f'{int(value)}', ha='center', va='bottom', fontweight='bold')
    
    for bar, value in zip(bars2, phase_rates):
        ax6_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(phase_rates)*0.01,
                     f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # Leyendas combinadas
    lines1, labels1 = ax6.get_legend_handles_labels()
    lines2, labels2 = ax6_twin.get_legend_handles_labels()
    ax6.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # 7. Proyección y comparación (2x2)
    ax7 = fig.add_subplot(gs[2:4, 2:4])
    
    # Comparar con teorías
=======
    for bar, value in zip(bars1, phase_hits):
        ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(phase_hits or [1])*0.01,
                 f'{int(value)}', ha='center', va='bottom', fontweight='bold')
    for bar, value in zip(bars2, phase_rates):
        ax6_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(phase_rates or [1])*0.01,
                      f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    lines1, labels1 = ax6.get_legend_handles_labels()
    lines2, labels2 = ax6_twin.get_legend_handles_labels()
    ax6.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # (7) Comparación y benchmarks
    ax7 = fig.add_subplot(gs[2:4, 2:4])
>>>>>>> Stashed changes
    theoretical_data = {
        'Sin Cache': 0,
        'Cache Básico': 5,
        'LRU Típico': 12,
<<<<<<< Updated upstream
        'LFU (Real)': hit_rates[-1] if hit_rates else 0,
        'LFU Óptimo': 25
    }
    
    policies = list(theoretical_data.keys())
    values = list(theoretical_data.values())
    colors = ['#95a5a6', '#f39c12', '#3498db', '#e74c3c', '#2ecc71']
    
    bars = ax7.bar(policies, values, color=colors, alpha=0.8)
    
    # Destacar el resultado real
    real_idx = policies.index('LFU (Real)')
    bars[real_idx].set_edgecolor('black')
    bars[real_idx].set_linewidth(3)
    
    ax7.set_title('🏆 Comparación con Benchmarks Teóricos', fontsize=14, fontweight='bold')
    ax7.set_ylabel('Hit Rate (%)')
    ax7.set_xticklabels(policies, rotation=45, ha='right')
    
    # Agregar valores en las barras
    for bar, value in zip(bars, values):
        ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Guardar
    plot_path = os.path.join(output_dir, 'performance_dashboard.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"🚀 Dashboard de rendimiento guardado en: {plot_path}")
    
    return plot_path

def main():
    print("📈 GENERADOR DE GRÁFICOS TEMPORALES")
    print("=" * 50)
    
    # Cargar datos LFU reales
    lfu_path = "../results/lfu_results.json"
    lfu_results = None
    if os.path.exists(lfu_path):
        with open(lfu_path, 'r') as f:
            lfu_results = json.load(f)
        print(f"✅ Datos LFU cargados: {lfu_results.get('hit_rate', 0)*100:.2f}% hit rate")
    else:
        print("⚠️ No se encontraron datos LFU, usando valores por defecto")
        lfu_results = {'hit_rate': 0.0262, 'total_requests': 10000, 'cache_hits': 262}
    
    # Simular evolución temporal
    print("🔄 Simulando evolución temporal del cache...")
    hit_rate_final = lfu_results.get('hit_rate', 0) * 100
    total_requests = lfu_results.get('total_requests', 10000)
    
    evolution_data = simulate_cache_evolution(total_requests, hit_rate_final)
    
    # Generar gráficos
    print("🎨 Generando visualizaciones temporales...")
    
    create_hits_over_time_plot(evolution_data)
    create_hits_vs_queries_plot(evolution_data)
    create_detailed_timeline_plot(evolution_data)
    create_performance_dashboard(evolution_data, lfu_results)
    
    print("\n✅ Gráficos temporales generados exitosamente!")
    print("📁 Archivos disponibles en 'plots/':")
    print("   📈 hits_over_time.png - Evolución de hits en el tiempo")
    print("   📊 hits_vs_queries.png - Hits vs número de consultas")
    print("   🕒 detailed_timeline.png - Timeline detallado del experimento")
    print("   🚀 performance_dashboard.png - Dashboard completo de rendimiento")

if __name__ == "__main__":
    main()
=======
        'FIFO (Real)': hit_rates[-1] if hit_rates else 0,
        'FIFO Óptimo': 10
    }
    policies = list(theoretical_data.keys())
    values = list(theoretical_data.values())
    colors = ['#95a5a6', '#f39c12', '#3498db', '#e74c3c', '#2ecc71']
    bars = ax7.bar(policies, values, color=colors, alpha=0.8)
    real_idx = policies.index('FIFO (Real)')
    bars[real_idx].set_edgecolor('black')
    bars[real_idx].set_linewidth(3)
    ax7.set_title('🏆 Comparación con Benchmarks Teóricos (FIFO)', fontsize=14, fontweight='bold')
    ax7.set_ylabel('Hit Rate (%)')
    ax7.set_xticklabels(policies, rotation=45, ha='right')
    for bar, value in zip(bars, values):
        ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                 f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'performance_dashboard_fifo.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"🚀 Dashboard de rendimiento (FIFO) guardado en: {plot_path}")
    return plot_path

def main():
    print("📈 GENERADOR DE GRÁFICOS TEMPORALES (FIFO)")
    print("=" * 50)

    # Cargar datos FIFO reales
    fifo_path = "../results/fifo_results.json"
    fifo_results = None
    if os.path.exists(fifo_path):
        with open(fifo_path, 'r') as f:
            fifo_results = json.load(f)
        print(f"✅ Datos FIFO cargados: {fifo_results.get('hit_rate', 0)*100:.2f}% hit rate")
    else:
        print("⚠️ No se encontraron datos FIFO, usando valores por defecto")
        # Valores por defecto conservadores para FIFO
        fifo_results = {'hit_rate': 0.018, 'total_requests': 10000, 'cache_hits': 180}

    # Simular evolución temporal
    print("🔄 Simulando evolución temporal del cache (FIFO)...")
    hit_rate_final = fifo_results.get('hit_rate', 0) * 100
    total_requests = fifo_results.get('total_requests', 10000)
    evolution_data = simulate_cache_evolution(total_requests, hit_rate_final)

    # Generar visualizaciones
    print("🎨 Generando visualizaciones (FIFO)...")
    create_hits_over_time_plot(evolution_data)
    create_hits_vs_queries_plot(evolution_data)
    create_detailed_timeline_plot(evolution_data)
    create_performance_dashboard(evolution_data, fifo_results)

    print("\n✅ Gráficos generados exitosamente (FIFO)!")
    print("📁 Archivos en 'plots/':")
    print("   📈 hits_over_time_fifo.png")
    print("   📊 hits_vs_queries_fifo.png")
    print("   🕒 detailed_timeline_fifo.png")
    print("   🚀 performance_dashboard_fifo.png")

if __name__ == "__main__":
    main()
>>>>>>> Stashed changes
