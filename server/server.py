import socket as skt

class Server:
    def __init__(self, address, port) -> None:
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.bind((address, port))

    def start():
        while True:
            pass