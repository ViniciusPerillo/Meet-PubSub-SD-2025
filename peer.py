import zmq
import threading
import random
import base58
import hashlib
from datetime import datetime
from time import sleep

from utils import *
from audio_manager import AudioManager

PUB_PORT= 5555
ROUTER_PORT= 6666

class InvalidInviteCode(Exception):
    pass

class WrongPassword(Exception):
    pass

class Peer:
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
        self.publisher.setsockopt(zmq.SNDHWM, 1)
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt(zmq.IPV6, 1)
        self.subscriber.setsockopt(zmq.RCVHWM, 1)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'status')
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'text')
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'audio')
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, 'video')

        self.audio_manager = AudioManager(self)


        self.ipv6 = get_ipv6()
        self.lock = threading.Lock()
        self.username = username

        self.peers_addr = []
        self.peers = 0
        self.room = None
        self.on_room = False
        self.invite = ''
        self.password = ''

    def close(self):
        self.publisher.close(1)
        self.subscriber.close(1)

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
                self._connectPub(ip)
                self.publisher.send_multipart([b'status', bytes_username, (ip + '1').encode('utf-8')])
            else:
                router.send_multipart([b'', b'', b'wrong'])
        
        router.close(1)

    def _getHost(self, ip: str, password: str):
        dealer: zmq.Socket = self.context.socket(zmq.DEALER)
        dealer.setsockopt(zmq.IPV6, 1)
        dealer.setsockopt(zmq.LINGER, 0)  
        #daler.setsockopt(zmq.RCVTIMEO, 3000)
        dealer.connect(f'tcp://[{ip}]:{ROUTER_PORT}') 
        
        bytes_ip = self.ipv6.encode('utf-8')
        dealer.setsockopt(zmq.IDENTITY, bytes_ip)
        bytes_username = self.username.encode('utf-8')
        bytes_password = password.encode('utf-8')


        dealer.send_multipart([bytes_ip, bytes_username, bytes_password])

        _, _, bytes_list_ips = dealer.recv_multipart()
        list_ips = bytes_list_ips.decode('utf-8')

        if list_ips == 'wrong':
            raise WrongPassword
        else: 
            with self.lock:
                self.peers_addr = [self.ipv6] 
            
            for ip in list_ips.split(', '):
                self._connectPub(ip)

        dealer.close(1)
    
    def _enterRoom(self):
        self.on_room = True
        self._create_invite_code()
        sleep(0.5)
        threading.Thread(target=self._inviteListener, daemon=True).start()
        self.audio_manager.setup_audio()

    def createRoom(self, password: str= ''):
        self.password = password
        self.peers_addr.append(self.ipv6)
        self.peers += 1
        self._enterRoom()

    def joinRoom(self, invite: str, password: str):
        ip, room = self._read_invite_code(invite)

        try:
            self._getHost(ip, password)
        except WrongPassword:
            pass
        else:
            self.room = room
            self._enterRoom()

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
        
        self.audio_manager.stop()

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
                    print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")}: {username.decode("utf-8")} entrou na sala')
                else:
                    self._disconnectPub(ip)
                    print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")}: {username.decode("utf-8")} saiu da sala')
            elif topic == b'text':
                print(f'{datetime.now().strftime("%d/%m/%Y, %H:%M")} - {username.decode("utf-8")}:  {msg.decode("utf-8")}')
            elif topic == b'audio':
                self.audio_manager.receive_audio(msg)    

            

        



        

        
        



