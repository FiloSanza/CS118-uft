from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging
import math
import pickle
from typing import Any, Dict, List, Tuple
from config import CONFIG
from utils import get_readable_size_string
from request_handler import handle_request

class Client:
    def __init__(self, srv_address: str, srv_port: int) -> None:
        self.address = (srv_address, srv_port)
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
                logging.error("Cannot find the file on the server.")
                return

            file_size = files[0][1]
            block_size = CONFIG["max_block_size"]
            nblocks = math.ceil(file_size / block_size)

            # 2) make the requests for each block
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Create a future object (thread) for each block of the file.
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
                    logging.error("Error downloading the file, try again.")
                    return
                # Write the file
                file_data = b"".join(map(lambda x: x.data, file))
                logging.debug(f"Received: {file_size} - Expected: {len(file_data)}")            

                with open(args["path"], "wb") as file:
                        file.write(file_data)

        except Exception as e:
            logging.error(f"Exception raised: {e}")
        
        logging.info("GET command executed successfully.")

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
            # Create a future object (thread) for each block of the file.
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
                logging.error("Error uploading the file, try again.")
                return

        # 2) send the "merge" command
        result = handle_request(pickle.dumps((command, {**args, "merge": True})), self.address)
        if not result.success:
            logging.error("Error, file not saved.")
            return

        logging.info("PUT command executed successfully.")

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
            logging.error("Error, try again.")

    def run(self, command, args) -> None:
        self.handlers[command](command, args)