import json
import asyncio
import logging
import sqlite3
import csv
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales
kafka_consumer: Optional[AIOKafkaConsumer] = None
DB = "data.db"
DATASET = "train.csv"
used_question_ids = set()  # Para evitar repetir preguntas

def init_db():
    """Inicializar base de datos"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS qa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT,
        question TEXT,
        best_answer TEXT,
        generated_answer TEXT,
        score REAL,
        timestamp TEXT,
        count INTEGER DEFAULT 1
    )""")
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada")

def load_dataset():
    """Cargar dataset si la DB está vacía"""
    if not os.path.exists(DATASET):
        logger.warning(f"Dataset {DATASET} no encontrado en el contenedor")
        return
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Verificar si ya hay datos
    count = c.execute("SELECT COUNT(*) FROM qa").fetchone()[0]
    if count > 0:
        logger.info(f"Base de datos ya contiene {count} registros")
        conn.close()
        return
    
    logger.info("Cargando dataset en la base de datos...")
    
    with open(DATASET, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # saltar header
        loaded = 0
        for row in reader:
            try:
                _, title, content, best = row
                q = title if title else content
                c.execute("INSERT INTO qa (question, best_answer) VALUES (?,?)", (q, best))
                loaded += 1
            except (ValueError, IndexError):
                continue
    
    conn.commit()
    conn.close()
    logger.info(f"Dataset cargado: {loaded} registros")

async def init_kafka():
    """Inicializar consumidor de Kafka"""
    global kafka_consumer
    
    try:
        kafka_consumer = AIOKafkaConsumer(
            'storage.persist',
            bootstrap_servers='kafka:29092',
            auto_offset_reset='earliest',
            group_id='storage_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await kafka_consumer.start()
        logger.info("Kafka consumer iniciado correctamente")
        
        # Iniciar el loop de consumo
        asyncio.create_task(consume_loop())
        
    except Exception as e:
        logger.error(f"Error al inicializar Kafka: {e}")
        raise

async def close_kafka():
    """Cerrar conexión de Kafka"""
    global kafka_consumer
    
    if kafka_consumer:
        await kafka_consumer.stop()
    
    logger.info("Conexión de Kafka cerrada")

async def consume_loop():
    """Loop principal para consumir mensajes de Kafka"""
    try:
        async for message in kafka_consumer:
            logger.info(f"Mensaje recibido para almacenamiento: {message.value}")
            await process_message(message.value)
    except Exception as e:
        logger.error(f"Error en consume_loop: {e}")

async def process_message(message_data):
    """Procesar mensaje y almacenar en base de datos"""
    try:
        message_id = message_data.get('id', '')
        question = message_data.get('question', '')
        answer = message_data.get('answer', '')
        score = message_data.get('score', 0.0)
        timestamp = message_data.get('timestamp', '')
        
        if not question or not answer:
            logger.warning("Mensaje incompleto recibido")
            return
        
        # Guardar en base de datos
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Verificar si ya existe esta pregunta
        existing = c.execute(
            "SELECT id, count FROM qa WHERE question=? LIMIT 1", 
            (question,)
        ).fetchone()
        
        if existing:
            # Actualizar registro existente
            c.execute(
                "UPDATE qa SET message_id=?, generated_answer=?, score=?, timestamp=?, count=? WHERE id=?",
                (message_id, answer, score, timestamp, existing[1] + 1, existing[0])
            )
            logger.info(f"Registro actualizado para pregunta existente (count: {existing[1] + 1})")
        else:
            # Insertar nuevo registro
            c.execute(
                "INSERT INTO qa (message_id, question, generated_answer, score, timestamp) VALUES (?,?,?,?,?)",
                (message_id, question, answer, score, timestamp)
            )
            logger.info("Nuevo registro insertado")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error procesando mensaje para almacenamiento: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    init_db()
    load_dataset()
    await init_kafka()
    
    yield
    
    # Shutdown
    await close_kafka()

# Crear aplicación FastAPI
app = FastAPI(
    title="Storage Service",
    description="Servicio de almacenamiento de preguntas y respuestas",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        count = c.execute("SELECT COUNT(*) FROM qa").fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "service": "storage",
            "kafka_connected": kafka_consumer is not None,
            "database_records": count
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "storage",
            "error": str(e)
        }

@app.get("/stats")
async def get_stats():
    """Estadísticas de la base de datos"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        total = c.execute("SELECT COUNT(*) FROM qa").fetchone()[0]
        with_answers = c.execute("SELECT COUNT(*) FROM qa WHERE generated_answer IS NOT NULL").fetchone()[0]
        avg_score = c.execute("SELECT AVG(score) FROM qa WHERE score IS NOT NULL").fetchone()[0]
        
        conn.close()
        
        return {
            "total_records": total,
            "records_with_answers": with_answers,
            "average_score": round(avg_score, 3) if avg_score else 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/records")
async def get_records(limit: int = 20):
    """Obtener registros de la base de datos"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        c.execute("SELECT * FROM qa ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                "id": row[0],
                "message_id": row[1],
                "question": row[2],
                "best_answer": row[3],
                "generated_answer": row[4],
                "score": row[5],
                "timestamp": row[6],
                "count": row[7]
            })
        
        return {"records": records}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/random")
async def get_random_question():
    """Obtener una pregunta aleatoria"""
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        c.execute("SELECT id, question, best_answer FROM qa ORDER BY RANDOM() LIMIT 1")
        row = c.fetchone()
        
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "question": row[1],
                "best_answer": row[2]
            }
        else:
            raise HTTPException(status_code=404, detail="No data in database")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/questions")
async def get_questions(limit: int = 100, offset: int = 0, random: bool = False, reset_history: bool = False):
    """Obtener múltiples preguntas de la base de datos"""
    global used_question_ids
    
    # Resetear historial si se solicita
    if reset_history:
        used_question_ids.clear()
    
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        if random:
            # Para preguntas aleatorias, excluir las ya usadas
            if used_question_ids:
                placeholders = ','.join(['?' for _ in used_question_ids])
                query = f"""
                    SELECT id, question, best_answer FROM qa 
                    WHERE question IS NOT NULL AND question != '' 
                    AND id NOT IN ({placeholders})
                    ORDER BY RANDOM() LIMIT ?
                """
                params = list(used_question_ids) + [limit]
            else:
                query = """
                    SELECT id, question, best_answer FROM qa 
                    WHERE question IS NOT NULL AND question != '' 
                    ORDER BY RANDOM() LIMIT ?
                """
                params = [limit]
            
            c.execute(query, params)
            rows = c.fetchall()
            
            # Si no hay suficientes preguntas nuevas, resetear y obtener más
            if len(rows) < limit and used_question_ids:
                used_question_ids.clear()
                c.execute("""
                    SELECT id, question, best_answer FROM qa 
                    WHERE question IS NOT NULL AND question != '' 
                    ORDER BY RANDOM() LIMIT ?
                """, (limit,))
                rows = c.fetchall()
        else:
            # Obtener preguntas con paginación (sin filtro de repetición)
            c.execute("SELECT id, question, best_answer FROM qa WHERE question IS NOT NULL AND question != '' LIMIT ? OFFSET ?", (limit, offset))
            rows = c.fetchall()
        
        conn.close()
        
        questions = []
        for row in rows:
            questions.append({
                "id": row[0],
                "question": row[1],
                "best_answer": row[2]
            })
            # Agregar al historial si es aleatorio
            if random:
                used_question_ids.add(row[0])
        
        return {
            "questions": questions,
            "count": len(questions),
            "limit": limit,
            "offset": offset,
            "random": random,
            "used_questions_count": len(used_question_ids) if random else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset_history")
async def reset_question_history():
    """Resetear el historial de preguntas usadas"""
    global used_question_ids
    count = len(used_question_ids)
    used_question_ids.clear()
    return {
        "message": "Historial de preguntas reseteado",
        "previous_count": count,
        "current_count": len(used_question_ids)
    }

@app.get("/popular_questions")
async def get_popular_questions(limit: int = 50, random: bool = False, reset_history: bool = False):
    """Obtener preguntas más frecuentes (si han sido procesadas múltiples veces)"""
    global used_question_ids
    
    # Resetear historial si se solicita
    if reset_history:
        used_question_ids.clear()
    
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        if random:
            # Para preguntas aleatorias, excluir las ya usadas
            if used_question_ids:
                placeholders = ','.join(['?' for _ in used_question_ids])
                query = f"""
                    SELECT id, question, best_answer, count, score 
                    FROM qa 
                    WHERE question IS NOT NULL AND question != '' 
                    AND id NOT IN ({placeholders})
                    ORDER BY RANDOM() 
                    LIMIT ?
                """
                params = list(used_question_ids) + [limit]
            else:
                query = """
                    SELECT id, question, best_answer, count, score 
                    FROM qa 
                    WHERE question IS NOT NULL AND question != '' 
                    ORDER BY RANDOM() 
                    LIMIT ?
                """
                params = [limit]
            
            c.execute(query, params)
            rows = c.fetchall()
            
            # Si no hay suficientes preguntas nuevas, resetear y obtener más
            if len(rows) < limit and used_question_ids:
                used_question_ids.clear()
                c.execute("""
                    SELECT id, question, best_answer, count, score 
                    FROM qa 
                    WHERE question IS NOT NULL AND question != '' 
                    ORDER BY RANDOM() 
                    LIMIT ?
                """, (limit,))
                rows = c.fetchall()
        else:
            # Ordenar por popularidad (count y score)
            c.execute("""
                SELECT id, question, best_answer, count, score 
                FROM qa 
                WHERE question IS NOT NULL AND question != '' 
                ORDER BY count DESC, score DESC 
                LIMIT ?
            """, (limit,))
            rows = c.fetchall()
        
        conn.close()
        
        questions = []
        for row in rows:
            questions.append({
                "id": row[0],
                "question": row[1],
                "best_answer": row[2],
                "count": row[3] or 1,
                "score": row[4]
            })
            # Agregar al historial si es aleatorio
            if random:
                used_question_ids.add(row[0])
        
        return {
            "questions": questions,
            "count": len(questions),
            "criteria": "random" if random else "popularity",
            "used_questions_count": len(used_question_ids) if random else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "Storage Service - Question & Answer Storage"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
