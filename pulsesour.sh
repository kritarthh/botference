#!/bin/bash
pactl load-module module-pipe-source source_name=virtmic file=/home/epsilon/plivo/onboarding/botference/virtmic format=s16le rate=16000 channels=1
pactl load-module module-null-sink sink_name=MySink
pacmd update-sink-proplist MySink device.description=MySink_null_sink
pactl load-module module-loopback sink=MySink

pactl load-module module-null-sink sink_name=MySink2
pacmd update-sink-proplist MySink2 device.description=MySink2_null_sink
# pactl load-module module-loopback sink=MySink2
