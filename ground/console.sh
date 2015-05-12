#!/bin/bash

this_dir=$(cd "`dirname "$0"`"; pwd)
start_dir=$(cd "$this_dir/.."; pwd)
dist_dir=$start_dir/dist

session_name=ground_station
window_name=ground_station

telemetry_row_height=15
chart_row_height=30
shell_row_height=35
log_row_height=20

time_width=33
position_width=33
stats_width=33
alt_chart_width=50
temp_chart_width=50

time_cmd="node $dist_dir/lib/ui/time.js || sleep 100"
position_cmd="node $dist_dir/lib/ui/position.js || sleep 100"
stats_cmd="node $dist_dir/lib/ui/stats.js || sleep 100"
alt_chart_cmd="node $dist_dir/lib/ui/altitude-chart.js|| sleep 100"
temp_chart_cmd="node $dist_dir/lib/ui/temp-chart.js|| sleep 100"
shell_cmd="node $dist_dir/lib/repl-client.js || sleep 100"
log_cmd="tail -f /tmp/vg-station.log | $start_dir/node_modules/bunyan/bin/bunyan -o short || sleep 100"

run() {
  echo "$@"
  "$@"
}

run tmux start-server

run tmux new-session -d -n "$window_name" \
  -s "$session_name" -c "$start_dir" "$time_cmd"

start_pane=$(tmux showw -gv pane-base-index)
time_pane=$start_pane
position_pane=$(( $start_pane + 5 ))
stats_pane=$(( $start_pane + 4 ))
alt_chart=$(( $start_pane + 3 ))
temp_chart=$(( $start_pane + 6 ))
shell=$(( $start_pane + 1 ))
log=$(( $start_pane + 2 ))

run tmux split-window -t $start_pane -v \
  -p $(( $shell_row_height + $log_row_height )) -c "$start_dir" "$shell_cmd"

run tmux split-window -t $shell -v \
  -p $(( $log_row_height * 2 )) -c "$start_dir" "$log_cmd"

top2_height=$(( $chart_row_height + $telemetry_row_height ))

run tmux split-window -t $start_pane -v \
  -p $(( $chart_row_height * 100 / $top2_height )) \
  -c "$start_dir" "$alt_chart_cmd"

run tmux split-window -t $start_pane -h -p $stats_width -c "$start_dir" "$stats_cmd"

leftover=$(( $time_width + $position_width ))
run tmux split-window -t $start_pane -h \
  -p $(( $position_width * 100 / $leftover )) -c "$start_dir" "$position_cmd"

run tmux split-window -t $alt_chart -h -p $temp_chart_width \
  -c "$start_dir" "$temp_chart_cmd"

run tmux select-pane -t $shell

run tmux attach-session -t "$session_name"
