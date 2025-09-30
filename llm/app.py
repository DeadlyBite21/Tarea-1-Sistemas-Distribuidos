import json
import asyncio
import logging
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import aiohttp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales para Kafka
kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None

# Configuración de Ollama
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

async def init_kafka():
    """Inicializar consumidor y productor de Kafka"""
    global kafka_consumer, kafka_producer
    
    try:
        # Configurar consumidor
        kafka_consumer = AIOKafkaConsumer(
            'questions.llm',
            bootstrap_servers='kafka:29092',
            auto_offset_reset='earliest',
            group_id='llm_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        # Configurar productor  
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers='kafka:29092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await kafka_consumer.start()
        await kafka_producer.start()
        
        logger.info("Kafka consumer y producer iniciados correctamente")
        
        # Iniciar el loop de consumo
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
    """Procesar mensaje y generar respuesta con Gemini"""
    try:
        question = message_data.get('question', '')
        message_id = message_data.get('id', '')
        
        if not question:
            logger.warning("Mensaje sin pregunta recibido")
            return
        
        # Generar respuesta con Ollama
        logger.info(f"Procesando pregunta: {question}")
        response = await generate_ollama_response(question)
        
        # Preparar mensaje para el servicio de score
        answer_message = {
            'id': message_id,
            'question': question,
            'answer': response,
            'timestamp': message_data.get('timestamp', '')
        }
        
        # Enviar a topic de respuestas
        await kafka_producer.send('questions.answers', answer_message)
        logger.info(f"Respuesta enviada para pregunta ID: {message_id}")
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

async def generate_ollama_response(question: str) -> str:
    """Generar respuesta usando Ollama"""
    try:
        # Preparar el payload para Ollama
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": question,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', 'No se pudo generar una respuesta.')
                else:
                    logger.error(f"Error en Ollama API: {response.status}")
                    return "Error al conectar con el servicio de LLM."
                    
    except asyncio.TimeoutError:
        logger.error("Timeout al conectar con Ollama")
        return "Timeout al procesar la pregunta."
    except Exception as e:
        logger.error(f"Error generando respuesta con Ollama: {e}")
        return f"Error al procesar la pregunta: {str(e)}"

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
    title="LLM Service",
    description="Servicio de generación de respuestas usando Ollama",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": "llm",
        "kafka_connected": kafka_consumer is not None and kafka_producer is not None
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "LLM Service - Powered by Ollama"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)