#!/usr/bin/env python
# -*- coding: utf8 -*-
#!/usr/bin/env python3
import os
from setuptools import setup
from setuptools.config import read_configuration

from pathlib import Path
thisDir=Path(__file__).parent
formatsPath=thisDir / "kaitai_struct_formats"

cfg = read_configuration(str((thisDir / 'setup.cfg').absolute()))
#print(cfg)
cfg["options"].update(cfg["metadata"])
cfg=cfg["options"]

cfg["kaitai"]={
    "formatsRepo": {
        "localPath" : str(formatsPath),
        "update": True
    },
    "formats":{
        "heroes_of_might_and_magic_agg.py": {"path": "game/heroes_of_might_and_magic_agg.ksy"},
        "quake_pak.py": {"path": "game/quake_pak.ksy"},
        "iso9660.py": {"path": "filesystem/iso9660.ksy"},
        "rar.py": {"path": "archive/rar.ksy"},
    },
    "outputDir": thisDir / "kaitaifs" / "parser",
    "inputDir": formatsPath
}

setup(**cfg)
