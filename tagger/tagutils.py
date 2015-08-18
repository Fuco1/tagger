import os
import os.path as path
import hashutils

# Each `tag' is a directory containing at most 256 directories which
# are 2-letter hexadecimal prefixes of sha1 hashes.


def get_common_hash_prefixes(repository, tags):
    """Return common hash prefixes for tags."""
    common = None
    for tag in tags:
        tag_directory = path.join(repository, tag)
        hash_prefixes = os.listdir(tag_directory)
        if common is None:
            common = frozenset(hash_prefixes)
        else:
            common = common.intersection(frozenset(hash_prefixes))
    return common


def get_common_hashes(repository, tags, hash_prefix):
    """Return hashes of files tagged with all the tags.

    All hashes have the same hash prefix.
    """
    common = None
    for tag in tags:
        file_list = os.listdir(path.join(repository, tag, hash_prefix))
        hash_list = [x[:40] for x in file_list]
        if common is None:
            common = frozenset(hash_list)
        else:
            common = common.intersection(frozenset(hash_list))
    return common


def get_files_for_hashes(directory, hashes):
    """Return files corresponding to hashes.

    Args:
        directory (string): Path.
        hashes (frozenset): Set of hashes.
    """
    directory = os.listdir(directory)
    files = []
    for f in directory:
        file_hash = f[:40]
        if file_hash in hashes:
            files.append(f)
    return files


# TODO: move to fuse utils?
# TODO: abstract query parsing
def get_file_from_fuse_path(repository, fuse_path):
    """Get file in the repository for path.

    Path is a fuse-path pointing to the file.
    """
    basename = path.basename(fuse_path)
    name_hash = hashutils.hash_string(basename)[:2]
    name_location = path.join(repository, '.names', name_hash)
    names = os.listdir(name_location)
    real_name = None
    for name in names:
        if name[40:] == basename:
            real_name = name
            break
    if real_name is not None:
        # TODO: We need to abstract query parsing here
        # 0th is empty because we start with /
        tag = fuse_path.split("/")[1]
        return path.join(repository, tag, real_name[:2], real_name)
    else:
        raise IOError("File not found")


def get_all_tags(repository):
    """Return all tags"""
    tags = [d for d in os.listdir(repository)
            if path.isdir(path.join(repository, d))]
    tags.remove('.names')
    return frozenset(tags)


def get_possible_tags(repository, query):
    """Return all tags possible to add to current query."""
    # TODO: abstract query parsing
    tags = frozenset(query.split('/'))
    all_tags = get_all_tags(repository)
    return all_tags.difference(tags)


def is_tag(repository, tag):
    """True if tag is a string representing a valid tag."""
    return tag in get_all_tags(repository)


# TODO: write a method which given a query can give us back
# - list of base tags (= from where we grab the actual files).  This
#   in principle is any one tag from any "and" subquery
# - all tags used in "this context" (that is, possible "next" tags)

# if we have tags foo, bar, baz, qux
# examples:
# - foo/bar -> ([foo], [baz, qux])
# - foo/+/bar -> ([foo,bar], [foo, baz, qux]), no sense attaching bar at
#   the end
# - foo/{/bar/baz/} -> ([foo], [qux]), this means the same as
#   foo/bar/+/foo/baz, however, with the expanded version the next set
#   would be [bar, qux]


def query(repository, query):
    """Run query represented by path and return list of matching files."""
    # TODO: abstract query parsing
    tags = [x for x in query.split('/') if x != '']
    if not tags:
        return []

    common_prefixes = get_common_hash_prefixes(repository, tags)
    common_files = []
    for prefix in common_prefixes:
        hashes = get_common_hashes(repository, tags, prefix)
        files = get_files_for_hashes(
            path.join(repository, tags[0], prefix),
            hashes
        )
        common_files += files

    return common_files

# query('/home/matus/test','scifi')(get_tags(repository))
