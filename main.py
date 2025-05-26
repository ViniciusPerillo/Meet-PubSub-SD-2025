from User import User
from time import sleep

user = User('ifood')

user.createRoom('123')

try: 
    print(user.invite)
    while True:
        user.publisher.send_multipart([b'text', user.username.encode('utf-8'), b'rede'])
        sleep(5)

    
except KeyboardInterrupt:
    user.exitRoom()