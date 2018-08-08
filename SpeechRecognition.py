import speech_recognition as sr

import logging
import time
import sys
import math
import pyaudio
from queue import Queue
from numpy import linspace,sin,pi,int16
from threading import Thread
import googleapiclient

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

class SpeechRecognizer(object):
    """docstring for SpeechRecognizer"""
    def __init__(self, sourceName, configParser, rawTextQueue):
        super(SpeechRecognizer, self).__init__()
        self.source_name = sourceName
        
        self.config = dict(configParser.items('speech-recognizer'))
        self.thresholds = {
            'pause_threshold': float(self.config['pause_threshold']),
            'phrase_threshold': float(self.config['phrase_threshold']),
            'non_speaking_duration': float(self.config['non_speaking_duration']),
            'dynamic_energy_threshold': str2bool(self.config['dynamic_energy_threshold'])
        }

        print(self.config)

        self.raw_text_queue = rawTextQueue

        # Create the Logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # stream to stdout
        log_handler_std = logging.StreamHandler()
        log_handler_std.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_handler_std.setFormatter(formatter)
        self.logger.addHandler(log_handler_std)

        # initialize recognizer
        self.recognizer = sr.Recognizer()
        self.setThresholds(self.thresholds)

        # initialize audio source
        self.source = sr.Microphone(self.getAudioSourceIndex())

        # initialize the audio queue
        self.audio_queue = Queue()
        # initialize the raw result queue
        self.raw_results_queue = Queue()

        # initialize the recognizer thread
        self.recognize_thread = Thread(target=self.recognize_worker)
        self.recognize_thread.daemon = True

        # initialize the printer thread
        self.print_thread = Thread(target=self.printResults)
        self.print_thread.daemon = True



    def recognize(self, audio, engine='google'):
        if (engine == 'google'):
            return self.recognizer.recognize_google(audio)
        elif (engine == 'google_cloud'):
            GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""
CONTENTS OF GOOGLE CREDENTIALS JSON HERE
"""
            return self.recognizer.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS)
        elif (engine == 'bing'):
            BING_KEY = "BING_KEY_HERE"
            return self.recognizer.recognize_bing(audio, key=BING_KEY)
        else:
            return self.recognizer.recognize_sphinx(audio)

    def recognize_worker(self):
        # this runs in a background thread
        while True:
            audio = self.audio_queue.get()  # retrieve the next audio processing job from the main thread
            if audio is None: break  # stop processing if the main thread is done

            try:
                results = self.recognize(audio)
                self.raw_results_queue.put(results)
                self.raw_text_queue.put(results)
                # process the phrase here
                # send it to the command engine

            except sr.UnknownValueError:
                # self.logger.error("Could not understand audio")
                pass
            except sr.RequestError as e:
                self.logger.error("Could not request results from service; {0}, retrying with sphinx".format(e))
                # try a different service
                try:
                    results = self.recognize(audio, 'sphinx')
                    self.raw_results_queue.put(results)
                    self.raw_text_queue.put(results)
                except sr.UnknownValueError:
                    # self.logger.error("Could not understand audio")
                    pass

            self.audio_queue.task_done()  # mark the audio processing job as completed in the queue


    def startRecognition(self):
        self.to_recognize = True
        # start the thread
        self.recognize_thread.start()
        # self.print_thread.start()

        self.logger.info('recognition started')

        # start listening
        with self.source as source:
            if str2bool(self.config['adjust_ambient']):
                self.logger.debug('adjust for ambient noise')
                self.recognizer.adjust_for_ambient_noise(self.source)

            while self.to_recognize:  # repeatedly listen for phrases and put the resulting audio on the audio processing job queue
                self.audio_queue.put(self.recognizer.listen(source, phrase_time_limit = int(self.config['phrase_limit'])))
                # self.logger.debug('audio put in the queue')

        # gracefully stop the recognition
        self.audio_queue.join()  # block until all current audio processing jobs are done
        self.audio_queue.put(None)  # tell the recognize_thread to stop
        self.raw_results_queue.put(None)
        self.raw_text_queue.put(None)
        self.recognize_thread.join() # wait for the recognize_thread to actually stop
        self.print_thread.join()

    def stopRecognition(self):
        self.to_recognize = False

    def printResults(self):
        self.logger.info('printing the raw results')
        while True:
            result = self.raw_results_queue.get()
            self.raw_results_queue.task_done()
            if result is None:
                break
            print(result, end=' ')
            sys.stdout.flush()

    def setThresholds(self, thresholds):
        for key, value in thresholds.items():
            self.recognizer.key = value
            self.logger.debug(key + ' = ' + str(value))

    def getAudioSourceIndex(self, name=''):
        if (name == ''):
            name = self.source_name
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        self.logger.debug('number of devices: ' + str(numdevices))
        idx = -1;
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                if (p.get_device_info_by_host_api_device_index(0, i).get('name') == name):
                    idx = i
                self.logger.debug("Input Device id " + str(i) + " - " + p.get_device_info_by_host_api_device_index(0, i).get('name'))
        # idx = 5
        if (idx != -1):
            self.logger.info(name + ' found')
        else:
            self.logger.error(name + ' source not found')
        return idx
        
