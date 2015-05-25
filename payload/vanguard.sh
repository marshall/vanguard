#!/bin/bash

this_dir=$(cd "`dirname "$0"`"; pwd)

export PYTHONPATH="$this_dir:$PYTHONPATH"
exec /usr/bin/env python -m vanguard.main $@
