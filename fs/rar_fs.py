from parser.rar import Rar

from kaitai_simple_fs import KaitaiSimpleFS

class RarFS(KaitaiSimpleFS):
    def __init__(self, filename):
        self.obj = Rar.from_file(filename)
        super(RarFS, self).__init__()

    def generate_tree(self):
        for block in self.obj.blocks:
            if block.block_type == Rar.BlockTypes.file_header:
                self.add_obj_to_path(block.body.file_name.split('\\'), block)

    def get_file_attrs(self, obj):
        return {
            'st_atime': 0,
            'st_ctime': 0,
            'st_mtime': 0,
            'st_nlink': 1,
            'st_mode': 0o100644,
            'st_size': obj.add_size,
            'st_gid': 0,
            'st_uid': 0,
        }

    def get_file_body(self, obj, offset, length):
        return obj.add_body[offset:offset + length]
