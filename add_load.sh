#!/usr/local/bin/bash
#
# Script to add some load to the machine.
#

function load_it
{
    while true; do
        A=$(( 1 + 1 ))
    done
}

load_it &
load_it &
load_it &
load_it &
load_it &
load_it &
