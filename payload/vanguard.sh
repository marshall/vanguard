#!/bin/bash

this_dir=$(cd "`dirname "$0"`"; pwd)
/usr/bin/env python "$this_dir/vanguard/main.py" $@
