import sys
from server import Server
from config import CONFIG
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def main():
    srv = Server(CONFIG["address"], CONFIG["port"])
    srv.start()

if __name__ == '__main__':
    main()