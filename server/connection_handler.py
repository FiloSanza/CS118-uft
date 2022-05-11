from command_handler import *
from threading import Thread
from typing import Tuple
import socket as skt
import logging

class ConnectionHandler(Thread):
    def __init__(self, address: Tuple[str, int], raw_data: bytes) -> None:
        super().__init__()
        self.address = address
        self.raw_data = raw_data
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

    def run(self):
        (command, args) = pickle.loads(self.raw_data)
        logging.info(f"Connection from {self.address} - {command} - {len(self.raw_data)} bytes")
        command = Commands.from_str(command)
        handler = CommandHandler(command, args)
        result = handler.handle()
        self.socket.sendto(pickle.dumps(result.__dict__), self.address)
        self.socket.close()
