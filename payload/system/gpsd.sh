#!/bin/bash

system_dir=$(cd "`dirname "$0"`"; pwd)

. "$system_dir/common.sh"

gps_device=$(get_config '.gps.device')
gps_uart=$(get_config '.gps.uart')
gpsd=$(get_config '.programs.gpsd')
gpsd_sock=$(get_config '.gps.gpsd_sock')

python -c "import Adafruit_BBIO.UART as UART; UART.setup('$gps_uart')"
exec_cmd $gpsd $gps_device -N -F $gpsd_sock
