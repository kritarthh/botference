import configparser
from SpeechRecognition import SpeechRecognizer
from CommandEngine import CommandEngine

configParser = configparser.RawConfigParser()
configParser.read(r'botference.cfg')

ceng = CommandEngine(configParser)
