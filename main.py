from User import User

user = User('ifood')

user.createRoom('123')

try: 
    print(user.invite)

    user.listeningPubs()
except KeyboardInterrupt:
    user.exitRoom()