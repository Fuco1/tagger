# tagger

(this is a work-in-progress name)

Filesystem using tags and fuse!

This system is built with two simple premises in mind:
- no metadata other than the filesystem itself[^1]
- no complicated usage patterns, just mount one dir and that's it

The major downsides of all solutions known to me is that they require
external files/databases to store metadata, and if you lose that or it
gets out of sync, you're out of luck.  Some systems also operate on
inode level which makes it very difficult to maintain backups.

This system stores all the required metadata (and there isn't much of
it) simply as files in directories---but no extra files you need to
keep in sync, just those you are tagging.  All the information can be
deduced from the directory nestings alone.

The basic layout of the repository is as follows:
- Each tag is a subdirectory.
- Inside each tag directory are directories `aa`, `ab`, ..., `ff`
  (prefixes of sha1 hashes), that means each tag directory has at most
  256 subdirectories.
- Files (= their content) are `sha1` hashed, then the filename is
  prefixed with the hash and stored inside
  `tag/two-letter-hash-prefix` directory.  This helps us to keep the
  listings under control (ext doesn't really like 100k files in one
  directory).
- For each file, there is an entry in a special directory `.names`,
  where the file *name* gets hashed and stored in the similar manner
  as files, under the 2-letter prefix of the file name hash.  The name
  of the file is the same as inside the "real" storage, prefixed with
  the *data* hash.  This helps us to map filenames to real files in
  the repository during searches.
- Files are not stored repeatedly but with hard links.  This also means
  you can maintain a regular hierarchy parallel with the tagger
  repository sharing the data blocks on the HDD to save space... so
  even if the entire repository is blown to pieces, you still have
  your data stored somewhere in the "regular" filesystem.

And that's it.

TODO: explain how to query for files using fuse

# Algorithms

TODO

# Similar work

- [Tagsistant](https://github.com/StrumentiResistenti/Tagsistant): Definitely the most mature option out there.
- [dantalian](https://github.com/darkfeline/dantalian): File organization and tagging using hard links

[^1]: To make this system reasonably efficient, we use sqlite database
to cache and preprocess data to speed up queries.  However, if you
lose the database file, nothing of value is lost as it can be
completely recovered from just the layout of the files.
