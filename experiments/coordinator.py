#!/usr/bin/env python3
"""
🧪 COORDINADOR DE EXPERIMENTOS - 10,000 PREGUNTAS REALES
Sistema de gestión para experimentos distribuidos entre equipo
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def check_system_health():
    """Verifica que todos los servicios estén funcionando"""
    print("🔍 VERIFICANDO ESTADO DEL SISTEMA...")
    
    services = {
        "Generator": "http://localhost:8000/health",
        "Cache": "http://localhost:8001/health", 
        "LLM": "http://localhost:8003/health",
        "Storage": "http://localhost:8004/health",
        "Score": "http://localhost:8002/health"
    }
    
    all_healthy = True
    
    for service, url in services.items():
        try:
            result = subprocess.run(
                ["curl", "-s", url], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get('status') == 'healthy':
                    print(f"  ✅ {service}: Healthy")
                else:
                    print(f"  ❌ {service}: Unhealthy")
                    all_healthy = False
            else:
                print(f"  ❌ {service}: No responde")
                all_healthy = False
        except Exception as e:
            print(f"  ❌ {service}: Error - {e}")
            all_healthy = False
    
    return all_healthy

def show_team_assignment():
    """Muestra la asignación de experimentos por compañero"""
    print(f"\n{'='*60}")
    print("👥 ASIGNACIÓN DE EXPERIMENTOS POR COMPAÑERO")
    print(f"{'='*60}")
    print("📋 Cada experimento toma ~16.7 horas")
    print("🎯 Total: 10,000 preguntas reales por experimento")
    print()
    print("🔵 COMPAÑERO 1 - EXPERIMENTO LRU:")
    print("   📁 Archivo: individual_experiments/experiment_lru.py")
    print("   💾 Resultado: results/lru_results.json")
    print("   ⏱️ Duración estimada: ~16.7 horas")
    print()
    print("🟢 COMPAÑERO 2 - EXPERIMENTO LFU:")
    print("   📁 Archivo: individual_experiments/experiment_lfu.py")
    print("   💾 Resultado: results/lfu_results.json")
    print("   ⏱️ Duración estimada: ~16.7 horas")
    print()
    print("🟡 COMPAÑERO 3 - EXPERIMENTO FIFO:")
    print("   📁 Archivo: individual_experiments/experiment_fifo.py")
    print("   💾 Resultado: results/fifo_results.json")
    print("   ⏱️ Duración estimada: ~16.7 horas")

def run_individual_experiment(policy):
    """Ejecuta un experimento individual"""
    policy_upper = policy.upper()
    script_path = f"individual_experiments/experiment_{policy.lower()}.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Archivo {script_path} no encontrado")
        return False
    
    print(f"\n🚀 INICIANDO EXPERIMENTO {policy_upper}")
    print(f"📁 Ejecutando: {script_path}")
    print(f"⏱️ Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️ Este proceso tomará aproximadamente 16.7 horas")
    print("💡 Puedes usar Ctrl+C para cancelar si es necesario")
    
    try:
        # Crear directorio de resultados si no existe
        os.makedirs("results", exist_ok=True)
        
        # Ejecutar experimento
        subprocess.run([sys.executable, script_path], check=True)
        
        print(f"✅ Experimento {policy_upper} completado exitosamente")
        return True
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Experimento {policy_upper} cancelado por el usuario")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando experimento {policy_upper}: {e}")
        return False

def check_results():
    """Verifica qué resultados están disponibles"""
    print("\n📊 VERIFICANDO RESULTADOS DISPONIBLES...")
    
    results_dir = "results"
    expected_files = ["lru_results.json", "lfu_results.json", "fifo_results.json"]
    found_files = []
    
    if os.path.exists(results_dir):
        for filename in expected_files:
            filepath = os.path.join(results_dir, filename)
            if os.path.exists(filepath):
                found_files.append(filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        policy = filename.replace('_results.json', '').upper()
                        hit_rate = data.get('hit_rate', 0)
                        total_requests = data.get('total_requests', 0)
                        print(f"  ✅ {policy}: {total_requests:,} requests, {hit_rate:.2%} hit rate")
                except:
                    print(f"  ⚠️ {filename}: Archivo existe pero con errores")
            else:
                policy = filename.replace('_results.json', '').upper()
                print(f"  ❌ {policy}: Sin resultados")
    
    print(f"\n📈 Progreso: {len(found_files)}/3 experimentos completados")
    
    if len(found_files) == 3:
        print("🎉 ¡Todos los experimentos completados!")
        print("💡 Ejecuta la comparación con: python3 run_comparison.py")
    
    return found_files

def run_comparison():
    """Ejecuta la comparación de resultados"""
    found_files = check_results()
    
    if len(found_files) < 2:
        print("❌ Se necesitan al menos 2 experimentos completados para comparar")
        return False
    
    print(f"\n🔄 EJECUTANDO COMPARACIÓN DE RESULTADOS...")
    
    try:
        subprocess.run([sys.executable, "compare_results.py"], check=True)
        print("✅ Comparación completada exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comparación: {e}")
        return False

def main():
    print("🧪 COORDINADOR DE EXPERIMENTOS DE CACHE")
    print("📋 Sistema distribuido para 10,000 preguntas reales")
    print(f"⏰ Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if len(sys.argv) < 2:
        print("\n📖 USO:")
        print("  python3 coordinator.py check        - Verificar estado del sistema")
        print("  python3 coordinator.py team         - Mostrar asignación del equipo")
        print("  python3 coordinator.py lru          - Ejecutar experimento LRU")
        print("  python3 coordinator.py lfu          - Ejecutar experimento LFU")
        print("  python3 coordinator.py fifo         - Ejecutar experimento FIFO")
        print("  python3 coordinator.py results      - Verificar resultados disponibles")
        print("  python3 coordinator.py compare      - Comparar todos los resultados")
        return
    
    command = sys.argv[1].lower()
    
    if command == "check":
        if check_system_health():
            print("\n✅ Sistema listo para experimentos")
        else:
            print("\n❌ Sistema no está listo. Verificar servicios.")
    
    elif command == "team":
        show_team_assignment()
    
    elif command in ["lru", "lfu", "fifo"]:
        if not check_system_health():
            print("❌ Sistema no está listo. Ejecuta 'check' primero.")
            return
        run_individual_experiment(command)
    
    elif command == "results":
        check_results()
    
    elif command == "compare":
        run_comparison()
    
    else:
        print(f"❌ Comando '{command}' no reconocido")
        print("💡 Usa 'python3 coordinator.py' para ver ayuda")

if __name__ == "__main__":
    main()