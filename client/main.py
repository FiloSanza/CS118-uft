from argparse import ArgumentParser
import logging
import sys
from client import Client
from typing import Tuple
from config import CONFIG

logging.basicConfig(
    level=CONFIG["log_level"],
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
    description="uft - UDP File Transfer", allow_abbrev=False)

    sub_parsers = parser.add_subparsers(dest="command", help="sub-command help.", required=True)

    parser_list = sub_parsers.add_parser("list", help="List the files on the server.")

    parser_put = sub_parsers.add_parser("put", help="Upload a file to the server (create a new file or replace it if it's already there).")
    parser_put.add_argument("--path", type=str, help="The path to the file to upload.", required=True)
    parser_put.add_argument("--name", type=str, help="The name used to save the file on the server.", required=True)

    parser_get = sub_parsers.add_parser("get", help="Download a file from the server.")
    parser_get.add_argument("--path", type=str, help="The path where to save the file.", required=True)
    parser_get.add_argument("--name", type=str, help="The file name.", required=True)

    return parser

def get_validated_input(parser: ArgumentParser) -> Tuple[list, dict]:
    args = parser.parse_args()
    command = args.command

    args_dict = args.__dict__
    del args_dict["command"]

    return (command, args_dict)

parser = get_parser()
command, args = get_validated_input(parser)
client = Client(CONFIG["server_address"], CONFIG["server_port"])
client.run(command, args)