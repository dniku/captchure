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

import os, cv, sys
from random import shuffle, randint, uniform, choice
from pyfann import libfann
from lconsts import segW, segH, num_input, num_output, charset, train_file, ann_file

test_file = "ann.test"

sys.path.append("..")

import cap
from cap import resizeFit as adjustSize, segment_dir

def addWhiteDots(image):
    for i in xrange(randint(10, 20)):
        image[randint(0, image.height - 1), randint(0, image.width - 1)] = 255
    return image

def addGrayDots(image):
    for i in xrange(randint(10, 20)):
        image[randint(0, image.height - 1), randint(0, image.width - 1)] = 96
    return image

def addBlackDots(image):
    for i in xrange(randint(10, 20)):
        image[randint(0, image.height - 1), randint(0, image.width - 1)] = 0
    return image

def addGrayLines(image):
    for i in xrange(randint(1, 3)):
        pt1 = (randint(0, image.width - 1), randint(0, image.height - 1))
        pt2 = (randint(0, image.width - 1), randint(0, image.height - 1))
        cv.Line(image, pt1, pt2, 96, 1)
    return image

def addGrayCircles(image):
    for i in xrange(randint(1, 4)):
        cv.Circle(image, (randint(0, image.width - 1), randint(0, image.height - 1)), randint(2, 4), 96, -1)
    return image

def addGrayRectsBad(image):
    for i in xrange(randint(1, 3)):
        pt1 = (randint(0, image.width - 2), randint(0, image.height - 2))
        pt2 = (randint(pt1[0] + 1, image.width - 1), randint(pt1[1] + 1, image.height - 1))
        cv.Rectangle(image, pt1, pt2, 128, -1)
    return image

def addGrayRects(image):
    for i in xrange(randint(1, 3)):
        w = randint(2, 5)
        h = randint(2, 5)
        pt1 = (randint(0, image.width - w), randint(0, image.height - h))
        pt2 = (pt1[0] + w - 1, pt1[1] + h - 1)
        cv.Rectangle(image, pt1, pt2, 96, -1)
    return image

def addRotation(image):
    angle = uniform(-15.0, 15.00000001)
    image = cap.doRotate(image, angle)
    return image

spoilers = (addWhiteDots, addGrayDots, addBlackDots, addGrayLines, addGrayCircles, addGrayRects, addRotation)

def spoil(image):
    return (choice(spoilers))(image)

def loadTest():
    global test
    test = libfann.training_data()
    test.read_train_from_file(test_file)

def loadSegments():
    global segments
    segments = os.listdir(segment_dir)
    segments = map(lambda name: (os.path.splitext(name)[0][0], cv.LoadImage(os.path.join(segment_dir, name), cv.CV_LOAD_IMAGE_GRAYSCALE)), segments)

def printStats():
    print "Samples: %d" % len(segments)
    print "Input: %d" % num_input
    print "Output: %d" % num_output

def initNet():
    learning_rate = 0.3
    num_neurons_hidden = num_input / 3
    
    #desired_error = 0.015
    #max_iterations = 10000
    #iterations_between_reports = 10
    
    global ann
    ann = libfann.neural_net()
    ann.create_standard_array((num_input, num_neurons_hidden, num_output))
    ann.set_learning_rate(learning_rate)
    ann.set_activation_function_hidden(libfann.SIGMOID_SYMMETRIC_STEPWISE)
    ann.set_activation_function_output(libfann.SIGMOID_SYMMETRIC_STEPWISE)

    train = libfann.training_data()
    train.read_train_from_file(train_file)
    ann.init_weights(train)
    train.destroy_train()

def mainLoop():
    n_iter = 0
    last_save = 0
    min_test_MSE = 1.0
    max_iters_after_save = 50
    
    try:
        while True:
            n_iter += 1
            print "Iteration: %5d " % (n_iter),
            seg_copy = map(lambda (c, seg): (c, cv.CloneImage(seg)), segments)
            seg_copy = map(lambda (c, seg): (c, spoil(seg)), seg_copy)
            shuffle(seg_copy)
            
            f = open(train_file, "w")
            f.write("%d %d %d\n" % (len(segments), num_input, num_output))
        
            for c, image in seg_copy:
                image = adjustSize(image, (segW, segH))
                for y in range(image.height):
                    for x in range(image.width):
                        n = image[y, x] / 159.375 - 0.8
                        f.write("%f " % n)
                f.write("\n")
                n = charset.index(c)
                f.write("-1 " * n + "1" + " -1" * (num_output - n - 1) + "\n")
        
            f.close()
            
            train = libfann.training_data()
            train.read_train_from_file(train_file)
            ann.train_epoch(train)
            train.destroy_train()
            print "Train MSE: %f " % (ann.get_MSE()),
            print "Train bit fail: %5d " % (ann.get_bit_fail()),
            ann.test_data(test)
            mse = ann.get_MSE()
            print "Test MSE: %f " % (mse),
            print "Test bit fail: %5d " % (ann.get_bit_fail()),
            if mse < min_test_MSE:
                min_test_MSE = mse
                ann.save(ann_file)
                last_save = n_iter
                print "saved",
            if n_iter - last_save > max_iters_after_save: break
            print
    except KeyboardInterrupt: print "Interrupted by user."

def cleanup():
    test.destroy_train()
    ann.destroy()

def train():
    loadTest()
    loadSegments()
    printStats()
    initNet()
    mainLoop()
    cleanup()

if __name__ == "__main__":
    train()