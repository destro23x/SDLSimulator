import lxml.etree as ET
import io
import pygame
from ctypes import windll
import random
import math
import Queue
import string

BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)
RED      = ( 255,   0,   0)
BLUE     = (   0,   0, 255)

TYPES = set(['start', 'input', 'output', 'state', 'task', 'condition'])

class Entry():
    def __init__(self, id, type, entry):
        self.id = id
        self.type = type
        self.entry = entry

# Represent connection inside process - for example between two states
class ProcessConnection():
    def __init__(self, id, sourceId, targetId):
        self.id = id
        self.sourceId = sourceId
        self.targetId = targetId
        #self.inputQueue = Queue(maxsize=20)

    def logic(self):
        while (true):
            if not self.inputQueue.empty():
                item = inputQueue.get()
                #musze zdefiniowac sygnaly
                #do_work(item)
                #q.task_done()


        #jezeli kolejka niepusta to

# Represent connection inside block - between process
class BlockConnection():
    def __init__(self, name, id, sourceId, targetId, sourcesl, targetsl, twoway):
        self.name = name
        self.id = id
        self.sourceId = sourceId
        self.targetId = targetId
        self.sourcesl = {}
        self.targetsl = {}

        for signal in string.split(sourcesl,","):
            parenthesis = signal.find("(")
            if parenthesis == -1:
                self.sourcesl[signal] = []
            else:
                self.sourcesl[signal[:parenthesis]] = [param for param in string.split(signal[parenthesis+1:-1].replace(" ",""),",")]


        print self.sourcesl
        print self.targetsl
        self.twoway = twoway

# This class represent Process
class Process(pygame.sprite.Sprite):
    def __init__(self, name, id, SITOList, processConnectionList ):
        pygame.sprite.Sprite.__init__(self)
        self.name = name
        self.id = id
        self.SITOList = SITOList
        self.processConnectionList = processConnectionList
        self.actualState = 'start'
        self.inputQueue = Queue.Queue()

        # To draw on the screen
        self.height = 50
        self.width = 2 * self.height
        self.r = 10

        self.click = False
        self.image = pygame.Surface([self.width, self.height], pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 0))
        self.rect = self.image.get_rect()

        #Draw process as STOP sign
        pygame.draw.polygon(self.image, BLACK, self.polygonPoints(), 0)

        #Display process name on the center of circle
        font = pygame.font.Font(None, 30)
        text = font.render(self.name, True, WHITE)
        textpos = text.get_rect()
        textpos.center = self.image.get_rect().center
        self.image.blit(text, textpos)

    def update(self, surface):
        if self.click:
            self.rect.center = pygame.mouse.get_pos()

    def polygonPoints(self):
        pointList = []
        pointList.append([self.rect.centerx - self.width/2 + self.r, self.rect.centery + self.height/2])
        pointList.append([self.rect.centerx - self.width/2, self.rect.centery + self.height/2 - self.r])
        pointList.append([self.rect.centerx - self.width/2, self.rect.centery - self.height/2 + self.r])
        pointList.append([self.rect.centerx - self.width/2 + self.r, self.rect.centery - self.height/2])
        pointList.append([self.rect.centerx + self.width/2 - self.r, self.rect.centery - self.height/2])
        pointList.append([self.rect.centerx + self.width/2, self.rect.centery - self.height/2 + self.r])
        pointList.append([self.rect.centerx + self.width/2, self.rect.centery + self.height/2 - self.r])
        pointList.append([self.rect.centerx + self.width/2 - self.r, self.rect.centery + self.height/2])
        return pointList

class Message(pygame.sprite.Sprite):
    """ Message from one process to another process """
    def __init__(self, source, destination, message): #source is a point of the source process destination is a point of the destination process, text is the content message
        pygame.sprite.Sprite.__init__(self)
        self.source = source
        self.destination = destination
        self.angle_in_radian = math.atan2(destination.rect.centery - source.rect.centery,destination.rect.centerx - source.rect.centerx)
        self.delivered = False
        self.message = message

        #Generate Message surface
        self.image = pygame.Surface([40, 20]) #,pygame.SRCALPHA
        self.image.fill((255,255,255,0))#128
        self.rect = self.image.get_rect()
        pygame.draw.rect(self.image, BLACK, self.rect, 1)
        font = pygame.font.Font(None, 15)
        text = font.render(message, True, BLACK)
        textpos = text.get_rect()
        textpos.center = self.image.get_rect().center
        self.image.blit(text, textpos)

        self.rect.centerx = source.rect.centerx
        self.rect.centery = source.rect.centery

        self.pos = [self.rect.centerx, self.rect.centery]

    def update(self, surface, speed=1.0):
        self.pos[0] += math.cos(self.angle_in_radian) * speed
        self.pos[1] += math.sin(self.angle_in_radian) * speed

        if abs(self.destination.rect.centerx - self.rect.centerx) < 2 and abs(self.destination.rect.centery - self.rect.centery) < 2 :
            self.delivered = True
            self.destination.inputQueue.put(self.message)
            self.kill()

        self.rect.centerx = self.pos[0]
        self.rect.centery = self.pos[1]
        surface.blit(self.image,self.rect)

# This class parse xml file from SDLSuite tool and generate new Process instances. The main response of this class is
# create reaction tables for each Process.
class ParseXml():
    def __init__(self, nameFile):
        self.nameFile = nameFile

    def parse(self):
        content = io.FileIO(self.nameFile, mode='r', closefd=True)
        context = ET.iterparse(content, tag=('block_process', 'block_connection'))
        context = iter(context)
        processList = []
        blockConnectionList = []
        for action, elem in context:
            if elem.tag == 'block_process':
                processName = elem.xpath('name/text()')[0]
                processId = elem.xpath('iID/text()')[0]
                processConnectionList = []
                SITOList = [] # Table of state, input, output, task

                for type in TYPES:
                    for name, id in zip(elem.xpath('process_children/process_'+type+'/name/text()'),
                                        elem.xpath('process_children/process_'+type+'/iID/text()')):
                        SITOList.append(Entry(id, type, name))

                for id, sourceId, targetId in zip(elem.xpath('process_children/process_connection/iID/text()'),
                                                  elem.xpath('process_children/process_connection/sourceIID/text()'),
                                                  elem.xpath('process_children/process_connection/targetIID/text()')):
                        processConnectionList.append(ProcessConnection(id, sourceId, targetId))

                # Print SITO List for process
                # print processName
                # for sito in SITOList:
                #      print sito.id + " " + sito.type + " " + sito.entry

                # Print Connection inside process
                # for pc in processConnectionList:
                #      print pc.id + " " + pc.sourceId + " " + pc.targetId

                x = Process(processName, processId, SITOList,  processConnectionList)
                #hashmap = {'key': processId, 'value': x}
                processList.append(x)
            elif elem.tag == 'block_connection':
                 blockConnectionList.append(BlockConnection(elem.xpath('name/text()')[0],
                                                           elem.xpath('iID/text()')[0],
                                                           elem.xpath('sourceIID/text()')[0],
                                                           elem.xpath('targetIID/text()')[0],
                                                           elem.xpath('sourcesl/text()')[0].replace(" ",""),
                                                           elem.xpath('targetsl/text()')[0].replace(" ",""),
                                                           elem.xpath('twoway/text()')[0]))
            elem.clear()
        return {'process': processList,
                'connections': blockConnectionList}

        # Print Connection between process
        # for bc in blockConnectionList:
        #     print bc.name + " " + bc.id + " " + bc.sourceId + " " + bc.targetId + " " + bc.twoway

def main():
    parser = ParseXml("plik2.sdl")
    pygame.init()
    parseResult = parser.parse()
    processList = parseResult['process']
    blockConnectionList = parseResult['connections']
    processes_group = pygame.sprite.Group()
    screen = pygame.display.set_mode((windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)))#, pygame.FULLSCREEN)
    for process in processList:
        conflict = True
        while (conflict == True):
            x = random.randrange(screen.get_width()) #centerx
            y = random.randrange(screen.get_height()) #centery

            if( x > (screen.get_width() - process.width/2)):
                 x = screen.get_width() - process.width/2

            if( x < process.width/2 ):
                 x = process.width/2

            if( y > (screen.get_height() - process.height/2) ):
                y = screen.get_height() - process.height/2

            if( y < process.height/2 ):
                y = process.height/2

            for p in processList:
                print "Wylosowany " + str(x) + "Byty " + str(p.rect.x)
                print "Wylosowany " + str(y) + "Byty " + str(p.rect.y)
                if ( y > p.rect.centery + p.height/2 + 50 or y < p.rect.centery - p.height/2 - 50 and x > p.rect.centerx + p.width/2 + 75 or x < p.rect.centerx - p.width/2 - 75):
                    conflict = False
                else:
                    conflict = True
                    break
        process.rect.centerx = x
        process.rect.centery = y
        processes_group.add(process)

    message = Message(processList[0], processList[1], "Siema")
    processes_group.add(message)

    done = False
    #Used to manage how fast the screen updates
    clock = pygame.time.Clock()
    while not done:
        clock.tick(1800)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE ):
                done = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for process in processes_group:
                    if process.rect.collidepoint(event.pos):
                        process.click = True
            elif event.type == pygame.MOUSEBUTTONUP:
                for process in processes_group:
                    if process.click == True:
                        process.click = False
        screen.fill(WHITE)
        for process in processes_group:
            process.update(screen)
        for line in blockConnectionList:
            for process in processList:
                if (line.sourceId == process.id):
                    source = process.rect.center
                if (line.targetId == process.id):
                    target = process.rect.center
            pygame.draw.line(screen, BLACK, source, target, 1)
        processes_group.draw(screen)
        pygame.display.flip()
    for process in processList:
        print process.name
        while not process.inputQueue.empty():
            print process.inputQueue.get()
    pygame.quit()

main()
