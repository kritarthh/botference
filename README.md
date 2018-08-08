Prerequisites
-------------
+ Plivo endpoint for the bot
+ Plivo account credentials for polling any ongoing conferences
+ tmux
+ linphonec
+ pulseaudio
+ espeak
+ speech_recognition module for python
+ (Optional) amazon polly

Getting Started
---------------
1. update botference.cfg with your plivo credentials
2. ensure tmux, linphonec are in path
3. create fifo pipe `mkfifo virtmic && chmod 666 virtmic`
4. update `pulsesour.sh` with your virtmic location
5. run `sh pulsesour.sh` there should be no errors/failures
4. run `python main.py`

Troubleshooting
---------------
Ensure that the pulseaudio sinks and sources are working correctly and examine if `set_pacmd.sh` 
works for your setup. You might need to refer online resources on pulseaudio custom sinks and 
sources.
