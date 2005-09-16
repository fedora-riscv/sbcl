#!/bin/sh

# Source global config, if it exists
if [  -f /etc/sbcl.conf ]; then
  source /etc/sbcl.conf
fi

exec ${SBCL_HOME}/sbcl ${1+"$@"}
