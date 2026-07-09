#!/usr/bin/python
# Copyright (C) 2019-2020 John Leslie Ries
# This script is free software.  You may copy it with or without modifications under the terms of the
# GNU General Public License, version 3; or at your option, any later version.

# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this script.  If not, see <https://www.gnu.org/licenses/>.

import getopt
import importlib.metadata
import pandas as pd
import sys
from xpartition import xpartition

# Define constants
COMMA = ","

USAGE = """\
Usage: xpartition [OPTIONS] [INFILE [OUTFILE]]

Randomly partition a CSV data table into learning, test, and holdout
samples, or into cross-validation folds, in exact proportions, optionally
balanced on one or more fields.  Reads from INFILE (default: standard
input) and writes the same table, plus one or more partition indicator
fields, to OUTFILE (default: standard output).

Options:
  --nlearn=N        Learning-sample records per assignment cycle (default: 1)
  --ntest=N         Test-sample records per assignment cycle (default: 1)
  --nholdout=N      Holdout-sample records per assignment cycle (default: 0)
  --cv=K            Assign records to K cross-validation folds instead of
                    learning/test/holdout samples (default: 0 = off)
  --by=FIELDS       Comma-separated list of fields to balance the
                    partitions on
  --indicators=NAMES
                    Comma-separated names of the indicator field(s) to add
                    (default: SAMPLE, or CVFOLD when --cv is used)
  --rseed=N         Random seed (default: 37)
  --himem           Read the input without pandas low-memory mode
  --help            Show this help message and exit
  --version         Show the version number and exit\
"""


def main():
    # Initialize options
    cv = 0
    indstr = ""
    nlearn = 1
    ntest = 1
    nholdout = 0
    rseed = 37
    by = []
    himem = False
    infile = sys.stdin
    outfile = sys.stdout

    # Define options and arguments
    try:
        (opts, argv) = getopt.gnu_getopt(sys.argv[1:], "",
                                         longopts=["cv=", "indicators=", "rseed=", "nlearn=",
                                                   "ntest=", "nholdout=", "by=", "himem", "help",
                                                   "version"])
    except getopt.GetoptError as err:
        print("xpartition: %s" % err, file=sys.stderr)
        print("Try 'xpartition --help' for more information.", file=sys.stderr)
        sys.exit(2)
    for optpair in opts:
        if optpair[0] == "--help":
            print(USAGE)
            sys.exit(0)
        elif optpair[0] == "--version":
            print("xpartition %s" % importlib.metadata.version("xpartition"))
            sys.exit(0)
        elif optpair[0] == "--by":
            by = optpair[1].split(sep=COMMA)
        elif optpair[0] == "--cv":
            cv = int(optpair[1])
        elif optpair[0] == "--himem":
            himem = True
        elif optpair[0] == "--rseed":
            rseed = int(optpair[1])
        elif optpair[0] == "--indicators":
            indstr = optpair[1]
        elif optpair[0] == "--nlearn":
            nlearn = float(optpair[1])
        elif optpair[0] == "--ntest":
            ntest = float(optpair[1])
        elif optpair[0] == "--nholdout":
            nholdout = float(optpair[1])

    argc = len(argv)
    if argc > 0:
        infile = argv[0]
    if argc > 1:
        outfile = argv[1]

    lowmem = not himem

    # Prepare indicators list
    if indstr == "":
        indicators = None  # Let xpartition function use its defaults
    else:
        indicators = indstr.split(sep=COMMA)

    # Read input data
    df = pd.read_csv(infile, low_memory=lowmem)

    # Call xpartition function
    df = xpartition(df, by=by, rseed=rseed, indicators=indicators,
                    nlearn=nlearn, ntest=ntest, nholdout=nholdout, cv=cv)

    # Write output data
    df.to_csv(outfile, index=False)


if __name__ == "__main__":
    main()
