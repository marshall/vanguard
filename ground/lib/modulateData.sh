#!/bin/bash
# Basic script to modulate the first parameter through python module AFSK.

aprs --callsign N0CALL --output - "$1" | play -t wav -
