import signal
from connection_handler import ConnectionHandler
from config import CONFIG
import socket as skt

class Server:
    def __init__(self, address: str, port: int) -> None:
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.bind((address, port))
        signal.signal(signal.SIGINT, self.close)

    def close(self, signum, frame):
        self.socket.close()
        exit(0)

    def start(self):
        while True:
            raw_data, address = self.socket.recvfrom(CONFIG["max_packet_size"])
            ConnectionHandler(address, raw_data).start()