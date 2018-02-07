# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
from kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO


if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class HeroesOfMightAndMagicAgg(KaitaiStruct):
    """
    .. seealso::
       Source - http://rewiki.regengedanken.de/wiki/.AGG_(Heroes_of_Might_and_Magic)
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.num_files = self._io.read_u2le()
        self.entries = [None] * (self.num_files)
        for i in range(self.num_files):
            self.entries[i] = self._root.Entry(self._io, self, self._root)


    class Entry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.hash = self._io.read_u2le()
            self.offset = self._io.read_u4le()
            self.size = self._io.read_u4le()
            self.size2 = self._io.read_u4le()

        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body if hasattr(self, '_m_body') else None

            _pos = self._io.pos()
            self._io.seek(self.offset)
            self._m_body = self._io.read_bytes(self.size)
            self._io.seek(_pos)
            return self._m_body if hasattr(self, '_m_body') else None


    class Filename(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.str = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")


    @property
    def filenames(self):
        if hasattr(self, '_m_filenames'):
            return self._m_filenames if hasattr(self, '_m_filenames') else None

        _pos = self._io.pos()
        self._io.seek((self.entries[-1].offset + self.entries[-1].size))
        self._raw__m_filenames = [None] * (self.num_files)
        self._m_filenames = [None] * (self.num_files)
        for i in range(self.num_files):
            self._raw__m_filenames[i] = self._io.read_bytes(15)
            io = KaitaiStream(BytesIO(self._raw__m_filenames[i]))
            self._m_filenames[i] = self._root.Filename(io, self, self._root)

        self._io.seek(_pos)
        return self._m_filenames if hasattr(self, '_m_filenames') else None


