#!/bin/bash

this_dir=$(cd "`dirname "$0"`"; pwd)

export PYTHONPATH="$this_dir/vanguard:$PYTHONPATH"
exec /usr/bin/env python -m main $@
