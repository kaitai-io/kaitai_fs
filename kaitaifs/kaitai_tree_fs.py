# -*- coding: utf-8 -*-
from fuse import Operations, LoggingMixIn
import os
import sys

import typing

def split_obj_path(pathstr:str) -> typing.Iterable[str]:
    if pathstr[0] != '/':
        raise RuntimeError(
            'Internal error: path is expected to start with /,'
            'but got {path!r}'.format(
                path=pathstr
            )
        )

    if pathstr == '/':
        path = []
    else:
        path = pathstr[1:].split('/')
    return path

isWin = sys.platform == "win32"

class KaitaiTreeFS(LoggingMixIn, Operations):
    ATTR_DIR = {
        'st_atime': 0,
        'st_ctime': 0,
        'st_mtime': 0,
        'st_nlink': 1,
        'st_mode': 0o040755,
        'st_size': 4096,
        'st_gid': os.getgid() if not isWin else 0,
        'st_uid': os.geteuid() if not isWin else 0,
    }

    def __init__(self):
        self.openfiles = []
        super().__init__()

    def obj_by_pathstr(self, pathstr:str):
        return self.obj_by_path(split_obj_path(pathstr))

    def getattr(self, path, fh=None):
        if path == "/":
            return self.ATTR_DIR

        obj = self.obj_by_pathstr(path)
        return self.get_file_attrs(obj)

    def readdir(self, path, fh):
        obj = self.obj_by_pathstr(path)
        for r in ['.', '..']:
            yield r
        for r in self.list_files(obj):
            yield r

    def open(self, path, flags):
        obj = self.obj_by_pathstr(path)
        self.openfiles.append(obj)
        n = len(self.openfiles) - 1
        return n

    def read(self, path, length, offset, fh):
        obj = self.openfiles[fh]
        data = self.get_file_body(obj, offset, length)
        return data

    def release(self, path, fh):
        self.openfiles[fh] = None

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
