from command_handler import *
from server import Server

def main():
    srv = Server('localhost', 12345)
    srv.start()

if __name__ == '__main__':
    main()