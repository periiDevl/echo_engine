


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

global G_is
G_is = True
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
                            vertices.append(x)
                        for x in faceTextures[i]:
                            vertices.append(x)
                        for x in faceNormals[i]:
                            vertices.append(x)
                        for x in tangent:
                            vertices.append(x)
                        for x in bitangent:
                            vertices.append(x)
                line = f.readline()
        return vertices
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))


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
            self.viewTransform = pyrr.matrix44.create_look_at(
                eye = self.position,
                target = self.position + self.forwards,
                up = self.up, 
                dtype = np.float32
            )
class SimpleComponent:

    
    def __init__(self, mesh, tex ,position, eulers):
        self.mesh = mesh
        self.tex = tex
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
    
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
        def createL3():

            for nonscriptname in levelthreebjects:

                
                
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


    def __init__(self):

        self.screenWidth = 1200
        self.screenHeight = 800

        #initialise pygame
        pg.init()
        pg.mouse.set_visible(False)
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
            near = 0.1, far = 50, dtype=np.float32
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
        self.wood_texture = AdvancedMaterial("moss", "bmp")
        self.cube_mesh = Mesh("models/monkey.obj", 1, 1)
        #self.medkit_texture = AdvancedMaterial("medkit")
        #self.medkit_billboard = BillBoard(w = 0.6, h = 0.5)

        glUseProgram(self.unlit_shader)
        self.light_texture = Material("gfx/lightPlaceHolder.png")
        self.light_billboard = BillBoard(w = 0.2, h = 0.1)

        self.screen = TexturedQuad(0, 0, 1, 1)

        self.font = Font()
        self.fps_label = TextLine("FPS: ", self.font, (-0.9, 0.9), (0.05, 0.05))
    
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

        self.fps_label.build_text(f"FPS: {new_fps}", self.font)
    
    def render(self, scene):
        
        #First pass
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbos[0])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        #lit shader
        glUseProgram(self.lighting_shader)

        glUniformMatrix4fv(self.viewMatrixLocation["lit"], 1, GL_FALSE, scene.player.viewTransform)

        glUniform3fv(self.cameraPosLoc, 1, scene.player.position)

        for i,light in enumerate(scene.lights):
            glUniform3fv(self.lightLocation["position"][i], 1, light.position)
            glUniform3fv(self.lightLocation["color"][i], 1, light.color)
            glUniform1f(self.lightLocation["strength"][i], light.strength)

        self.wood_texture.use()
        glBindVertexArray(self.cube_mesh.vao)
        for cube in scene.cubes:
            glUniformMatrix4fv(self.modelMatrixLocation["lit"],1,GL_FALSE,cube.modelTransform)
            glDrawArrays(GL_TRIANGLES, 0, self.cube_mesh.vertex_count)
        
        #self.medkit_texture.use()
        #glBindVertexArray(self.medkit_billboard.vao)
        #for medkit in scene.medkits:
         #   glUniformMatrix4fv(self.modelMatrixLocation["lit"],1,GL_FALSE,medkit.modelTransform)
          #  glDrawArrays(GL_TRIANGLES, 0, self.medkit_billboard.vertexCount)

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
        glBindVertexArray(self.fps_label.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.fps_label.vertex_count)

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

        #CRT emulation pass
        glUseProgram(self.post_shader)
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

        self.cube_mesh.destroy()
        self.wood_texture.destroy()
        #self.medkit_billboard.destroy()
        #self.medkit_texture.destroy()
        self.light_billboard.destroy()
        self.light_texture.destroy()
        self.font.destroy()
        self.fps_label.destroy()
        glDeleteProgram(self.lighting_shader)
        glDeleteProgram(self.unlit_shader)
        glDeleteProgram(self.post_shader)
        glDeleteTextures(len(self.colorBuffers), self.colorBuffers)
        glDeleteRenderbuffers(len(self.depthStencilBuffers), self.depthStencilBuffers)
        glDeleteFramebuffers(len(self.fbos), self.fbos)
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

        self.cubes = [
            SimpleComponent(
                position = [6,0,1],
                eulers = [0,0,0],
                mesh = 1,
                tex = 1
            ),
        ]

        
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
           BrightBillboard
            (
                position = [2, 0, -5],
                color = [1, 1, 1], strength= 1.5
                
            ),

            ]
        self.lightslevtwo = [
           BrightBillboard
            (
                position = [2, 0, -5],
                color = [1, 1, 1], strength= 1.5
                
            ),
            
        ]

        

        self.player = Player(
            position = [1,1,-5.5]
        )
        self.enemytarget2 = [3.8,-9.6,-5.8]
        
    
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
        pg.mixer.init()
        pickupkeySound = pg.mixer.Sound('sounds/pickupkey.wav')
        pickupkeySound.play()
        pickupkeySound.set_volume(0.1)
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
        
        G_is = self.is_grounded

        
        
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
            
            
        
                #jumpSound = pg.mixer.Sound('sounds/startjump.wav')
                #jumpSound.set_volume(0.3)
                #jumpSound.play(1)
                self.velocityY = self.jumpForce
        if keys[pg.K_LSHIFT]:
             print(self.player.position)
             
             self.curspeed = self.runspeed
        
            
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

    
    def __init__(self, winW, winH):

        self.screenWidth = winW
        self.screenHeight = winH

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
        #walkSoundw = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        #walkSounda = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        #walkSounds = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        #walkSoundd = pg.mixer.Sound('sounds/walkingOnWoodSound.mp3')
        
        #backroundSounds = pg.mixer.Sound('sounds/backroundSound.wav')
        #backroundSounds.play(-1)
        #backroundSounds.set_volume(0.3)
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
                        pass
                        #walkSoundw.play(-1)

                        #walkSoundw.set_volume(0.025)
                    if event.key == pg.K_a:
                        pass
                        #walkSounda.play(-1)

                        #walkSounda.set_volume(0.025)
                    if event.key == pg.K_s:
                        pass
                        #walkSounds.play(-1)

                        #walkSounds.set_volume(0.025)
                    if event.key == pg.K_d:
                        pass
                        #walkSoundd.play(-1)

                        #walkSoundd.set_volume(0.025)

                    

                    

            global G_is
        
            pressed_keys = pg.key.get_pressed()
            if not pressed_keys[pg.K_w] or G_is == False:
                        
                #walkSoundw.stop()

                #walkSoundw.set_volume(0.025)
                pass
            if not pressed_keys[pg.K_a] or G_is == False:
                        
                #walkSounda.stop()

                #walkSounda.set_volume(0.025)
                pass
            if not pressed_keys[pg.K_s] or G_is == False:
                        
                #walkSounds.stop()

                #walkSounds.set_volume(0.025)
                pass
            if not pressed_keys[pg.K_d] or G_is == False:
                        
                #walkSoundd.stop()

                #walkSoundd.set_volume(0.025)
                pass
               
            
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
