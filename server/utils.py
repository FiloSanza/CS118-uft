import os

KB_size = 1024
MB_size = KB_size * 1024
GB_size = MB_size * 1024

def get_readable_size_string(size_in_bytes: int) -> str:
    if size_in_bytes < KB_size:
        return f"{size_in_bytes} B"
    elif size_in_bytes < MB_size:
        return f"{round(size_in_bytes / KB_size, 2)} KB"
    elif size_in_bytes < GB_size:
        return f"{round(size_in_bytes / MB_size, 2)} MB"
    else:
        return f"{round(size_in_bytes, GB_size, 2)}, GB"

def file_exists(path: str) -> bool:
    return os.path.exists(path)