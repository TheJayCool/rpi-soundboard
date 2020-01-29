import RPi.GPIO as GPIO
import lcd1602 as display
from time import sleep
# import simpleaudio as sa
import subprocess
from os import listdir, openpty, write
import threading
import pty
import pprint

"""
Last updated: 29-Jan-2020
"""

# ---- Button handling
BtnPin1 = 21
BtnPin2 = 20
BtnPin3 = 16
CLKPin = 26
DTPin = 19
REBtnPin = 13

# ---- Defaults
defaultId = 0

# ---- Commands
commands = {
    "previous": [1],
    "next": [3],
    "select": [2],
    "reload": [1, 3],
    "bomb": [1, 2, 3],
    "volume down": ['left turn'],
    "volume up": ['right turn'],
    "save volume": [4],
    "clearText": [2, 3]
}

def getSoundsList():
    """
    Sound list setup
    """
    soundsListTemp = listdir("sounds")
    global soundsList
    soundsList = []
    volume = 100

    for sound in soundsListTemp:
        volume = 100
        volumesFile = open('volumes.txt')
        for line in volumesFile:
            if '=' in line:
                fileNameCursor, savedVolume = line.split('=')
                if sound == fileNameCursor:
                    volume = int(savedVolume)


        soundsList.append(dict(volume=volume,
                               fileName=sound,
                               isPlaying=False,
                               filePath='/home/pi/scripts/soundboard/sounds/%s' % sound,
                               process=None,
                               master=None,
                               slave=None))

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(soundsList)
    print("Sounds: %s\n" % len(soundsList))


def setup():
    """
    GPIO, LCD, Rotary Encoder Setup
    Run getSoundsList function
    """
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(BtnPin1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BtnPin2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BtnPin3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(REBtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CLKPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DTPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(REBtnPin, GPIO.FALLING, callback=saveButton)

    global clkLastState
    clkLastState = GPIO.input(CLKPin)

    global lcd
    lcd = display.LCD()
    lcd.clear()

    global currentId
    currentId = defaultId

    print("Yo, if you're using this and you don't know what each part of the code does, stop right now.\n")
    global soundsList
    getSoundsList()

def reload():
    """
    Reload function
    """
    getSoundsList()
    global currentId
    currentId = defaultId
    displayMsg(nameHandling(defaultId), "ID: %s, Reloaded." % defaultId)
    print("\nReloaded!\n")

def playSound(id):
    """
    Plays sound/song file based on given id
    Uses subprocess to open mpg123 in background and attaches it to a master and slave virtual terminal (pty)
    """
    global soundsList
    filePath = soundsList[id]['filePath']
    if soundsList[id]['isPlaying'] == True:
        soundsList[id]['process'].kill()
        soundsList[id]['process'] = None
        soundsList[id]['isPlaying'] = False
    else:
        soundsList[id]['master'], soundsList[id]['slave'] = openpty()

        soundsList[id]['process'] = subprocess.Popen(['mpg123', '-C', filePath], stdin=soundsList[id]['master'])
        if soundsList[id]['volume'] != 100:
            write(soundsList[id]['slave'], b's')
            volDiff = (100 - soundsList[id]['volume']) / 2
            for i in range(0, int(round(volDiff))):
                write(soundsList[id]['slave'], b'-')
            write(soundsList[id]['slave'], b's')

        displayMsg(nameHandling(currentId), "ID: %s, Playing." % currentId)
        print("now playing")
        soundsList[id]['isPlaying'] = True

        soundsList[id]['process'].wait()

        displayMsg(nameHandling(currentId), "ID: %s, Done." % currentId)
        print("now done")
        soundsList[id]['isPlaying'] = False

def displayMsg(firstLine, secondLine=""):
    """
    function for displaying text on lcd screen
    it just sends the text to lcd.message() reeeeeeeeeeeee
    """
    msg = "{0}\n{1}".format(firstLine, secondLine)
    lcd.clear()
    lcd.message(msg)

def destroy():
    """
    Destroy everything one by one
    """
    lcd.clear()
    GPIO.cleanup()

def nameHandling(id):
    """
    Turns id to display name
    """
    global soundsList
    sound = soundsList[id]
    fileName = soundsList[id]['fileName'][:soundsList[id]['fileName'].find(".")]
    if len(fileName) > 16:
        displayName = (fileName[:14] + "..")
    else:
        displayName = fileName

    print(displayName)
    return(displayName)

def command(presses):
    """
    Deals with all the commands, turns presses into a string command using the commands dict
    specified at the start of the file
    """
    global currentId
    global soundsList

    for command, sequence in commands.items():
        if presses == sequence:
            print(command, sequence)
            playingText = ""

            if command == "clearText":
                lcd.clear()

            if command == "previous":
                if currentId != 0:
                    currentId += -1
                    if soundsList[currentId]['isPlaying'] == True:
                        playingText = ", Playing."
                displayMsg(nameHandling(currentId), "ID: {0}{1}".format(currentId, playingText))

            elif command == "next":
                if currentId != len(soundsList)-1:
                    currentId += 1
                    if soundsList[currentId]['isPlaying'] == True:
                        playingText = ", Playing."
                displayMsg(nameHandling(currentId), "ID: {0}{1}".format(currentId, playingText))

            elif command == "select":
                t = threading.Thread(target=playSound, args=(currentId,))
                t.start()

            elif command == "reload":
                reload()

            elif command == "bomb":
                for i in reversed(range(1,5)):
                    displayMsg("Shutdown in:", "%s seconds" % i)
                    # displayMsg("Self destruct", "in: %s seconds" % i)
                    sleep(1)
                # line = 0
                # text = ["just kidding.", "...shutting down"]
                # for i in range(1, len(text[0]) + len(text[1]) + 1):
                #     if i == len(text[0]):
                #         line += 1
                #     if line == 1:
                #         displayMsg(text[0], text[1][:i-len(text[0])])
                #     else:
                #         displayMsg(text[0][:i])
                #     sleep(0.5)
                subprocess.call("sudo shutdown -h now", shell=True)

            elif command == 'save volume':

                volumesFile = open('volumes.txt', 'a')
                print('\n{}={}'.format(soundsList[currentId]['fileName'], soundsList[currentId]['volume']))

                volumesFile.write('{}={}\n'.format(soundsList[currentId]['fileName'], soundsList[currentId]['volume']))
                displayMsg(nameHandling(currentId), "ID: {0}, Saved Vol".format(currentId))

            elif 'volume' in command and soundsList[currentId]['isPlaying']:
                if command == "volume down":
                    if soundsList[currentId]['volume'] > 1:
                        write(soundsList[currentId]['slave'], b'-')
                        soundsList[currentId]['volume'] -= 2
                elif command == "volume up":
                    if soundsList[currentId]['volume'] < 999:
                        write(soundsList[currentId]['slave'], b'+')
                        soundsList[currentId]['volume'] += 2
                displayMsg(nameHandling(currentId), "ID: {0}, Vol: {1}".format(currentId, soundsList[currentId]['volume']))


def saveButton(ev=None):
    """
    callback function for the rotary encoder button
    what the fuck is this
    """
    command([4])

def buttonPressEv():
    """
    deals with the buttons
    and rotary encoder
    """
    presses = []
    global clkLastState
    global volume
    global soundsList
    while True:
        clkState = GPIO.input(CLKPin)
        dtState = GPIO.input(DTPin)

        if GPIO.input(BtnPin1) == True: # previous sound
            presses.append(1)
            sleep(0.15)

        if GPIO.input(BtnPin2) == True: # play sound
            presses.append(2)
            sleep(0.2)

        if GPIO.input(BtnPin3) == True: # next sound
            presses.append(3)
            sleep(0.15)

        # if CLK and DT are not the same: a turn has been made.
        if clkState != dtState:
            if clkLastState != clkState:
                presses.append('left turn')
            elif clkLastState == clkState:
                presses.append('right turn')
        clkLastState = clkState
        command(presses)
        presses.clear()

if __name__ == '__main__':
    """
    runs the actual thing
    """
    setup()
    displayMsg(nameHandling(defaultId), "ID: %s" % defaultId)
    windowsBootPath = '/home/pi/scripts/soundboard/windowsXPBoot.mp3'
    subprocess.Popen(['mpg123', windowsBootPath, "&"])
    try:
        buttonPressEv()
    except:
        destroy()
