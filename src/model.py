####
# 
# Contains the classes common to both level models & object models
#
####

from numpy import array, dot
from util import *

MAX_NUM_VERTS_PER_BATCH = 24
MAX_NUM_TRIS_PER_BATCH = 16


texNumber = 0 # TODO: Replace this with something better!

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

    def __str__(self):
        return '(' + str(self.x) + ', ' + str(self.y) + ', ' + str(self.z) + ')'

    def __repr__(self):
        return self.__str__()

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
