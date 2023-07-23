
import threading
from peer import Peer
from server import KServer
import asyncio
import sched
import time
        
boot_ip = "127.0.0.1"
ports = [7001, 7002, 7003]
threads = []

for i in range(3):
    bp = Peer(boot_ip, ports[i])
    kserver = KServer(boot_ip, ports[i])
    thread = threading.Thread(target=kserver.init_server, daemon=True)
    threads.append(thread)
    thread.start()

#def set_user_list(scheduler):
#    future = asyncio.run_coroutine_threadsafe(kserver.server.set("user_list", json.dumps({"user_list" : []})), kserver.main_loop)
#    value = future.result()
#    scheduler.cancel()
#    return value


def garbage_collector(scheduler):
    print("Garbage collection routines...")
    future = asyncio.run_coroutine_threadsafe(kserver.garbage_collect(), kserver.main_loop)
    value = future.result()
    scheduler.enter(20, 100, garbage_collector, (scheduler,))

def crash_check_function(scheduler):
    print("Looking for peer crashes...")
    future = asyncio.run_coroutine_threadsafe(kserver.bootpeer_check_online_peers(), kserver.main_loop)
    value = future.result()
    #print("Online peer checking returned: " + str(value))
    scheduler.enter(30,200, crash_check_function, (scheduler,))
    

scheduler_aux = sched.scheduler(time.time, time.sleep)
scheduler_aux.enter(20, 200, garbage_collector, (scheduler_aux, ))
scheduler_aux.enter(30, 200, crash_check_function,(scheduler_aux, ))
scheduler_aux.run()

for i in threads:
    i.join()