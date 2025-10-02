#!/usr/bin/env python3
"""
📊 ANALIZADOR DE LOGS Y VISUALIZADOR
Genera gráficos e informes basados en logs de Docker y resultados de experimentos
"""

import subprocess
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
import os

# Configurar estilo de gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def get_docker_logs(service, lines=1000):
    """Obtiene logs de un servicio específico de Docker"""
    try:
        result = subprocess.run(
            ["docker-compose", "logs", "--tail", str(lines), service],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error obteniendo logs de {service}: {e}")
        return ""

def parse_cache_logs(logs):
    """Parsea logs del servicio cache para extraer métricas"""
    events = []
    
    # Patrones para extraer información
    patterns = {
        'cache_hit': r'INFO:app:Cache hit para pregunta: (.+?)(?:\.\.\.|$)',
        'cache_miss': r'INFO:app:Pregunta no encontrada en cache, enviando al LLM: (.+?)(?:\.\.\.|$)',
        'cache_store': r'INFO:app:Respuesta cacheada para pregunta: (.+?)(?:\.\.\.|$)',
        'timestamp': r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)',
        'message_received': r'INFO:app:Mensaje recibido:'
    }
    
    for line in logs.split('\n'):
        if 'INFO:app:' in line:
            # Extraer timestamp si existe
            timestamp_match = re.search(patterns['timestamp'], line)
            timestamp = None
            if timestamp_match:
                try:
                    timestamp = datetime.fromisoformat(timestamp_match.group(1))
                except:
                    timestamp = None
            
            # Clasificar tipo de evento
            event_type = None
            question = None
            
            if 'Cache hit para pregunta:' in line:
                event_type = 'cache_hit'
                match = re.search(patterns['cache_hit'], line)
                if match:
                    question = match.group(1)
            elif 'Pregunta no encontrada en cache' in line:
                event_type = 'cache_miss'
                match = re.search(patterns['cache_miss'], line)
                if match:
                    question = match.group(1)
            elif 'Respuesta cacheada para pregunta:' in line:
                event_type = 'cache_store'
                match = re.search(patterns['cache_store'], line)
                if match:
                    question = match.group(1)
            elif 'Mensaje recibido:' in line:
                event_type = 'message_received'
            
            if event_type:
                events.append({
                    'timestamp': timestamp,
                    'event_type': event_type,
                    'question': question,
                    'raw_line': line
                })
    
    return events

def analyze_cache_performance(events):
    """Analiza el rendimiento del cache basado en eventos"""
    # Filtrar eventos con timestamp válido
    valid_events = [e for e in events if e['timestamp'] is not None]
    
    if not valid_events:
        return None
    
    df = pd.DataFrame(valid_events)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Calcular métricas por ventana de tiempo
    df.set_index('timestamp', inplace=True)
    
    # Agrupar por minutos
    hits = df[df['event_type'] == 'cache_hit'].resample('1min').size()
    misses = df[df['event_type'] == 'cache_miss'].resample('1min').size()
    stores = df[df['event_type'] == 'cache_store'].resample('1min').size()
    
    # Crear DataFrame combinado
    metrics = pd.DataFrame({
        'hits': hits,
        'misses': misses,
        'stores': stores
    }).fillna(0)
    
    # Calcular hit rate
    metrics['total_requests'] = metrics['hits'] + metrics['misses']
    metrics['hit_rate'] = metrics['hits'] / metrics['total_requests']
    metrics['hit_rate'] = metrics['hit_rate'].fillna(0)
    
    return metrics

def create_cache_performance_plots(metrics, output_dir='plots'):
    """Crea gráficos de rendimiento del cache"""
    os.makedirs(output_dir, exist_ok=True)
    
    if metrics is None or len(metrics) == 0:
        print("⚠️ No hay datos suficientes para generar gráficos")
        return
    
    # Configurar subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('📊 Análisis de Rendimiento del Cache en Tiempo Real', fontsize=16, fontweight='bold')
    
    # 1. Hits vs Misses en el tiempo
    ax1 = axes[0, 0]
    ax1.plot(metrics.index, metrics['hits'], label='Cache Hits', color='green', linewidth=2)
    ax1.plot(metrics.index, metrics['misses'], label='Cache Misses', color='red', linewidth=2)
    ax1.set_title('🎯 Cache Hits vs Misses por Minuto')
    ax1.set_ylabel('Número de Requests')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Hit Rate en el tiempo
    ax2 = axes[0, 1]
    ax2.plot(metrics.index, metrics['hit_rate'] * 100, color='blue', linewidth=2)
    ax2.fill_between(metrics.index, metrics['hit_rate'] * 100, alpha=0.3, color='blue')
    ax2.set_title('📈 Hit Rate del Cache (%)')
    ax2.set_ylabel('Hit Rate (%)')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    
    # 3. Total de requests por minuto
    ax3 = axes[1, 0]
    ax3.bar(metrics.index, metrics['total_requests'], color='purple', alpha=0.7)
    ax3.set_title('📊 Total de Requests por Minuto')
    ax3.set_ylabel('Número de Requests')
    ax3.grid(True, alpha=0.3)
    
    # 4. Distribución de eventos
    ax4 = axes[1, 1]
    total_hits = metrics['hits'].sum()
    total_misses = metrics['misses'].sum()
    total_stores = metrics['stores'].sum()
    
    labels = ['Cache Hits', 'Cache Misses', 'Cache Stores']
    sizes = [total_hits, total_misses, total_stores]
    colors = ['green', 'red', 'orange']
    
    wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax4.set_title('🥧 Distribución de Eventos del Cache')
    
    # Formatear fechas en ejes x
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Guardar gráfico
    plot_path = os.path.join(output_dir, 'cache_performance_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráfico guardado en: {plot_path}")
    
    return plot_path

def analyze_experiment_results(results_dir='results'):
    """Analiza y compara resultados de experimentos"""
    results = {}
    
    # Cargar resultados de experimentos
    for policy in ['lru', 'lfu', 'fifo']:
        filepath = os.path.join(results_dir, f'{policy}_results.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                results[policy.upper()] = json.load(f)
    
    if not results:
        print("⚠️ No se encontraron resultados de experimentos")
        return None
    
    return results

def create_experiment_comparison_plots(results, output_dir='plots'):
    """Crea gráficos comparativos de experimentos"""
    if not results:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer métricas
    policies = list(results.keys())
    hit_rates = [results[p].get('hit_rate', 0) * 100 for p in policies]
    total_requests = [results[p].get('total_requests', 0) for p in policies]
    cache_hits = [results[p].get('cache_hits', 0) for p in policies]
    evictions = [results[p].get('evictions', 0) for p in policies]
    response_times = [results[p].get('avg_response_time', 0) * 1000 for p in policies]  # En ms
    
    # Crear subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('🏆 Comparación de Políticas de Cache - 10,000 Preguntas', fontsize=16, fontweight='bold')
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    # 1. Hit Rates
    ax1 = axes[0, 0]
    bars1 = ax1.bar(policies, hit_rates, color=colors[:len(policies)])
    ax1.set_title('🎯 Hit Rate por Política (%)')
    ax1.set_ylabel('Hit Rate (%)')
    ax1.set_ylim(0, max(hit_rates) * 1.2 if hit_rates else 10)
    
    # Agregar valores en las barras
    for bar, value in zip(bars1, hit_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                f'{value:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    # 2. Total Requests
    ax2 = axes[0, 1]
    bars2 = ax2.bar(policies, total_requests, color=colors[:len(policies)])
    ax2.set_title('📊 Total de Requests Procesados')
    ax2.set_ylabel('Número de Requests')
    
    for bar, value in zip(bars2, total_requests):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(total_requests)*0.01, 
                f'{value:,}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Cache Hits
    ax3 = axes[0, 2]
    bars3 = ax3.bar(policies, cache_hits, color=colors[:len(policies)])
    ax3.set_title('✅ Cache Hits Absolutos')
    ax3.set_ylabel('Número de Hits')
    
    for bar, value in zip(bars3, cache_hits):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(cache_hits)*0.01, 
                f'{value:,}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Evictions
    ax4 = axes[1, 0]
    bars4 = ax4.bar(policies, evictions, color=colors[:len(policies)])
    ax4.set_title('🔄 Evictions del Cache')
    ax4.set_ylabel('Número de Evictions')
    
    for bar, value in zip(bars4, evictions):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(evictions)*0.01, 
                f'{value:,}', ha='center', va='bottom', fontweight='bold')
    
    # 5. Response Times
    ax5 = axes[1, 1]
    bars5 = ax5.bar(policies, response_times, color=colors[:len(policies)])
    ax5.set_title('⚡ Tiempo de Respuesta Promedio')
    ax5.set_ylabel('Tiempo (ms)')
    
    for bar, value in zip(bars5, response_times):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(response_times)*0.01, 
                f'{value:.2f}ms', ha='center', va='bottom', fontweight='bold')
    
    # 6. Eficiencia (Hit Rate vs Evictions)
    ax6 = axes[1, 2]
    scatter = ax6.scatter(evictions, hit_rates, c=range(len(policies)), 
                         s=200, cmap='viridis', alpha=0.7)
    
    for i, policy in enumerate(policies):
        ax6.annotate(policy, (evictions[i], hit_rates[i]), 
                    xytext=(5, 5), textcoords='offset points', fontweight='bold')
    
    ax6.set_xlabel('Número de Evictions')
    ax6.set_ylabel('Hit Rate (%)')
    ax6.set_title('🎯 Eficiencia: Hit Rate vs Evictions')
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar gráfico
    plot_path = os.path.join(output_dir, 'experiment_comparison.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"📊 Gráfico de comparación guardado en: {plot_path}")
    
    return plot_path

def generate_detailed_report(results, logs_analysis, output_dir='plots'):
    """Genera un reporte detallado en formato HTML"""
    os.makedirs(output_dir, exist_ok=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>📊 Reporte de Análisis de Cache - Experimentos 10K</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
            .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; }}
            .best {{ border-left-color: #28a745 !important; background: #d4edda !important; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .highlight {{ background-color: #fff3cd; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Reporte de Análisis de Cache</h1>
            <p>Experimentos con 10,000 preguntas reales del dataset</p>
            <p>Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    """
    
    if results:
        # Encontrar la mejor política
        best_policy = max(results.keys(), key=lambda k: results[k].get('hit_rate', 0))
        best_hit_rate = results[best_policy].get('hit_rate', 0) * 100
        
        html_content += f"""
        <div class="section">
            <h2>🏆 Resumen Ejecutivo</h2>
            <div class="metric best">
                <strong>Política Ganadora:</strong> {best_policy}<br>
                <strong>Hit Rate:</strong> {best_hit_rate:.2f}%
            </div>
        """
        
        for policy, data in results.items():
            css_class = "best" if policy == best_policy else ""
            html_content += f"""
            <div class="metric {css_class}">
                <strong>{policy}:</strong><br>
                Hit Rate: {data.get('hit_rate', 0)*100:.2f}%<br>
                Hits: {data.get('cache_hits', 0):,}<br>
                Evictions: {data.get('evictions', 0):,}
            </div>
            """
        
        html_content += "</div>"
        
        # Tabla detallada
        html_content += """
        <div class="section">
            <h2>📋 Comparación Detallada</h2>
            <table>
                <tr>
                    <th>Política</th>
                    <th>Hit Rate (%)</th>
                    <th>Total Requests</th>
                    <th>Cache Hits</th>
                    <th>Cache Misses</th>
                    <th>Evictions</th>
                    <th>Tiempo Respuesta (ms)</th>
                </tr>
        """
        
        for policy, data in results.items():
            highlight = "highlight" if policy == best_policy else ""
            html_content += f"""
                <tr class="{highlight}">
                    <td><strong>{policy}</strong></td>
                    <td>{data.get('hit_rate', 0)*100:.2f}%</td>
                    <td>{data.get('total_requests', 0):,}</td>
                    <td>{data.get('cache_hits', 0):,}</td>
                    <td>{data.get('cache_misses', 0):,}</td>
                    <td>{data.get('evictions', 0):,}</td>
                    <td>{data.get('avg_response_time', 0)*1000:.2f}</td>
                </tr>
            """
        
        html_content += "</table></div>"
    
    # Análisis de logs si está disponible
    if logs_analysis is not None and len(logs_analysis) > 0:
        total_hits = logs_analysis['hits'].sum()
        total_misses = logs_analysis['misses'].sum()
        avg_hit_rate = logs_analysis['hit_rate'].mean() * 100
        
        html_content += f"""
        <div class="section">
            <h2>📊 Análisis de Logs en Tiempo Real</h2>
            <div class="metric">
                <strong>Total Cache Hits:</strong> {total_hits:,}
            </div>
            <div class="metric">
                <strong>Total Cache Misses:</strong> {total_misses:,}
            </div>
            <div class="metric">
                <strong>Hit Rate Promedio:</strong> {avg_hit_rate:.2f}%
            </div>
        </div>
        """
    
    html_content += """
        <div class="section">
            <h2>📈 Gráficos Generados</h2>
            <p>Los siguientes gráficos han sido generados:</p>
            <ul>
                <li>📊 cache_performance_analysis.png - Análisis de rendimiento en tiempo real</li>
                <li>🏆 experiment_comparison.png - Comparación de políticas de cache</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    report_path = os.path.join(output_dir, 'cache_analysis_report.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 Reporte HTML generado en: {report_path}")
    return report_path

def main():
    print("📊 ANALIZADOR DE LOGS Y VISUALIZADOR DE EXPERIMENTOS")
    print("=" * 60)
    
    # Crear directorio de plots
    os.makedirs('plots', exist_ok=True)
    
    # 1. Analizar logs del cache
    print("\n🔍 Analizando logs del servicio cache...")
    cache_logs = get_docker_logs('cache', lines=2000)
    
    if cache_logs:
        events = parse_cache_logs(cache_logs)
        print(f"📝 Encontrados {len(events)} eventos en los logs")
        
        metrics = analyze_cache_performance(events)
        if metrics is not None:
            print(f"📊 Analizadas {len(metrics)} ventanas de tiempo")
            create_cache_performance_plots(metrics)
        else:
            print("⚠️ No hay suficientes datos con timestamps para análisis temporal")
            metrics = None
    else:
        print("❌ No se pudieron obtener logs del cache")
        metrics = None
    
    # 2. Analizar resultados de experimentos
    print("\n🧪 Analizando resultados de experimentos...")
    results = analyze_experiment_results()
    
    if results:
        print(f"📋 Encontrados resultados de {len(results)} experimentos: {', '.join(results.keys())}")
        create_experiment_comparison_plots(results)
    else:
        print("⚠️ No se encontraron resultados de experimentos")
    
    # 3. Generar reporte detallado
    print("\n📄 Generando reporte detallado...")
    generate_detailed_report(results, metrics)
    
    print("\n✅ Análisis completado!")
    print("📁 Archivos generados en la carpeta 'plots/':")
    print("   📊 cache_performance_analysis.png")
    print("   🏆 experiment_comparison.png")
    print("   📄 cache_analysis_report.html")
    print("\n💡 Abre 'plots/cache_analysis_report.html' en tu navegador para ver el reporte completo")

if __name__ == "__main__":
    main()