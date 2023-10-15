#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from .fs.rar_fs import RarFS
from .fs.quake_pak_fs import QuakePakFS
from .fs.heroes_of_might_and_magic_agg_fs import (
    HeroesOfMightAndMagicAggFS
)
from .fs.iso9660_fs import Iso9660FS

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
    parser.add_argument(
        "volume_name",
        metavar="VOLUME_NAME",
        type=str,
        help="volume name (osxfuse and winfsp only)",
        nargs="?",
        default="Kaitai",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    fs_class = FILESYSTEMS[args.fstype]
    FUSE(
        fs_class(args.image_file),
        args.mount_point,
        nothreads=True,
        foreground=True,
        volname=args.volume_name
    )

if __name__ == "__main__":
    main()
