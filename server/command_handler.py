from dataclasses import dataclass
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

    def _handle_list(self, _) -> CommandResult:
        files = filter(os.path.isfile, glob(CONFIG["file_path"] + "*"))
        files_with_size = [(utils.path_leaf(path), os.stat(path).st_size) for path in files]
        raw_data = pickle.dumps(files_with_size)
        checksum = hashlib.md5(raw_data).digest()

        return CommandResult(True, raw_data, checksum)

    def _handle_get_file(self, args) -> bool:
        path = CONFIG["file_path"] + args["name"]
        block_start = args["block_start"]
        block_end = args["block_end"]
        size = min(block_end - block_start, CONFIG["max_block_size"])

        print(f"Get file: {path} block {block_start} - {block_end} | {size=}")

        if utils.file_exists(path):
            with open(path, "rb") as file:
                data = file.read()[block_start:block_end]
                #TODO: hope it not die
                checksum = hashlib.md5(data).digest()
                return CommandResult(True, data, checksum)
        else:
            print(f"File {path} not found")
            return CommandResult(False)

    def _handle_put_file(self, args) -> bool:
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

    def handle(self) -> CommandResult:
        return self.handlers[self.command](self.args)
