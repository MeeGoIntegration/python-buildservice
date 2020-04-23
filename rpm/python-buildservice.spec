Name:       python-buildservice
Summary:    Python module to access OBS server
Version:    0.5.0
Release:    1
Group:      Development/Languages/Python
License:    GPL-2.0-or-later
URL:        https://github.com/MeeGoIntegration/python-buildservice
Source0:    %{name}-%{version}.tar.gz

BuildRequires: python-rpm-macros
BuildRequires: python-setuptools
BuildRequires: fdupes
BuildArch:  noarch

# Force 0.165 as this is python2.7 version
Requires:   osc == 0.165.4

%description
Python module to access OBS server, works as a convinience wrapper around osc.

%prep
%setup -q
echo "%{version}" > VERSION

%build
%python2_build

%install
%python2_install
%fdupes %{buildroot}%{$python_sitelib}

%files
%defattr(-,root,root,-)
%{python_sitelib}/*
