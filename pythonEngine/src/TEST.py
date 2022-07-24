from glob import glob
from operator import truediv
from re import A
from turtle import pos, speed
import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr
import math
import random
from tkinter import *
import os
####################### Model #################################################

global root
global EDITOR_MODE
EDITOR_MODE = False
root = Tk()
embed = Frame(root, width=640, height=10)
embed.grid(row=0,column=0)
root.update()


def EdFalse():
    global EDITOR_MODE
    if EDITOR_MODE == False:
        EDITOR_MODE = True
    else:
        EDITOR_MODE = False

B = Button(text ="play", command = EdFalse)

B.grid()





global beforeX, beforeZ, beforeY, is_grounded
beforeX = 0
beforeY = 0
beforeZ = 0
is_grounded = False
global player

global maplev
maplev = 0

class Mesh:


    def __init__(self, filename, tex, mod):
        tex, mod = tex, mod
        # x, y, z, s, t, nx, ny, nz, tx, ty, tz, bx, by, bz
        self.vertices = self.loadMesh(filename, tex, mod)
        self.vertex_count = len(self.vertices)//14
        self.vertices = np.array(self.vertices, dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        offset = 0
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 8
        #normal
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
        #tangent
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
        #bitangent
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
    
    def loadMesh(self, filename, tex, mod):

        tex, mod = tex, mod
        #raw, unassembled data
        v = []
        vt = []
        vn = []
        
        #final, assembled and packed result
        vertices = []

        #open the obj file and read the data
        with open(filename,'r') as f:
            line = f.readline()
            while line:
                firstSpace = line.find(" ")
                flag = line[0:firstSpace]
                if flag=="v":
                    #vertex
                    line = line.replace("v ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    v.append(l)
                elif flag=="vt":
                    #texture coordinate
                    line = line.replace("vt ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vt.append(l)
                elif flag=="vn":
                    #normal
                    line = line.replace("vn ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vn.append(l)
                elif flag=="f":
                    #face, three or more vertices in v/vt/vn form
                    line = line.replace("f ","")
                    line = line.replace("\n","")
                    #get the individual vertices for each line
                    line = line.split(" ")
                    faceVertices = []
                    faceTextures = []
                    faceNormals = []
                    for vertex in line:
                        #break out into [v,vt,vn],
                        #correct for 0 based indexing.
                        l = vertex.split("/")
                        position = int(l[0]) - 1
                        faceVertices.append(v[position])
                        texture = int(l[1]) - 1
                        faceTextures.append(vt[texture])
                        normal = int(l[2]) - 1
                        faceNormals.append(vn[normal])
                    # obj file uses triangle fan format for each face individually.
                    # unpack each face
                    triangles_in_face = len(line) - 2

                    vertex_order = []
                    """
                        eg. 0,1,2,3 unpacks to vertices: [0,1,2,0,2,3]
                    """
                    for i in range(triangles_in_face):
                        vertex_order.append(0)
                        vertex_order.append(i+1)
                        vertex_order.append(i+2)
                    # calculate tangent and bitangent for point
                    # how do model positions relate to texture positions?
                    point1 = faceVertices[vertex_order[0]]
                    point2 = faceVertices[vertex_order[1]]
                    point3 = faceVertices[vertex_order[2]]
                    uv1 = faceTextures[vertex_order[0]]
                    uv2 = faceTextures[vertex_order[1]]
                    uv3 = faceTextures[vertex_order[2]]
                    #direction vectors
                    deltaPos1 = [point2[i] - point1[i] for i in range(3)]
                    deltaPos2 = [point3[i] - point1[i] for i in range(3)]
                    deltaUV1 = [uv2[i] - uv1[i] for i in range(2)]
                    deltaUV2 = [uv3[i] - uv1[i] for i in range(2)]
                    # calculate
                    den = 1 / (deltaUV1[0] * deltaUV2[1] - deltaUV2[0] * deltaUV1[1])
                    tangent = []
                    #tangent x
                    tangent.append(den * (deltaUV2[1] * deltaPos1[0] - deltaUV1[1] * deltaPos2[0]))
                    #tangent y
                    tangent.append(den * (deltaUV2[1] * deltaPos1[1] - deltaUV1[1] * deltaPos2[1]))
                    #tangent z
                    tangent.append(den * (deltaUV2[1] * deltaPos1[2] - deltaUV1[1] * deltaPos2[2]))
                    bitangent = []
                    #bitangent x
                    bitangent.append(den * (-deltaUV2[0] * deltaPos1[0] + deltaUV1[0] * deltaPos2[0]))
                    #bitangent y
                    bitangent.append(den * (-deltaUV2[0] * deltaPos1[1] + deltaUV1[0] * deltaPos2[1]))
                    #bitangent z
                    bitangent.append(den * (-deltaUV2[0] * deltaPos1[2] + deltaUV1[0] * deltaPos2[2]))
                    for i in vertex_order:
                        for x in faceVertices[i]:
                            vertices.append(x* mod) 
                        for x in faceTextures[i]:
                            vertices.append(x* tex) 
                        for x in faceNormals[i]:
                            vertices.append(x* tex) 
                        for x in tangent:
                            vertices.append(x* tex) 
                        for x in bitangent:
                            vertices.append(x* tex) 
                line = f.readline()
        return vertices
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))


def groundCollider(z1, z2, x1, x2, y1, y2):
        global beforeX
        global beforeZ
        global beforeY
        global is_grounded, velocityY

        # Check if inside the box at X-axis and Check if inside the box at Z-axis and Check if inside the box at Y-axis
        if player.position[0] < x1 and player.position[0] > x2 and player.position[1] > z1 and player.position[1] < z2 and player.position[2] > y1 and player.position[2] < y2:
             if beforeZ > z1 and beforeZ < z2 and beforeX < x1 and beforeX > x2 and player.position[2]:
                is_grounded = True
                if velocityY <= 0:
                    velocityY = 0
                player.position[2] = beforeY



                #Check if before collsiion z was in collider
             if beforeZ > z1 and beforeZ < z2 :
                player.position[0] = beforeX

                #Check if before collsiion x was in collider
             if beforeX < x1 and beforeX > x2 :
                player.position[1] = beforeZ
             return True

        return False

def DoorCollider(z1, z2, x1, x2, y1, y2):
        global beforeX
        global beforeZ
        global beforeY
        global is_grounded, velocityY

        # Check if inside the box at X-axis and Check if inside the box at Z-axis and Check if inside the box at Y-axis
        if player.position[0] < x1 and player.position[0] > x2 and player.position[1] > z1 and player.position[1] < z2 and player.position[2] > y1 and player.position[2] < y2:
             
             return True

        return False



                

             

class SimpleComponent:


    def __init__(self,position, eulers):
        
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
    
    def update(self, rate):

        #self.eulers[1] += 0.25 * rate
        #self.eulers[1] > 360:
         #   self.eulers[1] -= 360
        
        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        self.modelTransform = pyrr.matrix44.multiply(
            m1=self.modelTransform, 
            m2=pyrr.matrix44.create_from_eulers(
                eulers=np.radians(self.eulers), dtype=np.float32
            )
        )
        self.modelTransform = pyrr.matrix44.multiply(
            m1=self.modelTransform, 
            m2=pyrr.matrix44.create_from_translation(
                vec=np.array(self.position),dtype=np.float32
            )
        )


        
        
class BillBoardComponent:

    def __init__(self, position):

        self.position = np.array(position, dtype=np.float32)
        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
    
    def update(self, playerPosition):
        
        directionFromPlayer = self.position - playerPosition
        angle1 = np.arctan2(-directionFromPlayer[1],directionFromPlayer[0])
        dist2d = math.sqrt(directionFromPlayer[0] ** 2 + directionFromPlayer[1] ** 2)
        angle2 = np.arctan2(directionFromPlayer[2],dist2d)

        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        self.modelTransform = pyrr.matrix44.multiply(
            self.modelTransform,
            pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32)
        )
        self.modelTransform = pyrr.matrix44.multiply(
           self.modelTransform,
            pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32)
        )
        self.modelTransform = pyrr.matrix44.multiply(
            self.modelTransform,
            pyrr.matrix44.create_from_translation(self.position,dtype=np.float32)
        )

class BrightBillboard:


    def __init__(self, position, color, strength):

        self.position = np.array(position, dtype=np.float32)
        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        self.color = np.array(color, dtype=np.float32)
        self.strength = strength
    
    def update(self, playerPosition):
        
        directionFromPlayer = self.position - playerPosition
        angle1 = np.arctan2(-directionFromPlayer[1],directionFromPlayer[0])
        dist2d = math.sqrt(directionFromPlayer[0] ** 2 + directionFromPlayer[1] ** 2)
        angle2 = np.arctan2(directionFromPlayer[2],dist2d)

        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        self.modelTransform = pyrr.matrix44.multiply(
            self.modelTransform,
            pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32)
        )
        self.modelTransform = pyrr.matrix44.multiply(
           self.modelTransform,
            pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32)
        )
        self.modelTransform = pyrr.matrix44.multiply(
            self.modelTransform,
            pyrr.matrix44.create_from_translation(self.position,dtype=np.float32)
        )

class Player:
    global velocityY
    velocityY = 0
    def __init__(self, position):

        self.position = np.array(position, dtype = np.float32)
        self.theta = 0
        self.phi = 0
        self.update_vectors()
    
    def update_vectors(self):
        
        self.forwards = np.array(
            [
                np.cos(np.deg2rad(self.theta)) * np.cos(np.deg2rad(self.phi)),
                np.sin(np.deg2rad(self.theta)) * np.cos(np.deg2rad(self.phi)),
                np.sin(np.deg2rad(self.phi))
            ],
            dtype = np.float32
        )

        globalUp = np.array([0,0,1], dtype=np.float32)

        self.right = np.cross(self.forwards, globalUp)

        self.up = np.cross(self.right, self.forwards)

        self.viewTransform = pyrr.matrix44.create_look_at(
            eye = self.position,
            target = self.position + self.forwards,
            up = self.up, 
            dtype = np.float32
        )

class Scene:


    def __init__(self):

       

        self.medkits = [
            BillBoardComponent(
                position = [3,0,0.5]
            )
        ]

        self.lights = [
            BrightBillboard(
                position = [
                    0.0, 
                    0.0, 
                    0.1
                ],
                color = [
                    1,1,1
                ],
                strength = 0.8
            ),

            BrightBillboard(
                position = [
                    -4.16, 
                    0.0, 
                    0.1
                ],
                color = [
                    1,1,1
                ],
                strength = 0.8
            ),

            BrightBillboard(
                position = [
                    -5.04, 
                    3.099, 
                    0.1
                ],
                color = [
                    0,1,0
                ],
                strength = 0.8
            )
            
            
            
        ]

        self.player = Player(
            position = [0,0,2]
        )
        global player
        player = self.player

    def update(self, rate):
        global root
        root.update()
        global TestGroup
        T = False
        
        for medkit in self.medkits:
            medkit.update(self.player.position)

        for light in self.lights:
            light.update(self.player.position)

        
        
        global beforeX, beforeZ,beforeY
        
        global velocityY, is_grounded
        is_grounded = False
        global mapcolliders
        keys = pg.key.get_pressed()
        
        
        if EDITOR_MODE == False or keys[pg.K_LSHIFT]:
            pg.mouse.set_visible(False)
        else:
            pg.mouse.set_visible(True)

        if EDITOR_MODE == True:
            mapcolliders = []
        else:
            mapcolliders = [groundCollider(-2500, 2500, 2500, -2500, -1, 0),
            groundCollider(-1.59,-1.05 ,1.55,-6.54,-1, 10),
            groundCollider(-1.59,3.9,-6.06,-6.58,-1, 10),
            groundCollider(1.037,1.552,1.547, -3.87, -1, 10),
            groundCollider(-1.7,1.71,1.8,1.01, -1, 10),
            groundCollider(1.06,4.07,-3.32,-3.85, -1, 10),
            groundCollider(3.512,3.94,-3.38,-6.7, -1, 10),
            #door!
            DoorCollider(3.2,3.87,-4.45,-5.62, -1, 10),]
        
            
        

        self.player.update_vectors()
        if EDITOR_MODE == False:
            collide = False
            for col in mapcolliders:
                if col:
                    collide = True

            if not is_grounded:
                velocityY += -0.2 * (1/1000)
                beforeZ = self.player.position[1]
                beforeX = self.player.position[0]
                beforeY = self.player.position[2]
            self.player.position[2] += velocityY

    
    def move_player(self, dPos):

        dPos = np.array(dPos, dtype = np.float32)
        
        self.player.position += dPos
    
    def spin_player(self, dTheta, dPhi):

        self.player.theta += dTheta
        if self.player.theta > 360:
            self.player.theta -= 360
        elif self.player.theta < 0:
            self.player.theta += 360
        
        self.player.phi = min(
            89, max(-89, self.player.phi + dPhi)
        )

####################### Control ###############################################


class SlowComponent:


    def __init__(self, mesh , tex ,position, eulers, draw):
        global mapcolliders
        self.mesh = mesh
        self.tex = tex
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        
        self.draw = draw
        
        
    def update(self, rate):

        #self.eulers[1] += 0.25 * rate
        #self.eulers[1] > 360:
         #   self.eulers[1] -= 360
        
        self.modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        self.modelTransform = pyrr.matrix44.multiply(
            m1=self.modelTransform, 
            m2=pyrr.matrix44.create_from_eulers(
                eulers=np.radians(self.eulers), dtype=np.float32
            )
        )
        self.modelTransform = pyrr.matrix44.multiply(
            m1=self.modelTransform, 
            m2=pyrr.matrix44.create_from_translation(
                vec=np.array(self.position),dtype=np.float32
            )
        )


class App:


    def __init__(self, screenWidth, screenHeight):

        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        self.renderer = GraphicsEngine(screenWidth, screenHeight)

        self.scene = Scene()

        self.lastTime = pg.time.get_ticks()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0
        self.lightCount = 0

        self.mainLoop()


    
    def mainLoop(self):
        
        running = True
        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
            self.scene.update(self.frameTime * 0.05)
            
            
            self.handleKeys()
            self.handleMouse()

            
            self.renderer.render(self.scene)

            #timing
            self.calculateFramerate()

           
            
        self.quit()

    def handleKeys(self):
        global EDITOR_MODE
        global is_grounded
        keys = pg.key.get_pressed()
        combo = 0
        directionModifier = 0
        """
        w: 1 -> 0 degrees
        a: 2 -> 90 degrees
        w & a: 3 -> 45 degrees
        s: 4 -> 180 degrees
        w & s: 5 -> x
        a & s: 6 -> 135 degrees
        w & a & s: 7 -> 90 degrees
        d: 8 -> 270 degrees
        w & d: 9 -> 315 degrees
        a & d: 10 -> x
        w & a & d: 11 -> 0 degrees
        s & d: 12 -> 225 degrees
        w & s & d: 13 -> 270 degrees
        a & s & d: 14 -> 180 degrees
        w & a & s & d: 15 -> x
        """

        if keys[pg.K_w]:
            combo += 1
        if keys[pg.K_a]:
            combo += 2
        if keys[pg.K_s]:
            combo += 4
        if keys[pg.K_d]:
            combo += 8
        
        if combo > 0:
            if combo == 3:
                directionModifier = 45
            elif combo == 2 or combo == 7:
                directionModifier = 90
            elif combo == 6:
                directionModifier = 135
            elif combo == 4 or combo == 14:
                directionModifier = 180
            elif combo == 12:
                directionModifier = 225
            elif combo == 8 or combo == 13:
                directionModifier = 270
            elif combo == 9:
                directionModifier = 315
            
            if is_grounded == False and EDITOR_MODE == False:
                dPos = [
                    self.frameTime * 0.004 * np.cos(np.deg2rad(self.scene.player.theta + directionModifier)),
                    self.frameTime * 0.004 * np.sin(np.deg2rad(self.scene.player.theta + directionModifier)),
                    0
                ]
            else:
                dPos = [
                    self.frameTime * 0.01 * np.cos(np.deg2rad(self.scene.player.theta + directionModifier)),
                    self.frameTime * 0.01 * np.sin(np.deg2rad(self.scene.player.theta + directionModifier)),
                    0
                ]


            if EDITOR_MODE == True:
                dPos = [
                    self.frameTime * 0.005 * np.cos(np.deg2rad(self.scene.player.theta + directionModifier)),
                    self.frameTime * 0.005 * np.sin(np.deg2rad(self.scene.player.theta + directionModifier)),
                    0
                ]
            self.scene.move_player(dPos)
        
        if keys[pg.K_LEFTBRACKET]:
            EDITOR_MODE = True
        if keys[pg.K_RIGHTBRACKET]:
            EDITOR_MODE = False

        if keys[pg.K_LSHIFT] and EDITOR_MODE == True:
            print(player.position)

        if EDITOR_MODE == True:
            if keys[pg.K_LCTRL]:
                self.scene.player.position[2] = self.scene.player.position[2] - 0.01
            if keys[pg.K_SPACE]:
                self.scene.player.position[2] = self.scene.player.position[2] + 0.01
        if EDITOR_MODE == False:
            if is_grounded and keys[pg.K_SPACE]:
                global velocityY
                velocityY = .0037
            

    def handleMouse(self):
        global x, y
        
        
        (x,y) = pg.mouse.get_pos()
        keys = pg.key.get_pressed()
        
        if EDITOR_MODE == False or keys[pg.K_LSHIFT]:
            theta_increment = self.frameTime * 0.045 * ((self.screenWidth // 2) - x)
            phi_increment = self.frameTime * 0.045 * ((self.screenHeight // 2) - y)
            self.scene.spin_player(theta_increment, phi_increment)
            pg.mouse.set_pos((self.screenWidth // 2,self.screenHeight // 2))
        

    def calculateFramerate(self):

        self.currentTime = pg.time.get_ticks()
        delta = self.currentTime - self.lastTime
        if (delta >= 1000):
            framerate = max(1,int(1000.0 * self.numFrames/delta))
            pg.display.set_caption(f"Echo window")
            self.renderer.update_fps(framerate)
            self.lastTime = self.currentTime
            self.numFrames = -1
            self.frameTime = float(1000.0 / max(1,framerate))
        self.numFrames += 1

    def quit(self):
        
        self.renderer.destroy()

####################### View  #################################################

class GraphicsEngine:


    def __init__(self, screenWidth, screenHeight):

        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        #initialise pygame
        pg.init()
        
        
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((self.screenWidth,self.screenHeight), pg.OPENGL|pg.DOUBLEBUF)

        

        #initialise opengl
        
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        

        self.create_framebuffers()

        self.setup_shaders()

        self.query_shader_locations()

        self.create_assets()
        
    def create_framebuffers(self):
        self.fbos = []
        self.colorBuffers = []
        self.depthStencilBuffers = []
        for i in range(2):
            self.fbos.append(glGenFramebuffers(1))
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbos[i])
        
            self.colorBuffers.append(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, self.colorBuffers[i])
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGB, 
                self.screenWidth, self.screenHeight,
                0, GL_RGB, GL_UNSIGNED_BYTE, None
            )
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glBindTexture(GL_TEXTURE_2D, 0)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 
                                    GL_TEXTURE_2D, self.colorBuffers[i], 0)
            
            self.depthStencilBuffers.append(glGenRenderbuffers(1))
            glBindRenderbuffer(GL_RENDERBUFFER, self.depthStencilBuffers[i])
            glRenderbufferStorage(
                GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.screenWidth, self.screenHeight
            )
            glBindRenderbuffer(GL_RENDERBUFFER,0)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, 
                                        GL_RENDERBUFFER, self.depthStencilBuffers[i])

            glBindFramebuffer(GL_FRAMEBUFFER, 0)
    
    def setup_shaders(self):

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = self.screenWidth/self.screenHeight, 
            near = 0.1, far = 200, dtype=np.float32
        )

        self.lighting_shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        glUseProgram(self.lighting_shader)
        glUniformMatrix4fv(
            glGetUniformLocation(self.lighting_shader,"projection"),
            1, GL_FALSE, projection_transform
        )
        glUniform1i(glGetUniformLocation(self.lighting_shader, "material.albedo"), 0)
        glUniform1i(glGetUniformLocation(self.lighting_shader, "material.ao"), 1)
        glUniform1i(glGetUniformLocation(self.lighting_shader, "material.specular"), 2)
        glUniform1i(glGetUniformLocation(self.lighting_shader, "material.normal"), 3)

        self.unlit_shader = self.createShader("shaders/vertex_light.txt", "shaders/fragment_light.txt")
        glUseProgram(self.unlit_shader)
        glUniformMatrix4fv(
            glGetUniformLocation(self.unlit_shader,"projection"),
            1, GL_FALSE, projection_transform
        )

        self.post_shader = self.createShader("shaders/simple_post_vertex.txt", "shaders/post_fragment.txt")

        self.EDITOR_shader = self.createShader("shaders/simple_post_vertex.txt", "shaders/editor_frag.txt")

        self.crt_shader = self.createShader("shaders/simple_post_vertex.txt", "shaders/crt_fragment.txt")

        self.screen_shader = self.createShader("shaders/simple_post_vertex.txt", "shaders/screen_fragment.txt")

    def query_shader_locations(self):

        #attributes shared by both shaders
        self.modelMatrixLocation = {}
        self.viewMatrixLocation = {}
        self.tintLoc = {}

        glUseProgram(self.lighting_shader)
        self.modelMatrixLocation["lit"] = glGetUniformLocation(self.lighting_shader, "model")
        self.viewMatrixLocation["lit"] = glGetUniformLocation(self.lighting_shader, "view")
        self.lightLocation = {
            "position": [
                glGetUniformLocation(self.lighting_shader, f"lightPos[{i}]")
                for i in range(8)
            ],
            "color": [
                glGetUniformLocation(self.lighting_shader, f"lights[{i}].color")
                for i in range(8)
            ],
            "strength": [
                glGetUniformLocation(self.lighting_shader, f"lights[{i}].strength")
                for i in range(8)
            ]
        }
        self.cameraPosLoc = glGetUniformLocation(self.lighting_shader, "viewPos")
        
       
        

        glUseProgram(self.unlit_shader)
        self.modelMatrixLocation["unlit"] = glGetUniformLocation(self.unlit_shader, "model")
        self.viewMatrixLocation["unlit"] = glGetUniformLocation(self.unlit_shader, "view")
        self.tintLoc["unlit"] = glGetUniformLocation(self.unlit_shader, "tint")

        glUseProgram(self.screen_shader)
        self.tintLoc["screen"] = glGetUniformLocation(self.screen_shader, "tint")

    def create_assets(self):

        glUseProgram(self.lighting_shader)
        
        
        self.wood = AdvancedMaterial("woodFloor/WoodFloor", "jpg")
        self.woodblack = AdvancedMaterial("brick/wall", "jpg")
        self.floor1Tex = AdvancedMaterial("floor/Florr", "jpg")
        self.CO = AdvancedMaterial("Tile/CO", "jpg")
        self.proto = AdvancedMaterial("Prototexture/Proto", "png")
        self.white = AdvancedMaterial("wh", "png")
        
        
        
        #self.plate = Mesh("models/plate.obj", 14, 0.5)
        #self.pancakes = Mesh("models/pancakes.obj", 14, 0.5)

        self.wall1 = Mesh("models/wall1.obj", 5, 1)
        self.wall1B = Mesh("models/wall1B.obj", 10, 1)
        self.floor = Mesh("models/floor1.obj", 10, 1)
        self.ceiling = Mesh("models/ceiling1.obj", 10, 1)
        self.fin = Mesh("models/fin.obj", 10, 1)

        #self.medkit_texture = AdvancedMaterial("medkit")
        self.medkit_billboard = BillBoard(w = 0.6, h = 0.5)

        glUseProgram(self.unlit_shader)
        self.light_texture = Material("gfx/lightPlaceHolder.png")
        self.light_billboard = BillBoard(w = 0.2, h = 0.1)

        self.screen = TexturedQuad(0, 0, 1, 1)
        
        self.font = Font()
        self.fps_label = TextLine("fps =", self.font, (-0.9, 0.9), (0.05, 0.05))
        self.mode_label = TextLine("mode =", self.font, (-0.9, 0.8), (0.05, 0.05))
        self.posx_label = TextLine("x =", self.font, (-0.9, 0.7), (0.05, 0.05))
        self.posy_label = TextLine("y =", self.font, (-0.9, 0.6), (0.05, 0.05))
        global TestGroup
        
        
        TestGroup = [
            SlowComponent(
                
                mesh = self.wall1,
                tex = self.wood,
                position = [0,0,0],
                eulers = [90,0,0],
                draw = True
            ),

            SlowComponent(
                
                mesh = self.wall1B,
                tex = self.woodblack,
                position = [0,0,0],
                eulers = [90,0,0],
                draw = True
            ),

            SlowComponent(
                
                mesh = self.floor,
                tex = self.CO,
                position = [0,0,0],
                eulers = [90,0,0],
                draw = True
            ),

            SlowComponent(
                
                mesh = self.ceiling,
                tex = self.floor1Tex,
                position = [0,0,0],
                eulers = [90,0,0],
                draw = True
            ),

            SlowComponent(
                
                mesh = self.fin,
                tex = self.white,
                position = [0,0,-0.5],
                eulers = [90,0,0],
                draw = True
            ),
            
            
            ]
        
    
    def createShader(self, vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER),
                            )
        
        return shader

    def update_fps(self, new_fps):
        global TestGroup
        for Tes in TestGroup:
            Tes.update(120)
        
        self.fps_label.build_text(f"fps =: {new_fps}", self.font)
        self.mode_label.build_text(f"mode =: {EDITOR_MODE}", self.font)
        self.posx_label.build_text(f"x =: {player.position[0]}", self.font)
        self.posy_label.build_text(f"y =: {player.position[1]}", self.font)
    
    
    def render(self, scene):
       
        
        #First pass
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbos[0])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        #lit shader
        glUseProgram(self.lighting_shader)

        glUniformMatrix4fv(self.viewMatrixLocation["lit"], 1, GL_FALSE, scene.player.viewTransform)

        glUniform3fv(self.cameraPosLoc, 1, scene.player.position)
        
        
        
        
        

        global TestGroup
        
        
        for nonscriptname in TestGroup:
                
                
                #mapcolliders = [groundCollider(-2500, 2500, 2500, -2500, -1, 0)]
                
                
                
                    

                model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
                model_transform = pyrr.matrix44.multiply(
                    m1=model_transform, 
                    m2=pyrr.matrix44.create_from_eulers(
                        eulers=np.radians(nonscriptname.eulers), dtype=np.float32
                    )
                )
                model_transform = pyrr.matrix44.multiply(
                    m1=model_transform, 
                    m2=pyrr.matrix44.create_from_translation(
                        vec=np.array(nonscriptname.position),dtype=np.float32
                    )
                )
                glUniformMatrix4fv(self.modelMatrixLocation["lit"],1,GL_FALSE,nonscriptname.modelTransform)
                
                nonscriptname.tex.use()
                glBindVertexArray(nonscriptname.mesh.vao)
                if nonscriptname.draw == True:
                    glDrawArrays(GL_TRIANGLES, 0, nonscriptname.mesh.vertex_count)
        for i,light in enumerate(scene.lights):
            glUniform3fv(self.lightLocation["position"][i], 1, light.position)
            glUniform3fv(self.lightLocation["color"][i], 1, light.color)
            glUniform1f(self.lightLocation["strength"][i], light.strength)

        #self.wood_texture.use()
        #glBindVertexArray(self.cube_mesh.vao)
        
        


        #CREATE_OBJECT(TestGroup)
        #self.medkit_texture.use()
        glBindVertexArray(self.medkit_billboard.vao)
        for medkit in scene.medkits:
            glUniformMatrix4fv(self.modelMatrixLocation["lit"],1,GL_FALSE,medkit.modelTransform)
            glDrawArrays(GL_TRIANGLES, 0, self.medkit_billboard.vertexCount)

        #unlit shader
        glUseProgram(self.unlit_shader)

        glUniformMatrix4fv(self.viewMatrixLocation["unlit"], 1, GL_FALSE, scene.player.viewTransform)

        self.light_texture.use()
        glBindVertexArray(self.light_billboard.vao)
        for i,light in enumerate(scene.lights):

            glUniform3fv(self.tintLoc["unlit"], 1, light.color)
            glUniformMatrix4fv(self.modelMatrixLocation["unlit"],1,GL_FALSE,light.modelTransform)
            glDrawArrays(GL_TRIANGLES, 0, self.light_billboard.vertexCount)
        
        #Post processing pass
        glUseProgram(self.screen_shader)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbos[0])
        glDisable(GL_DEPTH_TEST)

        glUniform4fv(self.tintLoc["screen"], 1, np.array([1.0, 0.0, 0.0, 1.0], dtype = np.float32))
        self.font.use()

        if EDITOR_MODE == True:
            glBindVertexArray(self.fps_label.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.fps_label.vertex_count)

            glBindVertexArray(self.mode_label.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.mode_label.vertex_count)

            glBindVertexArray(self.posx_label.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.posx_label.vertex_count)

            glBindVertexArray(self.posy_label.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.posy_label.vertex_count)

        """
        #Blit color buffer 1 onto color buffer 0
        glUseProgram(self.screen_shader)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbos[0])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)


        glBindTexture(GL_TEXTURE_2D, self.colorBuffers[1])
        glActiveTexture(GL_TEXTURE0)
        glBindVertexArray(self.screen.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.screen.vertex_count)
        """

        if EDITOR_MODE == True:
            glUseProgram(self.EDITOR_shader)
        else:
            glUseProgram(self.crt_shader)

        
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbos[1])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        glBindTexture(GL_TEXTURE_2D, self.colorBuffers[0])
        glActiveTexture(GL_TEXTURE0)
        glBindVertexArray(self.screen.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.screen.vertex_count)
        
        #Put the final result on screen
        glUseProgram(self.screen_shader)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
               
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        glUniform4fv(self.tintLoc["screen"], 1, np.array([1.0, 1.0, 1.0, 1.0], dtype = np.float32))
        glBindTexture(GL_TEXTURE_2D, self.colorBuffers[1])
        glActiveTexture(GL_TEXTURE0)
        glBindVertexArray(self.screen.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.screen.vertex_count)

        pg.display.flip()

    def destroy(self):

        
        
        
        self.medkit_billboard.destroy()
        #self.medkit_texture.destroy()
        self.light_billboard.destroy()
        self.light_texture.destroy()
        self.font.destroy()
        self.fps_label.destroy()
        glDeleteProgram(self.lighting_shader)
        glDeleteProgram(self.unlit_shader)
        glDeleteProgram(self.post_shader)
        glDeleteProgram(self.EDITOR_shader)
        glDeleteTextures(len(self.colorBuffers), self.colorBuffers)
        glDeleteRenderbuffers(len(self.depthStencilBuffers), self.depthStencilBuffers)
        glDeleteFramebuffers(len(self.fbos), self.fbos)
        pg.quit()


class Material:

    
    def __init__(self, filepath):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load(filepath).convert_alpha()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D,self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))

class AdvancedMaterial:

    
    def __init__(self, fileroot, type):

        #albedo
        self.albedoTexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.albedoTexture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load(f"gfx/{fileroot}_albedo." + type).convert_alpha()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

        #ambient occlusion
        self.ambientOcclusionTexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.ambientOcclusionTexture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load(f"gfx/{fileroot}_ao." + type).convert_alpha()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

        #glossmap
        self.glossmapTexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.glossmapTexture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load(f"gfx/{fileroot}_glossmap." + type).convert_alpha()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

        #normal
        self.normalTexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.normalTexture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load(f"gfx/{fileroot}_normal." + type).convert_alpha()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

        #handy list
        self.textures = [
            self.albedoTexture, self.ambientOcclusionTexture, self.glossmapTexture, self.normalTexture
        ]

    def use(self):

        for i,texture in enumerate(self.textures):
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(GL_TEXTURE_2D, texture)

    def destroy(self):
        glDeleteTextures(len(self.textures), self.textures)

class BillBoard:


    def __init__(self, w, h):

        #x,y,z, s,t, normal, tangent, bitangent

        self.vertices = (
            0, -w/2,  h/2, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0,
            0, -w/2, -h/2, 0, 1, -1, 0, 0, 0, 0, 1, 0, 1, 0,
            0,  w/2, -h/2, 1, 1, -1, 0, 0, 0, 0, 1, 0, 1, 0,

            0, -w/2,  h/2, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0,
            0,  w/2, -h/2, 1, 1, -1, 0, 0, 0, 0, 1, 0, 1, 0,
            0,  w/2,  h/2, 1, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.vertexCount = 6
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        offset = 0
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 8
        #normal
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
        #tangent
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
        #bitangent
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 56, ctypes.c_void_p(offset))
        offset += 12
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

class TexturedQuad:


    def __init__(self, x, y, w, h):
        self.vertices = (
            x - w, y + h, 0, 1,
            x - w, y - h, 0, 0,
            x + w, y - h, 1, 0,

            x - w, y + h, 0, 1,
            x + w, y - h, 1, 0,
            x + w, y + h, 1, 1
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vertex_count = 6
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

class Font:

    def __init__(self):

         #some parameters for fine tuning.
        w = 55.55 / 1000.0
        h =  63.88 / 1150.0
        heightOffset = 8.5 / 1150.0
        margin = 0.014

        """
            Letter: (left, top, width, height)
        """
        self.letterTexCoords = {
            'A': (       w, 1.0 - h,                          w - margin, h - margin), 'B': ( 3.0 * w, 1.0 - h,                          w - margin, h - margin),
            'C': ( 5.0 * w, 1.0 - h,                          w - margin, h - margin), 'D': ( 7.0 * w, 1.0 - h,                          w - margin, h - margin),
            'E': ( 9.0 * w, 1.0 - h,                          w - margin, h - margin), 'F': (11.0 * w, 1.0 - h,                          w - margin, h - margin),
            'G': (13.0 * w, 1.0 - h,                          w - margin, h - margin), 'H': (15.0 * w, 1.0 - h,                          w - margin, h - margin),
            'I': (17.0 * w, 1.0 - h,                          w - margin, h - margin), 'J': (       w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin),
            'K': ( 3.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin), 'L': ( 5.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin),
            'M': ( 7.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin), 'N': ( 9.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin),
            'O': (11.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin), 'P': (13.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin),
            'Q': (15.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin), 'R': (17.0 * w, 1.0 - 3.0 * h + heightOffset,     w - margin, h - margin),
            'S': (       w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin), 'T': ( 3.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin),
            'U': ( 5.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin), 'V': ( 7.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin),
            'W': ( 9.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin), 'X': (11.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin),
            'Y': (13.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin), 'Z': (15.0 * w, 1.0 - 5.0 * h + 2 * heightOffset, w - margin, h - margin),

            'a': (       w,                     1.0 - 7.0 * h, w - margin, h - margin), 'b': ( 3.0 * w,         1.0 - 7.0 * h, w - margin, h - margin),
            'c': ( 5.0 * w,                     1.0 - 7.0 * h, w - margin, h - margin), 'd': ( 7.0 * w,         1.0 - 7.0 * h, w - margin, h - margin),
            'e': ( 9.0 * w,                     1.0 - 7.0 * h, w - margin, h - margin), 'f': (11.0 * w,         1.0 - 7.0 * h, w - margin, h - margin),
            'g': (13.0 * w,                     1.0 - 7.0 * h, w - margin, h - margin), 'h': (15.0 * w,         1.0 - 7.0 * h, w - margin, h - margin),
            'i': (17.0 * w,                     1.0 - 7.0 * h, w - margin, h - margin), 'j': (       w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin),
            'k': ( 3.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin), 'l': ( 5.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin),
            'm': ( 7.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin), 'n': ( 9.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin),
            'o': (11.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin), 'p': (13.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin),
            'q': (15.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin), 'r': (17.0 * w,      1.0 - 9.0 * h + heightOffset, w - margin, h - margin),
            's': (       w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin), 't': ( 3.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin),
            'u': ( 5.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin), 'v': ( 7.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin),
            'w': ( 9.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin), 'x': (11.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin),
            'y': (13.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin), 'z': (15.0 * w, 1.0 - 11.0 * h + 2 * heightOffset, w - margin, h - margin),

            '0': (       w, 1.0 - 13.0 * h, w - margin, h - margin), '1':  ( 3.0 * w,                1.0 - 13.0 * h, w - margin, h - margin),
            '2': ( 5.0 * w, 1.0 - 13.0 * h, w - margin, h - margin), '3':  ( 7.0 * w,                1.0 - 13.0 * h, w - margin, h - margin),
            '4': ( 9.0 * w, 1.0 - 13.0 * h, w - margin, h - margin), '5':  (11.0 * w,                1.0 - 13.0 * h, w - margin, h - margin),
            '6': (13.0 * w, 1.0 - 13.0 * h, w - margin, h - margin), '7':  (15.0 * w,                1.0 - 13.0 * h, w - margin, h - margin),
            '8': (17.0 * w, 1.0 - 13.0 * h, w - margin, h - margin), '9':  (       w, 1.0 - 15.0 * h + heightOffset, w - margin, h - margin),
            
            '.':  ( 3.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin), ',': ( 5.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin),
            ';':  ( 7.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin), ':': ( 9.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin),
            '$':  (11.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin), '#': (13.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin),
            '\'': (15.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin), '!': (17.0 * w,     1.0 - 15.0 * h + heightOffset, w - margin, h - margin),
            '"':  (       w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin), '/': ( 3.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin),
            '?':  ( 5.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin), '%': ( 7.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin),
            '&':  ( 9.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin), '(': (11.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin),
            ')':  (13.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin), '@': (15.0 * w, 1.0 - 17.0 * h + 2 * heightOffset, w - margin, h - margin)
        }

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load("gfx/Inconsolata.png").convert_alpha()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)
        
    
    def get_bounding_box(self, letter):

        if letter in self.letterTexCoords:
            return self.letterTexCoords[letter]
        return None
    
    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D,self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))

class TextLine:

    
    def __init__(self, initial_text, font, start_position, letter_size):

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.start_position = start_position
        self.letter_size = letter_size
        self.build_text(initial_text, font)
    
    def build_text(self, new_text, font):

        self.vertices = []
        self.vertex_count = 0

        margin_adjustment = 0.96

        for i,letter in enumerate(new_text):

            bounding_box  = font.get_bounding_box(letter)
            if bounding_box is None:
                continue

            #top left
            self.vertices.append(
                self.start_position[0] - self.letter_size[0] + ((2 - margin_adjustment) * i * self.letter_size[0])
            )
            self.vertices.append(self.start_position[1] + self.letter_size[1])
            self.vertices.append(bounding_box[0] - bounding_box[2])
            self.vertices.append(bounding_box[1] + bounding_box[3])
            #top right
            self.vertices.append(
                self.start_position[0] + self.letter_size[0] + ((2 - margin_adjustment) * i * self.letter_size[0])
            )
            self.vertices.append(self.start_position[1] + self.letter_size[1])
            self.vertices.append(bounding_box[0] + bounding_box[2])
            self.vertices.append(bounding_box[1] + bounding_box[3])
            #bottom right
            self.vertices.append(
                self.start_position[0] + self.letter_size[0] + ((2 - margin_adjustment) * i * self.letter_size[0])
            )
            self.vertices.append(self.start_position[1] - self.letter_size[1])
            self.vertices.append(bounding_box[0] + bounding_box[2])
            self.vertices.append(bounding_box[1] - bounding_box[3])

            #bottom right
            self.vertices.append(
                self.start_position[0] + self.letter_size[0] + ((2 - margin_adjustment) * i * self.letter_size[0])
            )
            self.vertices.append(self.start_position[1] - self.letter_size[1])
            self.vertices.append(bounding_box[0] + bounding_box[2])
            self.vertices.append(bounding_box[1] - bounding_box[3])
            #bottom left
            self.vertices.append(
                self.start_position[0] - self.letter_size[0] + ((2 - margin_adjustment) * i * self.letter_size[0])
            )
            self.vertices.append(self.start_position[1] - self.letter_size[1])
            self.vertices.append(bounding_box[0] - bounding_box[2])
            self.vertices.append(bounding_box[1] - bounding_box[3])
            #top left
            self.vertices.append(
                self.start_position[0] - self.letter_size[0] + ((2 - margin_adjustment) * i * self.letter_size[0])
            )
            self.vertices.append(self.start_position[1] + self.letter_size[1])
            self.vertices.append(bounding_box[0] - bounding_box[2])
            self.vertices.append(bounding_box[1] + bounding_box[3])

            self.vertex_count += 6

        self.vertices = np.array(self.vertices, dtype=np.float32)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        offset = 0
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(offset))
        offset += 8
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(offset))
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))


myApp = App(1200,800)


