import contextlib
with contextlib.redirect_stdout(None):
    import pygame
import Scheduler
import Record
activeNotes = []
slidingNotes = []
slidingBeats=[]
keyWidth = 20
keyLength = 100
min = 0
maxNote = 0
running = True
def pianoRoll(game:pygame, screen:pygame.display,events,scheduler):
    global min,maxNote

    for i in range(0,screen.get_width()-keyWidth):
        x = (keyWidth+2)*i
        y = screen.get_height()-keyLength
        #white notes
        game.draw.rect(screen,'white',game.rect.Rect(x,
                                                     y,
                                                     keyWidth,
                                                     keyLength))
        # Lines for the keys without sharps
        if i % 7 == 3 or i % 7 == 0:
            game.draw.line(screen,pygame.Color(20,20,20),(x-1,0),(x-1,y),1)

        for note in activeNotes:

            #remove is note is done playing
            if pygame.time.get_ticks() > note['endTime']:
                activeNotes.remove(note)
            #add note to sliding notes if it is not already there
            if not note in slidingNotes:
                note['y'] = screen.get_height()-keyLength 
                slidingNotes.append(note)
            #if index of the loop corresponds to the note
            if i + min - (min%7) == note['note']:
                if note['channel'] == 1:
                    color = 'red'
                elif note['channel'] == 2:
                    color = 'blue'
                elif note['channel'] == 5:
                    color = 'green'
                #note
                game.draw.rect(screen,color,game.rect.Rect(x,
                                                     y,
                                                     keyWidth+2,
                                                     (keyLength)))
                #noteBorder
                game.draw.rect(screen,'black',game.rect.Rect(x,
                                                     y,
                                                     keyWidth+2,
                                                     (keyLength)),width=1)
    for i in range(0,screen.get_width()-keyWidth):
        if i % 7 == 0 or i % 7 == 1 or i % 7 == 3 or i % 7 == 4 or i % 7 == 5:
            #black notes
            game.draw.rect(screen,'black',game.rect.Rect((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4,
                                                     screen.get_height()-keyLength,
                                                     keyWidth/2+2,
                                                     keyLength/2))
            #black note vertical lines
            game.draw.line(screen,pygame.Color(20,20,20),((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4,0),((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4,screen.get_height()-keyLength),1)
            game.draw.line(screen,pygame.Color(20,20,20),(((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4)+keyWidth/2,0),(((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4)+keyWidth/2,screen.get_height()-keyLength),1)

def showSlidingNotes(game:pygame,screen:pygame.display):
    #loop through the screen width
    for i in range(0,screen.get_width()-keyWidth):
   
        for j,note in enumerate(slidingNotes):
            #move note up
            slidingNotes[j]['y'] -= 0.005

            #remove note if it is off the screen
            if note['y'] < 0-keyLength*note['length']:
                slidingNotes.remove(note)

            #if index of the loop corresponds to the note
            if i + min - (min%7) == note['note']:
                #set color based on channel
                if note['channel'] == 2:
                    color = 'blue'
                elif note['channel'] == 1:
                    color = 'red'
                elif note['channel'] == 5:
                    color = 'green'
                #draw the note
                game.draw.rect(screen,color,game.rect.Rect(0+(keyWidth+2)*i,
                                                     note['y'],
                                                     keyWidth+2,keyLength*note['length']))
                #draw the border
                game.draw.rect(screen,'black',game.rect.Rect(0+(keyWidth+2)*i,
                                                     note['y'],
                                                     keyWidth+2,keyLength*note['length']),width=1)
                

        
def getEvents(events,screen,stop_event):
    global running
    for event in events:
        if event:
            # exit
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

    screen.fill(color=pygame.color.Color(200,200,200))
    pygame.display.set_caption(title='Simple Piano')
    running = True
    min = scheduler.getMinNote()
    maxNote = scheduler.getMaxNote()
    # Screen Recording
    # recording = Record.Record()
    # recording.startRecording()
    while running:
        # poll for events
        events = pygame.event.get()
        #background
        screen.fill(color=pygame.color.Color(200,200,200))

        #get notes played for the frame
        getEvents(events,screen,stop_event)
        #draw the piano roll
        pianoRoll(pygame,screen,events,scheduler)
        #draw the sliding notes
        showSlidingNotes(pygame,screen)


        pygame.display.flip()

    # Stop recording
    # recording.stopRecording()
    pygame.quit()
    stop_event.set()