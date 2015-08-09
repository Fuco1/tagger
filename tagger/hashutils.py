import hashlib


def hash_file(stream, hasher, blocksize=1048576):
    """Hash the content of stream.

    We read at most blocksize bytes at the time.  This makes sure we
    won't overflow the memory.

    Args:
        stream: Input stream.
        hasher: A hash object.
    """
    buf = stream.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = stream.read(blocksize)
    return hasher.hexdigest()


def hash_file_sha1(file_path):
    """Hash file content using sha1 algorithm."""
    return hash_file(open(file_path, 'rb'), hashlib.sha1())


def hash_string(s):
    """Hash a string."""
    return hashlib.sha1(s.encode('UTF-8')).hexdigest()
