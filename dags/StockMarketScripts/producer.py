import json
from confluent_kafka import Producer
import socket
import time

def main(file_name):
    conf = {'bootstrap.servers': 'localhost:9092',
        'client.id': socket.gethostname()}
    producer = Producer(**conf)
    with open(f"{file_name}", 'r',encoding="utf-8") as file:
        reader = json.load(file)
        reader = json.dumps(reader).encode()
        #print(reader)
        producer.produce(key="key22",topic="Topic_1",value=reader)
            #time.sleep(0.5)
            


    producer.flush()

#main("./data.json")