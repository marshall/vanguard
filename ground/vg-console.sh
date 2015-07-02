#!/bin/bash

this_file=$0
if [[ -h "$0" ]]; then
    this_file=$(readlink "$0")
fi

# cd into the symlink dir first before trying to resolve the link when relative
this_dir=$(cd "`dirname "$0"`"; cd "`dirname "$this_file"`"; pwd)
dist_dir=$this_dir/dist

if [[ "$1" = "-h" || "$1" = "--help" ]]; then
  exec /usr/bin/env node $this_dir/lib/ui/console.js --help
fi

if [[ -f /tmp/.vg-console ]]; then
    rm /tmp/.vg-console
fi

BASE=$(tmux start-server\; showw -gv pane-base-index)

/usr/bin/env node $this_dir/lib/ui/console.js --base=$BASE --verbose $@ > /tmp/.vg-console

tmux start-server\; source-file /tmp/.vg-console
tmux attach-session -t vg-console
