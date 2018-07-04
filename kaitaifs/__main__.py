#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging

from .fs.rar_fs import RarFS
from .fs.quake_pak_fs import QuakePakFS
from .fs.heroes_of_might_and_magic_agg_fs import (
    HeroesOfMightAndMagicAggFS
)
from .fs.iso9660_fs import Iso9660FS
from .fs.AnyKSFS import AnyKSFS

from fuse import FUSE

from functools import partial

from kaitaifs.parser.rar import Rar

FILESYSTEMS = {
    'rar': RarFS,
    'quake_pak': QuakePakFS,
    'heroes_of_might_and_magic_agg': HeroesOfMightAndMagicAggFS,
    'iso9660': Iso9660FS,
}

def getParserCtor(moduleName:str):
    import importlib
    import ast
    from pathlib import Path
    try:
        mod=importlib.import_module("."+moduleName, package="kaitaifs.parser")
    except:
        mod=importlib.import_module(moduleName)
    p=Path(mod.__file__)
    a=ast.parse(p.read_text())
    for el in a.body:
        if isinstance(el, ast.ClassDef):
            return getattr(mod, el.name)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Mount a filesystem based on Kaitai Struct spec.'
    )
    parser.add_argument('--any', dest='any', action='store_true', default=False, help='use any KaitaiStruct parser class')
    parser.add_argument('--loglevel', dest='loglevel', choices=logging._levelToName.values(), default=None, help='show log')
    parser.add_argument(
        'fstype',
        metavar='TYPE',
        #choices=FILESYSTEMS.keys(),
        help='filesystem type'
    )
    parser.add_argument(
        'image_file',
        metavar='IMAGE_FILE',
        type=str,
        help='source image file (or block device)'
    )
    parser.add_argument(
        'mount_point',
        metavar='MOUNT_POINT',
        type=str,
        help='mount point'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    if args.any:
        fs_class = partial(AnyKSFS, getParserCtor(args.fstype))
    else:
        fs_class = FILESYSTEMS[args.fstype]
    if args.loglevel:
        logging.basicConfig(level=getattr(logging, args.loglevel))
    FUSE(
        fs_class(args.image_file),
        args.mount_point,
        nothreads=True,
        foreground=True
    )

if __name__ == "__main__":
    main()
