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

import cv, cap, os, sys, types, random
from optparse import OptionParser, OptionValueError


def makeParser():
    """Create an instance of OptionParser and fill it with appropriate options."""
    parser = OptionParser(prog="Captchure", version="%prog 0.1", usage="main.py <captcha_name> {-d DIR|-f FILE} [options]")
    
    parser.add_option("-d", "--dir", "--directory", action="store", type="string", metavar="DIR", dest="directory", default="", \
                      help="Subdirectory of the module folder that contains images to process. These images are called 'the dataset'.")
    parser.add_option("-r", "--random", action="store_true", dest="random", default=False, \
                      help="A randomly selected image will be taken from the dataset. It can't be used together with --file.")
    parser.add_option("-f", "--file", action="store", type="string", metavar="FILE", dest="file", default="", \
                      help="Process a specific FILE given as a parameter to this option.\n It can't be used together with --random.")
    parser.add_option("-m", "--mode", action="store", type="choice", choices=["gs", "grayscale", "c", "color"], metavar="MODE", dest="mode", default="gs", \
                      help="The image loading mode. Can be either 'grayscale' ('gs') or 'color' ('c'). Default: grayscale.")
    parser.add_option("-s", "--save", action="append", type="choice", choices=["preprocessed", "segmented", "recognised", "p", "s", "r"], metavar="STAGE", dest="save", \
                      help="Specify stages where intermediate results are saved. Can be either 'preprocessed', 'segmented' or 'recognised'.")
    parser.add_option("-p", "--preprocess", action="append_const", const=cap.CAP_STAGE_PREPROCESS, dest="stages", \
                      help="Preprocess the dataset.")
    parser.add_option("-g", "--segment", action="append_const", const=cap.CAP_STAGE_SEGMENT, dest="stages", \
                      help="Segment the dataset.")
    parser.add_option("-c", "--recognise", action="append_const", const=cap.CAP_STAGE_RECOGNISE, dest="stages", \
                      help="Recognise the dataset.")
    parser.add_option("-e", "--extras", action="store", type="choice", choices=["save", "show", "off"], metavar="ACTION", dest="extras", \
                      help="Enable or disable generating of extra information, such as steps performed. Can be either 'off', 'show' or 'save'.")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False, \
                      help="Disable showing images after each stage.")
    # Also, a recognition engine directory should be provided as an argument.
    return parser

class optsort:
    """Post-processor of the result obtained by OptionParser."""
    def setConsts(self):
        # Color mode
        self.grayscaleKeys = ["gs", "grayscale"]
        self.colorKeys = ["c", "color"]
        
        # Stages
        self.preprocessKeys = ["pre", "preprocess", "preprocessed"]
        self.segmentKeys = ["seg", "segment", "segmented"]
        self.recogniseKeys = ["rec", "recognise", "recognised"]
        
        # Extras
        self.extrasKeys = {"off": cap.CAP_EXTRAS_OFF, "show": cap.CAP_EXTRAS_SHOW, "save": cap.CAP_EXTRAS_SAVE}
    
    def __init__(self, (options, args)):
        # Check for trivial errors
        if options.random and options.file != "":
            raise OptionValueError("--random and --file are mutually exclusive")
        if args == [] or not os.path.exists(args[0]) or not os.path.isdir(args[0]):
            raise OptionValueError("A recognition engine directory must be provided as an argument")
        if options.directory == "" and options.file == "":
            raise OptionValueError("Some input files must be provided using the -d or -f keys.")
        
        # Set constants
        self.setConsts()
        
        # Set recognition engine
        self.engine = args[0]
        
        # Set required stages
        if options.stages is None: # default
            options.stages = [cap.CAP_STAGE_PREPROCESS, cap.CAP_STAGE_SEGMENT, cap.CAP_STAGE_RECOGNISE]
        self.preprocess = cap.CAP_STAGE_PREPROCESS in options.stages
        self.segment = cap.CAP_STAGE_SEGMENT in options.stages
        self.recognise = cap.CAP_STAGE_RECOGNISE in options.stages
        
        # Set color mode
        if   options.mode in self.grayscaleKeys: self.mode = cv.CV_LOAD_IMAGE_GRAYSCALE
        elif options.mode in self.colorKeys:     self.mode = cv.CV_LOAD_IMAGE_COLOR
        else: raise OptionValueError("Incorrect mode parameter.")
        
        # Set files to be processed
        if options.file != "":
            directory, names = os.path.split(options.file)
            self.directory = os.path.join(options.directory, directory)
            self.names = [names]
            self.total = 1
            self.single = True
        elif options.directory != "":
            self.directory = options.directory
            self.names = os.listdir(os.path.join(self.engine, self.directory))
            if options.random:
                self.names = [self.names[random.randint(0, len(self.names) - 1)]]
                self.total = 1
                self.single = True
            else:
                self.total = len(self.names)
                self.single = False
        else: raise OptionValueError("Something weird is going on...")
        
        # Set saving options
        if options.save is None:
            options.save = []
        self.savePreprocess = any([key in options.save for key in self.preprocessKeys])
        self.saveSegment = any([key in options.save for key in self.segmentKeys])
        self.saveRecognise = any([key in options.save for key in self.recogniseKeys])
        
        # Set showing options
        self.show = self.single and not options.quiet
        self.autosize = 0
        
        # Set extras options
        if options.extras is not None:
            self.extras = self.extrasKeys[options.extras]
        else:
            if self.single: self.extras = cap.CAP_EXTRAS_SHOW
            else:           self.extras = cap.CAP_EXTRAS_OFF

class cReport:
    """Used within the mainLoop() function to collect stats."""
    def __init__(self):
        self.loading = []
        self.preprocessing = []
        self.segmentation = []
        self.recognition = []
        self.saving = []
        
        self.successes = 0
        self.mismatches = 0
        self.distances = []
    def printNicely(self, lst, name):
        if lst == []:
            return
        print "%s (%d): " % (name, len(lst))
        print "",
        if len(lst) <= 7:
            print "\n ".join(lst)
        else:
            print "\n ".join(lst[:3])
            print " ..."
            print "",
            print "\n ".join(lst[-3:])
    def printErrors(self):
        self.printNicely(self.loading, "Loading")
        self.printNicely(self.preprocessing, "Preprocessing")
        self.printNicely(self.segmentation, "Segmentation")
        self.printNicely(self.recognition, "Recognition")
        self.printNicely(self.saving, "Saving")
    def printRecStats(self, total):
        print "Total: %d" % (total)
        print "Successes: %d, %d%%" % (self.successes, 100 * self.successes / total)
        print "Mismatches: %d, %d%%" % (self.mismatches, 100 * self.mismatches / total)
        if self.mismatches + self.successes != 0:
            totaldist = float(sum(self.distances))
            self.error = totaldist / (self.mismatches + self.successes)
            print "Average error: %f" % (self.error)
            if self.mismatches != 0:
                print "Average nonzero error: %f" % (totaldist / self.mismatches)

def importModules(options):
    """Imports all modules specified in the first argument (and optsort instance) into the global namespace.
    The second argument is a directory which contains all of the modules being imported.
    Note: sys.path and cwd must be already set as appropriate!"""
    if options.preprocess:
        try: _temp = __import__("preprocess", fromlist=["preprocess"]) # from preprocess import preprocess
        except ImportError:
            print "Cannot import preprocessing module for '%s'" % (options.engine)
            raise
        global preprocess
        preprocess = _temp.preprocess
    if options.segment:
        try: _temp = __import__("segment", fromlist=["segment"]) # from segment import segment
        except ImportError:
            print "Cannot import segmentation module for '%s'" % (options.engine)
            raise
        global segment
        segment = _temp.segment
    if options.recognise:
        try: _temp = __import__("recognise", fromlist=["recognise"]) # from recognise import recognise
        except ImportError:
            print "Cannot import recognition module for '%s'" % (options.engine)
            raise
        global recognise
        recognise = _temp.recognise

def findFilename(prefix, ext):
    """Inserts a numeric suffix between the given prefix and extension so that the resulting
    filename is guaranteed not to exist."""
    j = 0
    while os.path.exists(prefix + str(j) + ext): j += 1
    return prefix + str(j) + ext

def saveResult(result, directory, pre):
    """Saves the result of either preprocessing or segmentation into the given directory using
    the given prefix and the default extension (defext in cap.consts). The exact method of saving is
    determined by the type of the result - it can be either a list or an iplimage."""
    t = type(result)
    if t is types.ListType or t is types.TupleType:
        for index, image in enumerate(result):
            c = pre[len(pre) - 1] if index >= len(pre) else pre[index]
            prefix = os.path.join(directory, c + "_" + pre + "_")
            newname = findFilename(prefix, cap.defext)
            cv.SaveImage(newname, image)
    elif t is cv.iplimage:
        cv.SaveImage(os.path.join(directory, pre + cap.defext), result)
    else: raise TypeError("Incorrect result type: %s" % (str(t)))

def showResult(result, stage, wait, autosize):
    """Shows the result of either preprocessing or segmentation using the OpenCV's HighGUI module.
    The method of showing is determined by the type of the result - it can be either a list or an
    iplimage. The parameters let you control the title of the window(s) the result will be shown in,
    whether cv.WaitKey(0) should be called or not and whether the window should be autosized."""
    title = cap.getTitle(stage)
    t = type(result)
    if t is types.ListType or t is types.TupleType:
        for index, image in enumerate(result):
            cv.NamedWindow(title + str(index), autosize)
            cv.ShowImage(title + str(index), image)
    elif t is cv.iplimage:
        cv.NamedWindow(title, autosize)
        cv.ShowImage(title, result)
    else: raise TypeError("Incorrect result type: %s" % (str(t)))
    if wait: cv.WaitKey(0)

def levenshtein_distance(first, second):
    """Find the Levenshtein distance between two strings."""
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
       distance_matrix[i][0] = i
    for j in range(second_length):
       distance_matrix[0][j]=j
    for i in xrange(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + 1
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]

def mainLoop(options):
    """The Most Important Function Which Does Everything."""
    rep = cReport()
    for index, name in enumerate(options.names):
        pre = os.path.splitext(name)[0]
        addr = os.path.join(options.directory, name)
        if not options.single:
            print "%d/%d:" % (index + 1, options.total),
        print "%s ->" % (name),
        # Loading
        try:
            raw_image = cv.LoadImage(addr, options.mode)
        except KeyboardInterrupt:
            print "Interrupted by user."
            sys.exit(0)
        except:
            print "FAILED TO LOAD"
            rep.loading.append(name)
            if options.single: raise
            else: continue
        if options.show:
            cv.NamedWindow("Raw", options.autosize)
            cv.ShowImage("Raw", raw_image)
        if options.preprocess:
            # Preprocessing
            thisIsLastStage = (not options.segment) and (not options.recognise)
            try:
                preprocessed = preprocess(cv.CloneImage(raw_image), addr, options.extras)
            except KeyboardInterrupt:
                print "Interrupted by user."
                sys.exit(0)
            except:
                print "FAILED TO PREPROCESS"
                rep.preprocessing.append(name)
                if options.single:
                    cv.WaitKey(0)
                    raise
                else: continue
            if options.show:
                showResult(preprocessed, cap.CAP_STAGE_PREPROCESS, thisIsLastStage, options.autosize)
            if options.savePreprocess:
                # Saving preprocessed
                try:
                    saveResult(preprocessed, cap.preprocess_dir, pre)
                except KeyboardInterrupt:
                    print "Interrupted by user."
                    sys.exit(0)
                except:
                    print "FAILED TO SAVE PREPROCESSED"
                    rep.saving.append(name)
                    if options.single: raise
                    else: continue
            if thisIsLastStage:
                print "ok"
                #if single and options.quiet and extras == "show": cv.WaitKey(0)
        else:
            preprocessed = raw_image
        if options.segment:
            # Segmenting
            thisIsLastStage = not options.recognise
            try:
                segmented = segment(preprocessed, addr, options.extras)
            except KeyboardInterrupt:
                print "Interrupted by user."
                sys.exit(0)
            except:
                print "FAILED TO SEGMENT"
                rep.segmentation.append(name)
                if options.single:
                    cv.WaitKey(0)
                    raise
                else: continue
            if options.show:
                showResult(segmented, cap.CAP_STAGE_SEGMENT, thisIsLastStage, options.autosize)
            #if extras == "show" and thisIsLastStage: cv.WaitKey(0)
            if options.saveSegment:
                # Saving segmented
                try:
                    saveResult(segmented, cap.segment_dir, pre)
                except KeyboardInterrupt:
                    print "Interrupted by user."
                    sys.exit(0)
                except:
                    print "FAILED TO SAVE SEGMENTED"
                    rep.saving.append(name)
                    if options.single: raise
                    else: continue
            if thisIsLastStage: print "ok"
        else:
            segmented = [preprocessed]
        if options.recognise:
            # Recognising
            try:
                recognised = recognise(segmented, addr, options.extras)
            except KeyboardInterrupt:
                print "Interrupted by user."
                sys.exit(0)
            except:
                print "FAILED TO RECOGNISE"
                rep.recognition.append(name)
                if options.single:
                    cv.WaitKey(0)
                    raise
                else: continue
            if recognised == pre:
                rep.successes += 1
            else:
                dist = levenshtein_distance(pre, recognised)
                rep.distances.append(dist)
                rep.mismatches += 1
            print recognised,
            if options.saveRecognise:
                # Saving recognised
                try:
                    newname = recognised + "_" + pre
                    subdir = cap.success_dir if recognised == pre else cap.mismatch_dir
                    saveResult(raw_image, os.path.join(cap.recognise_dir, subdir), pre)
                except KeyboardInterrupt:
                    print "Interrupted by user."
                    sys.exit(0)
                except:
                    print "FAILED TO SAVE RECOGNISED"
                    rep.saving.append(name)
                    if options.single: raise
                    else: continue
            print "ok" if pre == recognised else ("MISMATCH (%d)" % dist)
            if options.single:
                cv.WaitKey(0)
    return rep

def main(args):
    """Accepts a list of command-line parameters except the first one and calls
    all internal functions as needed."""
    parser = makeParser()
    options = optsort(parser.parse_args(args))
    rootDir = os.getcwd()
    engineDir = os.path.join(rootDir, options.engine)
    sys.path.append(engineDir)
    os.chdir(engineDir)
    importModules(options)
    report = mainLoop(options)
    if not options.single:
        print "Done."
        report.printErrors()
        if options.recognise:
            report.printRecStats(options.total)
    os.chdir(rootDir)
    if __name__ != "__main__" and report.successes + report.mismatches != 0:
        return report.error

if __name__ == "__main__":
    main(sys.argv[1:])