from model import *
from util import *
import math
from PIL import Image, ImageOps

def get_uv(data, offset):
    u = get_s16(data, offset)
    v = get_s16(data, offset + 2)
    return UV(u, v)

splitAxises = ['X', 'Y', 'Z']
def parse_bsp_tree(data, startOffset, i):
    offset = startOffset + (i * SIZE_OF_BSP_TREE_NODE)
    leftIndex = get_s16(data, offset)
    rightIndex = get_s16(data, offset + 2)
    splitAxis = splitAxises[get_u8(data, offset + 4)]
    segment = get_u8(data, offset + 5)
    splitValue = get_s16(data, offset + 6)

    left = None
    if(leftIndex != -1):
        left = parse_bsp_tree(data, startOffset, leftIndex)
    right = None
    if(rightIndex != -1):
        right = parse_bsp_tree(data, startOffset, rightIndex)

    return BspTreeNode(splitAxis, splitValue, segment, leftIndex, left, rightIndex, right)


def import_dkr_level_binary(binaryPath):
    data = list(open(binaryPath, 'rb').read())
    model = Model3D()

    texturesOffset  = get_u32(data, 0x00)
    segmentsOffset  = get_u32(data, 0x04)
    # Don't need to get bounding boxes, since those are easy to calculate.
    # Don't need to get collision data either, I think.
    bitfieldsOffset = get_u32(data, 0x10)
    bspTreeOffset   = get_u32(data, 0x14)

    numTextures = get_u16(data, 0x18)
    numSegments = get_u16(data, 0x1A)

    for i in range(0, numTextures):
        texOffset = texturesOffset + (i * SIZE_OF_TEXTURE_NODE)
        originalTexIndex = get_u32(data, texOffset + 0)
        width = get_u8(data, texOffset + 4)
        height = get_u8(data, texOffset + 5)
        format = get_u8(data, texOffset + 6)
        collisionType = get_u8(data, texOffset + 7)
        decompPath = get_decomp_path()
        if decompPath != None:
            vanillaTexImgPath, vanillaTexProperties = get_vanilla_texture_image_path(decompPath, originalTexIndex)
            tex = Image.open(vanillaTexImgPath).convert('RGBA')
            if vanillaTexProperties["flipped-image"]:
                tex = ImageOps.flip(tex)
        else:
            tex = generate_temporary_texture(width, height, format & 0x7F)
        model.textures.append(TextureNode(tex, width, height, format, collisionType, originalTexIndex))
    for i in range(0, numSegments):
        segment = Model3DSegment()
        segOffset = segmentsOffset + (i * SIZE_OF_SEGMENT)
        numVertices  = get_u16(data, segOffset + 0x1C)
        numTriangles = get_u16(data, segOffset + 0x1E)
        numBatches   = get_u16(data, segOffset + 0x20)
        verticesOffset = get_u32(data, segOffset + 0x00)
        trianglesOffset = get_u32(data, segOffset + 0x04)
        batchesOffset = get_u32(data, segOffset + 0x0C)
        for j in range(0, numVertices):
            vertDataOffset = verticesOffset + (j * SIZE_OF_VERTEX)
            x = get_s16(data, vertDataOffset + 0x00)
            y = get_s16(data, vertDataOffset + 0x02)
            z = get_s16(data, vertDataOffset + 0x04)
            r = get_u8(data, vertDataOffset + 0x06)
            g = get_u8(data, vertDataOffset + 0x07)
            b = get_u8(data, vertDataOffset + 0x08)
            a = get_u8(data, vertDataOffset + 0x09)
            segment.vertices.append(Vertex(x, y, z, r, g, b, a))
        for j in range(0, numTriangles):
            triDataOffset = trianglesOffset + (j * SIZE_OF_TRIANGLE)
            flags = get_u8(data, triDataOffset + 0x00)
            vi0   = get_u8(data, triDataOffset + 0x01)
            vi1   = get_u8(data, triDataOffset + 0x02)
            vi2   = get_u8(data, triDataOffset + 0x03)
            uv0   = get_uv(data, triDataOffset + 0x04)
            uv1   = get_uv(data, triDataOffset + 0x08)
            uv2   = get_uv(data, triDataOffset + 0x0C)
            segment.triangles.append(Triangle(flags, vi0, vi1, vi2, uv0, uv1, uv2))
        for j in range(0, numBatches):
            batDataOffset = batchesOffset + (j * SIZE_OF_BATCH_INFO)
            texIndex       = get_s8(data, batDataOffset + 0x00)
            batchVertIndex = get_u16(data, batDataOffset + 0x02)
            batchNumVerts  = get_u16(data, batDataOffset + SIZE_OF_BATCH_INFO + 0x02) - batchVertIndex
            batchTriIndex  = get_u16(data, batDataOffset + 0x04)
            batchNumTris   = get_u16(data, batDataOffset + SIZE_OF_BATCH_INFO + 0x04) - batchTriIndex
            batchFlags     = get_u32(data, batDataOffset + 0x08)
            #print("This batch: Tex Index = " + str(texIndex) + ", Num Verts = " + str(batchNumVerts) + ", Num Tris = " + str(batchNumTris))
            if texIndex == -1:
                model.hasTrianglesWithoutATexture = True
            else:
                for k in range(0, batchNumTris):
                    texWidth = model.textures[texIndex].width
                    texHeight = model.textures[texIndex].height
                    segment.triangles[batchTriIndex + k].uv0.parse_uv(texWidth, texHeight)
                    segment.triangles[batchTriIndex + k].uv1.parse_uv(texWidth, texHeight)
                    segment.triangles[batchTriIndex + k].uv2.parse_uv(texWidth, texHeight)
            segment.batches.append(Model3DBatch(texIndex, batchFlags, batchVertIndex, batchNumVerts, batchTriIndex, batchNumTris))
        model.segments.append(segment)
    numBytesForBitfield = math.ceil(numSegments / 8)
    for i in range(0, numSegments):
        model.bspTree.bitfields.append(get_bitfield(data, bitfieldsOffset + (i * numBytesForBitfield), numBytesForBitfield))
    model.bspTree.rootNode = parse_bsp_tree(data, bspTreeOffset, 0)
    return model
