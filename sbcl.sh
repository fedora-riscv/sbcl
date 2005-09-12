#!/bin/sh

if [ -z "$SBCL_HOME" ] ; then
SBCL_HOME=/usr/lib/sbcl
export SBCL_HOME
fi

if [ -z "$SBCL_SETARCH" ] ; then
BCL_SETARCH="setarch i386 -R"
fi

exec ${SBCL_SETARCH} ${SBCL_HOME}/sbcl ${1+"$@"}
