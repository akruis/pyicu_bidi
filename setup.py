#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 by science+computing ag
# Author: Anselm Kruis <a.kruis@science-computing.de>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


from setuptools import setup

release = None
for line in open('conf.py'):
    if line.startswith('release = '):
        exec(line)
        break

setup(
    name='PyICU_BiDi',
    version=release,
    description='The Unicode bidirectional algorithm from ICU',
    author='Anselm Kruis',
    author_email='a.kruis@science-computing.de',
    url='http://pypi.python.org/pypi/PyICU_BiDi',
    packages=['icu_bidi'],

    # don't forget to add these files to MANIFEST.in too
    #package_data={'pyheapdump': ['examples/*.py']},

    long_description="""
PyICU_BiDi
----------

PyICU_BiDi is a quick and dirty ctypes-based binding of the
Unicode birirectional algorithm.

Git repository: https://github.com/akruis/pyicu_bidi.git
""",
    classifiers=[
                 "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: Implementation :: CPython",
                 "Environment :: Console",
                 "Operating System :: OS Independent",
                 "Development Status :: 3 - Alpha",  # hasn't been tested outside of flowGuide2
                 "Intended Audience :: Developers",
                 "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='unicode bidi',
      license='GNU Lesser General Public License, version 2.1 or any later version',
      install_requires=[
        'PyICU>=1.4', 'enum34'
      ],
      platforms="any",
      test_suite="icu_bidi",
    )
