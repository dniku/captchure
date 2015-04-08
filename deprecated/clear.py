"""
    Copyright 2011 Dmitry Nikulin

    This file is part of Captchure.

    Captchure is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Captchure is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Captchure.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys, os
from globConst import ann_file, train_file, segment_dir

if len(sys.argv) == 1:
    sys.exit(0)

def clear_pyc():
    files = os.listdir(".")
    for name in files:
        if name.endswith(".pyc"):
            os.remove(name)

def clear_data():
    if os.path.exists(train_file): os.remove(train_file)
    if os.path.exists(ann_file): os.remove(ann_file)

def clear_segments():
    files = os.listdir(segment_dir)
    for name in files:
        os.remove(os.path.join(segment_dir, name))

if sys.argv[1] == "pyc": clear_pyc()
elif sys.argv[1] == "data": clear_data()
elif sys.argv[1] == "segments": clear_segments()
elif sys.argv[1] == "all":
    clear_pyc()
    clear_data()
    clear_segments()