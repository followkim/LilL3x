#!/bin/sh
SSID=${1}
PASS=${2}

CMD="nmcli dev wifi connect \"${SSID}\" password \"${PASS}\""
eval $CMD
