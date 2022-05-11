from fcntl import F_SEAL_SEAL
import hashlib
from config import CONFIG
import socket as skt
import pickle

class Client:
    def __init__(self, srv_address, srv_port) -> None:
        self.srv_address = srv_address
        self.srv_port = srv_port
        self.socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)
        self.socket.settimeout(CONFIG["connection_timeout"])

        self.handlers = {
            'list': self._handle_list_command,
            'get': self._handle_get_command,
            'put': self._handle_put_command
        }

    def _get_payload(self, command, args) -> bytes:
        return pickle.dumps((command, args))

    def _is_response_valid(self, response) -> bool:
        if not response["success"]:
            return False
        if response["checksum"]:
            payload = response["data"]
            checksum = response["checksum"]
            payload_hash = hashlib.md5(payload).digest()
            return payload_hash == checksum
        return True

    def _try_handle(self, command, args, max_tries) -> None:
        tries = 1
        success = False

        while not success and tries <= max_tries:
            success = self.handlers[command](command, args)
            tries += 1
            if not success:
                print("There has been an error. I'll try again.")

        if not success:
            print("Could not connect to the server, try again.")

    def _handle_list_command(self, command, args) -> bool:
        """
            The client will send the command to the server,
            it will then make sure that the payload's md5 hash
            and the checksum from the server match.
        """

        try:
            self.socket.sendto(self._get_payload(command, args), (self.srv_address, self.srv_port))
            response, _ = self.socket.recvfrom(CONFIG["max_packet_size"])
            response = pickle.loads(response)

            if self._is_response_valid(response):
                data = pickle.loads(response["data"])
                printable_data = "\n".join([name + " - " + size for name, size in data])
                print(printable_data)
                return True
        except Exception:
            return False        

    def _handle_get_command(self, command, args) -> bool:
        address = (self.srv_address, self.srv_port)
        #1) send the first message with command
        self.socket.sendto(self._get_payload(command, args), address)
        #2) recive the packet with the number of blocks
        response, _ = self.socket.recvfrom(CONFIG["max_packet_size"])
        response = pickle.loads(response)
        nblocks = response["nblocks"]

        print(f"I will receive: {nblocks} blocks")
    
        self.socket.sendto(response["checksum"], address)

        # TODO: make it safe with checksum control

        #3) recv blocks
        data = []
        for _ in range(nblocks):
            response, _ = self.socket.recvfrom(CONFIG["max_packet_size"])
            response = pickle.loads(response)
            chunk = response["data"]
            data = data + chunk
            self.socket.sendto(response["checksum"], address)

        print(f"Received {len(data)} bytes")

        with open(args["path"], "wb") as file:
            file.write(data)
            print(f"File saved in {args['path']}")

    def _handle_put_command(self, command, args) -> bool:
        try:
            data = None
            with open(args["path"], "rb") as file:
                data = file.read()

            print(f"File {args['path']} opened, {len(data)} bytes.")

            args["data"] = data
            args["checksum"] = hashlib.md5(data).digest()

            self.socket.sendto(self._get_payload(command, args), (self.srv_address, self.srv_port))
            response, _ = self.socket.recvfrom(CONFIG["max_packet_size"])
            response = pickle.loads(response)
            print(response)

            if self._is_response_valid(response):
                return True

        except Exception as e:
            print(e)
            return False

    def run(self, command, args) -> None:
        self.handlers[command](command, args)