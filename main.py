from user import User
import sys

def main():
    argv = sys.argv

    user = User(argv[1])

    if '-c' in argv:
        user.createRoom(argv[3])
    elif '-e' in argv:
        user.joinRoom('3hCrJWK32xwQFXwhsvAdFcXgyxYwRncnu6eNdS8EFm7k', argv[3])

    print(user.invite)
    try:
        user.listeningPubs()
    except Exception as e:
        user.exitRoom()
        user.close()
        raise e


    user.exitRoom()
    user.close()

main()