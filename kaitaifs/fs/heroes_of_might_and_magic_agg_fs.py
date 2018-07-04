# -*- coding: utf-8 -*-
from ..parser.heroes_of_might_and_magic_agg import (
    HeroesOfMightAndMagicAgg
)

from ..kaitai_simple_fs import KaitaiSimpleFS


class HeroesOfMightAndMagicAggFS(KaitaiSimpleFS):
    def __init__(self, filename):
        self.obj = HeroesOfMightAndMagicAgg.from_file(filename)
        super(HeroesOfMightAndMagicAggFS, self).__init__()

    def generate_tree(self):
        for i in range(len(self.obj.filenames)):
            fn = self.obj.filenames[i].str
            entry = self.obj.entries[i]
            self.add_obj_to_path([fn], entry)

    def get_file_attrs(self, obj):
        a = super(HeroesOfMightAndMagicAggFS, self).get_file_attrs(obj)
        a['st_size'] = obj.size
        return a

    def get_file_body(self, obj, offset, length):
        return obj.body[offset:offset + length]
