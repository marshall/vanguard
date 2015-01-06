#!/bin/bash

system_dir=$(cd "`dirname "$0"`"; pwd)
config_dir=$(cd "$system_dir/../config"; pwd)

jq=$system_dir/jq-armhf
config_file=$config_dir/config.json

get_config() {
  $jq --raw-output $1 $config_file
}

run_cmd() {
  echo $@
  $@
}

exec_cmd() {
  run_cmd exec $@
}
