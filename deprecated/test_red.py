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

import os, cv, sys, random
from preprocess import preprocess
from segment import segment
from recognise import recognise
from globConst import sample_dir, test_dir

if len(sys.argv) == 1:
    folder = test_dir
    contents = os.listdir(folder)
    name = os.path.join(folder, contents[random.randint(0, len(contents) - 1)])
elif sys.argv[1] == "sample":
    folder = sample_dir
    contents = os.listdir(folder)
    name = os.path.join(folder, contents[random.randint(0, len(contents) - 1)])
else:
    name = sys.argv[1]

image = cv.LoadImage(name, cv.CV_LOAD_IMAGE_GRAYSCALE)
cv.NamedWindow("Original", 1)
cv.ShowImage("Original", image)
pp_image = preprocess(image)
print "%s: preprocessed" % name
cv.NamedWindow("Preprocessed", 1)
cv.ShowImage("Preprocessed", pp_image)
cv.WaitKey(0)
segments = segment(pp_image)
print "%s: segmented -> %d" % (name, len(segments))
for i in range(len(segments)):
    cv.NamedWindow(str(i), 1)
    cv.ShowImage(str(i), segments[i])
cv.WaitKey(0)
chars = map(recognise, segments)
result = "".join(map(str, chars))
print "%s: recognised -> %s" % (name, result)
cv.WaitKey(0)