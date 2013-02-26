
%if 0%{?fedora} > 9 || 0%{?rhel} > 5
%define common_lisp_controller 1
%endif

# generate/package docs
%ifnarch sparcv9
## texinfo seems borked on sparc atm 
## f19/texinfo-5.0 is busted, https://bugzilla.redhat.com/913274
%if 0%{?fedora} < 19
%define docs 1
%endif
%endif

# define to enable verbose build for debugging
#define sbcl_verbose 1 
%define sbcl_shell /bin/bash

Name: 	 sbcl
Summary: Steel Bank Common Lisp
Version: 1.1.5
Release: 1%{?dist}

License: BSD
Group: 	 Development/Languages
URL:	 http://sbcl.sourceforge.net/
Source0: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-source.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

ExclusiveArch: %{ix86} x86_64 ppc sparcv9

# Pre-generated html docs
Source1: http://downloads.sourceforge.net/sourceforge/sbcl/sbcl-%{version}-documentation-html.tar.bz2

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

%if 0%{?common_lisp_controller}
BuildRequires: common-lisp-controller
Requires:      common-lisp-controller
Requires(post): common-lisp-controller
Requires(preun): common-lisp-controller
Source200: sbcl.sh
Source201: sbcl.rc
Source202: sbcl-install-clc.lisp
%endif

Patch2: sbcl-0.9.5-personality.patch
Patch3: sbcl-1.1.1-optflags.patch
Patch6: sbcl-0.9.5-verbose-build.patch

## upstreamable patches
Patch50: sbcl-1.0.51-generate_version.patch

## upstream patches

# %%check/tests
BuildRequires: ed
%if 0%{?docs}
Requires(post): /sbin/install-info
Requires(preun): /sbin/install-info
# doc generation
BuildRequires: ghostscript
BuildRequires: texinfo
BuildRequires: time
%endif

%description
Steel Bank Common Lisp (SBCL) is a Open Source development environment
for Common Lisp. It includes an integrated native compiler,
interpreter, and debugger.


%prep
%setup -q %{?sbcl_bootstrap_src} -a 1

%patch2 -p1 -b .personality
%patch3 -p1 -b .optflags
%{?sbcl_verbose:%patch6 -p1 -b .verbose-build}
%patch50 -p1 -b .generate_version

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

export SBCL_HOME=%{_prefix}/lib/sbcl
%{?sbcl_arch:export SBCL_ARCH=%{sbcl_arch}}
%{?sbcl_shell} \
./make.sh \
  --prefix=%{_prefix} \
  %{?bootstrap}

# docs
%if 0%{?docs}
make -C doc/manual info
%endif

# Handle pre-generated docs
if [ -d %{name}-%{version}/doc/manual ]; then
cp -a %{name}-%{version}/doc/manual/* doc/manual/
fi


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
# verify --version output
test "$(source ./subr.sh; SBCL_ARGS= run_sbcl --version 2>/dev/null | cut -d' ' -f2)" = "%{version}-%{release}"
# still seeing Failure: threads.impure.lisp / (DEBUGGER-NO-HANG-ON-SESSION-LOCK-IF-INTERRUPTED)
time %{?sbcl_shell} ./run-tests.sh ||:
popd
exit $ERROR


%install
rm -rf %{buildroot}

mkdir -p %{buildroot}{%{_bindir},%{_prefix}/lib,%{_mandir}}

unset SBCL_HOME 
export INSTALL_ROOT=%{buildroot}%{_prefix} 
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
%if 0%{?docs}
/sbin/install-info %{_infodir}/sbcl.info %{_infodir}/dir ||:
/sbin/install-info %{_infodir}/asdf.info %{_infodir}/dir ||:
%endif
%if 0%{?common_lisp_controller}
/usr/sbin/register-common-lisp-implementation sbcl > /dev/null 2>&1 ||:
%endif

%preun
if [ $1 -eq 0 ]; then
%if 0%{?docs}
  /sbin/install-info --delete %{_infodir}/sbcl.info %{_infodir}/dir ||:
  /sbin/install-info --delete %{_infodir}/asdf.info %{_infodir}/dir ||:
%endif
%if 0%{?common_lisp_controller}
  /usr/sbin/unregister-common-lisp-implementation sbcl > /dev/null 2>&1 ||:
%endif
fi

%files
%defattr(-,root,root)
%doc BUGS COPYING README CREDITS NEWS TLA TODO
%doc PRINCIPLES
%{_bindir}/sbcl
%dir %{_prefix}/lib/sbcl/
%{_prefix}/lib/sbcl/asdf/
%{_prefix}/lib/sbcl/asdf-install/
%{_prefix}/lib/sbcl/sb-aclrepl/
%{_prefix}/lib/sbcl/sb-bsd-sockets/
%{_prefix}/lib/sbcl/sb-cltl2/
%{_prefix}/lib/sbcl/sb-concurrency/
%{_prefix}/lib/sbcl/sb-cover/
%{_prefix}/lib/sbcl/sb-executable/
%{_prefix}/lib/sbcl/sb-grovel/
%{_prefix}/lib/sbcl/sb-introspect/
%{_prefix}/lib/sbcl/sb-md5/
%{_prefix}/lib/sbcl/sb-posix/
%{_prefix}/lib/sbcl/sb-queue/
%{_prefix}/lib/sbcl/sb-rotate-byte/
%{_prefix}/lib/sbcl/sb-rt/
%{_prefix}/lib/sbcl/sb-simple-streams/
%{_prefix}/lib/sbcl/sb-sprof/
%{_prefix}/lib/sbcl/site-systems/
%{_mandir}/man1/sbcl.1*
%doc doc/manual/sbcl.html
%doc doc/manual/asdf.html
%if 0%{?docs}
%{_infodir}/asdf.info*
%{_infodir}/sbcl.info*
%endif
%if 0%{?common_lisp_controller}
%{_prefix}/lib/common-lisp/bin/*
%{_prefix}/lib/sbcl/install-clc.lisp
%{_prefix}/lib/sbcl/sbcl-dist.core
%verify(not md5 size) %{_prefix}/lib/sbcl/sbcl.core
%config(noreplace) %{_sysconfdir}/sbcl.rc
%else
%{_prefix}/lib/sbcl/sbcl.core
%endif


%clean
rm -rf %{buildroot}


%changelog
* Tue Feb 26 2013 Rex Dieter <rdieter@fedoraproject.org> 1.1.5-1
- 1.1.5

* Wed Feb 20 2013 Rex Dieter <rdieter@fedoraproject.org> 1.1.4-1
- 1.1.4
- omit texinfo generation on f19, texinfo-5.0 is borked (#913274)

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 08 2013 Rex Dieter <rdieter@fedoraproject.org> 1.1.3-1
- 1.1.3
- fix build against glibc-2.17 (launchpad#1095036)

* Sat Dec 08 2012 Rex Dieter <rdieter@fedoraproject.org> 1.1.2-1
- 1.1.2

* Fri Nov 02 2012 Rex Dieter <rdieter@fedoraproject.org> 1.1.1-1
- 1.1.1

* Sat Oct 27 2012 Rex Dieter <rdieter@fedoraproject.org> 1.1.0-1
- 1.1.0

* Tue Aug 07 2012 Rex Dieter <rdieter@fedoraproject.org> 1.0.58-1
- 1.0.58

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.57-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri May 25 2012 Rex Dieter <rdieter@fedoraproject.org> - 1.0.57-1
- sbcl-1.0.57
- fix/renable common-lisp support (accidentally disabled since 1.0.54-1)

* Thu Apr 12 2012 Rex Dieter <rdieter@fedoraproject.org> 1.0.56-1
- 1.0.56

* Thu Apr 05 2012 Rex Dieter <rdieter@fedoraproject.org> 1.0.55-1
- 1.0.55

* Mon Dec 05 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.54-1
- 1.0.54

* Mon Nov 07 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.53-1
- 1.0.53

* Fri Oct 14 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.52-1
- 1.0.52

* Mon Aug 22 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.51-2
- drop unused-for-a-long-time my_setarch.c
- fix sbcl --version output if built within git checkout

* Sun Aug 21 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.51-1
- 1.0.51

* Tue Jul 12 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.50-1
- 1.0.50

* Fri Mar 04 2011 Rex Dieter <rdieter@fedoraproject.org> 1.0.46-1
- 1.0.46

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.44-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Nov 29 2010 Rex Dieter <rdieter@fedoraproject.org> -  1.0.44-1
- sbcl-1.0.44
- BR: ed (for %%check , tests)

* Thu Sep 30 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.43-1
- sbcl-1.0.43
- remove explict threading options, already enabled by default where
  it makes sense

* Wed Sep 29 2010 jkeating - 1.0.42-2
- Rebuilt for gcc bug 634757

* Sat Sep 18 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.42-1
- sbcl-1.0.42

* Mon Aug 16 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.41-1
- sbcl-1.0.41

* Sat Jul 17 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.40-1
- sbcl-1.0.40

* Sat May 08 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.38-2
- shorten docs dangerously close to maxpathlen

* Fri Apr 30 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.38-1
- sbcl-1.0.38

* Wed Apr 07 2010 Rex Dieter <rdieter@fedoraproject.org> - 1.0.37-1
- sbcl-1.0.37

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
