from OpenGL.GLU import *
from OpenGL.GL import *
import glfw
from PIL import Image
import math

# TODO: Switch from immediate rendering to using VBO + Shaders

class BitfieldGeneratorModelSegment:
    def __init__(self, segmentNumber, segment):
        self.segment = segment

        segmentNumber += 1 # Pure black (0, 0, 0) is reserved for negative space.
        r = (segmentNumber >> 16) & 0xFF
        g = (segmentNumber >> 8) & 0xFF
        b = segmentNumber & 0xFF

        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        self._compile_list((r/255, g/255, b/255))
        glEndList()

        self.list_back = glGenLists(1)
        glNewList(self.list_back, GL_COMPILE)
        self._compile_list_backside()
        glEndList()
    
    def _compile_list(self, color):
        numBatches = len(self.segment.batches)
        for i in range(0, numBatches):
            batch = self.segment.batches[i]
            verticesIndex = batch.vertOffset
            trianglesOffset = batch.triOffset
            numTriangles = batch.numTriangles
            glBegin(GL_TRIANGLES)
            for j in range(0, numTriangles):
                tri = self.segment.triangles[trianglesOffset + j]
                vert0 = self.segment.vertices[verticesIndex + tri.vi0]
                vert1 = self.segment.vertices[verticesIndex + tri.vi1]
                vert2 = self.segment.vertices[verticesIndex + tri.vi2]
                glColor3f(color[0], color[1], color[2])
                glVertex3f(vert0.x, vert0.y, vert0.z)
                glVertex3f(vert1.x, vert1.y, vert1.z)
                glVertex3f(vert2.x, vert2.y, vert2.z)
            glEnd()
    
    def _compile_list_backside(self):
        numBatches = len(self.segment.batches)
        for i in range(0, numBatches):
            batch = self.segment.batches[i]
            verticesIndex = batch.vertOffset
            trianglesOffset = batch.triOffset
            numTriangles = batch.numTriangles
            glBegin(GL_TRIANGLES)
            for j in range(0, numTriangles):
                tri = self.segment.triangles[trianglesOffset + j]
                vert0 = self.segment.vertices[verticesIndex + tri.vi0]
                vert1 = self.segment.vertices[verticesIndex + tri.vi1]
                vert2 = self.segment.vertices[verticesIndex + tri.vi2]
                glColor3f(0, 0, 0) # Black 
                glVertex3f(vert0.x, vert0.y, vert0.z)
                glVertex3f(vert2.x, vert2.y, vert2.z)
                glVertex3f(vert1.x, vert1.y, vert1.z)
            glEnd()


    def render(self):
        glCallList(self.list)

    def render_back(self):
        glCallList(self.list_back)

class BitfieldGeneratorModel:
    def __init__(self, model):
        self.model = model
        self.renderSegments = []
        for i in range(0, len(model.segments)):
            self.renderSegments.append(BitfieldGeneratorModelSegment(i, model.segments[i]))
    
    def render(self, backsideIgnoreIndex=-1):
        for i in range(0, len(self.renderSegments)):
            self.renderSegments[i].render()
            if i != backsideIgnoreIndex:
                self.renderSegments[i].render_back()

def get_visible_segments_from_position(renderModel, segNum, shotSize, x, y, z, tx, ty, tz, tmpFilename='test.png'):
    visibleSegments = set()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_TEXTURE_2D)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    gluLookAt(x, y, z, tx, ty, tz, 0, 1, 0)
    renderModel.render(segNum)
    glPopMatrix()
    pixels = glReadPixels(0,0,shotSize[0],shotSize[1],GL_RGB,GL_UNSIGNED_BYTE)
    new_image = Image.frombytes('RGB', shotSize, pixels, 'raw')
    #new_image = ImageOps.flip(new_image)
    #new_image.save(tmpFilename)
    uniqueColors = new_image.getcolors()
    for entry in uniqueColors:
        color = entry[1] # entry[0] is the number of times this color appeared.
        segmentIndex = ((color[0] << 16) | (color[1] << 8) | color[2]) - 1 # Get segment index from color
        if segmentIndex >= 0:
            visibleSegments.add(segmentIndex)
    return visibleSegments

def init_gl(width, height):
    glShadeModel(GL_SMOOTH)
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glFrontFace(GL_CCW)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthFunc(GL_LEQUAL)
    glDepthMask(GL_TRUE)
    glAlphaFunc(GL_GEQUAL, 0.01)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(90, width/height, 1, 99999)

def construct_bitfield_from_visible_segments(visibleSegmentsList, numSegments):
    numBytesPerBitfield = math.ceil(numSegments / 8)
    val = 0
    for segmentIndex in visibleSegmentsList:
        byteIndex = (numBytesPerBitfield - (segmentIndex // 8) - 1) * 8
        val |= 1 << (byteIndex + (segmentIndex & 7))
    #print(hex(val) + ' = ' + str(visibleSegmentsList))
    return val

def get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x, y, z):
    visibleSegments = set()
    visibleSegments = visibleSegments.union(get_visible_segments_from_position(renderModel, i, shotSize, x, y, z, x + 1, y, z))
    visibleSegments = visibleSegments.union(get_visible_segments_from_position(renderModel, i, shotSize, x, y, z, x, y, z + 1))
    visibleSegments = visibleSegments.union(get_visible_segments_from_position(renderModel, i, shotSize, x, y, z, x - 1, y, z))
    visibleSegments = visibleSegments.union(get_visible_segments_from_position(renderModel, i, shotSize, x, y, z, x, y, z - 1))
    return visibleSegments
    
def process_segment_bitfields(model, shotSize):
    renderModel = BitfieldGeneratorModel(model)
    init_gl(shotSize[0], shotSize[1])
    print("Processing segments, this may take a few seconds...")
    numSegments = len(model.segments)
    model.bspTree.bitfields = []
    for i in range(0, len(model.segments)):
        seg = model.segments[i]
        x, y, z = seg.get_center()
        sizeX, sizeY, sizeZ = seg.get_bounding_box_size()
        halfSizeX = sizeX // 2
        halfSizeZ = sizeZ // 2
        # This is SLOW! How do I speed this up? Multiprocessing just makes things slower.
        visibleSegments = set()
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x + halfSizeX, y, z))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x - halfSizeX, y, z))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x, y, z + halfSizeZ))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x, y, z - halfSizeZ))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x + halfSizeX, y, z + halfSizeZ))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x - halfSizeX, y, z + halfSizeZ))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x + halfSizeX, y, z - halfSizeZ))
        visibleSegments = visibleSegments.union(get_visible_segments_from_surrounding_position(renderModel, i, shotSize, x - halfSizeX, y, z - halfSizeZ))
        model.bspTree.bitfields.append(construct_bitfield_from_visible_segments(list(visibleSegments), numSegments))
        

def calculate_segment_bitfields(model):
    if not glfw.init():
        raise SystemExit('Error: Could not initialize glfw!')
    # Set window hint NOT visible
    glfw.window_hint(glfw.VISIBLE, False)
    # Create a windowed mode window and its OpenGL context
    renderSize = (360, 240)
    window = glfw.create_window(renderSize[0], renderSize[1], "hidden window", None, None)
    if not window:
        glfw.terminate()
        raise SystemExit('Error: glfw could not make the hidden window!')
    # Make the window's context current
    glfw.make_context_current(window)
    process_segment_bitfields(model, renderSize)


