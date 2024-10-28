import pygame

class PianoKey:
    def __init__(self, x, y, color,note = None):
        self.x = x
        self.y = y
        self.width = 20
        self.length = 100
        self.color = color
        self.note = note
        self.startX = 0
        self.endX =0
    def __eq__(self, other):
        return self.note == other.note and self.note['endTime'] == other.note['endTime']
    def drawWhiteKeywherePreviousBlack(self, screen:pygame.display):
        self.startX = self.x+self.width/4
        self.endX = self.x+(self.width/2)*2
        topLeft = (self.x+self.width/4,self.y)
        topRight = (self.x+(self.width/2)*2,self.y)
        innerCorner = (self.x+(self.width/4),self.y+self.length/2)
        outerCorner = (self.x,self.y+self.length/2)
        bottomLeft = (self.x,self.y+self.length)
        bottomRight = (self.x+self.width,self.y+self.length)
        points =[topLeft,innerCorner,outerCorner,bottomLeft,bottomRight,topRight]
        pygame.draw.polygon(screen,self.color,points)
        # pygame.draw.line(screen,pygame.Color(20,20,20),(self.x+self.width/4,topMargin),(self.x+self.width/4,screen.get_height()-self.length),1)
    def drawBlackKey(self, screen:pygame.display):
        self.startX = self.x+self.width/4
        self.endX = self.x+self.width/2
        pygame.draw.rect(screen,self.color,pygame.rect.Rect(self.x-self.width/4,self.y,self.width/2,self.length/2))
        # pygame.draw.line(screen,pygame.Color(20,20,20),(self.x-self.width/4-1,topMargin),(self.x-self.width/4-1,screen.get_height()-self.length),1)
    def drawWhiteKey(self, screen:pygame.display):
        self.startX = self.x
        self.endX = self.x+self.width
        pygame.draw.rect(screen,self.color,pygame.rect.Rect(self.x,self.y,self.width,self.length))
        # pygame.draw.line(screen,pygame.Color(20,20,20),(self.x-1,topMargin),(self.x-1,screen.get_height()-self.length),1)
