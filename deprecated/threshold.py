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
from globConst import sample_dir

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

print name

class analyzer:
    def __init__(self, image):
        self.image = image
        self.clone = cv.CreateImage(cv.GetSize(image), image.depth, image.nChannels)
        self.tLetter = 64
        self.rBright = 30
    def clearNoise(self, image):
        for x in range(image.width):
            for y in range(image.height):
                if image[y, x] == 0:
                    continue
                if image[y, x] < self.tLetter:
                    cv.FloodFill(image, (x, y), 0, self.rBright, self.rBright, 8, None)
        cv.Threshold(image, image, 1, 255, cv.CV_THRESH_BINARY_INV)
    def reDraw(self):
        cv.Copy(self.image, self.clone)
        self.clearNoise(self.clone)
        cv.ShowImage("Threshold", self.clone)
    def onChangeLetter(self, ntLetter):
        self.tLetter = ntLetter
        self.reDraw()
    def onChangeBright(self, nrBright):
        self.rBright = nrBright
        self.reDraw()
    def run(self):
        cv.NamedWindow("Threshold", 1)
        cv.ShowImage("Threshold", image)
        cv.CreateTrackbar("tLetter", "Threshold", self.tLetter, 255, self.onChangeLetter)
        cv.CreateTrackbar("rBright", "Threshold", self.rBright, 255, self.onChangeBright)
        self.reDraw()
        cv.WaitKey(0)

    
image = cv.LoadImage(name, cv.CV_LOAD_IMAGE_GRAYSCALE)
analyzer(image).run()