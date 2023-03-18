import cv2
import pygame 
import random 
import time
import os 
pygame.font.init() 
width = 1280
height = 720
cam = cv2.VideoCapture(0,cv2.CAP_DSHOW)
cam.set(cv2.CAP_PROP_FRAME_WIDTH,width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
cam.set(cv2.CAP_PROP_FPS, 30)
cam.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG') )

# myPose=mp.solutions.pose.Pose(False,False,True,.5,.5)
# poseDraw=mp.solutions.drawing_utils

#0
initPosZ=[-100,10,1000,1000]

class mpFace():
    import mediapipe as mp 
    def __init__(self):
        self.faces=self.mp.solutions.face_detection.FaceDetection()

    def parseFace(self,frame):
        frameRGB=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        results=self.faces.process(frameRGB)
        locations=[]
        if results.detections!=None:
            for face in results.detections:
                faceBox=face.location_data.relative_bounding_box
                topLeft=(int(faceBox.xmin*width),int(faceBox.ymin*height))
                botRight=(int((faceBox.xmin+faceBox.width)*width),int((faceBox.ymin+faceBox.height)*height))
                dataList=[topLeft,botRight]
                locations.append(dataList)
        return locations 

class handDetection:
    import mediapipe as mp 
    def __init__(self,maxhands=2,tol1=0.5,tol2=0.5,static=False):
        self.hands=self.mp.solutions.hands.Hands(static,maxhands,model_complexity=1,min_detection_confidence=tol1,
        min_tracking_confidence=tol2)

    def landmarkse(self,frame):
        frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        results=self.hands.process(frame)
        bothHands=[]
        handType=[]
        if results.multi_hand_landmarks!=None: 
            for hand in results.multi_handedness:
                handType.append(hand.classification[0].label)
            for hand in results.multi_hand_landmarks: 
                allHand=[]
                for landmark in hand.landmark:
                    allHand.append((int(landmark.x*width),int(landmark.y*height)))
                bothHands.append(allHand)
        return bothHands,handType         

def shoot_detection(handLandmarks,type,hand_side='Left'):
    left_hand=False 
    right_hand=False 
    if len(handLandmarks)>=1:
        for hand,side in zip(handLandmarks,type):
            if side=='Left':
                handSize=hand[8][1]-hand[20][1]
                middle_fing=hand[12][0]
                index_fing=hand[8][0]
                #print(abs(middle_fing-index_fing))
                #print(abs((middle_fing-index_fing)/handSize))
                try:
                    if abs((middle_fing-index_fing)/handSize)>=0.6:
                        right_hand=True  
                except:
                    right_hand=False 
            if side=='Right':
                handSize=hand[8][1]-hand[20][1]
                middle_fing=hand[12][0]
                index_fing=hand[8][0]
                #print(abs(middle_fing-index_fing))
                #print(abs((middle_fing-index_fing)/handSize))
                try:
                    if abs((middle_fing-index_fing)/handSize)>=0.6:
                        left_hand=True  
                except:
                    left_hand=False   
    return left_hand,right_hand        

class sprites:
    from pygame import mixer 
    mixer.init()
    def __init__(self,imageList):
        self.images=[]
        for image in imageList:
            self.images.append(image)
        self.firstRun=True 
        self.index=0
        self.image=self.images[self.index]
        self.is_spawning=True 
        self.spawn_complete=False 
        self.pos=[100,100]
    #Death animation for the sprite 
    def death_animation(self,surface):
        self.index+=1
        if self.index==1:
            sound=self.mixer.Sound('Sounds\\explosion.mp3')
            self.mixer.Sound.play(sound)
        if self.index>=len(self.images):
            self.index=0
            self.is_spawning=True 
            self.firstRun=True 
            self.spawn_complete=False 
        self.image=self.images[self.index]
        surface.blit(self.image,self.pos)
    #Spawn sprite
    def spawn_sprite(self,surface):
        if self.is_spawning:
            if self.firstRun:
                self.pos=[random.randint(300,980),random.randint(200,520)]
                self.firstRun=False 
            self.image=self.images[0]
            surface.blit(self.image,self.pos)
            self.spawn_complete=True 
    #Checks if bullet shot hits the target
    def bullet_pos(self,gun_shot_pos,width=200,height=200):

        if self.pos[0]<=gun_shot_pos[0]<=self.pos[0]+width:
            if self.pos[1]<=gun_shot_pos[1]<=self.pos[1]+height:
                return True 
    #Combine all the methods in this class together 
    def complete_draw(self,surface,gun_shot,gun_shot_pos):
        if gun_shot and self.bullet_pos(gun_shot_pos):
            if self.spawn_complete:
                self.is_spawning=False 
        if not self.is_spawning:
            self.death_animation(surface)
        elif self.is_spawning:
            self.spawn_sprite(surface)
#Draw text on the screen
def textRender(string,color,surface,scorePos,size):

    font=pygame.font.SysFont('arial',size)
    render=font.render(string,1,color)
    surface.blit(render,scorePos)

class dodge_shots():
    def __init__(self):
        self.first_run=True 
        self.firing=False 
        self.start_time=time.time()
        self.death_places={'left':[[0,0],[width/2,height]],'right':[[width/2,0],[width,height]],
        'bot':[[0,height/2],[width,height]],'top':[[0,0],[width/2,height/2]]}

        self.death_places_text={'left':"Dodge to the right!",'right':"Dodge to the left!",
        'bot':"Keep your head up!",'top':"Duck down!"} 

    def choose_fire(self,surface,face_locations):
        if self.first_run:
            self.choices=['left','right','bot','top',None]
            self.choice=self.choices[random.randint(0,len(self.choices)-1)]
            self.start_time=time.time()
            self.first_run=False 
            print(self.choice)
        if self.choice!=None:
            textRender(self.death_places_text[self.choice],(0,0,0),surface,[100,200],75)
        if time.time()-self.start_time>=5:
            print('here')
            self.start_time=time.time()
            if self.choice!=None:
                for faceo in face_locations:
                    top_left_face=faceo[0]
                    bot_right_face=faceo[1]
                    face_center=[(top_left_face[0]+bot_right_face[0])/2,(top_left_face[1]+bot_right_face[1])/2]
                    top_left_zone=self.death_places[self.choice][0]
                    top_right_zone=self.death_places[self.choice][1]

                    if 1280-top_left_zone[0]>=face_center[0]>=1280-top_right_zone[0]:
                        if top_left_zone[1]<=face_center[1]<=top_right_zone[1]:
                            return True  
            return False 
        return None  
    
    def run_all(self,surface,face_locations):
        run_alg=self.choose_fire(surface,face_locations)
        if run_alg!=None:
            if run_alg:
                return True 
            self.first_run=True 
        
#Sequence of images when bat is shot
batList=[        
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack01.png'),(200,200)),
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack02.png'),(200,200)),
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack03.png'),(200,200)),
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack04.png'),(200,200)),
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack05.png'),(200,200)),
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack06.png'),(200,200)),
    pygame.transform.smoothscale(pygame.image.load('Enemy01\\attack07.png'),(200,200)),
]
os.environ['SDL_VIDEO_WINDOW_POS']='%d,%d'%(10,30)

my_bat=sprites(batList)
myHands=handDetection()
myFace=mpFace()

clock = pygame.time.Clock()  #Force frame rate to be slower
# Create surface of (width, height), and its window.
mainSurface = pygame.display.set_mode((width, height))
time.sleep(2)
os.environ['SDL_VIDEO_WINDOW_POS']='%d,%d'%(10,30)

mainSurface = pygame.display.set_mode((width-1, height-1))
mainSurface = pygame.display.set_mode((width, height))

dodges=dodge_shots()
circleCol=[25,128,136]
circleCol2=[0,255,0]
program_state="Alive"
widthE=0
heightE=0
while True: 

    ev=pygame.event.poll()
    if ev.type==pygame.QUIT:
        break 

    if program_state=="Alive":
        face_rect=[0,0,0,0]
        ignore, frame = cam.read()
        faces=myFace.parseFace(frame)
        handLandmarks,handType=myHands.landmarkse(frame)
        mainSurface.fill((78,250,147))

        for face in faces:
            widthE=face[1][0]-face[0][0]
            heightE=face[1][1]-face[0][1]
            pygame.draw.rect(mainSurface,[0,0,0],[width-face[0][0],face[0][1],widthE,heightE])
            
        gun_pos={'left':[-100,-100],'right':[-100,-100]}
        if len(handLandmarks)>=1:
            for hand,type in zip(handLandmarks,handType):
                if type=='Left':
                    gun_pos['right']=[1280-hand[8][0],hand[8][1]]
                    pygame.draw.circle(mainSurface,circleCol,[1280-hand[8][0],hand[8][1]],50)
                if type=='Right':
                    gun_pos['left']=[1280-hand[8][0],hand[8][1]]
                    pygame.draw.circle(mainSurface,circleCol2,[1280-hand[8][0],hand[8][1]],50)

        #pygame.draw.circle(mainSurface,(0,0,255),[400,400],50)
        hands_fired=shoot_detection(handLandmarks,handType)
        for hand_shot in hands_fired:
            if hands_fired.index(hand_shot)==0:
                my_bat.complete_draw(mainSurface,hand_shot,gun_pos['left'])
            elif hands_fired.index(hand_shot)==1:
                my_bat.complete_draw(mainSurface,hand_shot,gun_pos['right'])

        if hands_fired[0]:
            circleCol2=[255,0,0]
        else:
            circleCol2=[0,255,0]
        if hands_fired[1]:
            circleCol=[255,0,0]
        else:
            circleCol=[25,128,136]

        if dodges.run_all(mainSurface,faces):
            dodges.first_run=True 
            program_state="Dead"
        if cv2.waitKey(1) & 0xff == ord('q'):
            break 

    if program_state=="Dead":
        mainSurface.fill((0,0,0))
        textRender("Loser!",(0,255,255),mainSurface,[500,300],100)
        textRender("Click anywhere to restart",(0,255,255),mainSurface,[400,450],50)
        if ev.type==1026:
            print('hi')
            program_state="Alive"
    pygame.display.flip()
    clock.tick(60)
    # cv2.imshow('window',frame)
    # cv2.moveWindow('window',0,0)
cam.release()
pygame.quit()