#!/bin/bash

system_dir=$(cd "`dirname "$0"`"; pwd)

. "$system_dir/common.sh"

gps_device=$(get_config '.gps.device')
gpsd=$(get_config '.gps.gpsd')
gpsd_sock=$(get_config '.gps.gpsd_sock')

exec_cmd $gpsd $gps_device -N -F $gpsd_sock
