#!/usr/bin/python
# Chippy Ruxpin by Next Thing Co
# Powered by C.H.I.P., the world's first $9 computer!

# apt-get install python-setuptools python-dev build-essential espeak alsa-utils
# apt-get install python-alsaaudio python-numpy python-twitter python-bottle mplayer

# IMPORTANT NOTE ABOUT TWITTER STUFF!
# In order to retrieve tweets, you need to authorize this code to use your twitter account.
# This involves obtaining some special tokens that are specific to you.
# Please visit Twitter's website to obtain this information and put the values in the variables below.
# For more information, visit this URL:
# https://dev.twitter.com/oauth/overview/application-owner-access-tokens

consumerKey='INSERT YOUR CONSUMER KEY HERE FROM TWITTER'
consumerSecret='INSERT YOUR CONSUMER SECRET HERE FROM TWITTER'
accessTokenKey='INSERT YOUR ACCESS TOKEN KEY HERE FROM TWITTER'
accessTokenSecret='INSERT YOUR ACCESS TOKEN SECRET HERE FROM TWITTER'

import sys
import time
import subprocess
import os
from random import randint
from threading import Thread
from chippyRuxpin_audioPlayer import AudioPlayer
from chippyRuxpin_gpio import GPIO
from chippyRuxpin_twitter import ChippyTwitter
from chippyRuxpin_webFramework import WebFramework

fullMsg = ""

MOUTH_OPEN = 408 # GPIO pin assigned to open the mouth. XIO-P0
MOUTH_CLOSE = 412 # GPIO pin assigned to close the mouth. XIO-P2
EYES_OPEN = 410 # GPIO pin assigned to open the eyes. XIO-P4
EYES_CLOSE = 414 # GPIO pin assigned to close the eyes. XIO-P6

io = GPIO() #Establish connection to our GPIO pins.
io.setup( MOUTH_OPEN )
io.setup( EYES_OPEN )
io.setup( MOUTH_CLOSE )
io.setup( EYES_CLOSE )

audio = None
isRunning = True

def updateMouth():
    lastMouthEvent = 0
    lastMouthEventTime = 0

    while( audio == None ):
        time.sleep( 0.1 )
        
    while isRunning:
        if( audio.mouthValue != lastMouthEvent ):
            lastMouthEvent = audio.mouthValue
            lastMouthEventTime = time.time()

            if( audio.mouthValue == 1 ):
                io.set( MOUTH_OPEN, 1 )
                io.set( MOUTH_CLOSE, 0 )
            else:
                io.set( MOUTH_OPEN, 0 )
                io.set( MOUTH_CLOSE, 1 )
        else:
            if( time.time() - lastMouthEventTime > 0.4 ):
                io.set( MOUTH_OPEN, 0 )
                io.set( MOUTH_CLOSE, 0 )

# A routine for blinking the eyes in a semi-random fashion.
def updateEyes():
    while isRunning:
        io.set( EYES_CLOSE, 1 )
        io.set( EYES_OPEN, 0 )
        time.sleep(0.4)
        io.set( EYES_CLOSE, 0 )
        io.set( EYES_OPEN, 1 )
        time.sleep(0.4)
        io.set( EYES_CLOSE, 1 )
        io.set( EYES_OPEN, 0 )
        time.sleep(0.4)
        io.set( EYES_CLOSE, 0 )
        io.set( EYES_OPEN, 0 )
        time.sleep( randint( 0,7) )
   
def talk(myText):
    if( myText.find( "twitter" ) >= 0 ):
        myText += "0"
        myText = myText[7:-1]
        try:
	    myText = twitter.getTweet( myText )
	except:
	    print( "!!!ERROR: INVALID TWITTER CREDENTIALS. Please read README.md for instructions.")
            return
    
    os.system( "espeak \",...\" 2>/dev/null" ) # Sometimes the beginning of audio can get cut off. Insert silence.
    time.sleep( 0.5 )
    os.system( "espeak -w speech.wav \"" + myText + "\" -s 130" )
    audio.play("speech.wav")
    return myText

mouthThread = Thread(target=updateMouth)
mouthThread.start()
eyesThread = Thread(target=updateEyes)
eyesThread.start()     
audio = AudioPlayer()

if( consumerKey.find( 'TWITTER' ) >= 0 ):
    print( "WARNING: INVALID TWITTER CREDENTIALS. Please read README.md for instructions." )    
else:
    twitter = ChippyTwitter(consumerKey,consumerSecret,accessTokenKey,accessTokenSecret)

web = WebFramework(talk)
isRunning = False
io.cleanup()
sys.exit(1)
