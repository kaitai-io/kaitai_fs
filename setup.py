#!/usr/bin/env python
# -*- coding: utf8 -*-
from setuptools import setup
from setuptools.config import read_configuration
from pathlib import Path

cfg = read_configuration(str(Path(__file__).parent / 'setup.cfg'))
#print(cfg)
cfg["options"].update(cfg["metadata"])
cfg = cfg["options"]
setup(**cfg)
