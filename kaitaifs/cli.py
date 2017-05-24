#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from kaitaifs.fs.rar_fs import RarFS
from kaitaifs.fs.quake_pak_fs import QuakePakFS
from kaitaifs.fs.heroes_of_might_and_magic_agg_fs import (
    HeroesOfMightAndMagicAggFS
)
from kaitaifs.fs.iso9660_fs import Iso9660FS

from fuse import FUSE

FILESYSTEMS = {
    'rar': RarFS,
    'quake_pak': QuakePakFS,
    'heroes_of_might_and_magic_agg': HeroesOfMightAndMagicAggFS,
    'iso9660': Iso9660FS,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Mount a filesystem based on Kaitai Struct spec.'
    )
    parser.add_argument(
        'fstype',
        metavar='TYPE',
        choices=FILESYSTEMS.keys(),
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


def main(args):
    fs_class = FILESYSTEMS[args.fstype]
    FUSE(
        fs_class(args.image_file),
        args.mount_point,
        nothreads=True,
        foreground=True
    )

main(parse_args())
