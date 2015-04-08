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

preprocess_dir = "preprocessed"
segment_dir = "segmented"
recognise_dir = "recognised"
success_dir = "success"
mismatch_dir = "mismatch"
extras_dir = "extras"

defext = ".png"

CAP_STAGE_PRE = 0
CAP_STAGE_PREPROCESS = 0
CAP_STAGE_SEG = 1
CAP_STAGE_SEGMENT = 1
CAP_STAGE_REC = 2
CAP_STAGE_RECOGNISE = 2

CAP_EXTRAS_OFF = 0
CAP_EXTRAS_SHOW = 1
CAP_EXTRAS_SAVE = 2