import zmq
import threading
import random
import base58
import hashlib
from datetime import datetime

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
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'status')
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'text')
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'audio')
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'video')

        self.ipv6 = get_ipv6()
        self.lock = threading.Lock()
        self.on_room = False
        self.username = username
        self.peers_addr = []
        self.peers = 0
        self.room = None
        self.invite = ''
        self.password = ''

    def _create_invite_code(self):
        self.room = random.randint(0, 65535) if self.room == None else self.room
        ip_bin = convert_ipv6_str_to_bin(self.ipv6)
        invite = ip_bin<<128 | self.room

        encoded_invite = base58.b58encode(invite.to_bytes((invite.bit_length() + 7) // 8, 'big')).decode()
        

        self.invite = encoded_invite
        
    
    def _read_invite_code(self, encoded_invite:str) -> tuple[str]:
        invite = int.from_bytes(base58.b58decode(encoded_invite), 'big')
        ip = convert_bin_to_ipv6_str(invite>>128)
        room = invite - (invite>>128<<128)

        return (ip, room)
            
    def _inviteListener(self):
        print('cu')
        router: zmq.Socket = self.context.socket(zmq.ROUTER)
        router.setsockopt(zmq.IPV6, 1)
        router.bind(f'tcp://[::]:{ROUTER_PORT}')

        while self.on_room:
            ip, username, bytes_password = router.recv_multipart()
            length = bytes_password>>8
            password = (bytes_password - (bytes_password>>8<<8)).to_bytes(length, 'big').decode('utf-8')

            if password == self.password:
                router.send_multipart[ip, b'', convert_ipv6_list_to_bin(self.peers_addr)]
                with self.lock:
                    self.peers_addr.append(convert_bin_to_ipv6_str(ip))

            self.publisher.send_multipart([b'status', username.encode('utf-8'), (ip<<1 | 1)])
        
        router.close(1)

    def _getHost(self, ip: str, password: str):
        dealer: zmq.Socket = self.context.socket(zmq.DEALER)
        dealer.setsockopt(zmq.IPV6, 1)
        dealer.setsockopt(zmq.IDENTITY, convert_ipv6_str_to_bin(self.ipv6))
        dealer.setsockopt(zmq.LINGER, 0)  
        dealer.setsockopt(zmq.RCVTIMEO, 3000)
        dealer.connect(f'tcp://[{ip}]:{ROUTER_PORT}') 
        bytes_password = len(password)<<8 | int.from_bytes(password.encode('utf-8'), 'big')

        try:
            dealer.send_multipart([convert_ipv6_str_to_bin(self.ipv6), self.username, bytes_password])
            _, _, list_ips = dealer.recv_multipart()
        except zmq.Again:
            raise HostTimeOut
        else: 
            with self.lock:
                self.peers_addr = [self.ipv6] 
            
            for ip in convert_bin_to_ipv6_list(list_ips):
                self._connectPub(ip)

        dealer.close(1)
    
    def createRoom(self, password: str= ''):
        self.on_room = True
        self.password = password
        self.peers_addr.append(self.ipv6)
        self.peers += 1
        self._create_invite_code()
        threading.Thread(target=self._inviteListener, daemon=True).start()

    def joinRoom(self, invite: str, password: str):
        ip, room = self._read_invite_code(invite)

        try:
            self._getHost(ip, password)
        except HostTimeOut:
            pass
        else:
            self.room = room
            self.on_room = True
            self.peers = len(self.peers_addr)
            self._create_invite_code()
            threading.Thread(self._inviteListener, daemon=True).start()

        for ip in self.peers_addr[1:]:
            self._connectPub(ip)

    def exitRoom(self):
        for ip in self.peers_addr[1:]:
            self._disconnectPub(ip)
        
        self.publisher.send_multipart([b'status', self.username.encode('utf-8'), (convert_ipv6_str_to_bin(self.ipv6)<<1 | 1)])

        self.peers_addr.pop()
        self.peers -= 1
        self.room == None
        self.invite == ''
        self.password = ''

    def _connectPub(self, ip: str):
        self.subscriber.connect(f'tcp://[{ip}]:{PUB_PORT}')
        with self.lock:
            self.peers_addr.append(ip)
        
        self.peers += 1


    def _disconnectPub(self, ip: str):
        self.subscriber.disconnect(f'tcp://[{ip}]:{PUB_PORT}')

        with self.lock:
            self.peers_addr.remove(ip)
        
        self.peers -= 1

    def listeningPubs(self):
        
        while self.on_room:
            topic, username, msg = self.subscriber.recv_multipart()

            if topic == b'status':
                status = msg % 2
                ip = convert_bin_to_ipv6_str(msg>>1)

                if status:
                    self._connectPub(ip)
                    print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")}: {username.decode('utf-8')} entrou na sala')
                else:
                    self._disconnectPub(ip)
                    print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")}: {username.decode('utf-8')} saiu da sala')

            

        



        

        
        



