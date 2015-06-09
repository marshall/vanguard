#!/bin/bash

# 600g Pawan from Aether Industries
# Copied from http://www.aetherandbeyond.com/main/store/product/12-20-ft-dia-professional-weather-balloon-600g-white.html
#
# Product Details:
#
#    Diameter at release: (1.8 m)
#    Diameter at burst altitude: (6.1 m)
#    Nominal Lift: 3.8 lb (1,700 g)
#    Maximum Lift: (5,450 g)
#    Burst altitude: 100,000 ft (30,500 m)
#
#    Volume at release: 113 cu ft (1.42 cu m)
#    Neck diameter: 2.8 in ()
#    Neck length: 9 in ()
#    Ascent rate: /min (5 m/s)
#    Material: Latex Rubber




this_dir=$(cd "`dirname "$0"`"; pwd)

cd "$this_dir"

python burstcalc.py \
    --target-burst-alt 26000 \
    --payload-mass     2200 \
    --balloon          p600 \
    --burst-diameter   6.1 \
    $@
