#!/bin/bash

. ../scripts/shell_settings.sh
echo "memcached_ip=$memcached_ip"

. ../utils/utils.sh

num_servers=$2
num_clients=$3
workload=$4
run_time=$5

get_out_fname $1
out_fname=$ret_out_fname

if [ -z $out_fname ]; then
    echo "Unsupported server type $1"
    exit
fi

# memcached_ip="10.10.1.1"

python ../controller.py $workload -s $num_servers -c $num_clients -o $out_fname -m $memcached_ip -T $run_time

# remember to add "-f 2" on testing fiber

if [ ! -z "$6" ]; then
    mv $workload-sample-adaptive-s1-c$num_clients.json $workload-sample-adaptive-fc$5-s1-c$num_clients.json
fi