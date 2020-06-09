Name:       python3-buildservice
Summary:    Python module to access OBS server
Version:    0.6.0
Release:    1
Group:      Development/Languages/Python
License:    GPL-2.0-or-later
URL:        https://github.com/MeeGoIntegration/python-buildservice
Source0:    %{name}-%{version}.tar.gz

BuildRequires: python3-rpm-macros
BuildRequires: python3-setuptools
BuildRequires: fdupes
BuildArch:  noarch

Requires: osc3

%description
Python module to access OBS server, works as a convinience wrapper around osc.

%prep
%setup -q
echo "%{version}" > VERSION

%build
%python3_build

%install
%python3_install
%fdupes %{buildroot}%{$python_sitelib}

%files
%defattr(-,root,root,-)
%{python_sitelib}/*
