from peer import Peer
import sys

def main():
    argv = sys.argv

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
        if '-c' or '-e':
            user.exitRoom()
            user.close()
        elif '-i':
            user.disconnectByIPs()
        raise e


    user.exitRoom()
    user.close()

main()