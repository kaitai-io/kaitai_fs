# -*- coding: utf-8 -*-
import errno
from datetime import datetime

from kaitaifs.parser.iso9660 import Iso9660
from kaitaifs.kaitai_tree_fs import KaitaiTreeFS

from fuse import FuseOSError


class Iso9660FS(KaitaiTreeFS):
    def __init__(self, filename):
        self.obj = Iso9660.from_file(filename)
        super(Iso9660FS, self).__init__()

    def obj_by_path(self, path):
        tree = self.obj.primary_vol_desc.vol_desc_primary.root_dir.body
        for comp in path:
            tree = self.find_name_in_dir(tree, comp)
        return tree

    def list_files(self, cur_dir):
        for entry in cur_dir.extent_as_dir.entries:
            entry_body = getattr(entry, "body", None)
            if entry_body is not None:
                fn = entry_body.file_name
                if fn not in (u'\x00', u'\x01'):
                    yield entry_body.file_name

    def get_file_attrs(self, obj):
        # Directory or file?
        if obj.file_flags & 2 != 0:
            # Directory
            mode = 0o040755
        else:
            # Regular file
            mode = 0o100644

        # Calculate date & time for the file
        dt = obj.datetime
        t = datetime(
            1900 + dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.sec,
            # Microseconds
            0
        )
        timestamp = (t - datetime(1970, 1, 1)).total_seconds()

        return {
            'st_atime': timestamp,
            'st_ctime': timestamp,
            'st_mtime': timestamp,
            'st_nlink': 1,
            'st_mode': mode,
            'st_size': obj.size_extent.le,
            'st_gid': 0,
            'st_uid': 0,
        }

    def get_file_body(self, obj, offset, length):
        return obj.extent_as_file[offset:offset + length]

    def find_name_in_dir(self, cur_dir, name):
        for entry in cur_dir.extent_as_dir.entries:
            entry_body = getattr(entry, "body", None)
            if entry_body is not None and entry_body.file_name == name:
                return entry_body
        raise FuseOSError(errno.ENOENT)
