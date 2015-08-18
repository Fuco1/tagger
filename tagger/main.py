import os
import os.path as path
import hashutils


# TODO: make an executable out of this
def tag_file(repository, file_path, tag):
    """Tag a file.

    Args:
        repository: Path to the repository.
            Should be the full path pointing to the repository.
        file_path: File path.
            Should be the full path pointing to the file we want to tag.
        tag: Tag.
    """
    file_hash = hashutils.hash_file_sha1(file_path)

    # first, create the tag/hash_prefix/ directory
    level1_prefix = file_hash[:2]
    location = path.join(repository, tag, level1_prefix)
    if not path.exists(location):
        os.makedirs(location)

    # link the file there, but first prefix its name with the hash of
    # the file it points to.
    basename = path.basename(file_path)
    hashed_name = file_hash + basename

    # TODO: add check to see if file with this hash is already present
    # and ask user if they want to replace it (or rename).
    os.link(file_path, path.join(location, hashed_name))

    # add the file to the names database
    name_hash = hashutils.hash_string(basename)[:2]
    name_location = path.join(repository, '.names', name_hash)
    if not path.exists(name_location):
        os.makedirs(name_location)

    try:
        os.link(file_path, path.join(name_location, hashed_name))
    except os.FileExistsError:
        pass

# tag_file('/home/matus/test', '/home/matus/media/books/pdb/Kulhanek_Jiri/J_Kulhanek-Cesta_Krve_1-Dobrak.zip','scifi')
