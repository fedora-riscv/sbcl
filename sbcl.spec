
%if 0%{?fedora} > 9
%define common_lisp_controller 1
%endif

# define to enable verbose build for debugging
#define sbcl_verbose 1 
%define sbcl_shell /bin/bash

# threading support
## Enable sb-thread
%ifarch %{ix86} x86_64
%{?!_without_threads:%global _with_threads --with-threads}
%endif

Name: 	 sbcl
Summary: Steel Bank Common Lisp
Version: 1.0.35
Release: 1%{?dist}

License: BSD
Group: 	 Development/Languages
URL:	 http://sbcl.sourceforge.net/
Source0: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-source.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
%if 0%{?fedora} > 8
# reinclude ppc when fixed: http://bugzilla.redhat.com/448734 
ExclusiveArch: %{ix86} x86_64 sparcv9
%else
ExclusiveArch: %{ix86} x86_64 ppc sparcv9
%endif

# Pre-generated html docs (not used)
#Source1: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-documentation-html.tar.bz2
Source2: customize-target-features.lisp 

## x86 section
#Source10: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-1.0.15-x86-linux-binary.tar.bz2
%ifarch %{ix86}
%define sbcl_arch x86
BuildRequires: sbcl
# or
#define sbcl_bootstrap_src -a 10 
%endif

## x86_64 section
#Source20: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-1.0.17-x86-64-linux-binary.tar.bz2
%ifarch x86_64
%define sbcl_arch x86-64
BuildRequires: sbcl
# or
#define sbcl_bootstrap_src -a 20 
%endif

## ppc section
# Thanks David!
#Source30: sbcl-1.0.1-patched_el4-powerpc-linux.tar.bz2
#Source30: sbcl-1.0.1-patched-powerpc-linux.tar.bz2
%ifarch ppc 
%define sbcl_arch ppc
BuildRequires: sbcl
# or
#define sbcl_bootstrap_src -a 30
%endif

## sparc section
#Source40: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-0.9.17-sparc-linux-binary.tar.bz2
%ifarch sparcv9
%define sbcl_arch sparc 
BuildRequires: sbcl
# or
#define sbcl_bootstrap_src -a 40 
%endif

Source100: my_setarch.c

%if 0%{?common_lisp_controller}
BuildRequires: common-lisp-controller
Requires:      common-lisp-controller
Requires(post): common-lisp-controller
Requires(preun): common-lisp-controller
Source200: sbcl.sh
Source201: sbcl.rc
Source202: sbcl-install-clc.lisp
%endif

Patch1: sbcl-1.0.25-default_sbcl_home.patch
Patch2: sbcl-0.9.5-personality.patch
Patch3: sbcl-1.0.30-optflags.patch
Patch4: sbcl-0.9.17-LIB_DIR.patch
Patch6: sbcl-0.9.5-verbose-build.patch
# Allow override of contrib test failure(s)
Patch7: sbcl-1.0.2-permissive.patch

## upstream patches

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

#sed -i -e "s|/usr/local/lib/sbcl/|%{_prefix}/lib/sbcl/|" src/runtime/runtime.c
#or patch to use SBCL_HOME env var
%patch1 -p1 -b .default_sbcl_home
%patch2 -p1 -b .personality
%patch3 -p1 -b .optflags
%patch4 -p1 -b .LIB_DIR
%{?sbcl_verbose:%patch6 -p1 -b .verbose-build}
%patch7 -p1 -b .permissive

%if 0%{?_with_threads:1}
## Enable sb-thread
#sed -i -e "s|; :sb-thread|:sb-thread|" base-target-features.lisp-expr
# or
install -m644 -p %{SOURCE2} ./customize-target-features.lisp
%endif

# "install" local bootstrap
%if "x%{?sbcl_bootstrap_src}" != "x%{nil}"
mkdir sbcl-bootstrap
pushd sbcl-*-linux
INSTALL_ROOT=`pwd`/../sbcl-bootstrap %{?sbcl_shell} ./install.sh
popd
%endif

# fix permissions (some have eXecute bit set)
find . -name '*.c' | xargs chmod 644

# set version.lisp-expr
sed -i.rpmver -e "s|\"%{version}\"|\"%{version}-%{release}\"|" version.lisp-expr


%build

# setup local bootstrap
%if "x%{?sbcl_bootstrap_src}" != "x%{nil}"
export SBCL_HOME=`pwd`/sbcl-bootstrap/lib/sbcl
export PATH=`pwd`/sbcl-bootstrap/bin:${PATH}
%endif

# my_setarch, to set personality, (about) the same as setarch -R, but usable on fc3 too
#%{__cc} -o my_setarch %{optflags} %{SOURCE100} 
#define my_setarch ./my_setarch

# WORKAROUND sb-posix STAT.2, STAT.4 test failures (fc3/fc4 only, fc5 passes?)
# http://bugzilla.redhat.com/169506
#touch contrib/sb-posix/test-passed
# WORKAROUND sb-bsd-sockets test failures
# http://bugzilla.redhat.com/214568
#touch contrib/sb-bsd-sockets/test-passed

# WORKAROUND ppc linker issue
%ifarch ppc
#export RPM_OPT_FLAGS="$RPM_OPT_FLAGS -mlongcall"; 
#echo "RPM_OPT_FLAGS: $RPM_OPT_FLAGS"
%endif

export DEFAULT_SBCL_HOME=%{_prefix}/lib/sbcl
%{?sbcl_arch:export SBCL_ARCH=%{sbcl_arch}}
%{?setarch} %{?my_setarch} %{?sbcl_shell} ./make.sh %{?bootstrap}

# docs
make -C doc/manual html info


%check
ERROR=0
# santity check, essential contrib modules get built/included? 
CONTRIBS="sb-posix sb-bsd-sockets"
for CONTRIB in $CONTRIBS ; do
  if [ ! -d %{buildroot}%{_prefix}/lib/sbcl/$CONTRIB ]; then
    echo "WARNING: ${CONTRIB} awol!"
    ERROR=1 
    echo "ulimit -a"
    ulimit -a
  fi
done
pushd tests 
# still seeing periodic thread.impure failure(s) in koji
time %{?setarch} %{?sbcl_shell} ./run-tests.sh ||:
popd
exit $ERROR


%install
rm -rf %{buildroot}

mkdir -p %{buildroot}{%{_bindir},%{_prefix}/lib,%{_mandir}}

unset SBCL_HOME 
export INSTALL_ROOT=%{buildroot}%{_prefix} 
export LIB_DIR=%{buildroot}%{_prefix}/lib
%{?sbcl_shell} ./install.sh 

%if 0%{?common_lisp_controller}
install -m744 -p -D %{SOURCE200} %{buildroot}%{_prefix}/lib/common-lisp/bin/sbcl.sh
install -m644 -p -D %{SOURCE201} %{buildroot}%{_sysconfdir}/sbcl.rc
install -m644 -p -D %{SOURCE202} %{buildroot}%{_prefix}/lib/sbcl/install-clc.lisp
# linking ok? -- Rex
cp -p %{buildroot}%{_prefix}/lib/sbcl/sbcl.core %{buildroot}%{_prefix}/lib/sbcl/sbcl-dist.core
%endif

## Unpackaged files
rm -rf %{buildroot}%{_docdir}/sbcl
rm -f  %{buildroot}%{_infodir}/dir
# CVS crud 
find %{buildroot} -name CVS -type d | xargs rm -rf
find %{buildroot} -name .cvsignore | xargs rm -f
# 'test-passed' files from %%check
find %{buildroot} -name 'test-passed' | xargs rm -vf


%post
/sbin/install-info %{_infodir}/sbcl.info %{_infodir}/dir ||:
/sbin/install-info %{_infodir}/asdf.info %{_infodir}/dir ||:
/usr/sbin/register-common-lisp-implementation sbcl > /dev/null 2>&1 ||:

%preun
if [ $1 -eq 0 ]; then
  /sbin/install-info --delete %{_infodir}/sbcl.info %{_infodir}/dir ||:
  /sbin/install-info --delete %{_infodir}/asdf.info %{_infodir}/dir ||:
  /usr/sbin/unregister-common-lisp-implementation sbcl > /dev/null 2>&1 ||:
fi


%files
%defattr(-,root,root)
%doc BUGS COPYING README CREDITS NEWS TLA TODO
%doc STYLE PRINCIPLES
%{_bindir}/*
%{_prefix}/lib/sbcl/
%{_mandir}/man?/*
%doc doc/manual/sbcl
%doc doc/manual/asdf
%{_infodir}/*
%if 0%{?common_lisp_controller}
%{_prefix}/lib/common-lisp/bin/*
%{_sysconfdir}/*
%endif


%clean
rm -rf %{buildroot}


%changelog
* Mon Feb 01 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.35-1
- sbcl-1.0.35

* Tue Dec 22 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.33-1
- sbcl-1.0.33

* Mon Dec 21 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.32-2
- %%check: (re)enable run-tests.sh

* Mon Oct 26 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.32-1
- sbcl-1.0.32

* Tue Aug 18 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.30-2
- customize version.lisp-expr for rpm %%release
- s|%%_libdir|%%_prefix/lib|, so common-lisp-controller has at least
  a chance to work

* Tue Jul 28 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.30-1
- sbcl-1.0.30

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.29-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sun Jun 28 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.29-1
- sbcl-1.0.29

* Thu Apr 30 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.28-1
- sbcl-1.0.28

* Wed Mar 04 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.26-1
- sbcl-1.0.26

* Fri Feb 27 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.25-3
- ExclusiveArch: s/i386/%%ix86/

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.25-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Feb 03 2009 Rex Dieter <rdieter@fedoraproject.org> - 1.0.25-1
- sbcl-1.0.25

* Wed Dec 31 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.24-1
- sbcl-1.0.24

* Mon Dec 01 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.23-1
- sbcl-1.0.23

* Thu Oct 30 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.22-1
- sbcl-1.0.22

* Thu Oct 02 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.21-1
- sbcl-1.0.21
- common-lisp-controller bits f10+ only (for now)
- drop never-used min_bootstrap crud

* Mon Sep 22 2008 Anthony Green <green@redhat.com> - 1.0.20-3
- Create missing directories.

* Sun Sep 21 2008 Anthony Green <green@redhat.com> - 1.0.20-2
- Add common-lisp-controller bits.

* Tue Sep 02 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.20-1
- sbcl-1.0.20

* Wed Jul 30 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.19-1
- sbcl-1.0.19

* Thu May 29 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.17-3
- info removal should be done in %%preun (#448933)
- omit ppc only on f9+ (#448734)

* Wed May 28 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.17-2
- omit ppc build (#448734)
- skip tests, known to (sometimes) hang

* Wed May 28 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.17-1
- sbcl-1.0.17

* Sat Apr 25 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.16-1
- sbcl-1.0.16

* Thu Apr 10 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.15-2
- binutils patch

* Fri Feb 29 2008 Rex Dieter <rdieter@fedoraproject.org> - 1.0.15-1
- sbcl-1.0.15
- %%check: skip run-tests, hangs on room.test.sh

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1.0.14-2
- Autorebuild for GCC 4.3

* Mon Jan 28 2008 Rex Dieter <rdieter@fedoraproject.org> 1.0.14-1
- sbcl-1.0.14

* Thu Dec 27 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.13-1
- sbcl-1.0.13

* Mon Nov 26 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.12-1
- sbcl-1.0.12

* Wed Oct 31 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.11-1
- sbcl-1.0.11

* Mon Oct 08 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.10-1
- sbcl-1.0.10

* Sun Aug 26 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.9-1
- sbcl-1.0.9

* Sat Aug 25 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.8-3
- respin (ppc32)

* Fri Aug 10 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.8-2
- ExclusiveArch: i386 (#251689)
- License: BSD

* Sat Jul 28 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.8-1
- sbcl-1.0.8

* Wed Jun 27 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.7-1
- sbcl-1.0.7

* Wed Jun 06 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.6-2
- respin

* Tue May 29 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.6-1
- sbcl-1.0.6

* Sun Apr 29 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.5-1
- sbcl-1.0.5

* Mon Apr 09 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.4-2
- re-enable threading support (#235644)

* Mon Mar 26 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.4-1
- sbcl-1.0.4

* Wed Feb 28 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.3-1
- sbcl-1.0.3

* Thu Jan 25 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.2-1
- sbcl-1.0.2

* Fri Jan 05 2007 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.1-5
- respin, using native bootstrap

* Sun Dec 31 2006 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.1-4
- ppc patch, pached ppc bootstrap (David Woodhouse, #220053)

* Wed Dec 27 2006 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.1-3
- native bootstrap

* Wed Dec 27 2006 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.1-2
- ppc builds borked, disable for now (#220053)

* Wed Dec 27 2006 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0.1-1
- sbcl-1.0.1
- use binary bootstraps

* Thu Dec 14 2006 Rex Dieter <rdieter[AT]fedoraproject.org> 1.0-2
- initial sparc support (bootstrap, optflags)

* Mon Dec 04 2006 Rex Dieter <rexdieter[AT]users.sf.net> 1.0-1
- sbcl-1.0
- don't enable sb:thread (for now), to avoid hang in 'make check' tests 

* Mon Nov 13 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.18-2
- fix awol contrib/sb-bsd-sockets (#214568)

* Thu Oct 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.18-1
- sbcl-0.9.18

* Tue Sep 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.17-1
- sbcl-0.9.17

* Mon Aug 28 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.16-3
- fc6 respin

* Sun Aug 27 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.16-1
- 0.9.16

* Mon Jun 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.14-1
- 0.9.14

* Tue Jun 20 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.13-3
- use -fPIC in threads.impure.lisp

* Tue May 30 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.13-2
- 0.9.13

* Mon Apr 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.12-2
- respin, using new ppc bootstrap 

* Mon Apr 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.12-1.1
- try re-enabling ppc build

* Mon Apr 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.12-1
- 0.9.12

* Mon Mar 27 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.11-1
- 0.9.11

* Mon Feb 27 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.10-1
- 0.9.10
- update/fix make-config-ppc patch (still broken, #177029)
- cleanup bootstrap bits

* Fri Feb 10 2006 Rex Dieter <rexdieter[AT]users.sf.net>
- fc5: gcc/glibc respin
- disable verbose build options

* Thu Jan 26 2006 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.9-1
- 0.9.9

* Sat Dec 31 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.8-1
- 0.9.8

* Mon Nov 28 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.7-1
- 0.9.7

* Thu Oct 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.6-5
- override (bogus/mock-induced) sb-posix test failure(s).

* Thu Oct 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.6-4
- drop -D_FILE_OFFSET_BITS=64

* Thu Oct 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.6-3
- drop upstreamed stdlib_h patch

* Thu Oct 27 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.6-2
- CFLAGS += -D_GNU_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64
- (re)add/use stdlib_h patch (ppc)
- disable verbose build.log

* Wed Oct 26 2005 Rex Dieter <rexdieter[AT]users.sf.net> 0.9.6-1
- 0.9.6
- %%check: verify presence of sb-posix

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

