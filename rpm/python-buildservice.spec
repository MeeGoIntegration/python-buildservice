Name:       python-buildservice
Summary:    Python module to access OBS server
Version:    0.5.0
Release:    1
Group:      Development/Languages/Python
License:    GPL-2.0-or-later
BuildArch:  noarch
URL:        https://github.com/MeeGoIntegration/python-buildservice
Source0:    %{name}-%{version}.tar.gz
Requires:   python >= 2.5
Requires:   osc
BuildRequires:  python, python-sphinx, osc, python-distribute
BuildRoot:  %{_tmppath}/%{name}-%{version}-build

%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}


%description
Python module to access OBS server, works as a convinience wrapper around osc.

%prep
%setup -q -n %{name}-%{version}


%build
%{__python} setup.py build
%{__python} setup.py build_sphinx

%install
rm -rf $RPM_BUILD_ROOT
%if 0%{?suse_version}
%{__python} setup.py install --root=$RPM_BUILD_ROOT --prefix=%{_prefix}
%else
%{__python} setup.py install --root=$RPM_BUILD_ROOT -O1
%endif

%files
%defattr(-,root,root,-)
%{python_sitelib}/*

