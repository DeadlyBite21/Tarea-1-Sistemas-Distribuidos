import json
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer
import random
import aiohttp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales para Kafka
kafka_producer: Optional[AIOKafkaProducer] = None

# URL del servicio de storage
STORAGE_SERVICE_URL = "http://storage:8004"

async def get_random_question_from_storage():
    """Obtener una pregunta aleatoria del servicio de storage"""
    try:
        async with aiohttp.ClientSession() as session:
            # Intentar obtener una pregunta aleatoria del storage usando el parámetro random
            async with session.get(f"{STORAGE_SERVICE_URL}/questions?limit=1&random=true") as response:
                if response.status == 200:
                    data = await response.json()
                    questions = data.get('questions', [])
                    if questions and len(questions) > 0:
                        question = questions[0].get('question', '').strip()
                        if question:
                            return question
        
        # Si no se puede obtener del storage, usar fallback
        logger.warning("No se pudo obtener pregunta del storage, usando fallback")
        return random.choice(FALLBACK_QUESTIONS)
        
    except Exception as e:
        logger.error(f"Error obteniendo pregunta del storage: {e}")
        return random.choice(FALLBACK_QUESTIONS)

async def init_kafka():
    """Inicializar productor de Kafka"""
    global kafka_producer
    
    try:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers='kafka:29092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await kafka_producer.start()
        logger.info("Kafka producer iniciado correctamente")
        
    except Exception as e:
        logger.error(f"Error al inicializar Kafka: {e}")
        raise

async def close_kafka():
    """Cerrar conexión de Kafka"""
    global kafka_producer
    
    if kafka_producer:
        await kafka_producer.stop()
    
    logger.info("Conexión de Kafka cerrada")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    await init_kafka()
    yield
    # Shutdown
    await close_kafka()

# Crear aplicación FastAPI
app = FastAPI(
    title="Generator Service",
    description="Servicio generador de tráfico de preguntas",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/generate")
async def generate_question():
    """Generar una pregunta aleatoria y enviarla al sistema"""
    try:
        if not kafka_producer:
            raise HTTPException(status_code=500, detail="Kafka producer no disponible")
        
        # Obtener pregunta aleatoria del storage
        question = await get_random_question_from_storage()
        
        # Crear mensaje con ID único y timestamp
        message = {
            'id': str(uuid.uuid4()),
            'question': question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Enviar mensaje al topic de requests
        await kafka_producer.send('questions.requests', message)
        
        logger.info(f"Pregunta generada y enviada: {question}")
        
        return {
            "status": "success",
            "message": "Pregunta enviada al sistema",
            "question": question,
            "id": message['id']
        }
        
    except Exception as e:
        logger.error(f"Error generando pregunta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/custom")
async def generate_custom_question(question_data: dict):
    """Generar una pregunta personalizada"""
    try:
        if not kafka_producer:
            raise HTTPException(status_code=500, detail="Kafka producer no disponible")
        
        question = question_data.get('question', '').strip()
        
        if not question:
            raise HTTPException(status_code=400, detail="Pregunta no puede estar vacía")
        
        # Crear mensaje con ID único y timestamp
        message = {
            'id': str(uuid.uuid4()),
            'question': question,
            'timestamp': datetime.now().isoformat()
        }
        
        # Enviar mensaje al topic de requests
        await kafka_producer.send('questions.requests', message)
        
        logger.info(f"Pregunta personalizada enviada: {question}")
        
        return {
            "status": "success",
            "message": "Pregunta personalizada enviada al sistema",
            "question": question,
            "id": message['id']
        }
        
    except Exception as e:
        logger.error(f"Error enviando pregunta personalizada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/batch")
async def generate_batch_questions(batch_data: dict):
    """Generar múltiples preguntas aleatorias"""
    try:
        if not kafka_producer:
            raise HTTPException(status_code=500, detail="Kafka producer no disponible")
        
        count = batch_data.get('num_questions', batch_data.get('count', 5))
        count = min(max(count, 1), 10000)  # Limitar entre 1 y 10,000
        
        messages = []
        
        for _ in range(count):
            question = await get_random_question_from_storage()
            message = {
                'id': str(uuid.uuid4()),
                'question': question,
                'timestamp': datetime.now().isoformat()
            }
            
            await kafka_producer.send('questions.requests', message)
            messages.append({
                'id': message['id'],
                'question': question
            })
        
        logger.info(f"Enviadas {count} preguntas en lote")
        
        return {
            "status": "success",
            "message": f"{count} preguntas enviadas al sistema",
            "questions": messages
        }
        
    except Exception as e:
        logger.error(f"Error generando lote de preguntas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": "generator",
        "kafka_connected": kafka_producer is not None
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Generator Service - Traffic Generator",
        "endpoints": {
            "generate": "POST /generate - Generar pregunta aleatoria",
            "custom": "POST /generate/custom - Enviar pregunta personalizada", 
            "batch": "POST /generate/batch - Generar múltiples preguntas"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
