# $Id: sbcl.spec,v 1.8 2003/11/12 16:47:44 rexdieter Exp $

## Default to using a local bootstrap, 
## define one of the following to override 
## (non sbcl bootstraps untested)
#define sbcl_bootstrap sbcl
#define sbcl_bootstrap cmucl
#define sbcl_bootstrap clisp

%if "%{?fedora}" >= "3"
BuildRequires:setarch
Requires:setarch
%define setarch setarch %{_target_cpu}
%endif

#  Could test for setarch >= 1.7 instead
%if "%{?fedora}" >= "4"
%define setarch setarch %{_target_cpu} -R
%endif

Name: 	 sbcl
Summary: Steel Bank Common Lisp
Version: 0.9.4
Release: 10%{?dist}

License: BSD/MIT
Group: 	 Development/Languages
URL:	 http://sbcl.sourceforge.net/
Source0:  http://dl.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-source.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
ExclusiveArch: %{ix86}

Source1: sbcl.sh

%if "%{?sbcl_bootstrap}" == "%{nil}"
# local Bootstrap binaries
Source10: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-x86-linux-binary.tar.bz2
%ifarch %{ix86}
%define sbcl_bootstrap_src -a 10 
%endif
Source11: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-x86-64-linux-binary.tar.bz2
%ifarch x86_64
%define sbcl_bootstrap_src -a 11 
%endif
# Latest powerpc-linux bootstrap (untested)
Source12: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-0.8.15-powerpc-linux-binary.tar.bz2
%ifarch ppc 
%define sbcl_bootstrap_src -a 12
%endif
%endif

Patch1: sbcl-0.8.18-default-sbcl-home.patch
# See http://sourceforge.net/mailarchive/message.php?msg_id=12787069
Patch2: sbcl-0.9.4-ADDR_NO_RANDOMIZE.patch
Patch3: sbcl-0.9.4-optflags.patch
Patch4: sbcl-0.9.4-LIB_DIR.patch

%{?sbcl_bootstrap:BuildRequires: %{?sbcl_bootstrap}}

Requires(post): /sbin/install-info
Requires(preun): /sbin/install-info
# doc generation
BuildRequires: ghostscript
BuildRequires: texinfo

%description
Steel Bank Common Lisp (SBCL) is a Open Source development environment
for Common Lisp. It includes an integrated native compiler,
interpreter, and debugger.


%prep
%setup %{?sbcl_bootstrap_src} 

#sed -i -e "s|/usr/local/lib/sbcl/|%{_libdir}/sbcl/|" src/runtime/runtime.c
#or patch to use SBCL_HOME env var
%patch1 -p0 -b .default-sbcl-home
%patch2 -p1 -b .ADDR_NO_RANDOMIZE
%patch3 -p1 -b .optflags
%patch4 -p1 -b .LIB_DIR

# http://article.gmane.org/gmane.lisp.steel-bank.general/340
# enable threads (was only for >= 2.6, but code has checks to disable for <= 2.4)
## FIXME(?): per section 2.2 of INSTALL, should create/use customize-target-features.lisp
## to customize features -- Rex
#define kernel_ver %(uname -r | cut -d- -f1 | cut -d. -f-2 )
#if "%{?kernel_ver}" >= "2.6"
%ifarch %{ix86} x86_64
sed -i -e "s|; :sb-thread|:sb-thread|" base-target-features.lisp-expr
%endif
#endif

%if "%{?sbcl_bootstrap}" == "%{nil}"
mkdir sbcl-bootstrap
pushd sbcl-*-linux
chmod +x install.sh
INSTALL_ROOT=`pwd`/../sbcl-bootstrap ./install.sh
popd
%endif

# CVS crud 
find . -name CVS -type d | xargs rm -rf
find . -name '.cvsignore' | xargs rm -f
# fix permissions (some have eXecute bit set)
find . -name '*.c' | xargs chmod 644


%build
export DEFAULT_SBCL_HOME=%{_libdir}/sbcl

%if "%{?sbcl_bootstrap}" == "%{nil}"
export SBCL_HOME=`pwd`/sbcl-bootstrap/lib/sbcl
export PATH=`pwd`/sbcl-bootstrap/bin:${PATH}
%endif

%{?setarch} ./make.sh %{?bootstrap}

# docs
make -C doc/manual html info


%check || :
#if "%{?_with_check:1}" == "1"
pushd tests 
%{?setarch} sh ./run-tests.sh 
popd
#endif


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT{%{_bindir},%{_libdir},%{_mandir}}
unset SBCL_HOME ||:
export INSTALL_ROOT=$RPM_BUILD_ROOT%{_prefix}
export LIB_DIR=$RPM_BUILD_ROOT%{_libdir}
%{?setarch} sh ./install.sh

# app-wrapper for using setarch
%if 0
%if "%{?setarch}" != "%{nil}"
mv $RPM_BUILD_ROOT%{_bindir}/sbcl $RPM_BUILD_ROOT%{_libdir}/sbcl/sbcl
install -p -m755 %{SOURCE1} $RPM_BUILD_ROOT%{_bindir}/sbcl
sed -i -e "s|^SBCL_SETARCH=.*|SBCL_SETARCH=\"%{setarch}\"|" $RPM_BUILD_ROOT%{_bindir}/sbcl
%endif
%endif

## Unpackaged files
rm -rf $RPM_BUILD_ROOT%{_docdir}/sbcl
rm -f  $RPM_BUILD_ROOT%{_infodir}/dir
# from make check
find $RPM_BUILD_ROOT -name 'test-passed' | xargs rm -f


%post
/sbin/install-info %{_infodir}/sbcl.info %{_infodir}/dir ||:
/sbin/install-info %{_infodir}/asdf.info %{_infodir}/dir ||:


%postun
if [ $1 -eq 0 ]; then
  /sbin/install-info --delete %{_infodir}/sbcl.info %{_infodir}/dir ||:
  /sbin/install-info --delete %{_infodir}/asdf.info %{_infodir}/dir ||:
fi


%files
%defattr(-,root,root)
%doc BUGS COPYING README CREDITS NEWS TLA TODO
%doc SUPPORT STYLE PRINCIPLES
%doc doc/manual/sbcl
%doc doc/manual/asdf
%{_bindir}/*
%{_libdir}/sbcl/
%{_mandir}/man?/*
%{_infodir}/*


%clean
rm -rf $RPM_BUILD_ROOT


%changelog
* Mon Sep 13 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-10
- use/define LIB_DIR instead of hard-coded INSTALL_ROOT/lib
- ExclusiveArch: %{ix86} (for now)

* Mon Sep 12 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-7
- %{x86_64} -> x86_64

* Tue Aug 30 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-4
- safer NO_ADDR_RANDOMIZE patch
- use %%{?setarch} in %%check too

* Tue Aug 30 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-3
- patch to avoid need to use setarch/app-wrapper
- fix app-wrapper (quote SBCL_SETARCH)
- include ppc bootstrap (oldish 0.8.15, untested)

* Mon Aug 29 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-2
- rm -f /usr/share/info/dir
- fix perms on packaged .c files
- include all bootstrap binaries
- Requires(post,preun): /sbin/install-info
- sbcl.sh app-wrapper (when using setarch)

* Sat Aug 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-1
- 0.9.4

* Fri Aug 26 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.3-2
- fc3: setarch %%{target_cpu}
- fc4: setarch %%{target_cpu} -R

* Thu Aug 25 2005 Rex Dieter <rexdieter[AT]users.sf.net>
- run tests
- allow for sbcl_local, sbcl, clisp bootstrap

* Wed Aug 17 2005 Gerard Milmeister <gemi@bluewin.ch> - 0.9.3-1
- New Version 0.9.3

* Wed Jun 29 2005 Gerard Milmeister <gemi@bluewin.ch> - 0.9.2-1
- New Version 0.9.2

* Thu Jun 16 2005 Gerard Milmeister <gemi@bluewin.ch> - 0.9.1-1
- New Version 0.9.1

* Thu Apr 28 2005 Gerard Milmeister <gemi@bluewin.ch> - 0.9.0-1
- New Version 0.9.0

