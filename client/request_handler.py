from dataclasses import dataclass
import hashlib
import socket as skt
from typing import Any, Dict, Tuple
from config import CONFIG
import pickle

@dataclass
class Response:
    success: bool
    data: bytes = None

def _is_response_valid(response: Dict[str, Any]) -> bool:
    if not response["success"]:
        return False
    if response["checksum"]:
        payload = response["data"]
        checksum = response["checksum"]
        payload_hash = hashlib.md5(payload).digest()
        return payload_hash == checksum
    return True

def _try_request(data: bytes, socket: skt.socket, address: Tuple[str, int]) -> Response:
    try:
        socket.sendto(data, address)
        response, _ = socket.recvfrom(CONFIG["max_packet_size"])
        response = pickle.loads(response)        
        if _is_response_valid(response):
            return Response(True, response["data"])
    except Exception:
        pass
    return Response(False)

def handle_request(data: bytes, address: Tuple[str, int]) -> Response:
    socket = skt.socket(skt.AF_INET, skt.SOCK_DGRAM)

    tries = 1
    response = Response(False)
    while not response.success and tries <= CONFIG["max_tries"]:
        response = _try_request(data, socket, address)
        tries += 1
        if not response.success:
            print("There has been an error. I'll try again.")

    return response