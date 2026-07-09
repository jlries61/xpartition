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
import pandas as pd
import sys
from xpartition import xpartition

# Define constants
COMMA = ","


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
    (opts, argv) = getopt.gnu_getopt(sys.argv[1:], "",
                                     longopts=["cv=", "indicators=", "rseed=", "nlearn=", "ntest=",
                                               "nholdout=", "by=", "himem"])
    for optpair in opts:
        if optpair[0] == "--by":
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
