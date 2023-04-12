#!/usr/bin/env python
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name="djutils",
    version="0",
    description="Datajoint Utilities",
    author="Eric Y. Wang",
    author_email="eric.wang2@bcm.edu",
    packages=find_packages(exclude=[]),
    install_requires=[],
)
