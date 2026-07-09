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

import pandas as pd
import random


def _count(name, value):
    """Validate a cycle count: must be a non-negative integer (integral floats accepted)."""
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise ValueError("%s must be a non-negative integer, got %r" % (name, value))
    if ivalue != value or ivalue < 0:
        raise ValueError("%s must be a non-negative integer, got %r" % (name, value))
    return ivalue


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
    nlearn : int, optional
        Learning-sample records per assignment cycle (non-negative integer;
        integral floats such as 4.0 are accepted). Default is 1.
    ntest : int, optional
        Test-sample records per assignment cycle. Default is 1.
    nholdout : int, optional
        Holdout-sample records per assignment cycle. Default is 0.
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
        If any count is negative or fractional, if all of nlearn/ntest/nholdout
        are zero in sample mode, or if indicators is an empty list.
    """
    # Validate the input contract up front: a silently wrong partition is
    # worse than an error (milestone post-v2.0.0, finding SK-01/SK-04).
    nlearn = _count("nlearn", nlearn)
    ntest = _count("ntest", ntest)
    nholdout = _count("nholdout", nholdout)
    cv = _count("cv", cv)
    if cv == 0 and nlearn + ntest + nholdout < 1:
        raise ValueError("at least one of nlearn, ntest, nholdout must be positive")
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
        ncv = cv
    else:
        denom = nlearn + ntest + nholdout
    
    row_labels = df.index
    nrows = len(row_labels)
    nlearntest = nlearn + ntest
    sortkeys = by.copy()
    sortkeys.append(".rsortkey")
    random.seed(rseed)
    
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
            rsortkey[row] = random.uniform(0, 1)
        dfkeys = df[by].copy() if by else pd.DataFrame(index=df.index)
        dfkeys[".rsortkey"] = pd.Series(rsortkey)
        dfkeys.sort_values(by=sortkeys, inplace=True)
        
        dfkeys[indicator] = assign
        dfkeys.sort_index(inplace=True)
        df[indicator] = dfkeys[indicator]
    
    return df
