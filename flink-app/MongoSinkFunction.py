from pyflink.datastream import SinkFunction, RuntimeContext
import pymongo
import json

class MongoSinkFunction(SinkFunction):

    def __init__(self, uri, database, collection):
        self.uri = uri
        self.database = database
        self.collection = collection
        self.client = None
        self.col = None

    def open(self, runtime_context: RuntimeContext):
        # Connect to MongoDB when the sink starts
        self.client = pymongo.MongoClient(self.uri)
        self.col = self.client[self.database][self.collection]

    def invoke(self, value, context):
        # Insert each record into MongoDB
        try:
            # The value is a JSON string, convert it to dict
            doc = json.loads(value)
            self.col.insert_one(doc)
        except Exception as e:
            print(f"Error writing to MongoDB: {e}")

    def close(self):
        # Close MongoDB connection on sink close
        if self.client:
            self.client.close()
