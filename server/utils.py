import ntpath
import os

def file_exists(path: str) -> bool:
    return os.path.exists(path)

def path_leaf(path: str):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)