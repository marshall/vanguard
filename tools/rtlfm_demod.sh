#!/bin/bash
#
# WIP utility script to demodulate FM + AFSK + AX.25 + APRS from an
# RTL-SDR on the 433.9 UHF frequency. Parameters here will almost certainly
# need to be tweaked in each environment
#
# Requirements:
#   - librtlsdr: http://sdr.osmocom.org/trac/wiki/rtl-sdr#Software
#   - multimon-ng: https://github.com/EliasOenal/multimon-ng

demod=fm
frequency=433.8832M
squelch=-135.8
gain=-1.3
play=0

usage() {
    echo "$0 [-p|--play]"
    echo " -p|--play  Listen to FM audio through the sound card as well as demodulate"
    exit
}

if [[ "$1" = "-p" || "$1" = "--play" ]]; then
    play=1
fi

if [[ "$1" = "-h" || "$1" = "--help" ]]; then
    usage
fi

rtl_fm="rtl_fm -M $demod -f $frequency -l $squelch -g $gain -s 22050 -o 4"
multimon_ng="multimon-ng -t raw -a AFSK1200 -A -q -"

if [[ "$play" = "1" ]]; then
    play_cmd="play -r 22050 -t raw -es -b 16 -c 1 -V1 -"
    $rtl_fm | tee >($play_cmd) | $multimon_ng
else
    $rtl_fm | $multimon_ng
fi
