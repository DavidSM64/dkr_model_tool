from PIL import Image
import random
import json
import math

SIZE_OF_TEXTURE_NODE = 0x08
SIZE_OF_VERTEX = 0x0A
SIZE_OF_TRIANGLE = 0x10
SIZE_OF_LEVEL_HEADER = 0x50
SIZE_OF_SEGMENT = 0x44
SIZE_OF_BATCH_INFO = 0xC
SIZE_OF_BOUNDING_BOX = 0xC
SIZE_OF_COLLISION_NODE = 0x8
SIZE_OF_BSP_TREE_NODE = 0x8

TEX_FORMAT_RGBA32 = 0
TEX_FORMAT_RGBA16 = 1
TEX_FORMAT_I8     = 2
TEX_FORMAT_I4     = 3
TEX_FORMAT_IA16   = 4
TEX_FORMAT_IA8    = 5
TEX_FORMAT_IA4    = 6
TEX_FORMAT_CI4    = 7
TEX_FORMAT_CI8    = 8

def align16(val):
    return int(val + 15) & 0xFFFFFFF0

def align16_list(l):
    while(len(l) % 16 != 0):
        l.append(0)

def clamp(val, minVal, maxVal):
    return max(minVal, min(maxVal, val))

def distance2d(p0, p1):
    xDiff = p1.x - p0.x
    zDiff = p1.z - p0.z
    return math.sqrt(xDiff**2 + zDiff**2)

def distance3d(p0, p1):
    xDiff = p1.x - p0.x
    yDiff = p1.y - p0.y
    zDiff = p1.z - p0.z
    return math.sqrt(xDiff**2 + yDiff**2 + zDiff**2)

def get_u8(data, offset):
    return data[offset]

def get_s8(data, offset):
    val = get_u8(data, offset)
    if val > 127:
        val -= 256
    return val

def get_u16(data, offset):
    return (get_u8(data, offset) << 8) | get_u8(data, offset + 1)

def get_s16(data, offset):
    val = get_u16(data, offset)
    if val > 32767:
        val -= 65536
    return val

def get_u32(data, offset):
    return (get_u16(data, offset) << 16) | get_u16(data, offset + 2)

def get_bitfield(data, offset, numBytes):
    val = 0
    for i in range(0, numBytes):
        val |= data[offset + i] << (8 * (numBytes - i - 1))
    return val

def to_u8(val):
    return clamp(int(val), 0, 255)

def to_s16(val):
    return clamp(int(val), -32768, 32767)

PATH_TO_DECOMP_FILE = "path-to-decomp.txt"
displayedDecompFileError = False

def get_decomp_path():
    global displayedDecompFileError
    try:
        decompPath = open(PATH_TO_DECOMP_FILE, 'r').read()
        print(decompPath)
        if len(decompPath) > 0:
            return decompPath
    except:
        pass
    if not displayedDecompFileError:
        print('Warning: Decomp path is not set! Temporary textures may be used instead of actual ones.\nPlease create a "' + PATH_TO_DECOMP_FILE + '" file in the root directory that contains a path to the DKR decomp.')
        displayedDecompFileError = True
    return None

def get_vanilla_texture_image_path(decompPath, texIndex):
    try:
        decompPath += "/assets/vanilla/us_1.0"
        textures3dJson = json.loads(open(decompPath + "/asset_textures_3d.json", 'r').read())
        textureStringId = textures3dJson["files"]["order"][texIndex]
        decompPath += '/' + textures3dJson["folder"]
        texture3dJsonPath = decompPath + '/' + textures3dJson["files"]["sections"][textureStringId]["filename"]
        texture3dJson = json.loads(open(texture3dJsonPath, 'r').read())
        return (decompPath + '/' + texture3dJson['img'], texture3dJson)
    except:
        return (None, None)

existingColors = []

def check_if_color_is_similar_to_one_that_already_exists(newColor, scoreTolerance):
    for c in existingColors:
        simScore = 0
        simScore += abs(c[0] - newColor[0])
        simScore += abs(c[1] - newColor[1])
        simScore += abs(c[2] - newColor[2])
        if simScore < scoreTolerance:
            return True # This color is similar enough to another one.
    existingColors.append(newColor)
    return False # This color is not similar to any of the existing colors

def generate_temporary_texture(width, height, format):
    hasColor = (format == TEX_FORMAT_RGBA16 or format == TEX_FORMAT_RGBA32)
    r = g = b = 0
    color = (0, 0, 0)
    iterations = 0
    while True:
        while ((r < 60 and g < 60 and b < 60) or (r > 230 and g > 230 and b > 230)):
            if hasColor:
                r = to_u8(random.random() * 255)
                g = to_u8(random.random() * 255)
                b = to_u8(random.random() * 255)
            else:
                i = to_u8(random.random() * 255)
                r = g = b = i
        color = (r, g, b)
        if not check_if_color_is_similar_to_one_that_already_exists(color, 10 if hasColor else 30):
            break
        iterations += 1
        if iterations > 500 if hasColor else 100: # If too many iterations occur, then just give up and accept the similar color.
            break

    # We have a good color, now to generate a texture.
    newTex = Image.new(mode="RGBA", size=(width, height), color="white")
    
    halfWidth = width // 2
    halfHeight = height // 2

    for y in range(0, height):
        for x in range(0, width):
            if (y >= halfHeight and x < halfWidth) or (y < halfHeight and x >= halfWidth):
                newTex.putpixel((x, y), color)

    return newTex
