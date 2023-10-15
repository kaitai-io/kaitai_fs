#!/usr/bin/env python3

"""Parse a file using any Kaitai spec and expose its structure as a read-only filesystem."""

import argparse
import enum
import errno
import importlib
import pathlib
import stat
import sys

import fuse

from kaitaifs.kaitai_tree_fs import KaitaiTreeFS

def _data_for_obj(obj):
    """Convert a Python object to a filesystem representation.
    
    This function either returns a bytes object (meaning a file with those contents) or None (meaning a directory).
    """
    
    if isinstance(obj, bytes):
        return obj
    elif isinstance(obj, (type(None), bool, int, float, str, enum.Enum)):
        return str(obj).encode("utf-8")
    else:
        return None

def _snake_to_camel(snake):
    """Convert a snake_case identifier to CamelCase."""
    
    return "".join(part.title() for part in snake.split("_"))

class GenericFS(KaitaiTreeFS):
    """A generic read-only filesystem for any Kaitai spec.
    
    The given spec class is asked to parse the file, and the parsed structure is exposed as a filesystem, using Python's introspection capabilities.
    Simple objects like numbers, byte arrays and strings are exposed as files, and complex objects like lists and substructures are exposed as directories.
    Internal Kaitai and Python attributes are not exposed in the filesystem. This includes attributes whose name starts with an underscore, as well as all callable objects (methods and nested types and enums).
    """
    
    def __init__(self, spec_clazz, file_name):
        file_name = pathlib.Path(file_name)
        self.obj = spec_clazz.from_file(file_name)
        
        # Read and store the stat times of the main file.
        # These times are reused for all files in the mounted filesystem.
        stat_info = file_name.stat()
        self.stat_times = {
            "st_atime": stat_info.st_atime,
            "st_mtime": stat_info.st_mtime,
            "st_ctime": stat_info.st_ctime,
        }
        
        super().__init__()
    
    def obj_by_path(self, path):
        obj = self.obj
        for part in path:
            try:
                i = int(part)
            except ValueError:
                if part.startswith("_") or not hasattr(obj, part) or callable(getattr(obj, part)):
                    raise fuse.FuseOSError(errno.ENOENT)
                obj = getattr(obj, part)
            else:
                obj = obj[i]
        return obj
    
    def list_files(self, obj):
        try:
            l = len(obj)
        except TypeError:
            return (name for name in dir(obj) if not name.startswith("_") and not callable(getattr(obj, name)))
        else:
            return (str(i) for i in range(l))
    
    def get_file_attrs(self, obj):
        data = _data_for_obj(obj)
        permissions = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        
        if data is None:
            file_type = stat.S_IFDIR
            size = 4096
        else:
            file_type = stat.S_IFREG
            size = len(data)
        
        mode = file_type | permissions
        
        return {
            **self.stat_times,
            "st_nlink": 1,
            "st_mode": mode,
            "st_size": size,
            "st_gid": 0,
            "st_uid": 0,
        }
    
    def get_file_body(self, obj, offset, length):
        data = _data_for_obj(obj)
        if data is None:
            raise fuse.FuseOSError(errno.EISDIR)
        
        return data[offset:offset+length]

def main(args):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("module_name", type=str, help="the compiled Kaitai spec to use (full Python module name)")
    ap.add_argument("file_name", type=pathlib.Path, help="the file to parse")
    ap.add_argument("mount_point", type=pathlib.Path, help="where to mount the filesystem")
    opts = ap.parse_args(args)
    
    module = importlib.import_module(opts.module_name)
    class_name = _snake_to_camel(opts.module_name.split(".")[-1])
    spec_clazz = getattr(module, class_name)
    
    fuse.FUSE(
        GenericFS(spec_clazz, opts.file_name),
        str(opts.mount_point), # fuse does not like pathlib.Path
        nothreads=True,
        foreground=True,
    )

if __name__ == "__main__":
    main(sys.argv[1:])
