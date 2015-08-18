from __future__ import with_statement

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations

import tagutils
import sql


class Passthrough(Operations):
    def __init__(self, root):
        self.root = root

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode',
            'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


class Tagger(Operations):

    def __init__(self, repository, mountpoint):
        # TODO: add routine to automatically fill the DB with data if
        # empty.  Should probably require us to run the program with
        # some switch
        sql.init(repository)
        self.repository = repository
        self.mountpoint = mountpoint

    def access(self, path, mode):
        pass

    def fuse_path_to_real(self, path):
        # return tagutils.get_file_from_fuse_path(self.repository, path)
        basetag = path.split("/")[1]
        basename = os.path.basename(path)
        with sql.get_connection(self.repository) as con:
            # TODO: should depend on tags too
            filehash = sql.file_get_hash(con, basename)
            if filehash is not None:
                re = os.path.join(self.repository,
                                  basetag,
                                  filehash[:2],
                                  filehash + basename)
                return re
            else:
                return None

    def getattr(self, path, fh=None):
        # we need to figure out if this is a file or a tag or some
        # meta-nonsense
        base = os.path.basename(path)
        if path == '/':
            st = os.lstat(self.repository)
        elif tagutils.is_tag(self.repository, base):
            st = os.lstat(os.path.join(self.repository, base))
        else:
            full_path = self.fuse_path_to_real(path)
            if full_path is not None:
                st = os.lstat(full_path)
            else:
                return {}
        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode',
            'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        directories = tagutils.get_possible_tags(self.repository, path)
        # files = [x[40:] for x in tagutils.query(self.repository, path)]
        files = []
        for (f, _) in sql.get_tagged_files(
                self.repository,
                [x for x in path.split('/') if x != '']):
            files.append(f)
        return list(directories) + files

    def open(self, path, flags):
        full_path = self.fuse_path_to_real(path)
        return os.open(full_path, flags)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def release(self, path, fh):
        return os.close(fh)

# def main(mountpoint, root):
#     FUSE(Passthrough(root), mountpoint, nothreads=True, foreground=True)


def main(root, mountpoint):
    FUSE(Tagger(root, mountpoint), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
