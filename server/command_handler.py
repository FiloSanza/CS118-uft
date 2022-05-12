from dataclasses import dataclass
import re
from typing import Any, Dict
from config import CONFIG
from enum import Enum, auto
from glob import glob
import hashlib
import pickle
import logging
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
        # Get all the files
        files = filter(os.path.isfile, glob(CONFIG["file_path"] + "*"))
        # Find the size of each file
        files_with_size = [(utils.path_leaf(path), os.stat(path).st_size) for path in files]
        raw_data = pickle.dumps(files_with_size)
        checksum = hashlib.md5(raw_data).digest()

        return CommandResult(True, raw_data, checksum)

    def _handle_get_file(self, args: Dict[str, Any]) -> CommandResult:
        path = CONFIG["file_path"] + args["name"]
        block_start = args["block_start"]
        block_end = args["block_end"]

        logging.debug(f"get file {path} | {block_start} - {block_end}")

        size = os.path.getsize(path)
        if block_start >= size or block_end > size or block_start >= block_end:
            logging.warning(f"Invalid block requested ({block_start} - {block_end}) file is {size} bytes.")
            return CommandResult(False)

        # If the file exists and `block_start`, `block_end` are correct read the file and send it to the client.
        if utils.file_exists(path):
            with open(path, "rb") as file:
                file.seek(block_start)
                data = file.read(block_end - block_start)
                checksum = hashlib.md5(data).digest()
                return CommandResult(True, data, checksum)
        else:
            logging.warning(f"File {path} not found")
            return CommandResult(False)

    def _save_block(self, args: Dict[str, Any]) -> CommandResult:
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

        return CommandResult(True)

    def _read_block(self, filename: str) -> bytes:
        with open(filename, "rb") as file:
            return file.read()

    def _merge_file(self, args: Dict[str, Any]) -> CommandResult:
        try:
            name = args["name"]
            # 1) Find all the blocks related to this request in the temp folder
            r = re.compile(f"^{name}\.tmp\.(?P<id>\d+)$")
            files_raw = list(filter(lambda f: os.path.isfile(f) and r.match(utils.path_leaf(f)), glob(CONFIG["tmp_save_path"] + "*")))
            # 2) Load the blocks in memory
            files = list(map(
                lambda file: (file[0], self._read_block(file[1])), 
                [(r.match(utils.path_leaf(f))["id"], f) for f in files_raw]
            ))
            # 3) Sort them by id
            files.sort(key=lambda f: f[0])

            logging.debug(f"Save the file {name} - {len(files)} blocks.")
            path = CONFIG["file_path"] + name
            
            # 4) Write the file.
            with open(path, "wb") as file:
                file.write(b"".join(map(lambda x: x[1], files)))

            # 5) Remove temp files.
            logging.debug(f"Removing the temp blocks of {name}.")
            for file in files_raw:
                os.remove(file)

            logging.debug(f"Temp blocks of {name} removed.")
            return CommandResult(True)

        except Exception as e:
            logging.warning(f"There has been an error: {e}")
            return CommandResult(False)

    def _handle_put_file(self, args: Dict[str, Any]) -> CommandResult:
        merge = args["merge"]
        if merge:
            return self._merge_file(args)
        else:
            return self._save_block(args)
        

    def handle(self) -> CommandResult:
        return self.handlers[self.command](self.args)
