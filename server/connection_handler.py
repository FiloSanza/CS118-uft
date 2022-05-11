from command_handler import *
from threading import Thread
from typing import Tuple
import socket as skt

class ConnectionHandler(Thread):
    def __init__(self, address: Tuple[str, int], raw_data: bytes) -> None:
        super().__init__()
        self.address = address
        self.raw_data = raw_data
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

    def run(self):
        print(f"Received data from {self.address} - {len(self.raw_data)} bytes")
        (command, args) = pickle.loads(self.raw_data)
        command = Commands.from_str(command)
        print(f"command: {command} {args=}")
        handler = CommandHandler(command, args)
        result = handler.handle()
        self.socket.sendto(pickle.dumps(result.__dict__), self.address)
