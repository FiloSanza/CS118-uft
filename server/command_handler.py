from dataclasses import dataclass
import math
from tabnanny import check
from config import CONFIG
from enum import Enum, auto
from glob import glob
import hashlib
import pickle
import utils
import os

class Commands(Enum):
    PUT = auto()
    GET = auto()
    LIST = auto()
    
    def from_str(s: str):
        s = s.lower()
        if s == 'list':
            return Commands.LIST
        elif s == 'put':
            return Commands.PUT
        elif s == 'get':
            return Commands.GET
        else:
            return None

@dataclass
class CommandResult:
    success: bool
    data: bytes = None
    checksum: bytes = None

class CommandHandler:
    def __init__(self, command, args) -> None:
        self.command = command
        self.args = args
        self.handlers = {
            Commands.LIST : self._handle_list,
            Commands.PUT: self._handle_put_file,
            Commands.GET: self._handle_get_file
        }

    def _try_send(self, payload, socket, address) -> None:
        """
            Send payload to address using socket,
            wait to receive the checksum of payload before continuing
        """
        tries = 1
        checksum = hashlib.md5(payload).digest()
        while tries <= CONFIG["max_tries"]:
            try:
                socket.sendto(payload, address)
                client_hash, _ = socket.recvfrom(CONFIG["max_packet_size"])
                if client_hash == check:
                    return
            except Exception:
                pass
            tries += 1

    def _send_file(self, file, socket, address) -> None:
        block_size = CONFIG["max_block_size"]
        nblocks = math.ceil(len(file) / CONFIG["max_block_size"])
        blocks = [file[i:min(i+block_size, len(file))] for i in range(0, len(file), block_size)]

        #1) send the first packet with the number of blocks
        info = {
            'nblocks': nblocks,
            'checksum': hashlib.md5(str(nblocks).encode()).digest()
        }

        if not self._try_send(pickle.dumps(info), socket, address):
            print("An error occured while sendind the file.")
            return

        #2) send each block
        for block in blocks:
            payload = {
                'checksum': hashlib.md5(block).digest(),
                'data': block
            }

            if not self._try_send(pickle.dumps(payload), socket, address):
                print("An error occured while sendind the file.")
                return

    def _handle_list(self, _, socket, address) -> None:
        files = filter(os.path.isfile, glob(CONFIG["file_path"] + "*"))
        files_with_size = [(path, utils.get_readable_size_string(os.stat(path).st_size)) for path in files]
        raw_data = pickle.dumps(files_with_size)
        checksum = hashlib.md5(raw_data).digest()

        result = CommandResult(True, raw_data, checksum)
        socket.sendto(pickle.dumps(result.__dict__), address)

    def _handle_get_file(self, args, socket, address) -> None:
        path = CONFIG["file_path"] + args["name"]

        print(f"Get file: {path}")

        if not utils.file_exists(path):
            print(f"File {path} not found")
            socket.sendto(pickle.dumps(CommandResult(False).__dict__), address)
            return

        with open(path, "rb") as file:
            data = file.read()
            self._send_file(data, socket, address)

    def _handle_put_file(self, args, socket, address) -> None:
        name = args["name"]
        data = args["data"]
        original_checksum = args["checksum"]
        path = CONFIG["file_path"] + name
        checksum = hashlib.md5(data).digest()

        if checksum != original_checksum:
            return CommandResult(False)

        with open(path, "wb") as file:
            file.write(data)

        return CommandResult(True)

    def handle(self, socket, address) -> None:
        return self.handlers[self.command](self.args, socket, address)
