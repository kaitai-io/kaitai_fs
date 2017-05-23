import os
import errno

from fuse import FuseOSError, Operations

class KaitaiSimpleFS(Operations):
    """A filesystem that keeps its whole directory tree in memory.

    Most suited for simpler formats, which are effectively flat (and
    keep hierarchy information in file names, like "foo/bar/baz", so
    it takes extra processing step to build a tree anyway). Most
    archives and containers are like that.

    Filesystem implementation is expected to subclass this class and
    must implement:

    * `generate_tree(self)` - a method that will be invoked on startup
      to build an in-memory tree of objects; this is expected to use
      `self.add_obj_to_path(path, entry)` to actually add objects to
      the tree.
    * `get_file_body(self, obj, offset, length)` - a method that will
      be invoked for reading a fragment of a given file.

    Optionally, one can implement:

    * `get_file_attrs(self, obj)` - a method that returns a dictionary
      of file/directory attributes; useful to implement FS reporting
      file sizes / attributes / datetimes properly instead of some
      arbitrary defaults.

    Attributes:
        tree (dict): tree (dir name -> dir name -> ... -> "." ->
            object) that must be built by ``generate_tree()``; to
            be used heavily for all FS navigation purposes
    """

    def __init__(self):
        self.openfiles = []
        self.tree = {}
        self.generate_tree()

    # ========================================================================

    def get_file_attrs(self, obj):
        """Get file attributes for a given object.

        Expected to return normal getattr-style dict. Default
        implementation returns default "neutral" attributes, with
        creation / modification / access time zeroed out, mode set to
        traditional `rwxr--r--`, file belongs to root:root, size is
        around 1 block.

        Concrete implementations should override this to provide
        better `st_size`, `st_*time` and probably other members.
        """
        return {
            'st_atime': 0,
            'st_ctime': 0,
            'st_mtime': 0,
            'st_nlink': 1,
            'st_mode': 0o100644,
            'st_size': 4096,
            'st_gid': 0,
            'st_uid': 0,
        }        

    # ========================================================================

    def add_obj_to_path(self, path, obj):
        t = self.tree
        for comp in path:
            if comp not in t:
                t[comp] = {}
            t = t[comp]
        t['.'] = obj

    def tree_by_path(self, path):
        """Traverses pre-built tree by a given path and gets object.

        Args:
            path (str): Path as a string, as used in most of FUSE
                method calls. Must start with a "/".

        Returns:
            Object by the given path or None, if traversing fails at
            any stage.
        """
        if path[0] != '/':
            raise RuntimeError("Internal error: path is expected to start with /, but got %s" % (repr(path)))
        if path == '/':
            return self.tree

        paths = path[1:].split('/')
        t = self.tree
        for comp in paths:
            if comp not in t:
                return None
            t = t[comp]

        return t

    def obj_by_path(self, path):
        obj = self.tree_by_path(path)
        if obj == None or '.' not in obj:
            raise FuseOSError(errno.ENOENT)
        else:
            return obj['.']

    # ========================================================================

    def access(self, path, mode):
        tree = self.tree_by_path(path)
        if tree == None:
            raise FuseOSError(errno.ENOENT)
        return

    ATTR_DIR = {
        'st_atime': 0,
        'st_ctime': 0,
        'st_mtime': 0,
        'st_nlink': 1,
        'st_mode': 0o040755,
        'st_size': 4096,
        'st_gid': 0,
        'st_uid': 0,
    }

    def getattr(self, path, fh=None):
        if path == "/":
             return self.ATTR_DIR

        tree = self.tree_by_path(path)
        if tree == None:
            raise FuseOSError(errno.ENOENT)
        elif (len(tree) == 1 and '.' in tree):
            obj = tree['.']
            return self.get_file_attrs(obj)
        else:
            return self.ATTR_DIR

    def readdir(self, path, fh):
        tree = self.tree_by_path(path)
        for r in ['.', '..']:
            yield r
        for r in tree:
            if r != '.':
                yield r

    def statfs(self, path):
        return {
            'f_bsize': 4096,
            'f_frsize': 4096,
            'f_blocks': 1024 * 1024,
            'f_bfree': 0,
            'f_bavail': 1024 * 1024,
            'f_files': 1024 * 1024,
            'f_ffree': 1024 * 1024,
            'f_favail': 1024 * 1024,
            'f_flag': 4096,
            'f_namemax': 0xffff,
        }

    # ========================================================================

    def open(self, path, flags):
        block = self.obj_by_path(path)
        self.openfiles.append(block)
        n = len(self.openfiles) - 1
        return n

    def read(self, path, length, offset, fh):
        print "read(%s, %s, %s, %s)" % (repr(path), repr(length), repr(offset), repr(fh))
        obj = self.openfiles[fh]
        data = self.get_file_body(obj, offset, length)
        return data

    def release(self, path, fh):
        self.openfiles[fh] = None

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
