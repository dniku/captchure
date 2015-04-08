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

imgW = 450
imgH = 175

nSegs = 4

segW = 30
segH = 30
segSize = (segW, segH)

rsegW = 90
rsegH = 90

charset = "23456789abcdefkmnpqsuvwxyz"

num_input = segW * segH
num_output = len(charset)

train_file = "ann.train"
ann_file = "ann.net"

segment_dir = "segments"