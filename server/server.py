from connection_handler import ConnectionHandler
from config import CONFIG
import socket as skt

class Server:
    def __init__(self, address, port) -> None:
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.bind((address, port))

    def start(self):
        while True:
            raw_data, address = self.socket.recvfrom(CONFIG["max_packet_size"])
            ConnectionHandler(address, raw_data).start()