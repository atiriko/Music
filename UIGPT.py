import pygame
from typing import List, Dict
import Scheduler
import Record
import Button
import Pianokey
import Colors


activeNotes = []
slidingNotes=[]
topMargin = 100

def drawButtons(screen:pygame.display,events,scheduler:Scheduler.Scheduler):
    # print(events)
    pygame.draw.rect(screen,Colors.buttonBackgroundColor,pygame.rect.Rect(0,0,screen.get_width(),topMargin))
    buttons = []
    startButton = Button.Button(20, topMargin/2-Button.Button.height/2, 'Start', Colors.playButtonColor, Colors.playButtonColorHover, Colors.textColor)
    stopButton = Button.Button(150, topMargin/2-Button.Button.height/2, 'Stop', Colors.stopButtonColor, Colors.stopButtonColorHover, Colors.textColor)
    newsongButton = Button.Button(280, topMargin/2-Button.Button.height/2, 'New Song', Colors.newsongButtonColor, Colors.newsongButtonColorHover, Colors.textColor)
    freeplayButton = Button.Button(410, topMargin/2-Button.Button.height/2, 'Free Play', Colors.freeplayButtonColor, Colors.freeplayButtonColorHover, Colors.textColor)

    midiButton = Button.Button( 540, topMargin/2-Button.Button.height/2, 'Generate Midi',Colors. midiButtonColor, Colors.midiButtonColorHover, Colors.textColor)
    recordButton = Button.Button( 670, topMargin/2-Button.Button.height/2, 'Record Video', Colors.recordButtonColor, Colors.recordButtonColorHover, Colors.textColor)
    buttons.append(freeplayButton)
    buttons.append(recordButton)
    buttons.append(midiButton)
    buttons.append(newsongButton)
    buttons.append(startButton)
    buttons.append(stopButton)
    for button in buttons:
        button.isHover(pygame.mouse.get_pos())

        button.draw(screen)
        if len(events)>0:
            if events[0].type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if button.isHover(pos):
                    button.click(scheduler)


def pianoRoll(game:pygame, screen:pygame.display,events,scheduler):
    keyWidth = 20
    keyLength = 100
    global min,maxNote

    numberOfBlacks = 0
    previousBlack = False
    color = False
    for i in range(0,100):
 

        x = (keyWidth+2)*(i-numberOfBlacks)

        if x > screen.get_width():
            break
        for note in activeNotes:

            #remove is note is done playing
            if pygame.time.get_ticks() > note['endTime']:
                activeNotes.remove(note)
            if i+30 == note['note']:
                if note['channel'] == 1:
                    color = Colors.channel1Color
                elif note['channel'] == 2:
                    color = Colors.channel2Color
                elif note['channel'] == 5:
                    color = Colors.channel5Color
                key = Pianokey.PianoKey(x,screen.get_height()-keyLength,color,note=note)

                #add note to sliding notes if it is not already there
                if key in slidingNotes:
                    break
                if i % 12 == 1 or i % 12 == 3 or i % 12 == 6 or i % 12 == 8 or i % 12 == 10:
                    #black notes
                    key.startX = key.x-key.width/4
                    key.endX = key.x+key.width/4
                    # key.drawBlackKey(screen)
                else:

                    if previousBlack:
                        #previous note was black
                        key.startX = key.x+key.width/4
                        key.endX = key.x+(key.width/2)*2

                    else:
                        #previous note was white
                        key.startX = key.x
                        key.endX = key.x+key.width 
                
                slidingNotes.append(key)

        if i % 12 == 1 or i % 12 == 3 or i % 12 == 6 or i % 12 == 8 or i % 12 == 10:
            if color:
                key = Pianokey.PianoKey(x,screen.get_height()-keyLength,color)
            else:
                key = Pianokey.PianoKey(x,screen.get_height()-keyLength,Colors.BlackKeyColor)
            key.drawBlackKey(screen)
            numberOfBlacks += 1
            previousBlack = True
        else:
            if color:
                key = Pianokey.PianoKey(x,screen.get_height()-keyLength,color)
            else:
                key = Pianokey.PianoKey(x,screen.get_height()-keyLength,Colors.WhiteKeyColor)
            if previousBlack:
                key.drawWhiteKeywherePreviousBlack(screen)
            else:
                key.drawWhiteKey(screen)
            previousBlack = False
        color = False
def showSlidingNotes(game:pygame,screen:pygame.display):
    #loop through the screen width   
    for j,note in enumerate(slidingNotes):
        #move note up
        slidingNotes[j].y -= 4

        #remove note if it is off the screen
        if note.y < 0-note.length*note.note['length']:
            slidingNotes.remove(note)

        #draw the note
        game.draw.rect(screen,note.color,game.rect.Rect(note.startX,
                                             note.y,
                                             note.endX-note.startX,note.length*note.note['length']))
        #draw the border
        game.draw.rect(screen,'black',game.rect.Rect(note.startX,
                                             note.y,
                                             note.endX-note.startX,note.length*note.note['length']),width=1)
     

def getEvents(events,screen,stop_event):
    global running
    for event in events:
        if event:
            # exit
            # print(event)
            if event.type == pygame.QUIT:
                running = False
                stop_event.set()
            # note played
            if 'noteOn' in event.dict:
                if event.dict['noteOn']:
                    activeNotes.append({'note':event.dict['note'],'channel':event.dict['channel'],'length':event.dict['length'],'endTime':event.dict['length']*1000+pygame.time.get_ticks()})
def startUI(scheduler:Scheduler.Scheduler,stop_event):
    global running, min,maxNote
    pygame.init()
    screen = pygame.display.set_mode((990, 600))

    pygame.display.set_icon(pygame.image.load('Assets/music.png'))
    screen.fill(color=Colors.pianoRollBackgroundColor)
    pygame.display.set_caption(title='Composer')
    running = True
    min = scheduler.getMinNote()
    maxNote = scheduler.getMaxNote()

    while running:
        # poll for events
        events = pygame.event.get()
        #background
        screen.fill(color=pygame.color.Color(200,200,200))

        #get notes played for the frame
        getEvents(events,screen,stop_event)
        #draw the piano roll

        
        #draw the sliding notes
        showSlidingNotes(pygame,screen)
        pianoRoll(pygame,screen,events,scheduler)
        drawButtons(screen,events,scheduler)



        pygame.display.flip()

    # Stop recording
    # recording.stopRecording()
    pygame.quit()
    stop_event.set()