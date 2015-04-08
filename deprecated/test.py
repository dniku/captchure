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

import os, sys, copy, shutil, main
sys.path.append("beeline")
import train

original_spoilers = copy.copy(train.spoilers)

minerror = 10.0

for index in xrange(len(original_spoilers)):
    print "%d: " % (index),
    train.spoilers = original_spoilers[:index] + original_spoilers[index+1:]
    rootDir = os.getcwd()
    os.chdir("beeline")
    train.train()
    os.chdir(rootDir)
    error = main.main(["beeline", "--directory", "testset", "--mode", "color"])
    print error,
    if error < minerror:
        shutil.copyfile("beeline\\ann.net", "beeline\\beeline_" + str(int(error * 100)) + "_" + str(index) + ".net")
        print "saved"