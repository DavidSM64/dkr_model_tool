from OpenGL.GLU import *
from OpenGL.GL import *
import colorsys
import numpy

# TODO: Switch from immediate rendering to using VBO + Shaders

class PreviewRenderModelSegment:
    def __init__(self, segment, textures):
        self.segment = segment

        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        self._compile_list(textures)
        glEndList()
    
    def _compile_list(self, textures):
        lastTexIndex = -1
        numBatches = len(self.segment.batches)
        for i in range(0, numBatches):
            batch = self.segment.batches[i]
            if batch.texIndex != lastTexIndex:
                if batch.texIndex == -1:
                    glDisable(GL_TEXTURE_2D)
                else:
                    if lastTexIndex == -1:
                        glEnable(GL_TEXTURE_2D)
                    textures[batch.texIndex].bind()
                lastTexIndex = batch.texIndex
            verticesIndex = batch.vertOffset
            trianglesOffset = batch.triOffset
            numTriangles = batch.numTriangles
            glBegin(GL_TRIANGLES)
            for j in range(0, numTriangles):
                tri = self.segment.triangles[trianglesOffset + j]
                vert = self.segment.vertices[verticesIndex + tri.vi0]
                color = vert.color.as_doubles()
                glColor3f(color[0], color[1], color[2])
                glTexCoord2f(tri.uv0.u, tri.uv0.v)
                glVertex3f(vert.x, vert.y, vert.z)
                vert = self.segment.vertices[verticesIndex + tri.vi1]
                color = vert.color.as_doubles()
                glColor3f(color[0], color[1], color[2])
                glTexCoord2f(tri.uv1.u, tri.uv1.v)
                glVertex3f(vert.x, vert.y, vert.z)
                vert = self.segment.vertices[verticesIndex + tri.vi2]
                color = vert.color.as_doubles()
                glColor3f(color[0], color[1], color[2])
                glTexCoord2f(tri.uv2.u, tri.uv2.v)
                glVertex3f(vert.x, vert.y, vert.z)
            glEnd()


    def render(self):
        glCallList(self.list)

class PreviewRenderModelTexture:
    def __init__(self, texture):
        self.texture = texture
        if self.texture.tex == None:
            return
        self.glTex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.glTex)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        texData = numpy.asarray(texture.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texture.width, texture.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texData)

    def bind(self):
        if self.texture.tex == None:
            return
        glBindTexture(GL_TEXTURE_2D, self.glTex)

class PreviewRenderModel:
    def __init__(self, model):
        self.model = model
        self.renderSegments = []
        self.renderTextures = []
        for texture in model.textures:
            self.renderTextures.append(PreviewRenderModelTexture(texture))
        for segment in model.segments:
            self.renderSegments.append(PreviewRenderModelSegment(segment, self.renderTextures))
    
    def render(self):
        for renderSegment in self.renderSegments:
            renderSegment.render()



