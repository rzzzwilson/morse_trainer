#!/usr/local/bin/bash
#
# Script to time execution of 'morse_trainer'
# under various situations.
#

LOG=timeit.log
STATE=morse_trainer.state
SAVE=./saved_logs
CRASHDIR=~/Library/Logs/DiagnosticReports

touch $LOG

# figure out log dir to save crashes in
if [ $# -eq 1 ]; then
    SUBDIR=$1
    SAVE=$SAVE/${SUBDIR}_logs
    LOG=$SAVE/$LOG
fi

# create crash save dir if required
if [ ! -d $SAVE ]; then
    mkdir -p $SAVE
fi

CWPM=$(grep "copy_cwpm" $STATE | sed -e "s/^.*: //" | sed -e "s/,//")
WPM=$(grep "copy_wpm" $STATE | sed -e "s/^.*: //" | sed -e "s/,//")

# we turn crash reporting off for the test, but force it back on if interrupted
trap 'defaults write com.apple.CrashReporter DialogType crashreport; exit' SIGINT
defaults write com.apple.CrashReporter DialogType none

while true; do
    START=$(date +%s)
    make
    FINISH=$(date +%s)

    DELTA=$(( $FINISH - $START ))
    DATE=$(date "+%Y%m%d_%H%M%S")
    echo "$DATE|$CWPM|$WPM|$DELTA" >> $LOG
    echo "DATE=$DATE|CWPM=$CWPM|WPM=$WPM|DELTA=$DELTA"
    sleep 2
    mv $CRASHDIR/* $SAVE
done

# if we get here, turn crash reporting back on
defaults write com.apple.CrashReporter DialogType crashreport
