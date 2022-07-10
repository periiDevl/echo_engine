


import pygame as pg

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr
import math
import random

from functools import *

import time
global maplevel

maplevel = 0

global DeltaTime, FPS
DeltaTime = 1 / 60
FPS = 60


GotKey = False

class Mesh:

    
    def __init__(self, filename, objectsize, texSize):
        # x, y, z, s, t, nx, ny, nz
        self.vertices = self.loadMesh(filename, objectsize, texSize)
        self.vertex_count = len(self.vertices)//8
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
        #normal
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))
   
    def loadMesh(self, filename, objsize, texCoord):

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
                    for i in vertex_order:
                        for x in faceVertices[i]:
                            vertices.append(x * objsize)
                        for x in faceTextures[i]:
                            vertices.append(x * texCoord)
                        for x in faceNormals[i]:
                            vertices.append(x)
                line = f.readline()
        return vertices
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))

class SimpleComponent:

    
    def __init__(self, mesh, tex ,position, eulers):
        self.mesh = mesh
        self.tex = tex
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
    

    
    

class Light:


    def __init__(self, position, color, strength):

        self.position = np.array(position, dtype=np.float32)
        self.color = np.array(color, dtype=np.float32)
        self.strength = strength
        

class Player:

    
    
    def __init__(self, position):

        self.position = np.array(position, dtype = np.float32)
        self.theta = 90
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


global beforePosx
beforePosx = 0

global beforePosz
beforePosz = 0

global beforePosy
beforePosy = 0


class RenderPassTexturedLit3D:

    @lru_cache(maxsize=None)
    def __init__(self, shader):

        #initialise opengl
        self.shader = shader
        glUseProgram(self.shader)
        glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 60, aspect = 640/480, 
            near = 0.1, far = 50, dtype=np.float32
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader,"projection"),
            1, GL_FALSE, projection_transform
        )
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.lightLocation = {
            "position": [
                glGetUniformLocation(self.shader, f"Lights[{i}].position")
                for i in range(20)
            ],
            "color": [
                glGetUniformLocation(self.shader, f"Lights[{i}].color")
                for i in range(20)
            ],
            "strength": [
                glGetUniformLocation(self.shader, f"Lights[{i}].strength")
                for i in range(20)
            ]
        }
        self.cameraPosLoc = glGetUniformLocation(self.shader, "cameraPostion")
    #cant cache
    
    def render(self, scene, engine):

        
        global leveloneobjects
        global leveltwobjects
        def createL0():
            global maplevel
            for nonscriptname in levelzeroobjects:

                
                
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
                glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
                nonscriptname.tex.use()
                glBindVertexArray(nonscriptname.mesh.vao)
                glDrawArrays(GL_TRIANGLES, 0, nonscriptname.mesh.vertex_count)

        def createL1():

            for nonscriptname in levelonebjects:

                
                
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
                glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
                nonscriptname.tex.use()
                glBindVertexArray(nonscriptname.mesh.vao)
                glDrawArrays(GL_TRIANGLES, 0, nonscriptname.mesh.vertex_count)

        def createL2():

            for nonscriptname in leveltwobjects:

                
                
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
                glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
                nonscriptname.tex.use()
                glBindVertexArray(nonscriptname.mesh.vao)
                glDrawArrays(GL_TRIANGLES, 0, nonscriptname.mesh.vertex_count)

                

                
        
        glUseProgram(self.shader)

        view_transform = pyrr.matrix44.create_look_at(
            eye = scene.player.position,
            target = scene.player.position + scene.player.forwards,
            up = scene.player.up, dtype = np.float32
        )
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view_transform)

        glUniform3fv(self.cameraPosLoc, 1, scene.player.position)

        if maplevel == 0:
            for i,light in enumerate(scene.lights):
                glUniform3fv(self.lightLocation["position"][i], 1, light.position)
                glUniform3fv(self.lightLocation["color"][i], 1, light.color)
                glUniform1f(self.lightLocation["strength"][i], light.strength)
        if maplevel == 1:
            for i,light in enumerate(scene.lightslevtwo):
                glUniform3fv(self.lightLocation["position"][i], 1, light.position)
                glUniform3fv(self.lightLocation["color"][i], 1, light.color)
                glUniform1f(self.lightLocation["strength"][i], light.strength)
        if maplevel == 2:
            for i,light in enumerate(scene.lightslevthree):
                glUniform3fv(self.lightLocation["position"][i], 1, light.position)
                glUniform3fv(self.lightLocation["color"][i], 1, light.color)
                glUniform1f(self.lightLocation["strength"][i], light.strength)
       
        #leveloneobjects = [SimpleComponent(mesh = engine.ca,position = [6,0,1], eulers = [0,0,0]),]
        #def createNonObjects():
        
        
        
        if maplevel == 0:
            createL0()
        elif maplevel == 1:
            createL1()
        elif maplevel == 2:
            createL2()
        
            for fow in scene.fows:

                engine.fow_texture.use()

                directionFromPlayer = fow.position - scene.player.position
                wallpos = fow.position
                angle1 = np.arctan2(-directionFromPlayer[1],directionFromPlayer[0])
                dist2d = math.sqrt(directionFromPlayer[0] ** 2 + directionFromPlayer[1] ** 2)
                angle2 = np.arctan2(directionFromPlayer[2],dist2d)

                model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
                model_transform = pyrr.matrix44.multiply(
                    model_transform,
                    pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32)
                )
                model_transform = pyrr.matrix44.multiply(
                    model_transform,
                    pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32)
                )
                model_transform = pyrr.matrix44.multiply(
                    model_transform,
                    pyrr.matrix44.create_from_translation(fow.position,dtype=np.float32)
                )
                glUniformMatrix4fv(glGetUniformLocation(self.shader,"model"),1,GL_FALSE,model_transform)


                glBindVertexArray(engine.fow_billboard.vao)
                glDrawArrays(GL_TRIANGLES, 0, engine.fow_billboard.vertexCount)
   
    def destroy(self):
        
        
        glDeleteProgram(self.shader)

    

class GraphicsEngine:

    @lru_cache(maxsize=None)
    def __init__(self):

        #initialise pygame
        pg.init()
        
        pg.mouse.set_visible(False)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        #window
        pg.display.set_mode((1200,800), pg.OPENGL|pg.DOUBLEBUF)


        
        #initialise opengl
        glClearColor(0.0, 0.0, 0.0, 1)
        
        glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE)
        #glCullFace(GL_BACK)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        #create renderpasses and resources
        shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        self.texturedLitPass = RenderPassTexturedLit3D(shader)

        #MESH
        self.wall = Mesh("models/wallfull.obj", 1, 4)
        self.wallbounds = Mesh("models/wallbounds.obj", 1, 4)
        self.floor = Mesh("models/floor2.obj", 1, 200)
        self.ceilingFloor = Mesh("models/floor2.obj", 1, 70) 
        self.monkey = Mesh("models/wallfull.obj", 1, 4)        
        self.poster = Mesh("models/posterObj.obj", 0.3, 2.75)
        self.table = Mesh("models/table.obj", 0.8, 4)

        self.bacteriaman = Mesh("models/bacteria man.obj", .8, 1)
        self.boo_body = Mesh("models/boo_body.obj", .8, 1)
        self.boo_eye = Mesh("models/boo_eyes.obj", .8, 1)
        self.boo_eye_pup = Mesh("models/boo_eyes_pupels.obj", .8, 1)
        self.boo_bars = Mesh("models/boo_bars.obj", .8, 1)
        self.doorpart1 = Mesh("models/doorpart1.obj", 0.5, 4)
        self.doorpart2 = Mesh("models/doorpart2.obj", 0.5, 4)
        self.doorpart3 = Mesh("models/doorpart3.obj", 0.5, 4)

        self.levtwo = Mesh("models/level2W.obj", 3.25, 4)
        self.levtwoB = Mesh("models/level2B.obj", 3.25, 4)

        self.keymesh = Mesh("models/key.obj", 0.25, 4)
        
        self.bacteriaman = Mesh("models/ghostbody.obj", .25, .6)
        self.bacteriaeyes = Mesh("models/ghosteyes.obj", .25, .6)
        self.bacteriacloth = Mesh("models/ghostcloth.obj", .25, .6)
        self.bacteriahead = Mesh("models/ghosthead.obj", .25, .6)
        
        #TEXTURES
        self.walltexture = Material("gfx/Leather035C_2K_Color.jpg")
        self.floortexture = Material("gfx/wood2.jpg")
        self.floorbtexture = Material("gfx/woodb.jpg")
        self.fow_texture = Material("gfx/yellowFoliage.png")
        self.ceilingg = Material("gfx/ofce.jpg")
        self.bacteriamantexture = Material("gfx/BacteriaManTexture.png") 
        self.posterTexture = Material("gfx/wasdT.png")

        self.doorpart3Tex = Material("gfx/cone.jpg")
        self.doorpart2Tex = Material("gfx/lev.jpg") 
        self.doorpart2wTex = Material("gfx/lev.jpg")
        self.doorpart2wTex = Material("gfx/lev.jpg")

        self.boo_body_texture = Material("gfx/boo_body_tex.png")
        self.boo_eye_texture = Material("gfx/boo_eye_texture.png") 
        self.boo_eye_pup_texture = Material("gfx/boo_pup_texture.png")
        self.boo_bars_texture = Material("gfx/boo_bar_texture.png")

        self.wall_lev_two_texture = Material("gfx/woodlevtwo.jpg")
        self.mosstexture = Material("gfx/moss.jpg")

        self.bacteriamantexture = Material("gfx/Ghost texture.png")
        self.bacteriaeyetexture = Material("gfx/Ghost eyes.png")
        self.bacteriaclothtexture = Material("gfx/ghost cloth.png")
        
        self.keyTex = Material("gfx/key texture.png")
        
        #BILLBOARDS
        self.fow_billboard = BillBoard(w = 1, h = 1)
       
        
        shader = self.createShader("shaders/vertex_light.txt", "shaders/fragment_light.txt")
        self.texturedPass = RenderPassTextured3D(shader)
        self.light_texture = Material("gfx/lightPlaceHolder.png")
        self.light_billboard = BillBoard(w = 0.2, h = 0.1)
        global boobj
        boobj = [SimpleComponent(mesh = self.boo_body, tex = self.boo_body_texture ,position = [3.8,-9.6,-5.8], eulers = [270,0,90]),
                 SimpleComponent(mesh = self.boo_eye, tex = self.boo_eye_texture ,position = [3.8,-9.6,-5.8], eulers = [270,0,90]),
                 SimpleComponent(mesh = self.boo_eye_pup, tex = self.boo_eye_pup_texture ,position = [0,-9.6,-5.8], eulers = [270,0,90]),
                 SimpleComponent(mesh = self.boo_bars, tex = self.boo_bars_texture ,position = [3.8,-9.6,-5.8], eulers = [270,0,90])]
        
        global maplevel
        
        global levelzeroobjects
        levelzeroobjects = [SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [3.7,0,-5.8], eulers = [90,0,0]),
            SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-3.7,0,-5.8], eulers = [90,0,0]),
            SimpleComponent(mesh = self.floor, tex = self.floortexture ,position = [0,0,-9], eulers = [90,0,0]),
            SimpleComponent(mesh = self.ceilingFloor, tex = self.ceilingg ,position = [0,0,-2.5], eulers = [90,0,0]),
            SimpleComponent(mesh = self.poster, tex = self.posterTexture ,position = [2,8.6,-5.8], eulers = [-90,-90, 0]),
            SimpleComponent(mesh = self.table, tex = self.floorbtexture ,position = [2,7.7,-7.8], eulers = [-90,0, 90]),

            
            SimpleComponent(mesh = self.doorpart1, tex = self.floorbtexture ,position = [-2,-2.9,-6.62], eulers = [90,0,90]),
            SimpleComponent(mesh = self.doorpart2, tex = self.doorpart2Tex ,position = [-2.1,-2.8,-6.62], eulers = [90,0,90]),
            SimpleComponent(mesh = self.doorpart3, tex = self.doorpart3Tex ,position = [-2,-2.9,-6.62], eulers = [90,0,90]),
            SimpleComponent(mesh = self.doorpart2, tex = self.doorpart2wTex ,position = [-1.4,-2.8,-6.62], eulers = [90,0,90]),
            

            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-3.7,0,-5.8], eulers = [90,0,0]),
            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [3.7,0,-5.8], eulers = [90,0,0]),

            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-3.7, 6.9,-5.8], eulers = [90,0,0]),
            SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-3.7,6.9,-5.8], eulers = [90,0,0]),
            
            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [3.7, 6.9,-5.8], eulers = [90,0,0]),
            SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [3.7,6.9,-5.8], eulers = [90,0,0]),
            
            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [0, 9,-5.8], eulers = [90,0,90]),
            SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [0,9,-5.8], eulers = [90,0,90]),
            
            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [0, -3.4,-5.8], eulers = [90,0,90]),
            SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [0,-3.4,-5.8], eulers = [90,0,90]),

            SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [0, -1,-5.8], eulers = [90,0,0]),
            SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [0,-1,-5.8], eulers = [90,0,0]),
                                    
        ]
        global bacteriamanobject
        bacteriamanobject = [SimpleComponent(mesh = self.bacteriaman, tex = self.bacteriamantexture ,position = [0,-12.4,-6.8], eulers = [270,0,90]),
                             SimpleComponent(mesh = self.bacteriaeyes, tex = self.bacteriaeyetexture ,position = [0,-12.4,-6.8], eulers = [270,0,90]),
                             SimpleComponent(mesh = self.bacteriacloth, tex = self.bacteriaclothtexture ,position = [0,-12.4,-6.8], eulers = [270,0,90]),
                             SimpleComponent(mesh = self.bacteriahead, tex = self.bacteriamantexture ,position = [0,-12.4,-6.8], eulers = [270,0,90])]
        
        global levelonebjects
        key1 = SimpleComponent(mesh = self.keymesh, tex = self.keyTex ,position = [1.05,0,-6.5], eulers = [90,0,90])
        levelonebjects = [
            SimpleComponent(mesh = self.floor, tex = self.floortexture ,position = [0,0,-9], eulers = [90,0,0]),
        SimpleComponent(mesh = self.ceilingFloor, tex = self.ceilingg ,position = [0,0,-2.5], eulers = [90,0,0])
        ,
        # FIRST ROOM
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-3.7, 5.95,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-3.7,5.9,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-3.7,5.9-6.9,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-3.7,5.9-6.9,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [1.5, 2,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [1.5,2,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [2, 2,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [2,2,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [2.5, 2,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [2.5,2,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [0, 9,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [0,9,-5.8], eulers = [90,0,90])
        ,
        # SECOND ROOM
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-11, 5,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-11,5,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-11, -1,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-11,-1,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-14.5, 2,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-14.5,2,-5.8], eulers = [90,0,0])
        ,
        # THIRD ROOM
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [11, 5,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [11,5,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [11, -1,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [11,-1,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [14.5, 2,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [14.5,2,-5.8], eulers = [90,0,0])
        ,
        # AROUND ROOMS

        ### wall 1
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [11.5, 15,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [11.5,15,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [4.6, 15,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [4.6,15,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-2.3, 15,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-2.3,15,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-2.3-6.9, 15,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-2.3-6.9,15,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-2.3-13.8, 15,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-2.3-13.8,15,-5.8], eulers = [90,0,90])
        ,
        ### wall 2
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [14.5, 12.9+2.85,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [14.5,12.9+2.85,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [14.5, 6+2.85,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [14.5,6+2.85,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [14.5, -4.9,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [14.5,-4.9,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [14.5, 6+2.85,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [14.5,6+2.85,-5.8], eulers = [90,0,0])
        ,
        ### wall 3
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [11.5, -8.2,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [11.5,-8.2,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [4.6, -8.2,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [4.6,-8.2,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-2.3, -8.2,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-2.3,-8.2,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-2.3-6.9, -8.2,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-2.3-6.9,-8.2,-5.8], eulers = [90,0,90])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-2.3-13.8, -8.2,-5.8], eulers = [90,0,90]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-2.3-13.8,-8.2,-5.8], eulers = [90,0,90])
        ,
        
        ### wall 4
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-14.5, 12.9+2.85,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-14.5,12.9+2.85,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-14.5, 6+2.85,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-14.5,6+2.85,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-14.5, -4.9,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-14.5,-4.9,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.wallbounds, tex = self.floorbtexture ,position = [-14.5, 6+2.85,-5.8], eulers = [90,0,0]),
        SimpleComponent(mesh = self.wall, tex = self.walltexture ,position = [-14.5,6+2.85,-5.8], eulers = [90,0,0])
        ,
        SimpleComponent(mesh = self.doorpart1, tex = self.floorbtexture ,position = [11.45,4.5,-6.62], eulers = [90,0,-90]),
        SimpleComponent(mesh = self.doorpart2, tex = self.doorpart2Tex ,position = [11.45,4.5,-6.62], eulers = [90,0,-90]),
        SimpleComponent(mesh = self.doorpart3, tex = self.doorpart3Tex ,position = [11.45,4.5,-6.62], eulers = [90,0,-90]),
        SimpleComponent(mesh = self.doorpart2, tex = self.doorpart2wTex ,position = [11.45,4.5,-6.62], eulers = [90,0,-90])
        ,
        # ENEMY
        bacteriamanobject[0],bacteriamanobject[1],bacteriamanobject[2],bacteriamanobject[3],
        key1
        ]
        global leveltwobjects
        key2 = SimpleComponent(mesh = self.keymesh, tex = self.keyTex ,position = [1.75,23,-6.5], eulers = [90,0,90])
        leveltwobjects = [
            SimpleComponent(mesh = self.doorpart1, tex = self.floorbtexture ,position = [-13,9,-6.62], eulers = [90,0,180]),
            SimpleComponent(mesh = self.doorpart2, tex = self.doorpart2Tex ,position = [-13-.1,9+.1,-6.62], eulers = [90,0,180]),
            SimpleComponent(mesh = self.doorpart3, tex = self.doorpart3Tex ,position = [-13,9,-6.62], eulers = [90,0,180]),
            SimpleComponent(mesh = self.doorpart2, tex = self.doorpart2wTex ,position = [-13+.6,9+.1,-6.62], eulers = [90,0,180]),
            
            SimpleComponent(mesh = self.floor, tex = self.mosstexture ,position = [0,0,-9], eulers = [90,0,0]),
            SimpleComponent(mesh = self.ceilingFloor, tex = self.ceilingg ,position = [0,0,-2.5], eulers = [90,0,0]),
            
            SimpleComponent(mesh = self.levtwo, tex = self.doorpart2wTex ,position = [0,-3.4,-3.5], eulers = [90,0,90]),
            SimpleComponent(mesh = self.levtwoB, tex = self.wall_lev_two_texture ,position = [0,-3.4,-3.5], eulers = [90,0,90]),
            boobj[0],
            boobj[1],
            boobj[2],
            boobj[3],
            key2
            ]

        
        
        
        
    @lru_cache(maxsize=None)
    def createShader(self, vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader
    
    def render(self, scene):

        #refresh screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.texturedLitPass.render(scene, self)

        self.texturedPass.render(scene, self)

        pg.display.flip()

    
    def destroy(self):
        self.doorpart1.destroy()
        self.doorpart2.destroy()
        self.doorpart2.destroy()
        self.doorpart3Tex.destroy()
        self.doorpart2Tex.destroy()
        self.doorpart2wTex.destroy()
        self.poster.destroy()
        self.table.destroy()
        self.posterTexture.destroy()
        self.floor.destroy()
        self.ceilingg.destroy()
        self.floorbtexture.destroy()
        self.walltexture.destroy()
        self.fow_billboard.destroy()
        self.fow_texture.destroy()
        self.light_billboard.destroy()
        self.light_texture.destroy()
        self.texturedLitPass.destroy()
        self.texturedPass.destroy()
        self.boo_body.destroy()
        self.boo_eye.destroy()
        self.boo_eye_pup.destroy()
        self.boo_bars.destroy()

        self.boo_body_texture.destroy()
        self.boo_eye_texture.destroy()
        self.boo_eye_pup_texture.destroy()
        self.boo_bars_texture.destroy()

        self.levtwo.destroy()
        self.levtwoB.destroy()
        self.wall_lev_two_texture.destroy()
        
        pg.quit()

global boobj 
global EnemyL2pos
EnemyL2pos = [[-6 , 16.5, -6.5], [-16, 2, -6.5], [-16, -6.5, -6.5],
                       [5.5, -9.5, -6.5], [16,-6.5,-6.5],[16,2,-6.5],
                       [16,12,-6.5], [5.5,16.5,-6.5], [5.5,12,-6.5],
                       [-6,12,-6.5], [-6,2,-6.5], [-6,-6.5,-6.5],
                       [-1,-6.5,-6.5], [5.5, -6.5, -6.5], [16, -6.5, -6.5],
                       [-1,7,-6.5], [16, 7, -6.5]]
def EnemyL2pos():
    return [[-6 , 16.5, -6.5], [-16, 2, -6.5], [-16, -6.5, -6.5],
                       [5.5, -9.5, -6.5], [16,-6.5,-6.5],[16,2,-6.5],
                       [16,12,-6.5], [5.5,16.5,-6.5], [5.5,12,-6.5],
                       [-6,12,-6.5], [-6,2,-6.5], [-6,-6.5,-6.5],
                       [-1,-6.5,-6.5], [5.5, -6.5, -6.5], [16, -6.5, -6.5],
                       [-1,7,-6.5], [16, 7, -6.5]]
global enemyleveltwopartols
enemyleveltwopartols = [
                        [EnemyL2pos()[2-1], EnemyL2pos()[11-1], EnemyL2pos()[12-1], EnemyL2pos()[5-1]],
                        [EnemyL2pos()[4-1], EnemyL2pos()[9-1], EnemyL2pos()[10-1],EnemyL2pos()[12-1],EnemyL2pos()[3-1]],
                        [EnemyL2pos()[8-1], EnemyL2pos()[14-1], EnemyL2pos()[12-1],EnemyL2pos()[1-1]],
                        [EnemyL2pos()[5-1], EnemyL2pos()[12-1], EnemyL2pos()[10-1], EnemyL2pos()[9-1],EnemyL2pos()[15-1],EnemyL2pos()[6-1]],
                        [EnemyL2pos()[7-1], EnemyL2pos()[9-1], EnemyL2pos()[14-1],EnemyL2pos()[12-1],EnemyL2pos()[1-1]]]
def enemyleveltwopartols():
    return [
                        [EnemyL2pos()[2-1], EnemyL2pos()[11-1], EnemyL2pos()[12-1], EnemyL2pos()[5-1]],
                        [EnemyL2pos()[4-1], EnemyL2pos()[9-1], EnemyL2pos()[10-1],EnemyL2pos()[12-1],EnemyL2pos()[3-1]],
                        [EnemyL2pos()[8-1], EnemyL2pos()[14-1], EnemyL2pos()[12-1],EnemyL2pos()[1-1]],
                        [EnemyL2pos()[5-1], EnemyL2pos()[12-1], EnemyL2pos()[10-1], EnemyL2pos()[9-1],EnemyL2pos()[15-1],EnemyL2pos()[6-1]],
                        [EnemyL2pos()[7-1], EnemyL2pos()[9-1], EnemyL2pos()[14-1],EnemyL2pos()[12-1],EnemyL2pos()[1-1]]]

global indexpatrol,indexpatrolpos
indexpatrol = 0
indexpatrolpos = 0
class Scene:
    global beforekeys,collide
    global speed, runspeed

    global indexpatrol,indexpatrolpos
    enemytarget = (enemyleveltwopartols()[0])[0]
    
    
    beforekeys = []
    velocityY = 0.01
    keys = []
    
    def __init__(self):
        self.curspeed = 0
        self.fows = [
            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [0, 7, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [3, 5, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [3, 9, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [5, 8, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [9, 5, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [5, 2, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [10, 10, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [9, 5, -7.5],
                eulers = [0,0,0],

                
            ),

            SimpleComponent(
                mesh = 'monkey',
                tex ='monkeu'
                ,
                position = [0, 8, -7.5],
                eulers = [0,0,0]
            )
        ]
        self.lights = [
           Light(
                position = [0, 6, -5],
                color = (1, 1, 1), strength= 1.5
                
            ),
            Light(
                position = [2, 0, -5],
                color = (1, 1, 1), strength= 1.5
                
            ),

            Light(
                position = [-2, 0, -5],
                color = (1, 1, 1), strength= 1.5
                
            ),]
        self.lightslevtwo = [
           
            Light(
                position = [0, 3, -5.5],
                color = (1, 1, 1), strength= 3

            ),
            Light(
                position = [12, 12, -5.5],
                color = (1, 1, 1), strength= 3

            ),
           Light(
                position = [0, 12, -5.5],
                color = (1, 1, 1), strength= 3

            ),
           Light(
                position = [-8, 12, -5.5],
                color = (1, 1, 1), strength= 3

            ),
           Light(
                position = [-10, 2, -5.5],
                color = (1, 1, 1), strength= 3

            ),
           Light(
                position = [-10, -6, -5.5],
                color = (1, 1, 1), strength= 3

            ),
           Light(
                position = [12, -6.5, -5.5],
                color = (1, 1, 1), strength= 3

            ),
           Light(
                position = [12, 2.5, -5.5],
                color = (1, 1, 1), strength= 3

            )


        ]
        self.lightslevthree = [
           Light(
                position = [11.365149, 15.442753, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           Light(
                position = [-12.633909, -18.710358, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           Light(
                position = [11.683742,2.8594892, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           
           Light(
                position = [17.235008, -15.391624, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           Light(
                position = [-0.88856035, -10.726019, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           

           Light(
                position = [-15.060681,  -8.165347, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           Light(
                position = [-3.3407845,  8.536253, -5.5],
                color = (1, 1, 1), strength= 3

            ),

           Light(
                position = [-12.453144,  16.426233, -5.5],
                color = (1, 1, 1), strength= 3

            ),

        ]

        

        self.player = Player(
            position = [1,1,-5.5]
        )
        self.enemytarget2 = [3.8,-9.6,-5.8]
        for obj in bacteriamanobject:
            obj.position = (enemyleveltwopartols()[0])[0]
    
    def boxCollider(self, z1, z2, x1, x2, y1, y2):
        global beforePosx
        global beforePosz
        global beforePosy

        # Check if inside the box at X-axis and Check if inside the box at Z-axis and Check if inside the box at Y-axis
        if self.player.position[1] < x1 and self.player.position[1] > x2 and self.player.position[0] > z1 and self.player.position[0] < z2 and self.player.position[2] > y1 and self.player.position[2] < y2:
                #Check if before collsiion z was in collider
             if beforePosz > z1 and beforePosz < z2 :
                self.player.position[1] = beforePosx
                #Check if before collsiion x was in collider
             if beforePosx < x1 and beforePosx > x2 :
                self.player.position[0] = beforePosz
    
              
             return True
        else:
             return False
    def boxTrigger(self, z1, z2, x1, x2, y1, y2, event):
            global beforePosx
            global beforePosz
            global beforePosy


            # Check if inside the box at X-axis and Check if inside the box at Z-axis and Check if inside the box at Y-axis
            if self.player.position[1] < x1 and self.player.position[1] > x2 and self.player.position[0] > z1 and self.player.position[0] < z2 and self.player.position[2] > y1 and self.player.position[2] < y2:
                event()
                
                return True
            else:
                return False

    def PickupKey(self):
        global GotKey, maplevel,leveltwobjects
        GotKey = True
        if maplevel == 1:
            levelonebjects.remove(levelonebjects[len(levelonebjects)-1])
        if maplevel == 2:
            leveltwobjects.remove(leveltwobjects[len(leveltwobjects)-1])
        time.sleep(0.15)
        
    def groundCollider(self, z1, z2, x1, x2, y1, y2):
        global beforePosx
        global beforePosz
        global beforePosy

        # Check if inside the box at X-axis and Check if inside the box at Z-axis and Check if inside the box at Y-axis
        if self.player.position[1] < x1 and self.player.position[1] > x2 and self.player.position[0] > z1 and self.player.position[0] < z2 and self.player.position[2] > y1 and self.player.position[2] < y2:
             if beforePosz > z1 and beforePosz < z2 and beforePosx < x1 and beforePosx > x2:
                self.is_grounded = True
                self.velocityY = 0
                self.player.position[2] = beforePosy
                return True
                #Check if before collsiion z was in collider
             if beforePosz > z1 and beforePosz < z2 :
                self.player.position[1] = beforePosx
                #Check if before collsiion x was in collider
             if beforePosx < x1 and beforePosx > x2 :
                self.player.position[0] = beforePosz
    def CheckDoor(self):
         global GotKey, video,donevideo, running
         global maplevel
         if GotKey:
             maplevel += 1
             GotKey = False
             if maplevel == 1:
                 self.player.position = [-11, 13, -6.5]
             if maplevel == 2:
                 self.player.position = [-9, -24, -6.5]
                 for obj in boobj:
            
                     obj.position = [3.8,0,-5.8]
                     obj.position = [3.8,0,-5.8]
    def normalizevector(self, vec):
         length = math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
         if length == 0:
              length = .01
         return [vec[0]/length,vec[1]/length,vec[2]/length]
    def Abs(self, number):
         if number < 0:
              number *= -1
         return number

    def magnitude(self, V):
         return self.Abs(V[0]) +self.Abs(V[1]) +self.Abs(V[2])  
    def randomtarget(self):
         global boobj, randomenemypositions
         
         self.enemytarget2 = self.player.position
         
         return self.player.position
    def distance(self, v1, v2):
         return math.sqrt(self.Abs(v2[0] - v1[0]) + self.Abs(v2[1] - v1[1]))
    def patrolpos(self):
         global bacteriamanobject, indexpatrol, indexpatrolpos
         indexpatrolpos += 1
         if indexpatrolpos >= len(enemyleveltwopartols()[indexpatrol]):
              indexpatrol = random.randrange(0, len(enemyleveltwopartols()))
              indexpatrolpos = 0
              for obj in bacteriamanobject:
                   obj.position = enemyleveltwopartols()[indexpatrol][indexpatrolpos]

         self.enemytarget = enemyleveltwopartols()[indexpatrol][indexpatrolpos]
    def moveenemy(self):
        global DeltaTime
        if self.distance(self.enemytarget,bacteriamanobject[0].position ) > 0.5 and indexpatrolpos == 0:
             for obj in bacteriamanobject:
                   obj.position = enemyleveltwopartols()[indexpatrol][indexpatrolpos]           
        if self.distance(self.enemytarget,bacteriamanobject[0].position ) < 0.5:
             self.patrolpos()

        targetpos = [self.enemytarget[0] - bacteriamanobject[0].position[0],
                     self.enemytarget[1] - bacteriamanobject[0].position[1],
                     0]

        direction = targetpos
        angle = math.atan2(direction[0], direction[1]) * 57.29578 + -90
        for obj in bacteriamanobject:
             obj.eulers[2] = angle

        EnemySpeed = 2
        targetpos = self.normalizevector(targetpos)
        for obj in bacteriamanobject:
             obj.position[0] += targetpos[0] * (1/60) * EnemySpeed
             obj.position[1] += targetpos[1] * (1/60) * EnemySpeed
             
    def moveenemy2(self):
        global DeltaTime
        if self.distance(self.enemytarget2, boobj[0].position) < 0.07:
             self.enemytarget2 = self.randomtarget()
        targetpos2 = [self.enemytarget2[0] - boobj[0].position[0],
                     self.enemytarget2[1] - boobj[0].position[1],
                     self.enemytarget2[2] - boobj[0].position[2]]
        direction = targetpos2
        angle = math.atan2(direction[0], direction[1]) * 57.29578 + -90
        for obj in boobj:
             obj.eulers[2] = angle
        
        targetpos2 = self.normalizevector(targetpos2)
        EnemySpeed2 = 1.356
        desiredPos = [targetpos2[0] * (1/60) * EnemySpeed2 + boobj[0].position[0],targetpos2[1] * (1/60) * EnemySpeed2 + boobj[0].position[1], -5]
        for obj in boobj:
            
            obj.position = desiredPos
            obj.position = desiredPos

    def Jumpscare(self):
        #Reset Scene
        global maplevel
        if maplevel == 1:
            self.player.position =[-11, 12, -6.5]
            for obj in bacteriamanobject:      
                obj.position = [-6 , 16.5, -6.5]
        if maplevel == 2:
            self.player.position = [-9, -24, -6.5]
            for obj in boobj:
            
                obj.position = [3.8,0,-5.8]
                obj.position = [3.8,0,-5.8]
        
    def update(self, rate):
        global beforekeys,boobj, GotKey
        global beforePosx, beforePosz,beforePosy
        self.gravity = 5
        self.jumpForce = .03
        self.speed = 2.35
        self.runspeed = 7
        self.curspeed = self.speed
        self.is_grounded = False
        global maplevel
        global mapcolliders

        
        
        mapcolliders = [Scene.groundCollider(self, -250, 250, 250, -250, -10, -6.5)]

        #move bacteriaman
        if maplevel == 1:
            self.moveenemy()
        if maplevel == 2:
            self.moveenemy2()
        
        
        if maplevel == 0:
            GotKey = True
            mapcolliders = [Scene.groundCollider(self, -4, 4, -2.8, -4.5, -7, 0),
                         Scene.groundCollider(self, -4, 4, 10.3, 8.4, -7, 0),
                         Scene.groundCollider(self, 3, 4.5, 11.3, -4, -7, 0),
                         Scene.groundCollider(self, -4, -3, 11.3, -4, -7, 0),
                         Scene.groundCollider(self, -0.6, 0.5, 2.6, -11, -7, 0),
                         Scene.groundCollider(self, 1, 3, 8.5, 6.7, -7, -6),
                         #door!
                         Scene.boxTrigger(self, -3, -1, -2.65, -6.7, -7, -6, self.CheckDoor),
                         Scene.groundCollider(self, -250, 250, 250, -250, -10, -6.5),]
            
        if maplevel ==1:
            mapcolliders = [
                     Scene.boxCollider(self, 0.85, 3, 5.6, -1.65, -7, 10),
                     Scene.boxCollider(self,-4.25, -3, 9.55,-4.6, -7, 10),
                     Scene.boxCollider(self, -3.6, 3.6, 9.54, 8.5, -7, 10),
                     Scene.boxCollider(self, -15.15, -14, 15.5, -8.45, -7, 10),
                     Scene.boxCollider(self, -14.46, -7.4, -0.417, -1.564, -7, 10),
                     Scene.boxCollider(self, -14.46, -7.4, -0.417+6, -1.564+6, -7, 10),
                     Scene.boxCollider(self, 7.37, 14.57, -.498, -1.57, -7, 10),
                     Scene.boxCollider(self, 7.37, 14.57, 5.52, 4.4, -7, 10),
                     Scene.boxCollider(self, 13.84, 15,15.5, -8.45, -7, 10),
                     Scene.boxCollider(self, -15.15, 15,15.5, 14.5, -7, 10),
                     Scene.boxCollider(self, -15.15, 15,-7.7, -8.7, -7, 10),
                     Scene.boxTrigger(self, 10.5, 12.45, 4.8, 4.2, -10, 7.5, self.CheckDoor),
                     Scene.boxCollider(self, 10.5, 12.45, 4.8, 4.2, -10, 7.5)
                     ]
            mapcolliders.append(Scene.boxTrigger(self, bacteriamanobject[0].position[0]+-1,bacteriamanobject[0].position[0]+1, bacteriamanobject[0].position[1]+1, bacteriamanobject[0].position[1]+-1, -10, -6.5, self.Jumpscare))

            if not GotKey:
                mapcolliders.append(Scene.boxTrigger(self, 0.8, 1.5, 1, -0.65, -7, 10,self.PickupKey))
        if maplevel == 2:
            
            mapcolliders = [
                         
                         #cene.groundCollider(self, -0.6, 0.6 ,8.5, 6.6, -6.042, 0),
                         Scene.groundCollider(self, -0.593,0.683 ,6.03, -6.647, -7, 0),
                         Scene.groundCollider(self,-6.618, -5.5 ,6.03, -6.647, -7, 0),
                         Scene.groundCollider(self, -6.08, 6.54 ,12.5, 11.268 , -7, 0),
                         Scene.groundCollider(self, 0.3, 6.512 ,5.944, 4.68 , -7, 0),
                         Scene.groundCollider(self, -23.39, 13.515,20.83, 19.44 , -7, 0),
                         Scene.groundCollider(self, 19.684,20.919,25.92, -23.464 , -7, 0),
                         Scene.groundCollider(self,0.715, 20.93,25.89, 24.722 , -7, 0),
                         Scene.groundCollider(self,0.661, 1.93,25.89, 20 , -7, 0),
                         Scene.groundCollider(self,11.56, 24.417,-20.75, -21.95 , -7, 0),
                         Scene.groundCollider(self,-6.07, 12.789,-15.1, -28.55 , -7, 0),
                         Scene.groundCollider(self,-18.28, -4.25,-27.21, -28.469 , -7, 0),
                         Scene.groundCollider(self,-13.131, -11.76,-21.4,-30 , -7, 0),
                         Scene.groundCollider(self,-18.39, -17.09, 20.84,-28.48 , -7, 0),
                         Scene.groundCollider(self,-12.87,-5.5,-5.43,-6.74 , -7, 0),
                         Scene.groundCollider(self,-13.14,-11.77, 12.12,5.43 , -7, 0),
                         Scene.groundCollider(self,11.37,12.73, 12.12,5.43 , -7, 0),
                         Scene.groundCollider(self,-13.05,-6.48, -9.89,-11.178 , -7, 0),
                         Scene.groundCollider(self,-13.148,-11.88, -9.87, -16.38 , -7, 0),
                         
                         Scene.groundCollider(self,8.74, 15.29,0.364, -0.93 , -7, 0),
                         Scene.groundCollider(self, -250, 250, 250, -250, -10, -6.5),
                         Scene.boxTrigger(self,  -13.4, -12.5, 10, 8, -7, 0, self.CheckDoor),
                         Scene.boxCollider(self, -13.4, -12.5, 10, 8, -7, 0)]
            mapcolliders.append(Scene.boxTrigger(self, boobj[0].position[0]+-1,boobj[0].position[0]+1, boobj[0].position[1]+1, boobj[0].position[1]+-1, -10, -6.5, self.Jumpscare))

            if not GotKey:
                    mapcolliders.append(Scene.boxTrigger(self, 1.9, 2.25, 24, 22, -10, -6.5, self.PickupKey))
        
        collide = False
        for col in mapcolliders:
             if col:
                  collider = True
        
         
        keys = pg.key.get_pressed()

        
        if beforekeys != None:
            if keys[pg.K_SPACE] and not beforekeys[pg.K_SPACE] and self.is_grounded:
                self.velocityY = self.jumpForce
        if keys[pg.K_LSHIFT]:
             print(self.player.position)
             
             self.curspeed = self.runspeed
        if keys[pg.K_LCTRL]:
            print(bacteriamanobject[0].position)
        beforekeys = pg.key.get_pressed()
        if not self.is_grounded:
             self.velocityY += -self.gravity * (1/60)/100
        self.player.position[2] += self.velocityY
        if not collide:
             beforePosz = self.player.position[0]
             beforePosx = self.player.position[1]
             beforePosy = self.player.position[2]
             
        
    
    def move_player(self, dPos):
        dPos[0] *= self.curspeed
        dPos[1] *= self.curspeed
        dPos[2] *= self.curspeed
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
        self.player.update_vectors()

class App:

    
    def __init__(self, screenWidth, screenHeight):

        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        self.renderer = GraphicsEngine()

        self.scene = Scene()

        self.lastTime = pg.time.get_ticks()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0
        self.lightCount = 0

        self.mainLoop()
    
    def mainLoop(self):
        pg.mixer.init()

        #I really hate doing this but I need to
        walkSoundw = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        walkSounda = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        walkSounds = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        walkSoundd = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        
        backroundSounds = pg.mixer.Sound('sounds/LightBuzz.mp3')
        backroundSounds.play(-1)
        backroundSounds.set_volume(0.1)
        running = True
        self.scene.beforekeys = pg.key.get_pressed()
        while (running):
           
            #check events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
                    if event.key == pg.K_w:
                        
                        walkSoundw.play(-1)

                        walkSoundw.set_volume(0.025)
                    if event.key == pg.K_a:
                        
                        walkSounda.play(-1)

                        walkSounda.set_volume(0.025)
                    if event.key == pg.K_s:
                        
                        walkSounds.play(-1)

                        walkSounds.set_volume(0.025)
                    if event.key == pg.K_d:
                        
                        walkSoundd.play(-1)

                        walkSoundd.set_volume(0.025)

                    

                    

                
            pressed_keys = pg.key.get_pressed()
            if not pressed_keys[pg.K_w]:
                        
                walkSoundw.stop()

                walkSoundw.set_volume(0.025)

            if not pressed_keys[pg.K_a]:
                        
                walkSounda.stop()

                walkSounda.set_volume(0.025)
            if not pressed_keys[pg.K_s]:
                        
                walkSounds.stop()

                walkSounds.set_volume(0.025)
            if not pressed_keys[pg.K_d]:
                        
                walkSoundd.stop()

                walkSoundd.set_volume(0.025)
                
               
            
            self.handleKeys()
            self.handleMouse()

            self.scene.update(self.frameTime * 0.05)
            
            self.renderer.render(self.scene)

            #timing
            self.calculateFramerate()
        self.quit()
    
    def handleKeys(self):
        global DeltaTime

        keys = pg.key.get_pressed()
        key = 0
        directionModifier = 0
        
        if keys[pg.K_w]:
            key += 1
        if keys[pg.K_a]:
            key += 2
        if keys[pg.K_s]:
            key += 4
        if keys[pg.K_d]:
            key += 8
        
        if key > 0:
            if key == 3:
                directionModifier = 45
            elif key == 2 or key == 7:
                directionModifier = 90
            elif key == 6:
                directionModifier = 135
            elif key == 4 or key == 14:
                directionModifier = 180
            elif key == 12:
                directionModifier = 225
            elif key == 8 or key == 13:
                directionModifier = 270
            elif key == 9:
                directionModifier = 315
            
            dPos = [
                (1/60) * np.cos(np.deg2rad(self.scene.player.theta + directionModifier)),
                (1/60) * np.sin(np.deg2rad(self.scene.player.theta + directionModifier)),
                
                0
            ]

            self.scene.move_player(dPos)
        
    
    def handleMouse(self):
        
        (x,y) = pg.mouse.get_pos()
        
       
        
        theta_increment = 0.25 * ((self.screenWidth // 2) - x)
        phi_increment = 0.25 * ((self.screenHeight // 2) - y)
        self.scene.spin_player(theta_increment, phi_increment)
        pg.mouse.set_pos((self.screenWidth // 2,self.screenHeight // 2))
    
    def calculateFramerate(self):
        global FPS, DeltaTime
        self.currentTime = pg.time.get_ticks()
        delta = self.currentTime - self.lastTime
        if (delta >= 1000):
            framerate = max(1,int(1000.0 * self.numFrames/delta))
            pg.display.set_caption(f"Running at {framerate} fps.")
            self.lastTime = self.currentTime
            self.numFrames = -1
            self.frameTime = float(120.0 / max(1,framerate))
            FPS = framerate
        self.numFrames += 1
        DeltaTime = 1 / FPS

    def quit(self):
        
        self.renderer.destroy()




#load the music

#pg.mixer.init()
#buzz = pg.mixer.Sound('sounds/LightBuzz.mp3')
#buzz.play()

#buzz.set_volume(0.008)


class RenderPassTextured3D:

    @lru_cache(maxsize=None)
    def __init__(self, shader):

        #initialise opengl
        self.shader = shader
        glUseProgram(self.shader)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 640/480, 
            near = 0.1, far = 100, dtype=np.float32
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader,"projection"),
            1, GL_FALSE, projection_transform
        )
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.tintLoc = glGetUniformLocation(self.shader, "tint")
    
    def render(self, scene, engine):

        glUseProgram(self.shader)
        playerpos = scene.player.position
        for i,light in enumerate(scene.lights):

            glUniform3fv(self.tintLoc, 1, light.color)

            engine.light_texture.use()

            directionFromPlayer = light.position - scene.player.position
            angle1 = np.arctan2(-directionFromPlayer[1],directionFromPlayer[0])
            dist2d = math.sqrt(directionFromPlayer[0] ** 2 + directionFromPlayer[1] ** 2)
            angle2 = np.arctan2(directionFromPlayer[2],dist2d)

            model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
            model_transform = pyrr.matrix44.multiply(
                model_transform,
                pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32)
            )
            model_transform = pyrr.matrix44.multiply(
                model_transform,
                pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32)
            )
            model_transform = pyrr.matrix44.multiply(
                model_transform,
                pyrr.matrix44.create_from_translation(light.position,dtype=np.float32)
            )
            glUniformMatrix4fv(glGetUniformLocation(self.shader,"model"),1,GL_FALSE,model_transform)

            glBindVertexArray(engine.light_billboard.vao)
            
            glDrawArrays(GL_TRIANGLES, 0, engine.light_billboard.vertexCount)
        view_transform = pyrr.matrix44.create_look_at(
            eye = scene.player.position,
            target = scene.player.position + scene.player.forwards,
            up = scene.player.up, dtype = np.float32
        )
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view_transform)
        


       

    @lru_cache(maxsize=None)
    def destroy(self):

        glDeleteProgram(self.shader)
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


class BillBoard:
    @lru_cache(maxsize=None)
    def __init__(self, w, h):
        #x,y,z, s,t, normal
        self.vertices = (
            0, -w/2,  h/2, 0, 0, -1, 0, 0,
            0, -w/2, -h/2, 0, 1, -1, 0, 0,
            0,  w/2, -h/2, 1, 1, -1, 0, 0,

            0, -w/2,  h/2, 0, 0, -1, 0, 0,
            0,  w/2, -h/2, 1, 1, -1, 0, 0,
            0,  w/2,  h/2, 1, 0, -1, 0, 0
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.vertexCount = 6
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))
    @lru_cache(maxsize=None)
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

myApp = App(1200,800)
