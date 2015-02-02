#!/bin/bash

system_dir=$(cd "`dirname "$0"`"; pwd)
config_dir=$(cd "$system_dir/../config"; pwd)

jq=${jq:-$system_dir/jq-armhf}
config_file=$config_dir/config.json

get_config() {
  "$jq" --raw-output "$1" "$config_file"
}

run_cmd() {
  echo $@
  $@
}

exec_cmd() {
  run_cmd exec $@
}

_debug=$(get_config '.debug')
if [ "$_debug" = "true" ]; then
    export vanguard_debug=1
fi

export vanguard_work_dir=$(get_config '.work_dir')
export vanguard_config_dir="$config_dir"
