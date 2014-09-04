#!/usr/bin/python
import time
import sys
from threading import Timer
import RPi.GPIO as GPIO
from birdy.twitter import UserClient

# These are the secret keys received from the Twitter development center
client = None

# The name of the file storing the development keys ...
twitterKeysFileName = 'twitter.txt'

# Display detailed information when set to true
verbose = False

# The lastTweed is the ID of the last processed tweet. It's initialized to 1
# for the first call since the API returns an error with since_id=0
lastTweet = 1

# The filename used to save the id of the last tweet processed by the application
# This allows the Raspberry Pi or computer to be turned off without re-processing old tweets
fileName = 'id.txt'

# The delay between each call to the Twitter API. The function mentions_timeline is limited
# to 15 calls per block of 15 minutes. The extra 1 is to play safe.
sleepDelay = 61

IO_ACTION1 = 18
IO_ACTION2 = 23

DELAY_ACTION1 = 5
DELAY_ACTION2 = 10

# Create the client using the keys found in the twitter.txt file
def createClient():
    global client
    file = open(twitterKeysFileName, 'r')
    k1 =  file.readline().replace("\n", "")
    k2 =  file.readline().replace("\n", "")
    k3 =  file.readline().replace("\n", "")
    k4 =  file.readline().replace("\n", "")
    client = UserClient(k1,k2,k3,k4)
    file.close()

# Display a message to the console if the verbose mode is enabled
def printInfo(msg):
    if verbose:
        print msg

# Print an error message
def printError(error):
    print(error)

# Set the lastTweet variable to the most recent mention of the twitter account
def ignoreCurrentTweets():
    tweets = getTweets()
    if(len(tweets) > 0):
        markAsRead(tweets[0].id)

# Process the command line arguments if any
def processArgv():
    global verbose
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-i':
            print('-i: Ignoring current mentions')
            ignoreCurrentTweets()

        if sys.argv[i] == '-v':
            print('-v: Activating verbose mode')
            verbose = True

# Returns a list of tweets that mentioned the user using the @username tag
# A maximum of 100 tweets will be loaded since the last tweet identified by lastTweet
def getTweets():
    try:
        tweets = client.api.statuses.mentions_timeline.get(count=100,since_id=lastTweet)
        printInfo('Found ' + str(len(tweets.data)) + ' mentions')
        return tweets.data
    except:
        return []

# Save the ID of the last tweet processed
def markAsRead(id):
    global lastTweet
    try:
        lastTweet = id
        file = open(fileName,'w')
        file.write(str(id))
        file.close()
        printInfo('Last tweet mention processed: ' + str(id))
    except:
        printError('Failed to save the last processed tweet mention id ' + str(id))

# Load the ID of the last tweet processed from the file system
def loadLastTweetId():
    global lastTweet
    try:
        file = open(fileName,'r')
        lastTweet = long(file.read())
        file.close()
        printInfo('Last tweet mention id found: ' + str(lastTweet))
    except:
        printInfo('Last tweet mention id not found. Will load all mentions.')

# Read the content of the tweet message and trigger the right action
def processTweets(tweets):
    for i in range(len(tweets)-1, -1, -1):
        text = tweets[i].text
        printInfo('Processing: ' + text)
        for key in actions:
            if key in text:
                actions[key](text)

        markAsRead(tweets[i].id)

    return

def initGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    GPIO.setup(23, GPIO.OUT)

def action1(text):
    print('action1: ' + text)
    GPIO.output(IO_ACTION1, True)
    Timer(DELAY_ACTION1, action1Stop).start()

def action1Stop():
    GPIO.output(IO_ACTION1, False)

def action2(text):
    print('action2: ' + text)
    GPIO.output(IO_ACTION2, True)
    Timer(DELAY_ACTION2, action2Stop).start()

def action2Stop():
    GPIO.output(IO_ACTION2, False)

def action3(text):
    print('action3: ' + text)

# A dict of functions associated to the hashtag they are associated to
actions = {'#action1':action1, '#action2':action2, '#action3':action3}

createClient()
initGPIO()

# Read the command line arguments
processArgv()

printInfo('rkTwitter starting ...')

# Load the ID of the last tweet read by the application from the file system
loadLastTweetId()

while True:
    tweets = getTweets()
    processTweets(tweets)

    # Wait before to call the API again to avoid being blocked
    time.sleep(sleepDelay)


