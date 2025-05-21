import zmq
import threading
import random
import base58
import hashlib

from utils import *

PUB_PORT= 5555
ROUTER_PORT= 6666

class InvalidInviteCode(Exception):
    pass

class HostTimeOut(Exception):
    pass

class User:
    context: zmq.Context
    publisher: zmq.Socket
    subscriber: zmq.Socket
    ipv6: str
    lock: threading.Lock
    on_room: bool
    username: str
    peers_addr: list[str]
    peers: int
    room: int
    password: str


    def __init__(self, username: str):
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.setsockopt(zmq.IPV6, 1)
        self.publisher.bind(f'tcp://[::]:{PUB_PORT}')
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt(zmq.IPV6, 1)

        self.ipv6 = get_ipv6()
        self.lock = threading.Lock()
        self.on_room = False
        self.username = username
        self.peers_addr = []
        self.peers = 0
        self.room == None
        self.invite == ''
        self.password = ''

    def __create_invite_code(self):
        self.room = random.randint(0, 65535) if self.room == None else self.room
        ip_bin = convert_ipv6_str_to_bin(self.ipv6)
        payload = ip_bin<<128 | self.room

        hash = hashlib.sha256(ROUTER_PORT + payload)[:4]
        invite = payload<<4 | hash
        encoded_invite = base58.b58encode(invite).decode()
        readable_invite_splits = []
        
        for i in range(0, len(encoded_invite), 6):
            readable_invite_splits.append(encoded_invite[i:] if len(encoded_invite) else encoded_invite[i:i+6])

        self.invite = '-'.join(readable_invite_splits)
        
    
    def __read_invite_code(self, encoded_invite:str) -> tuple[str]:
        invite = base58.b58decode(''.join((invite.split('-'))))
        payload = invite>>4
        hash = invite - (invite>>4<<4)

        if hash != hashlib.sha256(ROUTER_PORT + payload)[:4]:
            raise InvalidInviteCode
        

        ip = convert_bin_to_ipv6_str(payload>>128)
        room = payload - (payload>>128<<128)

        return (ip, room)
            
    def inviteListener(self):
        router: zmq.Socket = self.context.socket(zmq.ROUTER)
        router.setsockopt(zmq.IPV6, 1)
        router.bind(f'tcp://[::]:{ROUTER_PORT}')

        while self.on_room:
            ip, _, bytes_password = router.recv_multipart()
            length = bytes_password>>8
            password = (bytes_password - (bytes_password>>8<<8)).to_bytes(length, 'big').decode('utf-8')

            if password == self.password:
                router.send_multipart[ip, b'', convert_ipv6_list_to_bin(self.peers_addr)]
                with self.lock:
                    self.peers_addr.append(convert_bin_to_ipv6_str(ip))
        
        router.close(1)

    def getHost(self, ip: str, password: str):
        dealer: zmq.Socket = self.context.socket(zmq.DEALER)
        dealer.setsockopt(zmq.IPV6, 1)
        dealer.setsockopt(zmq.IDENTITY, convert_ipv6_str_to_bin(self.ipv6))
        dealer.setsockopt(zmq.LINGER, 0)  
        dealer.setsockopt(zmq.RCVTIMEO, 3000)
        dealer.connect(f'tcp://[{ip}]:{ROUTER_PORT}') 
        bytes_password = len(password)<<8 | int.from_bytes(password.encode('utf-8'), 'big')

        try:
            dealer.send_multipart([convert_ipv6_str_to_bin(self.ipv6), b'', bytes_password])
            _, _, list_ips = dealer.recv_multipart()
        except zmq.Again:
            raise HostTimeOut
        else: 
            with self.lock:
                self.peers_addr = [self.ipv6] + convert_bin_to_ipv6_list(list_ips)

        dealer.close(1)
    
    def createRoom(self, password: str= ''):
        self.on_room = True
        self.password = password
        self.peers_addr.append(self.ipv6)
        self.peers += 1
        self.__create_invite_code()
        threading.Thread(self.inviteListener())

    def joinRoom(self, invite: str, password: str):
        ip, room = self.__read_invite_code(invite)

        try:
            self.getHost(ip, password)
        except HostTimeOut:
            pass
        else:
            self.room = room
            self.on_room = True
            self.peers = len(self.peers_addr)
            self.__create_invite_code()
            threading.Thread(self.inviteListener())

    def exitRoom(self):
        self.peers_addr = []
        self.peers = 0
        self.room == None
        self.invite == ''
        self.password = ''

    def connectPub(self):
        for ip in self.peers_addr[1:]:
            self.subscriber.connect(f'tpc://[{ip}]:{PUB_PORT}')
        



        

        
        



