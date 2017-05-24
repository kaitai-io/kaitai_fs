#!/usr/bin/env python
# -*- coding: utf8 -*-
from setuptools import setup, find_packages


if __name__ == '__main__':
    setup(
        name='kaitaifs',
        version='0.1.0',
        long_description=__doc__,
        packages=find_packages(),
        install_requires=[
            'enum34',
            'fusepy',
            'kaitaistruct==0.7'
        ],
        entry_points={
            'console_scripts': [
                'kaitaifs=kaitaifs.cli:main'
            ]
        }
    )
