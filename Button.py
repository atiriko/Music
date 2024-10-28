import pygame
import pygame.gfxdraw
import Record   
import Scheduler
class Button:
    width = 100
    height = 50
    def __init__(self, x, y, text, color, hoverColor, textColor, action=None):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.hoverColor = hoverColor
        self.textColor = textColor
        self.action = action
        self.rect = pygame.rect.Rect(x, y, self.width, self.height)
        self.hover = False

    def draw(self, screen:pygame.display):
        if self.hover:
            self.draw_rounded_rect(screen, self.rect, self.hoverColor, int(self.height/2))
            # pygame.draw.rect(screen, self.hoverColor, self.rect,border_radius=int(self.height/2))
        else:
            self.draw_rounded_rect(screen, self.rect, self.color, int(self.height/2))
            # pygame.draw.rect(screen, self.color, self.rect,border_radius=int(self.height/2))
        font = pygame.font.Font(None, 32)
        text = font.render(self.text, True, self.textColor)
        if text.get_width() > self.width-20:
            font = pygame.font.Font(None, 16)
            text = font.render(self.text, True, self.textColor)
        textRect = text.get_rect()
        text.get_width
        textRect.center = (self.x+self.width/2, self.y+self.height/2)
        screen.blit(text, textRect)

    def isHover(self, pos):
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                self.hover = True
                return True
        self.hover = False
        return False
    def draw_rounded_rect(self,surface, rect, color, corner_radius):
        ''' Draw a rectangle with rounded corners.
        Would prefer this: 
            pygame.draw.rect(surface, color, rect, border_radius=corner_radius)
        but this option is not yet supported in my version of pygame so do it ourselves.

        We use anti-aliased circles to make the corners smoother
        '''
        if rect.width < 2 * corner_radius or rect.height < 2 * corner_radius:
            raise ValueError(f"Both height (rect.height) and width (rect.width) must be > 2 * corner radius ({corner_radius})")

        # need to use anti aliasing circle drawing routines to smooth the corners
        pygame.gfxdraw.aacircle(surface, rect.left+corner_radius, rect.top+corner_radius, corner_radius, color)
        pygame.gfxdraw.aacircle(surface, rect.right-corner_radius-1, rect.top+corner_radius, corner_radius, color)
        pygame.gfxdraw.aacircle(surface, rect.left+corner_radius, rect.bottom-corner_radius-1, corner_radius, color)
        pygame.gfxdraw.aacircle(surface, rect.right-corner_radius-1, rect.bottom-corner_radius-1, corner_radius, color)

        pygame.gfxdraw.filled_circle(surface, rect.left+corner_radius, rect.top+corner_radius, corner_radius, color)
        pygame.gfxdraw.filled_circle(surface, rect.right-corner_radius-1, rect.top+corner_radius, corner_radius, color)
        pygame.gfxdraw.filled_circle(surface, rect.left+corner_radius, rect.bottom-corner_radius-1, corner_radius, color)
        pygame.gfxdraw.filled_circle(surface, rect.right-corner_radius-1, rect.bottom-corner_radius-1, corner_radius, color)

        rect_tmp = pygame.Rect(rect)
        rect_tmp.height = rect_tmp.height + 2

        rect_tmp.width -= 2 * corner_radius
        rect_tmp.center = rect.center
        pygame.draw.rect(surface, color, rect_tmp)

        rect_tmp.width = rect.width
        rect_tmp.height -= 2 * corner_radius
        rect_tmp.center = rect.center
        pygame.draw.rect(surface, color, rect_tmp)
    def click(self,scheduler:Scheduler.Scheduler):
        print('clicked' + self.text)
        if self.text == 'Record Video':
            recording = Record.Record()
            recording.startRecording()
        elif self.text == 'Generate Midi':
            pass

        elif self.text == 'Free Play':

            scheduler.freeplay()
        elif self.text == 'Stop':

            scheduler.stop()
        elif self.text == 'Start':
            scheduler.start()

