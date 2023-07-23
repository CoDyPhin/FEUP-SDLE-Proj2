import ntplib
import os
from time import ctime, time
from datetime import datetime

# 27 April 2019 20:30:00 GMT
epoch = 1556393400000

# sonyflake-py


def generate_timestamp_id(port):
    seq_number = 0
    last_timestamp = 0
    while True:

        # NTP para ajustar o clock do sistema:
        c = ntplib.NTPClient()
        try:
            response = c.request('pool.ntp.org', version=3)
            os.system('date ' + time.strftime('%m%d%H%M%Y.%S', time.localtime(response.tx_time)))
        except:
            pass
        
        timestamp = int(time() * 1000) # current
        if last_timestamp == timestamp:
            seq_number += 1
        elif last_timestamp > timestamp:
            time.sleep(last_timestamp - timestamp)
        else:
            seq_number = 0
        last_timestamp = timestamp

        yield build_timestamp_id(timestamp - epoch, port, seq_number)

def generate_datetime(id):
    diff = int(id >> 16 + 32)
    timestamp = int(epoch/1000 + diff/1000)
    id_time = ctime(timestamp)
    return datetime.strptime(id_time, "%a %b %d %H:%M:%S %Y")

def build_timestamp_id(timestamp, port, seq_number):
    timestamp_binary = "{0:048b}".format(timestamp)
    port_binary = "{0:032b}".format(port)
    seq_number_binary = "{0:016b}".format(seq_number)
    return int(timestamp_binary + port_binary + seq_number_binary, 2)