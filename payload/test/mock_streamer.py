#!/usr/bin/env python
import argparse
import os
import shutil

this_dir = os.path.abspath(os.path.dirname(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--resolution')
parser.add_argument('-j', '--quality')
parser.add_argument('-b', '--depth')
parser.add_argument('-o', '--filename')
parser.add_argument('device')

args = parser.parse_args()
shutil.copy(os.path.join(this_dir, 'test.jpeg'), args.filename)
