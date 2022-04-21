from model import *
import math

def write8(data, offset, val):
    data[offset] = val & 0xFF

def write16(data, offset, val):
    write8(data, offset, val >> 8)
    write8(data, offset + 1, val)

def write32(data, offset, val):
    write16(data, offset, val >> 16)
    write16(data, offset + 2, val)

def write_texture(data, offset, texture):
    if texture.originalTexIndex != -1:
        write32(data, offset + 0, texture.originalTexIndex)
    else:
        print('Warning: Custom Textures are current not supported yet!')
        write32(data, offset + 0, 0)
    write8(data, offset + 4, texture.width)
    write8(data, offset + 5, texture.height)
    write8(data, offset + 6, texture.format)
    write8(data, offset + 7, texture.collisionType)

def write_vertex(data, offset, vertex):
    write16(data, offset + 0, vertex.x)
    write16(data, offset + 2, vertex.y)
    write16(data, offset + 4, vertex.z)
    write8(data, offset + 6, vertex.color.r)
    write8(data, offset + 7, vertex.color.g)
    write8(data, offset + 8, vertex.color.b)
    write8(data, offset + 9, vertex.color.a)

def write_uv(data, offset, uv, tex):
    write16(data, offset + 0, uv.get_u(tex.width))
    write16(data, offset + 2, uv.get_v(tex.height))

def write_triangle(data, offset, tri, tex):
    write8(data, offset + 0, tri.flags)
    write8(data, offset + 1, tri.vi0)
    write8(data, offset + 2, tri.vi1)
    write8(data, offset + 3, tri.vi2)
    if tex != None:
        write_uv(data, offset + 4, tri.uv0, tex)
        write_uv(data, offset + 8, tri.uv1, tex)
        write_uv(data, offset + 12, tri.uv2, tex)
    else:
        write32(data, offset + 4, 0)
        write32(data, offset + 8, 0)
        write32(data, offset + 12, 0)

def write_batch(data, offset, batch):
    write8(data, offset + 0, batch.texIndex)
    write16(data, offset + 2, batch.vertOffset)
    write16(data, offset + 4, batch.triOffset)
    write32(data, offset + 8, batch.flags)

def write_bounding_box(data, offset, bbox):
    write16(data, offset + 0, bbox[0][0])
    write16(data, offset + 2, bbox[0][1])
    write16(data, offset + 4, bbox[0][2])
    write16(data, offset + 6, bbox[1][0])
    write16(data, offset + 8, bbox[1][1])
    write16(data, offset + 10, bbox[1][2])

def write_collision_data(data, offset, triIndex, tri0, tri1, tri2):
    write16(data, offset + 0, triIndex)
    write16(data, offset + 2, tri0)
    write16(data, offset + 4, tri1)
    write16(data, offset + 6, tri2)

SPLIT_AXIS_VALUES = {
    'X': 0,
    'Y': 1,
    'Z': 2
}

def write_bsp_tree_node_data(data, offset, leftIndex, rightIndex, splitAxis, segmentNumber, splitValue):
    write16(data, offset + 0, leftIndex)
    write16(data, offset + 2, rightIndex)
    write8(data, offset + 4, SPLIT_AXIS_VALUES[splitAxis])
    write8(data, offset + 5, segmentNumber)
    write16(data, offset + 6, splitValue)

def write_bsp_tree_node(data, index, node):
    if index == -1 or node == None:
        return
    offset = index * SIZE_OF_BSP_TREE_NODE
    write_bsp_tree_node_data(data, offset, node.leftIndex, node.rightIndex, node.splitAxis, node.segmentNumber, node.splitValue)
    write_bsp_tree_node(data, node.leftIndex, node.left)
    write_bsp_tree_node(data, node.rightIndex, node.right)

def write_bitfield(data, offset, numBytes, val):
    for i in range(0, numBytes):
        b = (val >> (8 * (numBytes - i - 1))) & 0xFF
        write8(data, offset + i, b)

def get_texture_nodes_data(model):
    numTextures = len(model.textures)

    out = [0] * (numTextures * SIZE_OF_TEXTURE_NODE)

    for i in range(0, numTextures):
        write_texture(out, i * SIZE_OF_TEXTURE_NODE, model.textures[i])

    return out

def get_segments_data(model, startOffset):
    numSegments = len(model.segments)

    # Calculate total size of data
    totalSize = 0
    segmentsSize = 0
    verticesSize = 0
    trianglesSize = 0
    batchesSize = 0
    for i in range(0, numSegments):
        segmentsSize += SIZE_OF_SEGMENT
        verticesSize += align8(len(model.segments[i].vertices) * SIZE_OF_VERTEX)
        trianglesSize += (len(model.segments[i].triangles) * SIZE_OF_TRIANGLE)
        batchesSize += align8((len(model.segments[i].batches) + 1) * SIZE_OF_BATCH_INFO)
    segmentsSize = align16(segmentsSize) + (startOffset % 16)
    totalSize = segmentsSize + verticesSize + trianglesSize + batchesSize

    numBytesPerBitfield = math.ceil(numSegments / 8)

    out = [0] * totalSize

    segmentDataOffset = segmentsSize
    for i in range(0, numSegments):
        segmentOffset = i * SIZE_OF_SEGMENT

        numVertices = len(model.segments[i].vertices)
        numTriangles = len(model.segments[i].triangles)
        numBatches = len(model.segments[i].batches)

        write16(out, segmentOffset + 0x1C, numVertices) # Write number of vertices
        write16(out, segmentOffset + 0x1E, numTriangles) # Write number of triangles
        write16(out, segmentOffset + 0x20, numBatches) # Write number of batches
        write16(out, segmentOffset + 0x28, i * numBytesPerBitfield) # Write bitfield offset
        write8(out, segmentOffset + 0x40, numBatches) # ???

        # Write segment batches
        write32(out, segmentOffset + 0x0C, startOffset + segmentDataOffset) # Write offset to batches
        for j in range(0, numBatches):
            write_batch(out, segmentDataOffset + (j * SIZE_OF_BATCH_INFO), model.segments[i].batches[j])
        write8(out, segmentDataOffset + (numBatches * SIZE_OF_BATCH_INFO), -1) # Write info for the last batch.
        write16(out, segmentDataOffset + (numBatches * SIZE_OF_BATCH_INFO) + 2, numVertices)
        write16(out, segmentDataOffset + (numBatches * SIZE_OF_BATCH_INFO) + 4, numTriangles)
        segmentDataOffset += align8((len(model.segments[i].batches) + 1) * SIZE_OF_BATCH_INFO)
    
        # Write segment triangles
        write32(out, segmentOffset + 0x04, startOffset + segmentDataOffset) # Write offset to triangles
        for j in range(0, numTriangles):
            texIndex = model.segments[i].get_texture_index_from_triangle_index(j)
            tex = None
            if texIndex != -1:
                tex = model.textures[texIndex]
            write_triangle(out, segmentDataOffset + (j * SIZE_OF_TRIANGLE), model.segments[i].triangles[j], tex)
        segmentDataOffset += (len(model.segments[i].triangles) * SIZE_OF_TRIANGLE)

        # Write segment vertices
        write32(out, segmentOffset + 0x00, startOffset + segmentDataOffset) # Write offset to vertices
        for j in range(0, numVertices):
            write_vertex(out, segmentDataOffset + (j * SIZE_OF_VERTEX), model.segments[i].vertices[j])
        segmentDataOffset += align8(len(model.segments[i].vertices) * SIZE_OF_VERTEX)

    return out

def get_bounding_boxes_data(model):
    numSegments = len(model.segments)
    out = [0] * (numSegments * SIZE_OF_BOUNDING_BOX)

    for i in range(0, numSegments):
        write_bounding_box(out, i * SIZE_OF_BOUNDING_BOX, model.segments[i].get_bounding_box())

    return out

def get_collision_data(model, startOffset, segmentsData):
    numSegments = len(model.segments)
    out = []

    curOffset = startOffset
    for segIndex in range(0, numSegments):
        seg = model.segments[segIndex]
        numTriangles = len(seg.triangles)
        collisionOut = [0] * (numTriangles * SIZE_OF_COLLISION_NODE)
        for i in range(0, numTriangles):
            tri0, tri1, tri2 = seg.get_collision_data_for_triangle(i)
            write_collision_data(collisionOut, i * SIZE_OF_COLLISION_NODE, i, tri0, tri1, tri2)
        write32(segmentsData, (segIndex * SIZE_OF_SEGMENT) + 0x14, curOffset)
        curOffset += len(collisionOut)
        out += collisionOut
    return out

def get_bsp_tree_data(model):
    numSegments = len(model.segments)
    if numSegments == 1 or model.bspTree.rootNode == None:
        # Write a single blank node.
        out = [0] * SIZE_OF_BSP_TREE_NODE
        write_bsp_tree_node_data(out, 0, -1, -1, 'X', 0, 0)
    else:
        out = [0] * align16((numSegments - 1) * SIZE_OF_BSP_TREE_NODE)
        write_bsp_tree_node(out, 0, model.bspTree.rootNode)
    return out

def get_bitfields_data(model):
    numSegments = len(model.segments)

    # Write a single blank node.
    if numSegments == 1 or model.bspTree.rootNode == None:
        out = [0] * 16
        out[0] = 1
        return out

    numBytesPerSegment = math.ceil(numSegments / 8)
    out = [0] * (numBytesPerSegment * numSegments)

    offset = 0
    for bitfield in model.bspTree.bitfields:
        write_bitfield(out, offset, numBytesPerSegment, bitfield)
        offset += numBytesPerSegment

    return out

def export_dkr_level_binary(model, args):
    out = [0] * SIZE_OF_LEVEL_HEADER

    # Number of Textures
    write16(out, 0x18, len(model.textures)) 
    # Number of Segments
    write16(out, 0x1A, len(model.segments))

    # Level boundaries?
    write32(out, 0x3C, 0x80007FFF)
    write32(out, 0x40, 0x80007FFF)
    write32(out, 0x44, 0x80007FFF)

    # Textures
    offset = len(out)
    write32(out, 0x00, offset)
    texturesData = get_texture_nodes_data(model)

    # Segments
    offset += len(texturesData)
    write32(out, 0x04, offset)
    segmentsData = get_segments_data(model, offset)

    # Bounding Boxes
    offset += len(segmentsData)
    write32(out, 0x08, offset)
    bbData = get_bounding_boxes_data(model)

    # BSP Tree
    offset += len(bbData)
    write32(out, 0x14, offset)
    bspData = get_bsp_tree_data(model)

    # Segment bitfields
    offset += len(bspData)
    write32(out, 0x10, offset)
    bfData = get_bitfields_data(model)

    # Collision Data
    offset +=len(bfData)
    write32(out, 0x0C, offset)
    colData = get_collision_data(model, offset, segmentsData)

    out += texturesData
    out += segmentsData
    out += bbData
    out += bspData
    out += bfData
    out += colData

    # Write size of file
    write32(out, 0x48, len(out))

    open(args.output, 'wb').write(bytearray(out))
