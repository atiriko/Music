# import os
# os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
# import pygame
import Sheduler
# pygame setup
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
    min = scheduler.getMinNote()
    maxNote = scheduler.getMaxNote()


    for i in range(0,screen.get_width()-keyWidth):

        game.draw.rect(screen,'white',game.rect.Rect(0+(keyWidth+2)*i,
                                                     screen.get_height()-keyLength,
                                                     keyWidth,
                                                     keyLength))

        if i % 7 == 3 or i % 7 == 0:
            game.draw.line(screen,pygame.Color(20,20,20),(0+(keyWidth+2)*i,0),(0+(keyWidth+2)*i,screen.get_height()),1)

        for note in activeNotes:
            if pygame.time.get_ticks() > note['endTime']:
                activeNotes.remove(note)
                # note['y'] = screen.get_height()-keyLength
                # slidingNotes.append(note)
            if not note in slidingNotes:
                note['y'] = screen.get_height()-keyLength 
                slidingNotes.append(note)
            if i + min - (min%7) == note['note']:
                if note['channel'] == 1:
                    color = 'red'
                elif note['channel'] == 2:
                    color = 'blue'
                elif note['channel'] == 5:
                    color = 'green'
                #note
                game.draw.rect(screen,color,game.rect.Rect(0+(keyWidth+2)*i,
                                                     screen.get_height()-keyLength,
                                                     keyWidth+2,
                                                     (keyLength)))
                #noteBorder
                game.draw.rect(screen,'black',game.rect.Rect(0+(keyWidth+2)*i,
                                                     screen.get_height()-keyLength,
                                                     keyWidth+2,
                                                     (keyLength)),width=1)
    for i in range(0,screen.get_width()-keyWidth):
        if i % 7 == 0 or i % 7 == 1 or i % 7 == 3 or i % 7 == 4 or i % 7 == 5:
            game.draw.rect(screen,'black',game.rect.Rect((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4,
                                                     screen.get_height()-keyLength,
                                                     keyWidth/2+2,
                                                     keyLength/2))
            game.draw.line(screen,pygame.Color(20,20,20),((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4,0),((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4,screen.get_height()-keyLength),1)
            game.draw.line(screen,pygame.Color(20,20,20),(((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4)+keyWidth/2,0),(((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4)+keyWidth/2,screen.get_height()-keyLength),1)

def showSlidingNotes(game:pygame,screen:pygame.display):
    for i in range(0,screen.get_width()-keyWidth):
   
        for j,note in enumerate(slidingNotes):
            slidingNotes[j]['y'] -= 0.005
            if note['y'] < 0-keyLength*note['length']:
                slidingNotes.remove(note)

            if i + min - (min%7) == note['note']:
                if note['channel'] == 2:
                    color = 'blue'
                elif note['channel'] == 1:
                    color = 'red'
                elif note['channel'] == 5:
                    color = 'green'
                game.draw.rect(screen,color,game.rect.Rect(0+(keyWidth+2)*i,
                                                     note['y'],
                                                     keyWidth+2,keyLength*note['length']))
                game.draw.rect(screen,'black',game.rect.Rect(0+(keyWidth+2)*i,
                                                     note['y'],
                                                     keyWidth+2,keyLength*note['length']),width=1)
                # game.draw.line(screen,pygame.Color(10,10,10),(0,note['y']),(screen.get_width(),note['y']))
                
    # for i in range(0,screen.get_width()-keyWidth):
lastTime = -1
def showSlidingLines(game:pygame,screen:pygame.display,scheduler:Sheduler.Sheduler, events):
    # print(game.time.get_ticks())
    global lastTime
    # print(scheduler.time)
    if scheduler.time % scheduler.tempo.quarter == 0 and scheduler.time != lastTime:
        slidingBeats.append({'y':screen.get_height()-keyLength + 30})
        lastTime = scheduler.time
    # print(scheduler.tempo.thirtysecond)
    for i,beat in enumerate(slidingBeats):
        # slidingBeats[i]['y'] -= 0.005
        slidingBeats[i]['y'] -= 4.95


        game.draw.line(screen,pygame.Color(10,10,10),(0,beat['y']),(screen.get_width(),beat['y']))
        # slidingBeats[i]['y'] = slidingBeats[i]['y'] - 5

        if beat['y'] < 0:
            slidingBeats.remove(beat)
        
def getEvents(events,screen,stop_event):
    global running
    for event in events:
        if event:
            if event.type == pygame.QUIT:
                running = False
                stop_event.set()
            # if 'beat' in event.dict:
            #     slidingBeats.append({'y':screen.get_height()-keyLength})
            if 'noteOn' in event.dict:

                if event.dict['noteOn']:
                    activeNotes.append({'note':event.dict['note'],'channel':event.dict['channel'],'length':event.dict['length'],'endTime':event.dict['length']*1000+pygame.time.get_ticks()})
def startUI(scheduler:Sheduler.Sheduler,stop_event):
    global running
    pygame.init()
    screen = pygame.display.set_mode((990, 600))

    screen.fill(color=pygame.color.Color(200,200,200))
    pygame.display.set_caption(title='Simple Piano')
    clock = pygame.time.Clock()
    running = True
    dt = 0
    while running:
        # poll for events
        events = pygame.event.get()
        
        screen.fill(color=pygame.color.Color(200,200,200))
        getEvents(events,screen,stop_event)
        pianoRoll(pygame,screen,events,scheduler)
        showSlidingNotes(pygame,screen)
        # showSlidingLines(pygame,screen,scheduler,events)


        # flip() the display to put your work on screen
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        # dt = clock.tick(60) / 1000

    pygame.quit()