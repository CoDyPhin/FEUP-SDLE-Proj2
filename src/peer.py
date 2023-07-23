import asyncio
import json
import logging
import sys
import threading
from mainmenu import Menu
from mainmenu import LoggedOut
from server import KServer

class Peer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        
    def init_logging_peer(self):
       # handler = logging.StreamHandler()
       # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
       # handler.setFormatter(formatter)
       # log = logging.getLogger('kademlia')
       # #log.addHandler(handler)
       # #log.setLevel(logging.DEBUG)

        try:
            kserver = KServer(self.ip, int(self.port))
            t1 = threading.Thread(target=kserver.init_server, daemon=True)
            t1.start()

            menu = Menu(kserver)
            menu.run_menu()

        except (KeyboardInterrupt, LoggedOut):
            if kserver.logged_user != None:
                kserver.shutdown_hook()
                future = asyncio.run_coroutine_threadsafe(kserver.logout(), kserver.main_loop)
                retval = future.result()
                kserver.server.stop()
            return
