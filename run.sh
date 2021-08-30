#!/bin/bash
set -e

# https://unix.stackexchange.com/questions/55558/how-can-i-kill-and-wait-for-background-processes-to-finish-in-a-shell-script-whe

trap 'killall' INT

killall() {
    trap '' INT TERM
    echo "****...Shutting Down...****"
    kill -TERM 0
    wait
    echo DONE
}

echo "WAIT"
python3 main.py &
echo $!
sleep 5s
python3 watch_stream.py & 
echo $!

cat