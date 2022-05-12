import logging

CONFIG = {
    'max_tries': 5,
    'max_packet_size': 2**16,
    'max_block_size': 2**15,
    'connection_timeout': 2,
    'log_level': logging.INFO,
    'server_address': 'localhost',
    'server_port': 12345
}