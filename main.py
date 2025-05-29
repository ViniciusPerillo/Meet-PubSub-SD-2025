from peer import Peer
import sys

def main():
    argv = ['', 'vini', '-i', '2804:14d:8084:a679::1001']

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
        if '-c' in argv or '-e' in argv:
            user.exitRoom()
            user.close()
        elif '-i' in argv:
            user.disconnectByIPs()
            user.close()
        raise e


    user.exitRoom()
    user.close()

main()