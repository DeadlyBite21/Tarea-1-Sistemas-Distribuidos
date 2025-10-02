#!/usr/bin/env python3
"""
🎨 COORDINADOR DE VISUALIZACIONES
Dashboard para generar y gestionar todos los gráficos y análisis
"""

import os
import subprocess
import webbrowser
from datetime import datetime

def show_available_plots():
    """Muestra los gráficos disponibles"""
    plots_dir = "plots"
    if not os.path.exists(plots_dir):
        print("❌ Carpeta 'plots' no encontrada")
        return
    
    files = [f for f in os.listdir(plots_dir) if f.endswith(('.png', '.html', '.jpg', '.jpeg'))]
    
    if not files:
        print("📂 No hay gráficos disponibles en la carpeta 'plots'")
        return
    
    print("📊 GRÁFICOS DISPONIBLES:")
    print("=" * 50)
    
    for i, file in enumerate(files, 1):
        size = os.path.getsize(os.path.join(plots_dir, file))
        size_mb = size / (1024 * 1024)
        
        # Emojis por tipo de archivo
        emoji = "🌐" if file.endswith('.html') else "📊"
        
        print(f"{i:2d}. {emoji} {file} ({size_mb:.2f} MB)")

def open_plot(filename):
    """Abre un gráfico en el visor predeterminado"""
    plot_path = os.path.join("plots", filename)
    
    if not os.path.exists(plot_path):
        print(f"❌ Archivo {filename} no encontrado")
        return False
    
    try:
        if filename.endswith('.html'):
            # Abrir HTML en navegador
            webbrowser.open(f"file://{os.path.abspath(plot_path)}")
            print(f"🌐 Abriendo {filename} en navegador...")
        else:
            # Abrir imagen en visor predeterminado
            if os.name == 'nt':  # Windows
                os.startfile(plot_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', plot_path])
            print(f"📊 Abriendo {filename}...")
        
        return True
    except Exception as e:
        print(f"❌ Error abriendo {filename}: {e}")
        return False

def generate_all_plots():
    """Genera todos los tipos de gráficos disponibles"""
    print("🎨 GENERANDO TODOS LOS GRÁFICOS...")
    print("=" * 50)
    
    scripts = [
        ("quick_graphs.py", "📊 Gráficos del experimento LFU"),
        ("docker_analyzer.py", "🐳 Análisis de servicios Docker"),
        ("log_analyzer.py", "📝 Análisis completo de logs")
    ]
    
    python_cmd = "/Users/benjaminzunigapueller/Documents/GitHub/Tarea-1-Sistemas-Distribuidos/.venv/bin/python"
    
    for script, description in scripts:
        if os.path.exists(script):
            print(f"\\n🔄 {description}...")
            try:
                result = subprocess.run([python_cmd, script], 
                                      capture_output=True, text=True, check=True)
                print(f"✅ {script} ejecutado exitosamente")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error ejecutando {script}: {e}")
        else:
            print(f"⚠️ {script} no encontrado")

def create_dashboard_html():
    """Crea un dashboard HTML con todos los gráficos"""
    plots_dir = "plots"
    os.makedirs(plots_dir, exist_ok=True)
    
    # Obtener archivos de imagen
    image_files = [f for f in os.listdir(plots_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    html_files = [f for f in os.listdir(plots_dir) if f.endswith('.html') and f != 'dashboard.html']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>📊 Dashboard de Análisis de Cache</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{ 
                text-align: center; 
                margin-bottom: 40px; 
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }}
            .section {{ 
                margin: 30px 0; 
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 5px solid #007bff;
            }}
            .image-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 30px;
                margin: 20px 0;
            }}
            .image-container {{
                text-align: center;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .image-container img {{
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            .image-title {{
                font-weight: bold;
                margin: 10px 0;
                color: #333;
            }}
            .stats {{
                background: #e8f5e8;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .links {{
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                justify-content: center;
                margin: 20px 0;
            }}
            .link {{
                background: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }}
            .link:hover {{
                background: #0056b3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Dashboard de Análisis de Cache</h1>
                <p>Sistema Distribuido de Q&A con 10,000 Preguntas Reales</p>
                <p>Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
    """
    
    # Sección de reportes HTML
    if html_files:
        html_content += """
            <div class="section">
                <h2>📄 Reportes Detallados</h2>
                <div class="links">
        """
        
        for html_file in html_files:
            name = html_file.replace('_', ' ').replace('.html', '').title()
            html_content += f'<a href="{html_file}" class="link">🌐 {name}</a>'
        
        html_content += "</div></div>"
    
    # Sección de gráficos
    if image_files:
        html_content += """
            <div class="section">
                <h2>📊 Visualizaciones Generadas</h2>
                <div class="image-grid">
        """
        
        for image_file in image_files:
            # Crear título descriptivo
            title = image_file.replace('_', ' ').replace('.png', '').title()
            if 'lfu' in image_file.lower():
                title = "🧪 " + title + " - Experimento LFU"
            elif 'docker' in image_file.lower():
                title = "🐳 " + title + " - Servicios Docker"
            elif 'system' in image_file.lower():
                title = "🏗️ " + title + " - Arquitectura"
            else:
                title = "📊 " + title
            
            html_content += f"""
                <div class="image-container">
                    <div class="image-title">{title}</div>
                    <img src="{image_file}" alt="{title}" />
                    <div class="stats">
                        <small>Archivo: {image_file}</small>
                    </div>
                </div>
            """
        
        html_content += "</div></div>"
    
    # Información del sistema
    html_content += """
        <div class="section">
            <h2>⚙️ Información del Sistema</h2>
            <div class="stats">
                <strong>🏗️ Arquitectura:</strong> Microservicios con Docker Compose<br>
                <strong>💾 Cache:</strong> Políticas LRU, LFU, FIFO<br>
                <strong>🤖 LLM:</strong> Google Gemini 2.5 Flash<br>
                <strong>📊 Dataset:</strong> 1.4M+ preguntas reales<br>
                <strong>🔄 Messaging:</strong> Apache Kafka<br>
                <strong>⚡ Rate Limit:</strong> 10 RPM (Gemini API)
            </div>
        </div>
        
        <div class="section">
            <h2>🛠️ Herramientas de Análisis</h2>
            <p>Este dashboard fue generado usando las siguientes herramientas:</p>
            <ul>
                <li>📊 <strong>quick_graphs.py</strong> - Análisis específico del experimento LFU</li>
                <li>🐳 <strong>docker_analyzer.py</strong> - Métricas de servicios Docker</li>
                <li>📝 <strong>log_analyzer.py</strong> - Análisis completo de logs</li>
                <li>🎨 <strong>visualization_coordinator.py</strong> - Coordinador de visualizaciones</li>
            </ul>
        </div>
        
        </div>
    </body>
    </html>
    """
    
    dashboard_path = os.path.join(plots_dir, 'dashboard.html')
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"🎨 Dashboard generado en: {dashboard_path}")
    return dashboard_path

def main():
    import sys
    
    print("🎨 COORDINADOR DE VISUALIZACIONES")
    print("=" * 50)
    
    if len(sys.argv) == 1:
        print("📖 USO:")
        print("  python3 visualization_coordinator.py list      - Ver gráficos disponibles")
        print("  python3 visualization_coordinator.py generate  - Generar todos los gráficos")
        print("  python3 visualization_coordinator.py dashboard - Crear dashboard HTML")
        print("  python3 visualization_coordinator.py open [archivo] - Abrir gráfico específico")
        print("  python3 visualization_coordinator.py view      - Abrir dashboard en navegador")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        show_available_plots()
    
    elif command == "generate":
        generate_all_plots()
        print("\\n✅ Generación completada")
        show_available_plots()
    
    elif command == "dashboard":
        dashboard_path = create_dashboard_html()
        print("\\n💡 Para ver el dashboard, ejecuta:")
        print(f"   python3 visualization_coordinator.py view")
    
    elif command == "open" and len(sys.argv) > 2:
        filename = sys.argv[2]
        open_plot(filename)
    
    elif command == "view":
        dashboard_path = os.path.join("plots", "dashboard.html")
        if os.path.exists(dashboard_path):
            open_plot("dashboard.html")
        else:
            print("❌ Dashboard no encontrado. Ejecuta 'dashboard' primero.")
    
    else:
        print(f"❌ Comando '{command}' no reconocido")

if __name__ == "__main__":
    main()