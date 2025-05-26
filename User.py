import zmq
import threading
import random
import base58
import hashlib
from datetime import datetime
from time import sleep

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
        self.username = username

        self.peers_addr = []
        self.peers = 0
        self.room = None
        self.on_room = False
        self.invite = ''
        self.password = ''

    

    def _create_invite_code(self):
        #self.room = random.randint(0, 65535) if self.room == None else self.room
        self.room = 1111 if self.room == None else self.room
        
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
            dealer_id, bytes_ip, bytes_username, bytes_password = router.recv_multipart()
            ip = bytes_ip.decode('utf-8')
            password = bytes_password.decode('utf-8')

            if password == self.password:
                bytes_ips = str(self.peers_addr)[1:-1].replace("'","").encode('utf-8')
                router.send_multipart([dealer_id, b'', b'', bytes_ips])
                with self.lock:
                    self.peers_addr.append(ip)

                self.publisher.send_multipart([b'status', bytes_username, (ip + '1').encode('utf-8')])
            else:
                router.send_multipart([b'', b'', b'wrong'])
        
        router.close(1)

    def _getHost(self, ip: str, password: str):
        dealer: zmq.Socket = self.context.socket(zmq.DEALER)
        dealer.setsockopt(zmq.IPV6, 1)
        dealer.setsockopt(zmq.LINGER, 0)  
        dealer.setsockopt(zmq.RCVTIMEO, 3000)
        dealer.connect(f'tcp://[{ip}]:{ROUTER_PORT}') 
        
        bytes_ip = self.ipv6.encode('utf-8')
        bytes_username = self.username.encode('utf-8')
        bytes_password = password.encode('utf-8')

        try:
            dealer.send_multipart([bytes_ip, bytes_username, bytes_password])
            _, _, list_ips = dealer.recv_multipart()
        except zmq.Again:
            raise HostTimeOut
        else: 
            with self.lock:
                self.peers_addr = [self.ipv6] 
            
            for ip in list_ips.split(', '):
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
        
        self.publisher.send_multipart([b'status', self.username.encode('utf-8'), (self.ipv6 + '0').encode('utf-8')])

        self.peers_addr.pop()
        self.peers -= 1
        self.room = None
        self.on_room = False
        self.invite = ''
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
                status = bool(int(msg[-1]))
                ip = msg[:-1].decode('utf-8')

                if status:
                    self._connectPub(ip)
                    print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")}: {username.decode('utf-8')} entrou na sala')
                else:
                    self._disconnectPub(ip)
                    print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")}: {username.decode('utf-8')} saiu da sala')

            

        



        

        
        



