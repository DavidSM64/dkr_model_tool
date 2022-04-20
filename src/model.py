from xml.dom.expatbuilder import parseString
from util import *

MAX_NUM_VERTS_PER_BATCH = 32
MAX_NUM_TRIS_PER_BATCH = 16

class UV:
    def __init__(self, u, v):
        self.u = u
        self.v = v
        self.parsedU = False
        self.parsedV = False

    def parse_uv(self, texWidth, texHeight):
        self.parse_u(texWidth)
        self.parse_v(texHeight)

    def parse_u(self, texWidth):
        if self.parsedU:
            raise SystemExit("This U coordinate has already been parsed!")
        self.parsedU = True
        if(texWidth == 0):
            self.u = 0
            return
        self.u /= (texWidth * 32.0)

    def parse_v(self, texHeight):
        if self.parsedV:
            raise SystemExit("This V coordinate has already been parsed!")
        self.parsedV = True
        if(texHeight == 0):
            self.v = 0
            return
        self.v /= (texHeight * 32.0)

    def get_u(self, texWidth):
        return to_s16(self.u * texWidth * 32.0)

    def get_v(self, texHeight):
        return to_s16(self.v * texHeight * 32.0)

UV_ZERO = UV(0, 0)

class VertexColor:
    def __init__(self, r=255, g=255, b=255, a=255):
        self.set(r, g, b, a)

    def set(self, r, g, b, a=255):
        # Color channels are unsigned 8-bit values
        if r > 0.0 and r < 1.0:
            r *= 255
        if g > 0.0 and g < 1.0:
            g *= 255
        if b > 0.0 and b < 1.0:
            b *= 255
        if a > 0.0 and a < 1.0:
            a *= 255
        self.r = to_u8(r)
        self.g = to_u8(g)
        self.b = to_u8(b)
        self.a = to_u8(a)

    def set_from_hex_string(self, hexString):
        hexStringLower = hexString.lower() # The hex string should be case insensitive
        if hexStringLower.startswith('0x'):
            hexStringLower = hexStringLower[2:] # Removing the leading 0x
        elif hexStringLower.startswith('$') or hexStringLower.startswith('#'):
            hexStringLower = hexStringLower[1:] # Removing the leading $/#
        hexStringLen = len(hexStringLower)
        if hexStringLen == 6 or hexStringLen == 8:
            try:
                self.r = int(hexStringLower[0:2], 16)
                self.g = int(hexStringLower[2:4], 16)
                self.b = int(hexStringLower[4:6], 16)
                if hexStringLen == 8:
                    self.a = int(hexStringLower[6:8], 16)
                return
            except:
                pass
        raise SystemExit('Error: Invalid hex string: "' + hexString + '"')

    # Valid color string values:
    #   3 integers  (RGB): 250 100 50
    #   4 integers (RGBA): 250 100 50 255
    #   3 doubles (must have the decimal point)  (RGB): 0.9 0.4 0.1 
    #   4 doubles (must have the decimal point) (RGBA): 0.9 0.4 0.1 1.0
    #   (Note: You can mix integers and doubles)
    #   1 hex value (RGB): F05511
    #               (RGB): #F05511
    #               (RGB): $F05511
    #               (RGB): 0xF05511
    #              (RGBA): F05511FF
    #              (RGBA): #F05511FF
    #              (RGBA): $F05511FF
    #              (RGBA): 0xF05511FF
    def set_from_string(self, stringValue):
        stringValue = stringValue.strip() # Remove leading/trailing whitespace
        errorOccured = False
        if '  ' in stringValue:
            errorOccured = True
        try:
            if not errorOccured:
                parts = stringValue.split(' ')
                numParts = len(parts)
                if numParts == 1:
                    self.set_from_hex_string(parts[0])
                elif numParts == 3 or numParts == 4:
                    values = [ 255, 255, 255, 255 ]
                    for i in range(0, numParts):
                        if '.' in parts[i]: # Detect if channel is a double
                            values[i] = round(float(parts[i]) * 255.0)
                        else:
                            values[i] = int(parts[i])
                    self.set(values[0], values[1], values[2], values[3])
                else:
                    errorOccured = True
        except:
            errorOccured = True

        if errorOccured:
            raise SystemExit('Error: The color "' + stringValue + '" is poorly formatted.')

    def as_doubles(self):
        return (self.r / 255.0, self.g / 255.0, self.b / 255.0, self.a /255.0)

    def as_rgb_hex_string(self):
        return "#{:06x}".format((self.r << 16) | (self.g << 8) | self.b).upper()

    def as_rgba_hex_string(self):
        return "#{:08x}".format((self.r << 24) | (self.g << 16) | (self.b << 8) | self.a).upper()

    def as_hex_string(self):
        if self.a < 255:
            return self.as_rgba_hex_string()
        return self.as_rgb_hex_string()
    
    def __eq__(self, other): 
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
    
    def __repr__(self):
        return self.as_hex_string()

class Vertex:
    def __init__(self, x, y, z, r=255, g=255, b=255, a=255):
        # Position coordinates are signed 16-bit values
        self.x = to_s16(x)
        self.y = to_s16(y)
        self.z = to_s16(z)
        self.color = VertexColor(r, g, b, a)

    def set_color(self, r, g, b, a=255):
        self.color.set(r, g, b, a)

    def __eq__(self, other): 
        if other == None:
            return False
        return self.in_same_position_as_other_vertex(other) and self.color == other.color

    def in_same_position_as_other_vertex(self, other):
        if other == None:
            return False
        return self.x == other.x and self.y == other.y and self.z == other.z

# Currently known triangle flags
TRIANGLE_FLAG_RENDER_BACKFACE = 0x40

class Triangle:
    def __init__(self, flags, vi0, vi1, vi2, uv0 = UV_ZERO, uv1 = UV_ZERO, uv2 = UV_ZERO):
        self.flags = flags
        # Indices into the vertex array
        self.vi0 = vi0
        self.vi1 = vi1
        self.vi2 = vi2
        # Indices into the uv array
        self.uv0 = uv0
        self.uv1 = uv1
        self.uv2 = uv2

class Model3DBatch:
    def __init__(self, texIndex=-1, flags=0, vertOffset=0, numVertices=0, triOffset=0, numTriangles=0):
        self.texIndex = texIndex
        self.vertOffset = vertOffset
        self.triOffset = triOffset
        self.numVertices = numVertices
        self.numTriangles = numTriangles
        self.flags = flags
    
    def __repr__(self):
        return str(self.texIndex) + ":verts{" + str(self.vertOffset) + "," + str(self.numVertices) + "}"

class Model3DSegment:
    def __init__(self):
        self.batches = []
        self.vertices = []
        self.triangles = []

    # Should only be called internally.
    def _add_vertices(self, curBatchIndex, texIndex, flags, vert0, vert1, vert2):
        indices = [-1, -1, -1]
        numberOfNewVerts = 3
        startIndex = self.batches[curBatchIndex].vertOffset
        endIndex = startIndex + self.batches[curBatchIndex].numVertices

        # First check if vertices already exists in current batch
        localVertIndex = 0
        for i in range(startIndex, endIndex):
            if indices[0] == -1 and self.vertices[i] == vert0:
                indices[0] = localVertIndex
                numberOfNewVerts -= 1
            if indices[1] == -1 and self.vertices[i] == vert1:
                indices[1] = localVertIndex
                numberOfNewVerts -= 1
            if indices[2] == -1 and self.vertices[i] == vert2:
                indices[2] = localVertIndex
                numberOfNewVerts -= 1
            localVertIndex += 1

        # Batches can only have up to 32 vertices, so we need to check for that.
        if self.batches[curBatchIndex].numVertices + numberOfNewVerts > 32:
            self._new_batch(curBatchIndex, texIndex, flags)
            curBatchIndex += 1

        # Add vertices to batch if they we're not already.
        if indices[0] == -1:
            self.vertices.append(vert0)
            indices[0] = self.batches[curBatchIndex].numVertices
            self.batches[curBatchIndex].numVertices += 1
        if indices[1] == -1:
            self.vertices.append(vert1)
            indices[1] = self.batches[curBatchIndex].numVertices
            self.batches[curBatchIndex].numVertices += 1
        if indices[2] == -1:
            self.vertices.append(vert2)
            indices[2] = self.batches[curBatchIndex].numVertices
            self.batches[curBatchIndex].numVertices += 1
        return (indices, curBatchIndex)

    # Should only be called internally.
    def _new_batch(self, curBatchIndex, texIndex, flags):
        newBatch = Model3DBatch(texIndex, flags)
        newBatch.vertOffset = self.batches[curBatchIndex].vertOffset + self.batches[curBatchIndex].numVertices
        newBatch.triOffset = self.batches[curBatchIndex].triOffset + self.batches[curBatchIndex].numTriangles
        self.batches.append(newBatch)

    def add_triangle(self, texIndex, batchFlags, flags, vert0, vert1, vert2, uv0, uv1, uv2):
        curBatchIndex = len(self.batches) - 1
        # Check if there are no batches, and create the first one if so.
        if curBatchIndex == -1: 
            self.batches.append(Model3DBatch(texIndex, batchFlags))
            curBatchIndex += 1
        # Check if the texture or flags have changed. If so, then create a new batch.
        elif texIndex != self.batches[curBatchIndex].texIndex or batchFlags != self.batches[curBatchIndex].flags:
            self._new_batch(curBatchIndex, texIndex, batchFlags)
            curBatchIndex += 1
        indices,curBatchIndex = self._add_vertices(curBatchIndex, texIndex, batchFlags, vert0, vert1, vert2)
        self.triangles.append(Triangle(flags, indices[0], indices[1], indices[2], uv0, uv1, uv2))
        self.batches[curBatchIndex].numTriangles += 1
        # Batches can only have up to 16 triangles, so create a new one if we've reached the limit.
        if self.batches[curBatchIndex].numTriangles >= 16:
            self._new_batch(curBatchIndex, texIndex, batchFlags)
            curBatchIndex += 1

    def get_texture_index_from_triangle_index(self, triIndex):
        for b in self.batches:
            if triIndex >= b.triOffset and triIndex < b.triOffset + b.numTriangles:
                return b.texIndex
        raise SystemExit('Error Invalid triangle index "' + str(triIndex) + '"')

    def get_vertices_from_triangle_index(self, triIndex):
        vert0 = vert1 = vert2 = None

        tri = self.triangles[triIndex]
        for batch in self.batches:
            if triIndex >= batch.triOffset and triIndex < batch.triOffset + batch.numTriangles:
                vert0 = self.vertices[batch.vertOffset + tri.vi0]
                vert1 = self.vertices[batch.vertOffset + tri.vi1]
                vert2 = self.vertices[batch.vertOffset + tri.vi2]
        
        if vert0 == None or vert1 == None or vert2 == None:
            raise SystemExit('Error: get_vertices_from_triangle_index() failed!')

        return (vert0, vert1, vert2)

    def vertex_is_in_other(self, v0, vo0, vo1, vo2):
        if v0.in_same_position_as_other_vertex(vo0):
            return True
        elif v0.in_same_position_as_other_vertex(vo1):
            return True
        elif v0.in_same_position_as_other_vertex(vo2):
            return True
        return False

    def get_collision_data_for_triangle(self, triIndex):
        outIndices = [ triIndex, triIndex, triIndex ]
        checkIndices = [ True, True, True ]

        vert0, vert1, vert2 = self.get_vertices_from_triangle_index(triIndex)

        for i in range(0, len(self.triangles)):
            if i == triIndex:
                continue
            if not checkIndices[0] and not checkIndices[1] and not checkIndices[2]: # Found all edges, so exit.
                break
            
            otherVert0, otherVert1, otherVert2 = self.get_vertices_from_triangle_index(i)
            vert0IsInOther = self.vertex_is_in_other(vert0, otherVert0, otherVert1, otherVert2)
            vert1IsInOther = self.vertex_is_in_other(vert1, otherVert0, otherVert1, otherVert2)
            vert2IsInOther = self.vertex_is_in_other(vert2, otherVert0, otherVert1, otherVert2)

            if checkIndices[0] and vert0IsInOther and vert1IsInOther: # Check edge 01
                outIndices[0] = i
                checkIndices[0] = False
            if checkIndices[1] and vert1IsInOther and vert2IsInOther: # Check edge 12
                outIndices[1] = i
                checkIndices[1] = False
            if checkIndices[2] and vert2IsInOther and vert0IsInOther: # Check edge 20
                outIndices[2] = i
                checkIndices[2] = False

        return tuple(outIndices)
    def get_bounding_box(self):
        maxPos = [-999999, -999999, -999999]
        minPos = [999999, 999999, 999999]

        for vert in self.vertices:
            minPos[0] = min(minPos[0], vert.x)
            minPos[1] = min(minPos[1], vert.y)
            minPos[2] = min(minPos[2], vert.z)
            maxPos[0] = max(maxPos[0], vert.x)
            maxPos[1] = max(maxPos[1], vert.y)
            maxPos[2] = max(maxPos[2], vert.z)

        return (minPos, maxPos)

texNumber = 0

class TextureNode:
    def __init__(self, tex, width, height, format, collisionType, originalTexIndex = -1):
        global texNumber
        self.tex = tex
        self.width = width
        self.height = height
        self.format = format
        self.collisionType = collisionType
        self.name = "tex_" + str(texNumber) # Default name for this texture.
        texNumber += 1
        self.originalTexIndex = originalTexIndex # Only when importing from a DKR binary file.
    
    def get_format(self):
        return self.format & 0x7F

    def set_name(self, newName):
        self.name = newName

class BspTreeNode:
    def __init__(self, splitAxis, splitValue, segmentToRender, leftIndex = -1, left = None, rightIndex = -1, right = None):
        self.splitAxis = splitAxis
        self.splitValue = splitValue
        self.segmentNumber = segmentToRender
        self.leftIndex = leftIndex
        self.left = left
        self.rightIndex = rightIndex
        self.right = right

class BspTree:
    def __init__(self):
        self.rootNode = None
        self.bitfields = []

class Model3D:
    def __init__(self):
        self.segments = []
        self.textures = []
        self.hasTrianglesWithoutATexture = False
        self.bspTree = BspTree()


