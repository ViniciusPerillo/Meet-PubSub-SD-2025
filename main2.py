from User import User


user = User('dell')

user.joinRoom('3hCrJWK32xwQFXwhsvAdFcXgyxYwRncnu6eNdS8EFuuW', '123')

print(user.invite)

user.listeningPubs()