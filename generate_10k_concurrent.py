#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Configuración
GENERATOR_URL = "http://localhost:8000/generate/batch"
STORAGE_URL = "http://localhost:8004/stats"
TARGET_QUESTIONS = 10000
BATCH_SIZE = 20  # Preguntas por lote (aumentado para ser más eficiente)
MAX_CONCURRENT = 5  # Número máximo de requests concurrentes (reducido mucho más)
DELAY_BETWEEN_BATCHES = 1.0  # Delay en segundos entre lotes (aumentado para mayor estabilidad)

async def send_batch(session, batch_num, batch_size):
    """Envía un lote de preguntas al generador"""
    try:
        payload = {"num_questions": batch_size}
        async with session.post(GENERATOR_URL, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✓ Lote {batch_num}: {batch_size} preguntas enviadas")
                return batch_size
            else:
                error_text = await response.text()
                print(f"✗ Error en lote {batch_num}: HTTP {response.status} - {error_text[:100]}")
                return 0
    except asyncio.TimeoutError:
        print(f"✗ Timeout en lote {batch_num}")
        return 0
    except Exception as e:
        print(f"✗ Error en lote {batch_num}: {str(e)[:100]}")
        return 0

async def get_stats(session):
    """Obtiene estadísticas del storage"""
    try:
        async with session.get(STORAGE_URL) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return None

async def monitor_progress(session, initial_records):
    """Monitorea el progreso del procesamiento"""
    while True:
        stats = await get_stats(session)
        if stats:
            current_records = stats.get('records_with_answers', 0)
            processed = current_records - initial_records
            print(f"📊 Progreso: {processed} preguntas procesadas, Score promedio: {stats.get('average_score', 0):.3f}")
        await asyncio.sleep(10)

async def main():
    print(f"🚀 Iniciando generación concurrente de {TARGET_QUESTIONS} preguntas")
    print(f"📦 Lotes de {BATCH_SIZE} preguntas con máximo {MAX_CONCURRENT} concurrentes")
    
    # Configurar sesión HTTP con timeout más alto
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # Obtener estadísticas iniciales
        initial_stats = await get_stats(session)
        initial_records = initial_stats.get('records_with_answers', 0) if initial_stats else 0
        print(f"📈 Records iniciales con respuestas: {initial_records}")
        
        # Iniciar monitor de progreso en background
        monitor_task = asyncio.create_task(monitor_progress(session, initial_records))
        
        # Calcular número de lotes necesarios
        total_batches = (TARGET_QUESTIONS + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"📊 Total de lotes a enviar: {total_batches}")
        
        # Crear semáforo para controlar concurrencia
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        async def send_with_semaphore(batch_num, batch_size):
            async with semaphore:
                result = await send_batch(session, batch_num, batch_size)
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)
                return result
        
        # Enviar todos los lotes concurrentemente
        start_time = time.time()
        tasks = []
        
        for i in range(total_batches):
            batch_num = i + 1
            # Calcular el tamaño del lote (el último puede ser menor)
            remaining = TARGET_QUESTIONS - (i * BATCH_SIZE)
            current_batch_size = min(BATCH_SIZE, remaining)
            
            task = send_with_semaphore(batch_num, current_batch_size)
            tasks.append(task)
        
        # Ejecutar todos los lotes
        print(f"⏳ Enviando {total_batches} lotes...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calcular resultados
        total_sent = sum(r for r in results if isinstance(r, int))
        failed_batches = sum(1 for r in results if isinstance(r, Exception) or r == 0)
        
        elapsed_time = time.time() - start_time
        
        # Cancelar monitor
        monitor_task.cancel()
        
        # Estadísticas finales
        print(f"\n🎯 Resumen de envío:")
        print(f"   • Total preguntas enviadas: {total_sent}")
        print(f"   • Lotes exitosos: {total_batches - failed_batches}")
        print(f"   • Lotes fallidos: {failed_batches}")
        print(f"   • Tiempo total: {elapsed_time:.2f} segundos")
        print(f"   • Velocidad: {total_sent/elapsed_time:.1f} preguntas/segundo")
        
        # Estadísticas finales del storage
        final_stats = await get_stats(session)
        if final_stats:
            final_records = final_stats.get('records_with_answers', 0)
            total_processed = final_records - initial_records
            print(f"\n📈 Estado del sistema:")
            print(f"   • Records procesados durante la ejecución: {total_processed}")
            print(f"   • Total records con respuestas: {final_records}")
            print(f"   • Score promedio: {final_stats.get('average_score', 0):.3f}")

if __name__ == "__main__":
    asyncio.run(main())