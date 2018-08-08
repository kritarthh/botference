import plivo
from threading import Thread
from SpeechRecognition import SpeechRecognizer
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from Bot import Bot
from queue import Queue
import logging
import time
import subprocess
import sys
from subprocess import call
import polly as polly

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

class CommandEngine(object):
    """docstring for CommandEngine"""
    def __init__(self, configParser):
        super(CommandEngine, self).__init__()
        self.initialize_logger()
        self.config_parser = configParser
        self.config = dict(self.config_parser.items('command-engine'))

        self.client = plivo.RestClient(auth_id=self.config['client_auth_id'], auth_token=self.config['client_auth_token'])

        self.conference = {}
        self.polling_thread = Thread(target=self.find_conference)
        self.polling_thread.daemon = True

        self.raw_text_queue = Queue()

        self.bot = Bot(dict(self.config_parser.items('bot')))

        # thread for recognition
        self.recognition_thread = Thread(target=self.speech_recognition)
        self.recognition_thread.daemon = True
        self.recognition_thread_started = False

        self.polling = True
        self.polling_thread.start()
        # self.find_conference()
        # join the polling thread in the end

        self.commander()
        # self.polling_thread.join()


    def initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # stream to stdout
        log_handler_std = logging.StreamHandler()
        log_handler_std.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_handler_std.setFormatter(formatter)
        self.logger.addHandler(log_handler_std)

        self.logger.info('logger initialized')


    def speech_recognition(self):
        self.sr = SpeechRecognizer('pulse_monitor', self.config_parser, self.raw_text_queue)
        self.sr.startRecognition()

    # start the bot if a conference is underway
    def start_bot(self):
        bot_present = False
        for member in self.conference['members']:
            if 'confBot' in member['caller_name']:
                # self.logger.debug(member)
                bot_present = True
                break
        if bot_present:
            self.logger.debug('bot found')
            # if bot is the only member present then hangup the bot
            if len(self.conference['members']) == 1:
                self.logger.debug('hangup the bot')
                self.bot.remove()

                # stop processing the audio
                try:
                    self.sr.stopRecognition()
                    self.recognition_thread.join()
                except Exception:
                    self.logger.error('recognition not active')
        else:
            self.logger.debug('bot not found in conference, add the bot')
            self.bot.add()
            # start processing the audio
            self.logger.debug('start audio processing')
            if self.recognition_thread_started == False:
                self.recognition_thread_started = True
                self.recognition_thread.start()


    # replace polling with proper response from conference application
    def find_conference(self):
        try:
            while self.polling:
                conferences = self.client.conferences.list().conferences
                if conferences == []:
                    self.logger.debug('no conferences found')
                    # clear the conference object
                    self.conference = {}
                else:
                    # if self.conference == {}:
                    # take the first conference
                    self.conference = self.client.conferences.get(conference_name=conferences[0])
                    self.logger.debug('conference going on with ' + str(len(self.conference['members'])) + ' members')
                    self.start_bot()
                time.sleep(int(self.config['polling_in_seconds']))
        except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
            self.logger.info('bot interrupted with Ctrl + C')
            self.sr.stopRecognition()
            self.bot.remove()

    def matcher(self, words, phrase):
        match_cnt = 0
        for word in words:
            if word in phrase:
                match_cnt += 1

        # if match_cnt == len(words):
        if match_cnt >= 2:
            return True

        return False

    def executioner(self, phrase):
        if self.matcher(['hello', 'there'], phrase):
            self.logger.debug('hello there')
            self.bot.play_text('hello there, how may I help you')
            return True
        if self.matcher(['start', 'recording'], phrase):
            self.logger.debug('start recording')
            self.bot.play_text('sure thing')
            # do something to record the pulseaudio sink
            return True
        if self.matcher(['call', 'Sam'], phrase):
            self.logger.debug('call sam')
            self.bot.play_text('sure, calling Sam and adding him to the conference.')
            self.client.calls.create(
                from_='10000',
                to_='919999999999',
                answer_url='https://s3.amazonaws.com/plivosamplexml/conference_url.xml',
                answer_method='GET'
            )
            return True

        if len(phrase) > 50:
            self.logger.debug('phrase too long, resetting')
            return True
        return False

    def commander(self):
        self.logger.info('printing the raw results')
        phrase = ''
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        try:
            while True:
                result = self.raw_text_queue.get()
                self.raw_text_queue.task_done()
                with open("raw_text", "a") as myfile:
                    myfile.write(result + ' ')

                # we get None when recognition is stopped
                # recognition is stopped when we get into keyboard interrupt
                # so for now it will never get None
                if result is None:
                    break
                print(result, end=' ')
                sys.stdout.flush()
                phrase += result
                exec_result = self.executioner(phrase)
                if exec_result:
                    phrase = ''
        except KeyboardInterrupt:  # allow Ctrl + C to shut down the program
            self.logger.info('bot interrupted with Ctrl + C')
            self.bot.remove()
            self.sr.stopRecognition()

