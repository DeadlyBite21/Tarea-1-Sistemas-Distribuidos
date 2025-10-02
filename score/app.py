
import json
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None

async def init_kafka():
    """Inicializar consumidor y productor de Kafka"""
    global kafka_consumer, kafka_producer
    
    try:
        kafka_consumer = AIOKafkaConsumer(
            'questions.answers',
            bootstrap_servers='kafka:29092',
            auto_offset_reset='earliest',
            group_id='score_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers='kafka:29092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await kafka_consumer.start()
        await kafka_producer.start()
        
        logger.info("Kafka consumer y producer iniciados correctamente")
        
        asyncio.create_task(consume_loop())
        
    except Exception as e:
        logger.error(f"Error al inicializar Kafka: {e}")
        raise

async def close_kafka():
    """Cerrar conexiones de Kafka"""
    global kafka_consumer, kafka_producer
    
    if kafka_consumer:
        await kafka_consumer.stop()
    if kafka_producer:
        await kafka_producer.stop()
    
    logger.info("Conexiones de Kafka cerradas")

async def consume_loop():
    """Loop principal para consumir mensajes de Kafka"""
    try:
        async for message in kafka_consumer:
            logger.info(f"Mensaje recibido para scoring: {message.value}")
            await process_message(message.value)
    except Exception as e:
        logger.error(f"Error en consume_loop: {e}")

async def process_message(message_data):
    """Procesar mensaje de respuesta y calcular score"""
    try:
        question = message_data.get('question', '')
        answer = message_data.get('answer', '')
        message_id = message_data.get('id', '')
        timestamp = message_data.get('timestamp', '')
        
        score = calculate_score(question, answer)
        
        storage_message = {
            'id': message_id,
            'question': question,
            'answer': answer,
            'score': score,
            'timestamp': timestamp
        }
        
        await kafka_producer.send('storage.persist', storage_message)
        logger.info(f"Mensaje enviado a storage con score: {score}")
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

def calculate_score(question: str, answer: str) -> float:
    """Calcular un score simple para la respuesta"""
    try:
        score = 0.0

        answer_length = len(answer.split())
        if 10 <= answer_length <= 200:
            score += 0.4
        elif 5 <= answer_length < 10 or 200 < answer_length <= 300:
            score += 0.2
        
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        relevance = len(question_words.intersection(answer_words)) / max(len(question_words), 1)
        score += relevance * 0.3

        if any(punct in answer for punct in ['.', '!', '?']):
            score += 0.2

        error_indicators = ['error', 'lo siento', 'no pude', 'disculpe']
        if not any(indicator in answer.lower() for indicator in error_indicators):
            score += 0.1

        return min(1.0, max(0.0, score))
        
    except Exception as e:
        logger.error(f"Error calculando score: {e}")
        return 0.5  

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    await init_kafka()
    yield
    await close_kafka()

app = FastAPI(
    title="Score Service",
    description="Servicio de evaluación y scoring de respuestas",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": "score",
        "kafka_connected": kafka_consumer is not None and kafka_producer is not None
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "Score Service - Response Evaluation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
