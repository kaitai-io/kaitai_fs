__all__=("dumpStruct",)
from fuse import FuseOSError
import errno

from pathlib import Path, PurePath

import os
from kaitaistruct import KaitaiStruct
from collections import OrderedDict

from ..kaitai_tree_fs import KaitaiTreeFS, split_obj_path
from datetime import *
import typing
import math

someServiceMethodsAndProps={
    'close',
    'from_bytes',
    'from_file',
    'from_io',
    'from_any'
}
def isFinalProductPropertyName(name):
    return (name[0].islower() and name not in someServiceMethodsAndProps)

from fuse import Operations
import stat

class TypeSplitter:
    fileExtension = None
    def __init__(self):
        raise NotImplementedError()
    
    def splitSuitable(self, obj) -> (typing.Mapping, typing.Mapping):
        raise NotImplementedError()
    
    def getObj(self, cur_dir, name, getObj) -> bytes:
        return self.suitableToBytes(getObj(cur_dir, name))
    
    def suitableToBytes(self) -> bytes:
        raise NotImplementedError()

class PerObjSplitter(TypeSplitter):
    suitableTypes = None
    def isSuitable(self, obj):
        res = isinstance(obj, self.__class__.suitableTypes)
        return res
    
    def splitSuitableForASeq(self, arr, suitable, rest):
        """Return a new `suitable` if needed. If not needed, return the one passed in args. You can also modify that one."""
        return suitable
    
    def splitSuitable(self, s) -> (typing.Mapping, typing.Mapping):
        suitable = OrderedDict()
        rest = OrderedDict()
        
        if self.isSuitable(s):
            return s, rest
        if isinstance(s, list):
            suitable = self.splitSuitableForASeq(s, suitable, rest)
        elif isinstance(s, KaitaiStruct):
            s = OrderedDict((name, getattr(s, name)) for name in filter(isFinalProductPropertyName, dir(s)))
        
        if isinstance(s, dict): # it is a KaitaiStruct spec
            for name, prop in s.items():
                if self.isSuitable(prop):
                    suitable[name] = prop
                else:
                    rest[name] = prop
        return (suitable, rest)
    
    def getNames(self, splitted):
        for name in splitted.keys():
            yield name + "." + self.fileExtension

class DumbSplitter(PerObjSplitter):
    def __init__(self):
        pass

class BinarySplitter(DumbSplitter):
    fileExtension = "bin"
    suitableTypes = (bytes, bytearray)
    def suitableToBytes(self, suitable:bytes) -> bytes:
        return suitable

class StrSplitter(DumbSplitter):
    fileExtension = "txt"
    suitableTypes = str
    def suitableToBytes(self, suitable:str) -> bytes:
        return suitable.encode("utf-8")


class ObjectArrayDeciderSplitter(PerObjSplitter):
    arrayIndexSkipSpace = None
    objectIndexOverhead = None
    
    def numberOverhead(self, base:int) -> int:
        return 0 if base == 10 else 2 # 0x, 0b, 0o ...
    
    def numberRepresentationSize(self, log: int, base: int) -> int:
        return log
    
    def splitSuitableForASeq(self, arr, suitable, rest):
        arrayPlainProp = [None] * len(arr)
        cumulativeStringIndexSize = 0
        cumulativeNullInArraySize = 0
        intBase = 10
        nextExponent = 1
        currentIntStrSize = 0 # log(nextExponent, base) = log(currentExponent, base) + 1
        for i, item in enumerate(arr):
            if i % nextExponent == 0:
                currentIntStrSize += 1
                nextExponent *= intBase
            
            if self.isSuitable(item):
                arrayPlainProp[i] = item
            else:
                cumulativeNullInArraySize += self.__class__.arrayIndexSkipSpace
                cumulativeStringIndexSize = self.__class__.objectIndexOverhead + self.numberOverhead(intBase) + self.numberRepresentationSize(currentIntStrSize, intBase)
            
                rest[str(i)] = item
            
        if cumulativeNullInArraySize <= cumulativeStringIndexSize:
            return arrayPlainProp
        else:
            return suitable

class JSONSplitter(ObjectArrayDeciderSplitter):
    fileExtension = "json"
    suitableTypes = (int, float, str)
    
    arrayIndexSkipSpace = 4 # `null`
    objectIndexOverhead = 2 # pair of quotes
    
    def __init__(self):
        import json
        self.json = json
    
    def getObj(self, cur_dir:typing.Any, name:str, getObj:typing.Callable) -> bytes:
        if name == "__dict__":
            o = self.splitSuitable(cur_dir)[0]
        else:
            o = getObj(cur_dir, name)
        return self.suitableToBytes(o)
    
    def suitableToBytes(self, suitable) -> bytes:
        return self.json.dumps(suitable, ensure_ascii=False, indent="\t").encode("utf-8")
    
    def getNames(self, splitted):
        if splitted:
            yield "__dict__" + "." + self.fileExtension


class YAMLSplitter(JSONSplitter):
    fileExtension = "yml"
    
    arrayIndexSkipSpace = 4 # `null`
    objectIndexOverhead = 2 # pair of quotes
    
    def __init__(self):
        import ruamel.yaml
        from io import StringIO
        self.yaml = ruamel.yaml
        def toYaml(o):
            yamlDumper = self.yaml.YAML(typ="rt")
            yamlDumper.indent(mapping=2, sequence=4, offset=2)
            with StringIO() as s:
                yamlDumper.dump(o, s)
                return s.getvalue()
        # TODO: type comments or tags support
        self.toYaml = toYaml
    
    def suitableToBytes(self, suitable) -> bytes:
        return self.toYaml(suitable).encode("utf-8")


class MSGPackSplitter(JSONSplitter):
    fileExtension = "msgpack"
    suitableTypes = (int, float, str)
    
    arrayIndexSkipSpace = 0
    objectIndexOverhead = 0
    
    def __init__(self):
        import msgpack
        self.msgpack = msgpack
    
    def suitableToBytes(self, suitable) -> bytes:
        return self.msgpack.dumps(suitable)


defaultSplitterStack = (
    JSONSplitter(),
    #StrSplitter(),
    BinarySplitter()
)

class AnyKSFS(KaitaiTreeFS):
    def __init__(self, ctor, filename:Path, splitterStack:typing.Optional[typing.Sequence[TypeSplitter]] = None):
        filename = Path(filename)
        st = filename.lstat()
        self.ATTR_DIR = {
            "st_mode": st.st_mode & 0o777,
            'st_atime': st.st_atime,
            'st_ctime': st.st_ctime,
            'st_mtime': st.st_mtime,
            "st_nlink": 2,
            'st_gid': st.st_gid,
            'st_uid': st.st_uid,
        }
        if splitterStack is None:
            splitterStack = defaultSplitterStack
        self.splitterStack = splitterStack
        self.extSplitterMapping = {
            s.fileExtension: s for s in splitterStack
        }
        self.obj = ctor.from_file(str(filename))
        super().__init__()
        self.fd = 0

    def obj_by_pathstr(self, pathstr:str):
        return self.obj_by_path(split_obj_path(pathstr))
    
    def obj_by_path(self, path):
        tree = self.obj
        for comp in path:
            tree = self.find_name_in_dir(tree, comp)
        return tree

    def find_name_in_dir(self, cur_dir, name):
        extSplit = name.split(".")
        
        def getObj(cur_dir, name):
            if hasattr(cur_dir, name):
                return getattr(cur_dir, name)
            else:
                raise FuseOSError(errno.ENOENT)
        
        if len(extSplit) == 2:
            name, ext = extSplit
            if ext in self.extSplitterMapping:
                s = self.extSplitterMapping[ext]
                return s.getObj(cur_dir, name, getObj)
            else:
                raise FuseOSError(errno.ENOENT)
        else:
            if isinstance(cur_dir, list):
                try:
                    name = int(name)
                except:
                    raise FuseOSError(errno.ENOENT)
                
                if name < len(cur_dir):
                    return cur_dir[name]
                else:
                    raise FuseOSError(errno.ENOENT)
            else:
                return getObj(cur_dir, name)
    
    def splitProps(self, s) -> (typing.Sequence[typing.Mapping], typing.Mapping):
        rest = s
        splittedSeq = []
        for s in self.splitterStack:
            splitted, rest = s.splitSuitable(rest)
            splittedSeq.append((s, splitted))
        
        return splittedSeq, rest
        

    def readdir(self, path, fh):
        obj = self.obj_by_pathstr(path)
        for r in ('.', '..'):
            yield r
        for r in self.list_files(obj):
            yield r


    def list_files(self, cur_dir):
        splittedSeq, rest = self.splitProps(cur_dir)
        for splitter, splitted in splittedSeq:
            yield from splitter.getNames(splitted)
        
        for fn in rest:
            yield fn
    

    def getattr(self, path, fh=None):
        obj = self.obj_by_pathstr(path)
        res = type(self.ATTR_DIR)(self.ATTR_DIR)
        res.update(self.get_file_attrs(obj))
        return res

    #def getxattr(self, path, name, position=0):
    #    return {}

    def get_file_attrs(self, obj):
        mode = self.ATTR_DIR["st_mode"]
        
        # Directory or file?
        if isinstance(obj, (list, KaitaiStruct)):
            mode |= stat.S_IFDIR
        else:
            mode |= stat.S_IFREG
        
        res = {
            'st_mode': mode,
            'st_nlink': 1,
        }
        
        if isinstance(obj, (bytes, bytearray)):
            res['st_size'] = len(obj)
        
        return res

    def read(self, path, length, offset, fh):
        obj = self.openfiles[fh]
        data = self.get_file_body(obj, offset, length)
        return data
    
    def get_file_body(self, obj, offset, length):
        return obj[offset:offset + length]

