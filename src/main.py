
import sys
import threading
from mainmenu import Menu
from mainmenu import LoggedOut
from server import KServer
from peer import Peer

def main():
    ip = "127.0.0.1"
    port = sys.argv[1] # 6001

    peer=Peer(ip,port)
    peer.init_logging_peer()


if __name__ == '__main__':
    main()