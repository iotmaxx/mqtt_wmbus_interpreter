import zlib
import logging
from queue import Queue
import json
import paho.mqtt.client as mqtt

wmbusQueue = None
topic_prefix = None

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(topic_prefix+"/+/out")

def on_message(client, userdata, msg):
#    print(msg.topic, msg.payload)
    try:
        if msg.topic.endswith("/zlib"):
            payload = json.loads(zlib.decompress(msg.payload).decode('utf-8'))
        else:
            payload = json.loads(msg.payload.decode('utf-8'))
#        print(f"Msg. in: {msg.topic}: {payload}")
        if 'method' in payload:
            if payload['method'] == 'wmbus':
                for telegram in payload['params']['telegrams']:
#                    print(f"WMBUS: {telegram}")
                    if wmbusQueue != None:
                        wmbusQueue.put(telegram)
    except Exception as e:
        print(e)

def startReceiver(server, port, username, password, queue, topicPrefix='gwmqtt'):
    global client
    global wmbusQueue
    global topic_prefix 
    topic_prefix=topicPrefix
    wmbusQueue = queue
    client = mqtt.Client(client_id="", clean_session=True, userdata=None, protocol=mqtt.MQTTv311, transport="tcp")
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username=username, password=password)
    print("Connecting...")
    try:
        client.connect(server, port, 10)
        client.loop_start()
    except Exception as e:
        return False
    return True

