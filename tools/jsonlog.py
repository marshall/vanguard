#!/usr/bin/python

import sys
import csv
import json
import unicodedata
import re
import os

# Sample entry:
# u'{
#   "free_mem": 436400, 
#   "int_temp": 16.67024923021694, 
#   "uptime": 7491.07, 
#   "cpu_usage": 57, 
#   "ext_temp": -13.193173533505671
# }'

bigKeys = ['telemetry', 'location', 'location_session_count']
singleKeys=['time', 'free_mem', 'int_temp', 'uptime', 'cpu_usage', 'ext_temp']
file1   = "telemetryoutput.json"
output  = "telemetry.tab"

f = open(file1)

try:
    fdata = json.load(f)
except ValueError:
    print "\nValue Error occurred: this file may not be properly formatted JSON.\n"
    sys.exit()

#print "fdata type: " +  str(type(fdata))
wholedoc = fdata[0]
#print "Length of wholedoc: " + str(len(wholedoc))
#print "wholedoc type: " + str(type(wholedoc))
telem=wholedoc['telemetry']
#print "Length of telem: " + str(len(telem))
#print str(telem)

g = open(output, 'w')

g.write('index')
for key in singleKeys:
    g.write( '\t' + key )
g.write('\n')

for index in range(0,len(telem)):
#    print str(telem[index])
    item = json.loads(telem[index])
#    print str(item.keys() )
    g.write(str(index))
    for key in singleKeys:
        g.write('\t' + str(item[key]) )
    g.write('\n')

g.close()
f.close()
