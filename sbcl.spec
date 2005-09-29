# $Id: sbcl.spec,v 1.8 2003/11/12 16:47:44 rexdieter Exp $

Name: 	 sbcl
Summary: Steel Bank Common Lisp
Version: 0.9.5
Release: 15%{?dist}

License: BSD/MIT
Group: 	 Development/Languages
URL:	 http://sbcl.sourceforge.net/
Source0: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-source.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
ExclusiveArch: %{ix86} x86_64

# Pre-generated html docs (not used)
#Source1: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-html.tar.bz2
Source2: customize-target-features.lisp 

## x86 section
#Source10: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-0.9.5-x86-linux-binary.tar.bz2
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
Source30: http://dl.sourceforge.net/sourceforge/sbcl/sbcl-0.8.15-powerpc-linux-binary.tar.bz2
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
Patch5: sbcl-0.9.5-make-config-fix.patch
Patch6: sbcl-0.9.5-verbose-build.patch
Patch7: sbcl-0.9.5-stdlib_h.patch

Requires(post): /sbin/install-info
Requires(preun): /sbin/install-info
# doc generation
BuildRequires: ghostscript
BuildRequires: texinfo
BuildRequires: time

%description
Steel Bank Common Lisp (SBCL) is a Open Source development environment
for Common Lisp. It includes an integrated native compiler,
interpreter, and debugger.


%prep
%setup -q %{?sbcl_bootstrap_src} 

# Handle pre-generated docs
if [ -d %{name}-%{version}/doc/manual ]; then
  mv %{name}-%{version}/doc/manual/* doc/manual/
fi

#sed -i -e "s|/usr/local/lib/sbcl/|%{_libdir}/sbcl/|" src/runtime/runtime.c
#or patch to use SBCL_HOME env var
%patch1 -p0 -b .default-sbcl-home
%patch2 -p1 -b .personality
%patch3 -p1 -b .optflags
%patch4 -p1 -b .LIB_DIR
%patch5 -p1 -b .make-config-fix
%patch6 -p1 -b .verbose-build
%patch7 -p1 -b .stdlib_h

# Enable sb-thread
%ifarch %{ix86} x86_64
#sed -i -e "s|; :sb-thread|:sb-thread|" base-target-features.lisp-expr
cp %{SOURCE2} ./customize-target-features.lisp
%endif

# "install" local bootstrap
%if "%{?sbcl_bootstrap_src}" != "%{nil}"
mkdir sbcl-bootstrap
pushd sbcl-*-linux
chmod +x install.sh
INSTALL_ROOT=`pwd`/../sbcl-bootstrap ./install.sh
popd
%endif

# fix permissions (some have eXecute bit set)
find . -name '*.c' | xargs chmod 644


%build

# setup local bootstrap
%if "%{?sbcl_bootstrap_src}" != "%{nil}"
export SBCL_HOME=`pwd`/sbcl-bootstrap/lib/sbcl
export PATH=`pwd`/sbcl-bootstrap/bin:${PATH}
%endif

# my_setarch, to set personality, (about) the same as setarch -R, 
# but usable on fc3 too
%{__cc} -o my_setarch %{optflags} %{SOURCE100} 
%define my_setarch ./my_setarch

# trick contrib/ modules to use optflags too 
export EXTRA_CFLAGS="$RPM_OPT_FLAGS"
export DEFAULT_SBCL_HOME=%{_libdir}/sbcl
%{?sbcl_arch:export SBCL_ARCH=%{sbcl_arch}}
%{?setarch} %{?my_setarch} sh -x ./make.sh %{?bootstrap}

# docs
make -C doc/manual html info


%check || :
pushd tests 
# Only x86 builds are expected to pass all
%ifarch %{ix86} x86_64
%{?setarch} sh ./run-tests.sh
%else
%{?setarch} sh ./run-tests.sh ||:
%endif
popd


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT{%{_bindir},%{_libdir},%{_mandir}}

unset SBCL_HOME 
export INSTALL_ROOT=$RPM_BUILD_ROOT%{_prefix} 
export LIB_DIR=$RPM_BUILD_ROOT%{_libdir} 
sh -x ./install.sh 

## Unpackaged files
rm -rf $RPM_BUILD_ROOT%{_docdir}/sbcl
rm -f  $RPM_BUILD_ROOT%{_infodir}/dir
# CVS crud 
find $RPM_BUILD_ROOT -name CVS -type d | xargs rm -rf
find $RPM_BUILD_ROOT -name .cvsignore | xargs rm -f
# 'test-passed' files from make check (leave these in, for now -- Rex)
# find $RPM_BUILD_ROOT -name 'test-passed' | xargs rm -f


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
* Thu Sep 29 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.5-15
- enable sb-thread
- set EXTRA_CFLAGS to so optflags are used for building contrib/ too
- hope that a rebuild will include missing sb-posix (bz #169506)

* Wed Sep 28 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.5-14
- more ppc work

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

