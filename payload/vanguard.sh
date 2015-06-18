#!/bin/bash

this_dir=$(cd "`dirname "$0"`"; pwd)

. "$this_dir/../system/common.sh"

export PYTHONPATH="$this_dir:$PYTHONPATH"
exec /usr/bin/env python -m vanguard.main $@
