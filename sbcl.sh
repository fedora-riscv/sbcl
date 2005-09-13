#!/bin/sh

# Source global config, if it exists
if [ -f /etc/sysconfig/sbcl ]; then
  source /etc/sysconfig/sbcl
fi

exec ${SBCL_HOME}/sbcl ${1+"$@"}
