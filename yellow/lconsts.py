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

mygray = 153
myblue = 102
mylgrn = 51
mydgrn = 1
myunkn = 128

mycolors = (mygray, myblue, mylgrn, mydgrn)

nSegs = 5

charset = "#123456789abcdefhkmoprt"

segW = 30
segH = 30
segSize = (segW, segH)

num_input = segW * segH
num_output = len(charset)

ann_dir = "anns"
train_file = "ann.train"
ann_file = "ann.net"
test_file = "ann.test"