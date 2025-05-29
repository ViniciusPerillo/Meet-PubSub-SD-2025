from peer import Peer
import sys

def main():
    argv = ['', 'vini', '-i', 'fdfd::1af4:a441']

    user = Peer('vini')

    try:
        if '-c' in argv:
            user.createRoom(argv[3])
        elif '-e' in argv:
            user.joinRoom('3hCrJWK3NLRJpSTYc2goJqp2ibxDognTkLxoaQKkTx2a', argv[3])
        elif '-i':
            user.connectByIPs(argv[3:])

        print(user.invite)
        user.listeningPubs()
    except Exception as e:
        user.exitRoom()
        user.close()
        raise e

    user.exitRoom()
    user.close()

main()