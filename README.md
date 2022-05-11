# CS118-uft

Simple Client/Server app that allows file transfer over UDP. 

## Instructions

The application requires python 3.8+

### Server

To run the server use the following command in the server folder:

```sh
python3 main.py
```

#### Configure

To configure the server you can edit the `config.py` file, here's an example:

```py
CONFIG = {
    'file_path': '/tmp/cs118/',
    'tmp_save_path': '/tmp/cs118/tmp/',
    'max_packet_size': 2**16,
    'max_block_size': 2**15,
    'address': 'localhost',
    'port': 12345,
    'log_level': logging.INFO,
    'connection_timeout': 2
}
```

- `file_path`: where the shared files are.
- `tmp_save_path`: where the temporary data is saved.
- `max_packet_size`: the maximum packet size in bytes.
- `max_block_size`: the maximum file-block size in bytes, used when files are too big to be sent in packet. Must be less than `max_packet_size`.
- `address`: ip address of the server.
- `port`: port of the server.
- `log_level`: log level.
- `connection_timeout`: connection timeout in seconds.

### Client

### List

To list the files on the server run the following command in the `client` folder:

```sh
python3 main.py list
```

### Get

To get a file from the server run the following command in the `client` folder:

```sh
python3 main.py get --name NAME --path PATH
```

The parameters are:
- name: the name of the file on the server (as in list);
- path: the local path where the file will be saved.

### Put

To put a file on the server run the following command in the `client` folder:

```sh
python3 main.py put --name NAME --path PATH
```

The parameters are:
- name: the name used on the server to save the file;
- path: the path of the file to upload.

#### Configure

To configure the client you can edit the `config.py` file, here's an example:

```py
CONFIG = {
    'max_tries': 5,
    'max_packet_size': 2**16,
    'max_block_size': 2**15,
    'connection_timeout': 2,
    'log_level': logging.WARNING,
    'server_address': 'localhost',
    'server_port': 12345
}
```

- `max_tries`: number of tries in case the request fails.
- `max_packet_size`: the maximum packet size in bytes.
- `max_block_size`: the maximum file-block size in bytes, used when files are too big to be sent in packet. Must be less than `max_packet_size`.
- `connection_timeout`: connection timeout in seconds.
- `server_address`: ip address of the server.
- `server_port`: port of the server.
- `log_level`: log level.

__The `max_packet_size` and `max_block_size` must match the same as in the server's configuration file__