import json
import asyncio
import logging
from typing import Optional, Dict
from fastapi import FastAPI
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None
cache: Dict[str, str] = {}

async def init_kafka():
    """Inicializar consumidor y productor de Kafka"""
    global kafka_consumer, kafka_producer
    
    try:
        kafka_consumer = AIOKafkaConsumer(
            'questions.requests',
            bootstrap_servers='kafka:29092',
            auto_offset_reset='earliest',
            group_id='cache_group',
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
            logger.info(f"Mensaje recibido: {message.value}")
            await process_message(message.value)
    except Exception as e:
        logger.error(f"Error en consume_loop: {e}")

async def process_message(message_data):
    """Procesar mensaje de pregunta y verificar cache"""
    try:
        question = message_data.get('question', '')
        message_id = message_data.get('id', '')
        timestamp = message_data.get('timestamp', '')
        
        if not question:
            logger.warning("Mensaje sin pregunta recibido")
            return

        if question in cache:
            logger.info(f"Respuesta encontrada en cache para: {question}")
            
            cache_response = {
                'id': message_id,
                'question': question,
                'answer': cache[question],
                'timestamp': timestamp,
                'source': 'cache'
            }
            
            await kafka_producer.send('questions.answers', cache_response)
            logger.info(f"Respuesta desde cache enviada para pregunta ID: {message_id}")
            
        else:
            logger.info(f"Pregunta no encontrada en cache, enviando al LLM: {question}")
            
            llm_message = {
                'id': message_id,
                'question': question,
                'timestamp': timestamp
            }
            
            await kafka_producer.send('questions.llm', llm_message)
            logger.info(f"Pregunta enviada al LLM para procesamiento: {message_id}")
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

async def init_answer_cache_consumer():
    """Inicializar consumidor para cachear respuestas del LLM"""
    try:
        answer_consumer = AIOKafkaConsumer(
            'questions.answers',
            bootstrap_servers='kafka:29092',
            auto_offset_reset='earliest',
            group_id='cache_answer_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await answer_consumer.start()
        logger.info("Answer cache consumer iniciado")

        async for message in answer_consumer:
            answer_data = message.value
            question = answer_data.get('question', '')
            answer = answer_data.get('answer', '')
            source = answer_data.get('source', '')

            if question and answer and source != 'cache':
                cache[question] = answer
                logger.info(f"Respuesta cacheada para pregunta: {question[:50]}...")
                
    except Exception as e:
        logger.error(f"Error en answer cache consumer: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    await init_kafka()
    
    asyncio.create_task(init_answer_cache_consumer())
    
    yield
    await close_kafka()

app = FastAPI(
    title="Cache Service",
    description="Servicio de cache para preguntas y respuestas",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": "cache",
        "kafka_connected": kafka_consumer is not None and kafka_producer is not None,
        "cache_size": len(cache)
    }

@app.get("/cache/stats")
async def cache_stats():
    """Estadísticas del cache"""
    return {
        "cache_size": len(cache),
        "cached_questions": list(cache.keys())[:10] if cache else []
    }

@app.delete("/cache/clear")
async def clear_cache():
    """Limpiar el cache"""
    global cache
    old_size = len(cache)
    cache.clear()
    logger.info("Cache limpiado")
    return {
        "message": "Cache limpiado",
        "previous_size": old_size
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "Cache Service - Question & Answer Cache"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
