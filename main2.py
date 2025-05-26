from User import User


user = User('dell')

user.joinRoom('3hCrJWK32xwQFXwhsvAdFcXgyxYwRncnu6eNdS8EFm7k', '123')

try: 
    print(user.invite)

    user.listeningPubs()
except KeyboardInterrupt:
    user.exitRoom()