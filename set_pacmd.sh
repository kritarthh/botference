res="Moved failed."
while [ "$res" == "Moved failed." ]; do echo 'trying to set pacmd'; res=$(pacmd move-source-output $(pactl list source-outputs | sed ':a;N;$!ba;s/linphonec.*/linphonec/g' | sed ':a;N;$!ba;s/.*Source Output #//g' | head -n 1) 4); sleep 1; done
echo 'set pacmd'