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
        if s == 'list' or s == 'ls':
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
        files_with_size = [(path, utils.get_readable_size_string(os.stat(path).st_size)) for path in files]
        raw_data = pickle.dumps(files_with_size)
        checksum = hashlib.md5(raw_data).digest()

        return CommandResult(True, raw_data, checksum)

    def _handle_get_file(self, args) -> bool:
        path = CONFIG["file_path"] + args["name"]

        print(f"Get file: {path}")

        if utils.file_exists(path):
            with open(path, "rb") as file:
                data = file.read()
                checksum = hashlib.md5(data).hexdigest()
                return CommandResult(True, data, checksum)
        else:
            return CommandResult(False)

    def _handle_put_file(self, args) -> bool:
        name = args["name"]
        data = args["data"]
        original_checksum = args["checksum"]
        path = CONFIG["file_path"] + name
        checksum = hashlib.md5(data).digest()

        if utils.file_exists(path) or checksum != original_checksum:
            return CommandResult(False)

        with open(path, "wb") as file:
            file.write(data)

        return CommandResult(True)

    def handle(self) -> CommandResult:
        return self.handlers[self.command](self.args)
