# -*- coding: utf-8 -*-
from ..parser.quake_pak import QuakePak
from ..kaitai_simple_fs import KaitaiSimpleFS


class QuakePakFS(KaitaiSimpleFS):
    def __init__(self, filename):
        self.obj = QuakePak.from_file(filename)
        super(QuakePakFS, self).__init__()

    def generate_tree(self):
        for entry in self.obj.index.entries:
            self.add_obj_to_path(entry.name.split('/'), entry)

    def get_file_attrs(self, obj):
        a = super(QuakePakFS, self).get_file_attrs(obj)
        a['st_size'] = obj.size
        return a

    def get_file_body(self, obj, offset, length):
        return obj.body[offset:offset + length]
