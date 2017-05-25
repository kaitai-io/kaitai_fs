# -*- coding: utf-8 -*-
from kaitaifs.parser.rar import Rar

from kaitaifs.kaitai_simple_fs import KaitaiSimpleFS


class RarFS(KaitaiSimpleFS):
    def __init__(self, filename):
        self.obj = Rar.from_file(filename)
        super(RarFS, self).__init__()

    def generate_tree(self):
        for block in self.obj.blocks:
            if block.block_type == Rar.BlockTypes.file_header:
                self.add_obj_to_path(block.body.file_name.split('\\'), block)

    def get_file_attrs(self, obj):
        a = super(RarFS, self).get_file_attrs(obj)
        a['st_size'] = obj.add_size
        return a

    def get_file_body(self, obj, offset, length):
        return obj.add_body[offset:offset + length]
