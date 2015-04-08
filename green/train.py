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

import os, cv
from pyfann import libfann
from lconsts import segW, segH, num_input, num_output, charset, train_file, ann_file

sys.path.append("..")

from cap import resizeFit as adjustSize, segment_dir

segments = os.listdir(segment_dir)

f = open(train_file, "w")
f.write("%d %d %d\n" % (len(segments), num_input, num_output))


for name in segments:
    image = cv.LoadImage(os.path.join(segment_dir, name), cv.CV_LOAD_IMAGE_GRAYSCALE)
    image = adjustSize(image, (segW, segH))
    for y in range(image.height):
        for x in range(image.width):
            n = image[y, x] / 159.375 - 0.8
            f.write("%f " % n)
    f.write("\n")
    c = os.path.splitext(name)[0][0]
    n = charset.index(c)
    f.write("-1 " * n + "1" + " -1" * (num_output - n - 1) + "\n")

f.close()

print "Samples: %d" % len(segments)
print "Input: %d" % num_input
print "Output: %d" % num_output

connection_rate = 1.0
learning_rate = 0.3
num_neurons_hidden = num_input / 3

desired_error = 0.00001
max_iterations = 10000
iterations_between_reports = 20

ann = libfann.neural_net()
ann.create_sparse_array(connection_rate, (num_input, num_neurons_hidden, num_output))
ann.set_learning_rate(learning_rate)
ann.set_activation_function_hidden(libfann.SIGMOID_SYMMETRIC_STEPWISE)
ann.set_activation_function_output(libfann.SIGMOID_SYMMETRIC_STEPWISE)

ann.train_on_file(train_file, max_iterations, iterations_between_reports, desired_error)

ann.save(ann_file)