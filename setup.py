#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="djutils",
    version="0.1.0",
    description="Datajoint Utilities",
    packages=find_packages(),
    install_requires=["datajoint>=0.12.9,<0.13.0"],
)
