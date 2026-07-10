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

import math
import random
from fractions import Fraction

import pandas as pd


def _count(name, value):
    """Validate a cycle count: must be a non-negative integer (integral floats accepted)."""
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise ValueError("%s must be a non-negative integer, got %r" % (name, value))
    if ivalue != value or ivalue < 0:
        raise ValueError("%s must be a non-negative integer, got %r" % (name, value))
    return ivalue


def _normalize_counts(nlearn, ntest, nholdout):
    """Reduce possibly-fractional sample sizes to the smallest whole-number cycle.

    Fractions and integers alike are treated as relative proportions, so
    nlearn=0.8, ntest=0.2 becomes the cycle 4:1 and nlearn=2, ntest=1,
    nholdout=1 stays 2:1:1.  Float imprecision is absorbed by snapping to
    the nearest rational with denominator <= 10**6 (so 1/3 really means
    one third).
    """
    fracs = []
    for name, value in (("nlearn", nlearn), ("ntest", ntest), ("nholdout", nholdout)):
        try:
            frac = Fraction(value).limit_denominator(1000000)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("%s must be a finite non-negative number, got %r" % (name, value))
        if frac < 0:
            raise ValueError("%s must be a non-negative number, got %r" % (name, value))
        fracs.append(frac)
    if sum(fracs) == 0:
        raise ValueError("at least one of nlearn, ntest, nholdout must be positive")
    denom_lcm = math.lcm(*(frac.denominator for frac in fracs))
    counts = [int(frac * denom_lcm) for frac in fracs]
    divisor = math.gcd(*counts)
    return [count // divisor for count in counts]


def xpartition(df, by=None, rseed=37, indicators=None, nlearn=1, ntest=1, nholdout=0, cv=0):
    """
    Partition a dataframe into learning, test, and holdout samples or cross-validation folds.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input data frame to partition
    by : list of str, optional
        List of column names to group by before partitioning. Default is None (empty list).
    rseed : int, optional
        Random seed for reproducibility. Default is 37.
    indicators : list of str, optional
        List of column names to create for partition indicators. 
        Default is ["CVFOLD"] if cv > 0, otherwise ["SAMPLE"].
    nlearn : int or float, optional
        Relative size of the learning sample. Fractions are allowed and are
        normalized with the other sizes to the smallest whole-number
        assignment cycle (nlearn=0.8, ntest=0.2 is the same as nlearn=4,
        ntest=1). Default is 1.
    ntest : int or float, optional
        Relative size of the test sample. Default is 1.
    nholdout : int or float, optional
        Relative size of the holdout sample. Default is 0.
    cv : int, optional
        Number of cross-validation folds. If > 0, enables CV mode and
        nlearn/ntest/nholdout are ignored. Default is 0.

    Returns
    -------
    pandas.DataFrame
        Modified dataframe with partition indicator column(s) added

    Raises
    ------
    ValueError
        If any size is negative or non-finite (or cv is negative or
        fractional), if all of nlearn/ntest/nholdout are zero in sample mode,
        if indicators is an empty list, or if the normalized assignment cycle
        (or cv) is larger than the number of records — proportions that
        precise cannot be realized on a table that small.

    Notes
    -----
    Fractional sizes are snapped to the nearest rational with denominator
    at most 10**6, so sizes smaller than about 5e-7 of the total are
    treated as zero.
    """
    # Validate the input contract up front: a silently wrong partition is
    # worse than an error (milestone post-v2.0.0, finding SK-01/SK-04).
    nlearn, ntest, nholdout = _normalize_counts(nlearn, ntest, nholdout)
    cv = _count("cv", cv)
    if indicators is not None and len(indicators) == 0:
        raise ValueError("indicators must not be empty")

    # Make a copy to avoid modifying the original
    df = df.copy()

    # Handle default values
    if by is None:
        by = []

    if indicators is None:
        if cv > 0:
            indicators = ["CVFOLD"]
        else:
            indicators = ["SAMPLE"]
    
    # Determine partitioning mode
    if cv > 0:
        denom = cv
    else:
        denom = nlearn + ntest + nholdout
    
    row_labels = df.index
    nrows = len(row_labels)
    # A cycle longer than the table means the requested proportions cannot be
    # realized at all (every record would land in the cycle's first segment) —
    # loud error, not a silently degenerate partition. Empty frames are exempt:
    # zero rows partition trivially.
    if cv > 0:
        if 0 < nrows < cv:
            raise ValueError("cv (%d) exceeds the number of records (%d)" % (cv, nrows))
    elif 0 < nrows < denom:
        raise ValueError(
            "the requested sample sizes need an assignment cycle of %d records, "
            "but the table has only %d; use coarser proportions" % (denom, nrows))
    nlearntest = nlearn + ntest
    sortkeys = by.copy()
    sortkeys.append(".rsortkey")
    # Instance RNG: same Mersenne Twister stream as random.seed()/uniform(),
    # so assignments are unchanged, but the caller's global RNG state is not.
    rng = random.Random(rseed)
    
    # Generate the assignments list once
    assign = []
    num = 0
    for row in range(nrows):
        if num >= denom:
            num = 0
        if cv > 0:
            assign.append(num + 1)
        else:
            if num < nlearn:
                assign.append("Learn")
            elif num < nlearntest:
                assign.append("Test")
            else:
                assign.append("Holdout")
        num = num + 1
    
    # Create indicator columns
    for indicator in indicators:
        rsortkey = dict()
        for row in row_labels:
            rsortkey[row] = rng.uniform(0, 1)
        dfkeys = df[by].copy() if by else pd.DataFrame(index=df.index)
        dfkeys[".rsortkey"] = pd.Series(rsortkey)
        dfkeys.sort_values(by=sortkeys, inplace=True)
        
        dfkeys[indicator] = assign
        dfkeys.sort_index(inplace=True)
        df[indicator] = dfkeys[indicator]
    
    return df
