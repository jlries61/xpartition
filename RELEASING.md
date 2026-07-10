# Releasing xpartition

Checklist for cutting a new release.

## 1. Bump the version (two places)

The version number is maintained by hand in **two** files and they must agree:

- `pyproject.toml` — the `version =` line under `[project]`
- `xpartition.spec` — the `Version:` line, **plus** a new `%changelog` entry
  at the top (format: `* Day Mon DD YYYY Name <email> - X.Y.Z-1`; the
  weekday must match the date or rpmbuild will complain)

## 2. Test

```
pip install .[test]
pytest
```

`pytest` tests the `src/` working tree directly (configured via
`pythonpath` in `pyproject.toml`), so edits are picked up without
reinstalling. For day-to-day development an editable install is
recommended: `pip install -e .[test]`.

CI (GitHub Actions) runs the same suite on push, along with a
distribution build check.

## 3. Build

```
./build-rpm.sh
```

This produces the sdist, SRPM, and noarch RPM under `dist/`. Install the
RPM locally with:

```
sudo dnf install dist/noarch/xpartition-*.noarch.rpm
```

## 4. Tag

```
git tag -a vX.Y.Z -m "xpartition X.Y.Z"
git push origin vX.Y.Z
```

Pushing the tag triggers the Release workflow (GitHub Actions), which
builds the sdist and wheel, verifies the tag matches the packaged
version, and attaches both artifacts to a GitHub Release. The locally
built RPM is not uploaded automatically; add it to the release by hand
if desired:

```
gh release upload vX.Y.Z dist/noarch/xpartition-*.noarch.rpm
```

## 5. PyPI (not yet enabled)

The name `xpartition` is taken on PyPI, so the project must be renamed
before it can be published there. Once that happens:

1. Change `name =` in `pyproject.toml` (and the spec's `Name:` line if
   the RPM should follow the new name).
2. `python3 -m build`
3. `twine upload dist/*.tar.gz dist/*.whl`
