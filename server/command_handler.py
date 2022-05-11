from dataclasses import dataclass
import re
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

    def _handle_get_file(self, args) -> CommandResult:
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

    def _save_block(self, args) -> CommandResult:
        name = args["name"]
        block = args["block"]
        data = args["data"]
        original_checksum = args["checksum"]
        path = f"{CONFIG['tmp_save_path']}{name}.tmp.{block}"
        checksum = hashlib.md5(data).digest()

        if checksum != original_checksum:
            return CommandResult(False)

        with open(path, "wb") as file:
            file.write(data)

        print(f"block {block} saved")

        return CommandResult(True)

    def _read_block(self, filename) -> bytes:
        with open(filename, "rb") as file:
            return file.read()

    def _merge_file(self, args) -> CommandResult:
        try:
            name = args["name"]
            r = re.compile(f"^{name}\.tmp\.(?P<id>\d+)$")
            files_raw = list(filter(lambda f: os.path.isfile(f) and r.match(utils.path_leaf(f)), glob(CONFIG["tmp_save_path"] + "*")))
            files = list(map(
                lambda file: (file[0], self._read_block(file[1])), 
                [(r.match(utils.path_leaf(f))["id"], f) for f in files_raw]
            ))
            files.sort(key=lambda f: f[0])

            path = CONFIG["file_path"] + name
            with open(path, "wb") as file:
                file.write(b"".join(map(lambda x: x[1], files)))

            for file in files_raw:
                os.remove(file)

            return CommandResult(True)
        except Exception as e:
            print(f"There has been an error: {e}")
            return CommandResult(False)

    def _handle_put_file(self, args) -> CommandResult:
        merge = args["merge"]
        if merge:
            return self._merge_file(args)
        else:
            return self._save_block(args)
        

    def handle(self) -> CommandResult:
        return self.handlers[self.command](self.args)
