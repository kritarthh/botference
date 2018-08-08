from queue import Queue
import logging
import time
import subprocess
from subprocess import call
import polly as polly

class Bot(object):
    """docstring for Bot"""
    def __init__(self, config):
        super(Bot, self).__init__()
        self.config = config
        self.in_conference = False

    def add(self):
        # use some sip client
        call(['tmux', 'new-session', '-d', '-s', 'linphone'])
        # launch linphonec
        call(['tmux', 'send-keys', '-t', 'linphone', '-l', 'linphonec'])
        call(['tmux', 'send-keys', '-t', 'linphone', 'Enter'])
        # register the bot
        call(['tmux', 'send-keys', '-t', 'linphone', '-l', 'register ' + self.config['bot_username'] + ' ' + self.config['bot_realm'] + ' ' + self.config['bot_password']])
        call(['tmux', 'send-keys', '-t', 'linphone', 'Enter'])

        # source_output_number = get_source_output()
        # call(['pacmd', 'move-source-output', source_output_number, '4'])
        # pacmd move-source-output $(cat sampleout | sed ':a;N;$!ba;s/linphonec.*/linphonec/g' | sed ':a;N;$!ba;s/.*Source Output #//g' | head -n 1) 4

        # # enable autoanswer
        # call(['tmux', 'send-keys', '-t', 'linphone', '-l', 'autoanswer enable'])
        # call(['tmux', 'send-keys', '-t', 'linphone', 'Enter'])
        # call the conference
        call(['tmux', 'send-keys', '-t', 'linphone', '-l', 'call 1'])
        call(['tmux', 'send-keys', '-t', 'linphone', 'Enter'])

        call(['sh', 'set_pacmd.sh'])
        call(['sh', 'set_pacmd.sh'])
        call(['sh', 'set_pacmd.sh'])
        call(['sh', 'set_pacmd.sh'])
        call(['sh', 'set_pacmd.sh'])
        # self.arecord_process = subprocess.Popen(['arecord', '-D', 'dummy', '-r', '8000', '-c', '1', '-f', 'S16_LE', '>', 'virtmic'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        self.in_conference = True
        self.play_text('Bot has joined the conference')
        

    def remove(self):
        call(['tmux', 'send-keys', '-t', 'linphone', '-l', 'terminate'])
        call(['tmux', 'send-keys', '-t', 'linphone', 'Enter'])
        call(['tmux', 'send-keys', '-t', 'linphone', '-l', 'proxy remove 0'])
        call(['tmux', 'send-keys', '-t', 'linphone', 'Enter'])
        self.in_conference = False
        # self.arecord_process.kill()

    def play_text(self, text):
        # polly.get_mp3(text)
        call('espeak "' + text + '" --stdout | ffmpeg -i - -f mp3 - | mpg123 -o pulse -a 2 -', shell=True)
        # call('mpg123 -o pulse -a 2 polly_output.mp3', shell=True)
        
