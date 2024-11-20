from kafka import KafkaProducer, KafkaConsumer
import json

# Kafka Configuration
KAFKA_BROKER = 'localhost:9092'
TOPIC = 'chat_messages'

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Kafka Consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    group_id='chat_consumer_group'
)
