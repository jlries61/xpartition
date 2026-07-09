Name:           xpartition
Version:        2.0.0
Release:        1%{?dist}
Summary:        Exact data partitioner for learning, test, and holdout samples

License:        GPL-3.0-or-later
URL:            https://github.com/jlries61/xpartition
# Build the source tarball with: python3 -m build --sdist  (or use ./build-rpm.sh)
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

%py_provides python3-%{name}

%description
xpartition randomly partitions a table (CSV) into learning, test, and
holdout samples -- or cross-validation folds -- in exact proportions,
optionally balanced on one or more fields. It provides both a
command-line tool and an importable Python module.

%prep
%autosetup

%generate_buildrequires
%pyproject_buildrequires -x test

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l %{name}

%check
%pyproject_check_import
%pytest

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/xpartition

%changelog
* Thu Jul 09 2026 John L. Ries <john@theyarnbard.com> - 2.0.0-1
- Initial RPM packaging
- Version 2.0.0 marks the conversion from a stand-alone script to an
  installable Python package; the original script is retroactively 1.0.0
