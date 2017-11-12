import os


def safe_open_w(path, write_options):
    # Open "path" for writing, creating any parent directories as needed.
    try:
        os.makedirs(os.path.dirname(path))
    except FileExistsError:
        pass

    return open(path, write_options)
