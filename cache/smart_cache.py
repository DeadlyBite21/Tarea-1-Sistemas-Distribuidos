import json
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from collections import OrderedDict, defaultdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheConfig(BaseModel):
    policy: str = "LRU"  
    max_size: int = 100
    ttl: int = 300  

class CacheStats(BaseModel):
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    avg_response_time: float = 0.0
    memory_usage: int = 0
    evictions: int = 0
    current_size: int = 0

class CacheEntry:
    def __init__(self, value, ttl=None):
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 1
        self.ttl = ttl
    
    def is_expired(self):
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def access(self):
        self.last_accessed = time.time()
        self.access_count += 1

class SmartCache:
    def __init__(self, policy="LRU", max_size=100, ttl=300):
        self.policy = policy
        self.max_size = max_size
        self.ttl = ttl
        
        if policy == "LRU":
            self.cache = OrderedDict()
        else:
            self.cache = {}
        
        self.entries = {}  
        self.access_times = {} 
        self.access_counts = defaultdict(int)  
        self.insertion_order = []  
        
        self.stats = CacheStats()
        self.response_times = []
        self.lock = threading.RLock()
    
    def _cleanup_expired(self):
        """Eliminar entradas expiradas"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.entries.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_key(key)
    
    def _remove_key(self, key):
        """Remover una clave del cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.entries:
            del self.entries[key]
        if key in self.access_times:
            del self.access_times[key]
        if key in self.access_counts:
            del self.access_counts[key]
        if key in self.insertion_order:
            self.insertion_order.remove(key)
    
    def _evict_entry(self):
        """Evictar una entrada según la política"""
        if not self.cache:
            return
        
        self.stats.evictions += 1
        
        if self.policy == "LRU":
            key = next(iter(self.cache))
            self._remove_key(key)
        
        elif self.policy == "LFU":
            min_count = min(self.access_counts.values())
            lfu_key = None
            for key, count in self.access_counts.items():
                if count == min_count:
                    lfu_key = key
                    break
            if lfu_key:
                self._remove_key(lfu_key)
        
        elif self.policy == "FIFO":
            if self.insertion_order:
                key = self.insertion_order.pop(0)
                self._remove_key(key)
    
    def get(self, key):
        """Obtener valor del cache"""
        with self.lock:
            start_time = time.time()
            self.stats.total_requests += 1

            self._cleanup_expired()
            
            if key in self.cache and key in self.entries:
                entry = self.entries[key]
                if not entry.is_expired():
                    entry.access()
                    self.stats.cache_hits += 1

                    if self.policy == "LRU":
                        self.cache.move_to_end(key)

                    if self.policy == "LFU":
                        self.access_counts[key] += 1
                    
                    response_time = time.time() - start_time
                    self.response_times.append(response_time)
                    self._update_avg_response_time()
                    
                    return entry.value
                else:

                    self._remove_key(key)
            
            self.stats.cache_misses += 1
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self._update_avg_response_time()
            
            return None
    
    def put(self, key, value):
        """Almacenar valor en el cache"""
        with self.lock:

            self._cleanup_expired()
            

            if key in self.cache:
                self.entries[key] = CacheEntry(value, self.ttl)
                if self.policy == "LRU":
                    self.cache.move_to_end(key)
                return
            
            while len(self.cache) >= self.max_size:
                self._evict_entry()

            self.cache[key] = value
            self.entries[key] = CacheEntry(value, self.ttl)
            
            if self.policy == "LFU":
                self.access_counts[key] = 1
            elif self.policy == "FIFO":
                self.insertion_order.append(key)
            
            self.stats.current_size = len(self.cache)
    
    def _update_avg_response_time(self):
        """Actualizar tiempo de respuesta promedio"""
        if self.response_times:

            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
            self.stats.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    def get_stats(self):
        """Obtener estadísticas del cache"""
        with self.lock:
            self.stats.hit_rate = (
                self.stats.cache_hits / self.stats.total_requests 
                if self.stats.total_requests > 0 else 0
            )
            self.stats.memory_usage = len(self.cache)
            self.stats.current_size = len(self.cache)
            return self.stats.dict()
    
    def reset(self):
        """Resetear el cache y estadísticas"""
        with self.lock:
            self.cache.clear()
            self.entries.clear()
            self.access_times.clear()
            self.access_counts.clear()
            self.insertion_order.clear()
            self.response_times.clear()
            self.stats = CacheStats()
    
    def configure(self, policy, max_size, ttl):
        """Reconfigurar el cache"""
        with self.lock:
            self.policy = policy
            self.max_size = max_size
            self.ttl = ttl

            if policy == "LRU":
                new_cache = OrderedDict()
                for key, value in self.cache.items():
                    new_cache[key] = value
                self.cache = new_cache
            else:
                if isinstance(self.cache, OrderedDict):
                    self.cache = dict(self.cache)

kafka_consumer: Optional[AIOKafkaConsumer] = None
kafka_producer: Optional[AIOKafkaProducer] = None
smart_cache = SmartCache()

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

        cached_answer = smart_cache.get(question)
        
        if cached_answer is not None:
            logger.info(f"Respuesta encontrada en cache para: {question[:50]}...")
            cache_response = {
                'id': message_id,
                'question': question,
                'answer': cached_answer,
                'timestamp': timestamp,
                'source': 'cache'
            }
            
            await kafka_producer.send('questions.answers', cache_response)
            logger.info(f"Respuesta desde cache enviada para pregunta ID: {message_id}")
            
        else:
            logger.info(f"Pregunta no encontrada en cache, enviando al LLM: {question[:50]}...")

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
                smart_cache.put(question, answer)
                logger.info(f"Respuesta cacheada para pregunta: {question[:50]}...")
                
    except Exception as e:
        logger.error(f"Error en answer cache consumer: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""

    await init_kafka()
    
    # Iniciar consumer para cachear respuestas en background
    asyncio.create_task(init_answer_cache_consumer())
    
    yield
    # Shutdown
    await close_kafka()

app = FastAPI(
    title="Smart Cache Service",
    description="Servicio de cache inteligente con múltiples políticas",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": "smart_cache",
        "kafka_connected": kafka_consumer is not None and kafka_producer is not None,
        "cache_policy": smart_cache.policy,
        "cache_size": smart_cache.stats.current_size,
        "max_size": smart_cache.max_size
    }

@app.get("/stats")
async def get_cache_stats():
    """Obtener estadísticas detalladas del cache"""
    return smart_cache.get_stats()

@app.post("/configure")
async def configure_cache(config: CacheConfig):
    """Configurar la política de cache"""
    try:
        smart_cache.configure(config.policy, config.max_size, config.ttl)
        logger.info(f"Cache reconfigurado: {config.policy}, tamaño={config.max_size}, TTL={config.ttl}")
        return {
            "message": "Cache configurado exitosamente",
            "policy": config.policy,
            "max_size": config.max_size,
            "ttl": config.ttl
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/reset")
async def reset_cache():
    """Resetear el cache y estadísticas"""
    old_stats = smart_cache.get_stats()
    smart_cache.reset()
    logger.info("Cache y estadísticas reseteadas")
    return {
        "message": "Cache reseteado exitosamente",
        "previous_stats": old_stats
    }

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Smart Cache Service - Múltiples Políticas de Cache",
        "current_policy": smart_cache.policy,
        "supported_policies": ["LRU", "LFU", "FIFO"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)