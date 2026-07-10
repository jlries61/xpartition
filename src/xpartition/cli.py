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

import argparse
import importlib.metadata
import sys

import pandas as pd

from xpartition import xpartition

DESCRIPTION = """\
Randomly partition a CSV data table into learning, test, and holdout
samples, or into cross-validation folds, in exact proportions, optionally
balanced on one or more fields.  Reads from INFILE (default: standard
input) and writes the same table, plus one or more partition indicator
fields, to OUTFILE (default: standard output)."""

EPILOG = """\
Sample sizes may be fractional; they are normalized to the smallest
whole-number assignment cycle, so --nlearn=0.8 --ntest=0.2 is the same
as --nlearn=4 --ntest=1."""


class _Parser(argparse.ArgumentParser):
    """ArgumentParser with the GNU-style two-line error message."""

    def error(self, message):
        print("xpartition: %s" % message, file=sys.stderr)
        print("Try 'xpartition --help' for more information.", file=sys.stderr)
        sys.exit(2)


def _nonneg_number(text):
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a number, got %r" % text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative, got %r" % text)
    return value


def _nonneg_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a non-negative integer, got %r" % text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative, got %r" % text)
    return value


def _comma_list(text):
    return [token for token in text.split(",") if token]


def main():
    parser = _Parser(
        prog="xpartition",
        usage="xpartition [OPTIONS] [INFILE [OUTFILE]]",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--nlearn", type=_nonneg_number, default=None, metavar="N",
                        help="relative size of the learning sample (default: 1)")
    parser.add_argument("--ntest", type=_nonneg_number, default=None, metavar="N",
                        help="relative size of the test sample (default: 1)")
    parser.add_argument("--nholdout", type=_nonneg_number, default=None, metavar="N",
                        help="relative size of the holdout sample (default: 0)")
    parser.add_argument("--cv", type=_nonneg_int, default=0, metavar="K",
                        help="assign records to K cross-validation folds instead of "
                             "learning/test/holdout samples (default: 0 = off)")
    parser.add_argument("--by", type=_comma_list, default=[], metavar="FIELDS",
                        help="comma-separated list of fields to balance the partitions on")
    parser.add_argument("--indicators", type=_comma_list, default=None, metavar="NAMES",
                        help="comma-separated names of the indicator field(s) to add "
                             "(default: SAMPLE, or CVFOLD when --cv is used)")
    parser.add_argument("--rseed", type=int, default=37, metavar="N",
                        help="random seed (default: 37)")
    parser.add_argument("--himem", action="store_true",
                        help="read the input without pandas low-memory mode")
    parser.add_argument("--version", action="version",
                        version="xpartition %s" % importlib.metadata.version("xpartition"))
    parser.add_argument("infile", nargs="?", default=None, metavar="INFILE",
                        help="input CSV file (default: standard input)")
    parser.add_argument("outfile", nargs="?", default=None, metavar="OUTFILE",
                        help="output CSV file (default: standard output)")
    args = parser.parse_args()

    if args.cv > 0 and any(size is not None
                           for size in (args.nlearn, args.ntest, args.nholdout)):
        print("xpartition: --cv given; --nlearn, --ntest, and --nholdout are ignored",
              file=sys.stderr)
    nlearn = 1 if args.nlearn is None else args.nlearn
    ntest = 1 if args.ntest is None else args.ntest
    nholdout = 0 if args.nholdout is None else args.nholdout

    infile = args.infile if args.infile is not None else sys.stdin
    outfile = args.outfile if args.outfile is not None else sys.stdout

    # Read input data
    try:
        df = pd.read_csv(infile, low_memory=not args.himem)
    except (OSError, ValueError) as err:
        name = args.infile if args.infile is not None else "standard input"
        print("xpartition: cannot read %s: %s" % (name, err), file=sys.stderr)
        sys.exit(1)

    missing = [field for field in args.by if field not in df.columns]
    if missing:
        print("xpartition: --by field(s) not in the input: %s" % ", ".join(missing),
              file=sys.stderr)
        print("Try 'xpartition --help' for more information.", file=sys.stderr)
        sys.exit(2)

    # Call xpartition function
    try:
        df = xpartition(df, by=args.by, rseed=args.rseed, indicators=args.indicators,
                        nlearn=nlearn, ntest=ntest, nholdout=nholdout, cv=args.cv)
    except ValueError as err:
        print("xpartition: %s" % err, file=sys.stderr)
        print("Try 'xpartition --help' for more information.", file=sys.stderr)
        sys.exit(2)

    # Write output data
    df.to_csv(outfile, index=False)


if __name__ == "__main__":
    main()
