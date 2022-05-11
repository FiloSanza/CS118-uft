from concurrent.futures import ThreadPoolExecutor
import hashlib
import math
import pickle
import socket as skt
from typing import Any, Dict, List, Tuple

from numpy import block
from config import CONFIG
from utils import get_readable_size_string
from request_handler import handle_request

class Client:
    def __init__(self, srv_address: str, srv_port: int) -> None:
        self.address = (srv_address, srv_port)
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.settimeout(CONFIG["connection_timeout"])

        self.handlers = {
            'list': self._handle_list_command,
            'get': self._handle_get_command,
            'put': self._handle_put_command
        }

    def _handle_get_command(self, command: str, args: Dict[str, Any]) -> None:
        try:
            # 1) get the size of the selected file
            files = list(filter(lambda x: x[0] == args["name"], self._get_list_data()))

            if not files or len(files) != 1:
                print("File not present.")
                return

            file_size = files[0][1]
            block_size = CONFIG["max_block_size"]
            nblocks = math.ceil(file_size / block_size)

            # 2) make the requests for each block
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(
                    handle_request,
                    pickle.dumps((command, {
                        **args, 
                        "block_start": i * block_size,
                        "block_end": min((i + 1) * block_size, file_size)})),
                    self.address
                ) for i in range(nblocks)]

                file = [f.result() for f in futures]
                if any([not res.success for res in file]):
                    print("Error downloading the file, try again.")
                    return
                file_data = b"".join(map(lambda x: x.data, file))
                print(f"expected file size: {file_size} - actual file size {len(file_data)}")            

                with open(args["path"], "wb") as file:
                        file.write(file_data)

        except Exception as e:
            print(f"Something went wrong: {e}")

    def _handle_put_command(self, command: str, args: Dict[str, Any]) -> None:
        # 1) send the blocks of the file
        path = args["path"]
        
        file_raw = []
        with open(path, "rb") as file:
            file_raw = file.read()
        
        block_size = CONFIG["max_block_size"]
        nblocks = math.ceil(len(file_raw) / block_size)
        blocks = [(i, file_raw[i*block_size : min(len(file_raw), (i+1)*block_size)]) for i in range(nblocks)]

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(
                handle_request,
                pickle.dumps((command, {
                    **args,
                    "block": id,
                    "merge": False,
                    "checksum": hashlib.md5(data).digest(),
                    "data": data
                })),
                self.address
            ) for id, data in blocks]
            results = [f.result() for f in futures]
            if any([not res.success for res in results]):
                print("Error uploading the file, try again.")
                return

        # 2) send the "merge" command
        result = handle_request(pickle.dumps((command, {**args, "merge": True})), self.address)
        if not result.success:
            print("Error on the merge command.")
            return

    def _get_list_data(self, command: str = 'list', args: Dict[str, Any] = {}) -> List[Tuple[str, int]]:
        payload = pickle.dumps((command, args))
        response = handle_request(payload, self.address)
        files = None
        if response.success:
            files = pickle.loads(response.data)
        return files

    def _handle_list_command(self, command: str, args: Dict[str, Any]) -> None:
        files = self._get_list_data(command, args)
        if files:
            printable = "\n".join([f"{file} - {get_readable_size_string(size)}" for file, size in files])
            print(printable)
        else:
            print("An error occurred.")

    def run(self, command, args) -> None:
        self.handlers[command](command, args)