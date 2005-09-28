# $Id: sbcl.spec,v 1.23 2005/09/28 01:23:45 rdieter Exp $

Name: 	 sbcl
Summary: Steel Bank Common Lisp
Version: 0.9.5
Release: 8%{?dist}

License: BSD/MIT
Group: 	 Development/Languages
URL:	 http://sbcl.sourceforge.net/
Source0: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-source.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
ExclusiveArch: %{ix86} x86_64

## x86 section
#Source10: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-0.9.4-x86-linux-binary.tar.bz2
%ifarch %{ix86}
%define sbcl_arch x86
BuildRequires: sbcl
#define sbcl_bootstrap_src -a 10 
%endif

## x86_64 section
#Source20: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-0.9.4-x86-64-linux-binary.tar.bz2
%ifarch x86_64
%define sbcl_arch x86-64
BuildRequires: sbcl
#define sbcl_bootstrap_src -a 20 
%endif

## ppc section
# Latest powerpc-linux bootstrap, busted:
# buildsys.fedoraproject.org/logs/development/1131-sbcl-0.9.4-14.fc5/ppc/build.log
#Source30: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-0.8.15-powerpc-linux-binary.tar.bz2
# another possible ppc bootstrap to try
#Source31: http://clozure.com/openmcl/ftp/openmcl-linuxppc-all-0.14.3.tar.gz
%ifarch ppc 
%define sbcl_arch ppc
%define sbcl_bootstrap_src -a 30
BuildRequires: setarch
%define setarch setarch %{_target_cpu}
%endif

Source100: my_setarch.c

Patch1: sbcl-0.8.18-default-sbcl-home.patch
Patch2: sbcl-0.9.5-personality.patch
Patch3: sbcl-0.9.5-optflags.patch
Patch4: sbcl-0.9.4-LIB_DIR.patch

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
%setup -q %{?sbcl_bootstrap_src} 

#sed -i -e "s|/usr/local/lib/sbcl/|%{_libdir}/sbcl/|" src/runtime/runtime.c
#or patch to use SBCL_HOME env var
%patch1 -p0 -b .default-sbcl-home
%patch2 -p1 -b .personality
%patch3 -p1 -b .optflags
%patch4 -p1 -b .LIB_DIR

# http://article.gmane.org/gmane.lisp.steel-bank.general/340
# enable threads (was only for >= 2.6, but code has checks to disable for <= 2.4)
## FIXME(?): per section 2.2 of INSTALL, should create/use customize-target-features.lisp
## to customize features -- Rex
#define kernel_ver %(uname -r | cut -d- -f1 | cut -d. -f-2 )
#if "%{?kernel_ver}" >= "2.6"
%ifarch %{ix86} x86_64
#sed -i -e "s|; :sb-thread|:sb-thread|" base-target-features.lisp-expr
%endif
#endif

%if "%{?sbcl_bootstrap_src}" != "%{nil}"
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

%if "%{?sbcl_bootstrap_src}" != "%{nil}"
export SBCL_HOME=`pwd`/sbcl-bootstrap/lib/sbcl
export PATH=`pwd`/sbcl-bootstrap/bin:${PATH}

%{__cc} -o my_setarch %{optflags} %{SOURCE100} 
%define my_setarch ./my_setarch
%endif

%{?sbcl_arch:export SBCL_ARCH=%{sbcl_arch}}
%{?setarch} %{?my_setarch} ./make.sh %{?bootstrap}

# docs
make -C doc/manual html info


%check || :
pushd tests 
%{?setarch} sh ./run-tests.sh
popd


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT{%{_bindir},%{_libdir},%{_mandir}}
unset SBCL_HOME ||:
export INSTALL_ROOT=$RPM_BUILD_ROOT%{_prefix}
export LIB_DIR=$RPM_BUILD_ROOT%{_libdir}
sh ./install.sh

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
* Tue Sep 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.5-8
- respin (fc3/fc4)

* Tue Sep 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.5-7
- drop ppc
- cleaner optflags patch

* Tue Sep 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.5-5
- set/use SBCL_ARCH/setarch (esp on ppc)
- allow arch-specific build-options

* Tue Sep 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.5-2
- 0.9.5
- use native sbcl bootstraps, when available (ie, %%{ix86},x86_64)
- try ppc again

* Thu Sep 22 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-19
- drop use of setarch, use my_setarch.c

* Mon Sep 19 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-17
- rework personality/reexec patch (execve -> execvp)

* Sat Sep 16 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-15
- disable ppc (probably related to #166347)

* Fri Sep 16 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-14
- re-enable ppc
- drop Req: setarch
- drop extraneous app-wrapper bits

* Tue Sep 13 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-13
- don't enable sb-thread

* Tue Sep 13 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-12
- omit ppc (for now, broken buildsystem)

* Tue Sep 13 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-11
- fix botched NO_ADDR_RANDOMIZE patch
- fix botched LIB_DIR patch

* Mon Sep 12 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.4-10
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

