#!/bin/bash

system_dir=$(cd "`dirname "$0"`"; pwd)

. "$system_dir/common.sh"

direwolf=$(get_config '.programs.direwolf')
log_dir="$vanguard_work_dir/logs/direwolf"
config_file="$vanguard_config_dir/direwolf.conf"

mkdir -p "$log_dir"

if [ ! -d "$log_dir" ]; then
    echo "$log_dir doesn't exist"
    exit 1
fi

debug_args=
if [ "$vanguard_debug" ]; then
    debug_args=" -d kkpt"
fi

exec_cmd "$direwolf" -p -t 0 -l "$log_dir" -c "$config_file" $debug_args
