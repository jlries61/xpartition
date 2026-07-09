# Copyright (C) 2026 John Leslie Ries
# Tests for the xpartition package. Distributed under the terms of the
# GNU General Public License, version 3 or later; see LICENSE.

import os
import subprocess
import sys

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
    assert result.stdout.startswith("Usage: xpartition")


def test_cli_version():
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.startswith("xpartition ")


def test_cli_rejects_unknown_option():
    result = run_cli("--bogus")
    assert result.returncode == 2
    assert "--help" in result.stderr
