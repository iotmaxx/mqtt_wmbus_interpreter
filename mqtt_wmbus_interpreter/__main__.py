import logging
from .gwmqtt_client import startReceiver
from.wmbus_interpreter import interpret
from queue import Queue
import time

if __name__ == '__main__':
    recvQueue = Queue()
    startReceiver("192.168.1.10", 1883, 'testuser', 'testuser', recvQueue)
    while(True):
        time.sleep(1)
        while not recvQueue.empty():
            telegram = recvQueue.get()
#            print(f"Recv: {telegram}")
            print(interpret(telegram))
