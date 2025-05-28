from peer import Peer
import sys

def main():
    argv = sys.argv

    user = Peer(argv[1])

    if '-c' in argv:
        user.createRoom(argv[3])
    elif '-e' in argv:
        user.joinRoom('3hCrJWK32xwSQr5xq8eBWSDiHuVyJoPrUPJd6dNWEanA', argv[3])

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