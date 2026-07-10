# Copyright (C) 2026 John Leslie Ries
# Tests for the xpartition package. Distributed under the terms of the
# GNU General Public License, version 3 or later; see LICENSE.

import io
import os
import subprocess
import sys
import warnings

import pandas as pd
import pytest

from xpartition import xpartition

# Run the CLI subprocess against the src/ working tree (same code the
# in-process tests import via pytest's pythonpath), not whatever copy of
# the package happens to be installed.
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")


@pytest.fixture
def df():
    """A small deterministic frame with a categorical field to balance on."""
    n = 100
    return pd.DataFrame({
        "X": range(n),
        "GROUP": ["A", "B"] * (n // 2),
    })


def test_default_split_is_exactly_even(df):
    out = xpartition(df)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 50
    assert counts["Test"] == 50
    assert "Holdout" not in counts


def test_proportional_split(df):
    out = xpartition(df, nlearn=4, ntest=1)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 80
    assert counts["Test"] == 20


def test_holdout_sample(df):
    out = xpartition(df, nlearn=2, ntest=1, nholdout=1)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 50
    assert counts["Test"] == 25
    assert counts["Holdout"] == 25


def test_cv_folds(df):
    out = xpartition(df, cv=10)
    counts = out["CVFOLD"].value_counts()
    assert sorted(counts.index) == list(range(1, 11))
    assert (counts == 10).all()


def test_balanced_on_group(df):
    out = xpartition(df, by=["GROUP"], nlearn=1, ntest=1)
    for group in ("A", "B"):
        counts = out.loc[out["GROUP"] == group, "SAMPLE"].value_counts()
        assert counts["Learn"] == 25
        assert counts["Test"] == 25


def test_custom_indicator_name(df):
    out = xpartition(df, indicators=["PARTITION"])
    assert "PARTITION" in out.columns
    assert "SAMPLE" not in out.columns


def test_same_seed_reproduces_assignments(df):
    out1 = xpartition(df, rseed=99)
    out2 = xpartition(df, rseed=99)
    assert out1["SAMPLE"].equals(out2["SAMPLE"])


def test_different_seed_changes_assignments(df):
    out1 = xpartition(df, rseed=1)
    out2 = xpartition(df, rseed=2)
    assert not out1["SAMPLE"].equals(out2["SAMPLE"])


def test_input_frame_not_modified(df):
    before = df.copy()
    xpartition(df)
    pd.testing.assert_frame_equal(df, before)


def test_row_order_and_data_preserved(df):
    out = xpartition(df)
    pd.testing.assert_frame_equal(out.drop(columns=["SAMPLE"]), df)


def test_fractional_proportions_normalized(df):
    out = xpartition(df, nlearn=0.8, ntest=0.2)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 80
    assert counts["Test"] == 20


def test_fractional_three_way_split_normalized(df):
    out = xpartition(df, nlearn=0.5, ntest=0.25, nholdout=0.25)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 50
    assert counts["Test"] == 25
    assert counts["Holdout"] == 25


def test_fractions_equivalent_to_integer_ratio(df):
    frac = xpartition(df, nlearn=0.8, ntest=0.2)
    ints = xpartition(df, nlearn=4, ntest=1)
    assert frac["SAMPLE"].equals(ints["SAMPLE"])


def test_repeating_decimal_fraction_normalized(df):
    out = xpartition(df, nlearn=1 / 3, ntest=2 / 3)
    counts = out["SAMPLE"].value_counts()
    # cycle is Learn,Test,Test over 100 rows
    assert counts["Learn"] == 34
    assert counts["Test"] == 66


def test_all_zero_proportions_rejected(df):
    with pytest.raises(ValueError):
        xpartition(df, nlearn=0, ntest=0, nholdout=0)


def test_negative_proportion_rejected(df):
    with pytest.raises(ValueError, match="ntest"):
        xpartition(df, ntest=-1)


def test_integral_float_proportions_accepted(df):
    out = xpartition(df, nlearn=4.0, ntest=1.0)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 80
    assert counts["Test"] == 20


def test_negative_cv_rejected(df):
    with pytest.raises(ValueError, match="cv"):
        xpartition(df, cv=-2)


def test_fractional_cv_rejected(df):
    with pytest.raises(ValueError, match="cv"):
        xpartition(df, cv=2.5)


def test_empty_indicators_rejected(df):
    with pytest.raises(ValueError, match="indicators"):
        xpartition(df, indicators=[])


def test_cycle_longer_than_table_rejected(df):
    # High-precision fractions normalize to a cycle longer than the table;
    # that must be a loud error, not a silent 100%-Learn partition.
    with pytest.raises(ValueError, match="cycle"):
        xpartition(df, nlearn=0.123457, ntest=0.876543)
    with pytest.raises(ValueError, match="cycle"):
        xpartition(df, nlearn=199, ntest=301)


def test_reducible_integer_ratio_normalized(df):
    # 200:300 reduces to 2:3 — realizable on 100 rows, not an error.
    out = xpartition(df, nlearn=200, ntest=300)
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 40
    assert counts["Test"] == 60


def test_cv_exceeding_rows_rejected(df):
    with pytest.raises(ValueError, match="cv"):
        xpartition(df, cv=101)


def test_infinite_proportion_rejected(df):
    with pytest.raises(ValueError, match="nlearn"):
        xpartition(df, nlearn=float("inf"))


def test_empty_frame_still_partitions():
    empty = pd.DataFrame({"X": []})
    out = xpartition(empty)
    assert len(out) == 0
    assert "SAMPLE" in out.columns


def test_indicator_collision_warns_and_overwrites(df):
    # Re-partitioning already-partitioned output is a feature: the existing
    # indicator column is replaced, with a warning.
    first = xpartition(df, rseed=1)
    with pytest.warns(UserWarning, match="SAMPLE"):
        second = xpartition(first, rseed=2)
    assert not second["SAMPLE"].equals(first["SAMPLE"])
    assert list(second.columns) == list(first.columns)


def test_indicator_collision_with_data_column_warns(df):
    with pytest.warns(UserWarning, match="GROUP"):
        out = xpartition(df, indicators=["GROUP"])
    assert set(out["GROUP"]) == {"Learn", "Test"}


def test_no_warning_without_collision(df):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        xpartition(df)


def test_pinned_assignments_for_fixed_seed():
    """Regression pin: exact assignments for a fixed frame and seed.

    Guards against unintended changes to the RNG stream or the
    assignment algorithm. If this fails, partition output has changed
    for every user — that must be a deliberate, versioned decision.
    """
    frame = pd.DataFrame({"X": range(10)})
    out = xpartition(frame, rseed=37)
    assert list(out["SAMPLE"]) == [
        "Test", "Learn", "Test", "Test", "Learn",
        "Test", "Learn", "Learn", "Learn", "Test",
    ]


def test_global_random_state_untouched(df):
    """Calling xpartition() must not reseed the caller's global RNG."""
    import random
    random.seed(12345)
    expected = [random.random() for _ in range(3)]
    random.seed(12345)
    xpartition(df)
    observed = [random.random() for _ in range(3)]
    assert observed == expected


def run_cli(*args, stdin=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC_DIR + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "xpartition.cli", *args],
                          capture_output=True, text=True, input=stdin, env=env)


def test_cli_partitions_csv(tmp_path, df):
    infile = tmp_path / "in.csv"
    outfile = tmp_path / "out.csv"
    df.to_csv(infile, index=False)
    result = run_cli(str(infile), str(outfile))
    assert result.returncode == 0
    out = pd.read_csv(outfile)
    assert list(out["X"]) == list(df["X"])
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 50
    assert counts["Test"] == 50


def test_cli_stdin_stdout(df):
    result = run_cli("--cv=4", stdin=df.to_csv(index=False))
    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "X,GROUP,CVFOLD"


def test_cli_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert result.stdout.startswith("usage: xpartition")


def test_cli_bad_numeric_option_value():
    result = run_cli("--cv=ten")
    assert result.returncode == 2
    assert "cv" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_unreadable_input_file():
    result = run_cli("/nonexistent/input.csv")
    assert result.returncode == 1
    assert "cannot read" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.startswith("xpartition ")


def test_cli_fractional_proportions(df):
    result = run_cli("--nlearn=0.8", "--ntest=0.2", stdin=df.to_csv(index=False))
    assert result.returncode == 0
    out = pd.read_csv(io.StringIO(result.stdout))
    counts = out["SAMPLE"].value_counts()
    assert counts["Learn"] == 80
    assert counts["Test"] == 20


def test_cli_unknown_by_field(df):
    result = run_cli("--by=NOSUCH", stdin=df.to_csv(index=False))
    assert result.returncode == 2
    assert "NOSUCH" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_rejects_negative_nlearn(df):
    result = run_cli("--nlearn=-1", stdin=df.to_csv(index=False))
    assert result.returncode == 2
    assert "nlearn" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_warns_when_cv_overrides_proportions(df):
    result = run_cli("--cv=4", "--nlearn=2", stdin=df.to_csv(index=False))
    assert result.returncode == 0
    assert "ignored" in result.stderr


def test_cli_warns_on_indicator_collision(df):
    once = run_cli(stdin=df.to_csv(index=False))
    twice = run_cli(stdin=once.stdout)
    assert twice.returncode == 0
    assert "warning" in twice.stderr
    assert "SAMPLE" in twice.stderr
    assert twice.stdout.splitlines()[0] == "X,GROUP,SAMPLE"


def test_cli_rejects_unknown_option():
    result = run_cli("--bogus")
    assert result.returncode == 2
    assert "--help" in result.stderr
