import zmq
import random

def create_random_chars(chars: int) -> str:
    string = ''
    
    for char in range(chars):
        string += chr(97 + random.randint(0, 25))

    return string


class PubSubEntitiy:
    def __init__(self):
        self.context = zmq.Context()
        self.publisher_list = [self.context.socket(zmq.PUB)]
        self.subscriber = [self.context.socket(zmq.SUB)]

    def createPublisher(self):
        self.publisher_list.append(self.context.socket(zmq.PUB))

    def subscribe():

class User:
    def __init__(self, username: str):
        self.username = username + '#' + create_random_chars(12)

class Room:
    def __init__(self):
        

    def createRoom(self) -> str:
        pass
        

    

