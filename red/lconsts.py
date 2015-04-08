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

imgW = 83
imgH = 23

factor = 2

rimgW = imgW * factor
rimgH = imgH * factor

nSegs = 5

segW = 18
segH = 18
segSize = (segW, segH)

num_input = segW * segH
num_output = 30

charset = "2345689abcdefghjkmnpqrstuvwxyz"

ann_file = "ann.net"
train_file = "ann.train"