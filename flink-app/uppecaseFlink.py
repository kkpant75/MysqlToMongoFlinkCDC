from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaSink, KafkaRecordSerializationSchema, DeliveryGuarantee
from pyflink.common.typeinfo import Types
from pyflink.common.watermark_strategy import WatermarkStrategy

from pyflink.datastream.functions import MapFunction, RuntimeContext

import json
import pymongo


# MongoDB writer as a map function
class MongoWriter(MapFunction):

    def open(self, runtime_context: RuntimeContext):
        self.client = pymongo.MongoClient("mongodb://mongoe2e:27017")
        self.collection = self.client["upperdb"]["uppercollection"]

    def map(self, value):
        try:
            doc = json.loads(value)
            self.collection.insert_one(doc)
        except Exception as e:
            print(f"Mongo insert error: {e}")
        return value  # Continue passing value downstream if needed

    def close(self):
        if self.client:
            self.client.close()


# Upper-case mapper function
def upper_case_mapper(record: str):
    try:
        obj = json.loads(record)

        # Debug print (optional)
        print("Original Record:", obj)

        if obj.get('after') and isinstance(obj['after'], dict):
            for key, value in obj['after'].items():
                if isinstance(value, str):
                    obj['after'][key] = value.upper()

        return json.dumps(obj)

    except Exception as e:
        print(f"Error processing record: {record}, error: {e}")
        return json.dumps({"error": "processing_failed", "reason": str(e)})


# Setup environment
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

# Kafka source
source = KafkaSource.builder() \
    .set_bootstrap_servers("kafkae2e:9092") \
    .set_topics("mysql_server.testdb.users") \
    .set_group_id("flink-upper-group") \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

# Kafka sink
kafka_sink = KafkaSink.builder() \
    .set_bootstrap_servers("kafkae2e:9092") \
    .set_record_serializer(
        KafkaRecordSerializationSchema.builder()
        .set_topic("uppercase_users")
        .set_value_serialization_schema(SimpleStringSchema())
        .build()
    ) \
    .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE) \
    .build()

# Build stream
stream = env.from_source(
    source,
    watermark_strategy=WatermarkStrategy.no_watermarks(),
    source_name="Kafka Source"
).map(upper_case_mapper, output_type=Types.STRING())

# Add MongoDB writer (via map)
stream.map(MongoWriter(), output_type=Types.STRING())

# Add Kafka sink
stream.sink_to(kafka_sink)

# Execute Flink job
env.execute("Uppercase Transformer with MongoDB and Kafka")
