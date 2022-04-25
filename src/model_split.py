from model import *
import json
from sutherlandhodgman import clip_AABB
from numpy import array, copy, cross, divide, multiply, dot, sqrt as numpy_sqrt
from segment_bitfield_generator import calculate_segment_bitfields

class TriangleData:
    def __init__(self, batch, triangle, vert0, vert1, vert2):
        self.batch = batch
        self.tri = triangle
        self.verts = [
            array([vert0.x, vert0.y, vert0.z]),
            array([vert1.x, vert1.y, vert1.z]),
            array([vert2.x, vert2.y, vert2.z])
        ]

class SplitNode:
    def __init__(self, axis, value):
        self.axis = str(axis).upper()
        assert self.axis == 'X' or self.axis == 'Y' or self.axis == 'Z'
        self.value = value

def _get_triangles_data(model):
    trianglesData = []
    for segment in model.segments:
        for batch in segment.batches:
            for i in range(0, batch.numTriangles):
                tri = segment.triangles[batch.triOffset + i]
                vert0 = segment.vertices[batch.vertOffset + tri.vi0]
                vert1 = segment.vertices[batch.vertOffset + tri.vi1]
                vert2 = segment.vertices[batch.vertOffset + tri.vi2]
                trianglesData.append(TriangleData(batch, tri, vert0, vert1, vert2))
    return trianglesData

AXIS_TO_VALUE = {
    'X' : 0,
    'Y' : 1,
    'Z' : 2
}

MIN_S16 = -32768
MAX_S16 = 32767

class SegmentAABB:
    def __init__(self, minX=MIN_S16, minY=MIN_S16, minZ=MIN_S16, maxX=MAX_S16, maxY=MAX_S16, maxZ=MAX_S16):
        self.min = array([minX, minY, minZ])
        self.max = array([maxX, maxY, maxZ])
        self.extents = array([maxX - minX, maxY - minY, maxZ - minZ])
        
    def __repr__(self):
        return 'min: ' + str(self.min) + ', max: ' + str(self.max) + ', extents: ' + str(self.extents)

    def split(self, axis, splitValue):
        assert axis == 'X' or axis == 'Y' or axis == 'Z'
        axisIndex = AXIS_TO_VALUE[axis]
        assert splitValue >= self.min[axisIndex] and splitValue <= self.max[axisIndex]
        self.extents[axisIndex] = splitValue - self.min[axisIndex]
        oldMax = self.max[axisIndex]
        self.max[axisIndex] = splitValue
        if axis == 'X':
            return SegmentAABB(splitValue, self.min[1], self.min[2], oldMax, self.max[1], self.max[2])
        elif axis == 'Y':
            return SegmentAABB(self.min[0], splitValue, self.min[2], self.max[0], oldMax, self.max[2])
        else: # axis == 'Z'
            return SegmentAABB(self.min[0], self.min[1], splitValue, self.max[0], self.max[1], oldMax)

def split_segment_equally(segments, seg, numSegmentsLeft, nodeCount, depth=0):
    if numSegmentsLeft == 1:
        segments.append(seg)
        return None
    split = {}
    isX = (depth & 1) == 0
    axis = 'X' if isX else 'Z'
    split["axis"] = axis
    axisIndex = AXIS_TO_VALUE[axis]
    splitValue = seg.min[axisIndex] + (seg.extents[axisIndex] // 2)
    split["value"] = splitValue
    newSeg = seg.split(axis, splitValue)
    newSegNumSegmentsLeft = numSegmentsLeft // 2
    split["left"] = split_segment_equally(segments, seg, numSegmentsLeft - newSegNumSegmentsLeft, nodeCount, depth + 1)
    split["segment"] = nodeCount[0]
    nodeCount[0] += 1
    split["right"] = split_segment_equally(segments, newSeg, newSegNumSegmentsLeft, nodeCount, depth + 1)
    return split
   
def get_equal_segments(numSegments, boundingBox=None):
    assert numSegments >= 1
    segments = []
    if boundingBox == None:
        split_segment_equally(segments, SegmentAABB(), numSegments)
        return segments
    minX = boundingBox[0][0]
    minY = boundingBox[0][1]
    minZ = boundingBox[0][2]
    maxX = boundingBox[1][0]
    maxY = boundingBox[1][1]
    maxZ = boundingBox[1][2]
    split_segment_equally(segments, SegmentAABB(minX, minY, minZ, maxX, maxY, maxZ), numSegments)
    return segments

def split_segment(segments, seg, nodeCount, node=None):
    if node == None:
        segments.append(seg)
        return
    axis = node["axis"]
    splitValue = node["value"]
    newSeg = seg.split(axis, splitValue)
    split_segment(segments, seg, nodeCount, node["left"])
    node["segment"] = nodeCount[0]
    nodeCount[0] += 1
    split_segment(segments, newSeg, nodeCount, node["right"])

def validate_split_node(node):
    axis = node["axis"].upper()
    assert axis == 'X' or axis == 'Y' or axis == 'Z'
    value = node["value"]
    assert value >= MIN_S16 and value <= MAX_S16
    if node["left"] != None:
        validate_split_node(node["left"])
    if node["right"] != None:
        validate_split_node(node["right"])

# The numbers end up being too big, so I need to scale down the number first.
MAG_SCALE_FACTOR = 10000.0
def magnitude(vec):
    vec2 = divide(vec, MAG_SCALE_FACTOR)
    return multiply(numpy_sqrt(vec2.dot(vec2)), MAG_SCALE_FACTOR)

# `point` is a vertex that is somewhere on the triangle itself.
# Taken from: https://answers.unity.com/questions/383804/calculate-uv-coordinates-of-3d-point-on-plane-of-m.html
def calculate_uv_for_point_in_triangle(point, vert0, vert1, vert2, tri):
    # calculate vectors from point f to vertices p1, p2 and p3:
    f1 = vert0 - point
    f2 = vert1 - point
    f3 = vert2 - point
    # calculate the areas and factors (order of parameters doesn't matter):
    a = magnitude(cross(vert0-vert1, vert0-vert2))
    if a == 0:
        a = 0.0001 # Don't want division by 0.
    a1 = magnitude(cross(f2, f3)) / a
    a2 = magnitude(cross(f3, f1)) / a
    a3 = magnitude(cross(f1, f2)) / a
    # Put triangle's UV coordinates into numpy arrays
    uv1 = array([ tri.uv0.u, tri.uv0.v ])
    uv2 = array([ tri.uv1.u, tri.uv1.v ])
    uv3 = array([ tri.uv2.u, tri.uv2.v ])
    # find the uv corresponding to point f (uv1/uv2/uv3 are associated to p1/p2/p3):
    uv = uv1 * a1 + uv2 * a2 + uv3 * a3
    # Return the new UV
    return UV(uv[0], uv[1])

def get_bsp_node(splitDataNode, index):
    nodeIndex = index[0]
    index[0] += 1
    left = right = None
    leftIndex = rightIndex = -1
    if splitDataNode["left"] != None:
        left, leftIndex = get_bsp_node(splitDataNode["left"], index)
    if splitDataNode["right"] != None:
        right, rightIndex = get_bsp_node(splitDataNode["right"], index)
    splitAxis = splitDataNode["axis"]
    splitValue = splitDataNode["value"]
    segment = splitDataNode["segment"]
    return (BspTreeNode(splitAxis, splitValue, segment, leftIndex, left, rightIndex, right), nodeIndex)

# Returns a new version of the model that is split up into segments.
def split_model(model, splitData, segmentBoundingBoxes):
    trianglesData = _get_triangles_data(model)
    newModel = Model3D()
    newModel.textures = model.textures
    for bb in segmentBoundingBoxes:
        newSegment = Model3DSegment()
        for tri in trianglesData:
            verts = clip_AABB(copy(tri.verts), bb.min, bb.max)
            if len(verts) >= 3:
                vert0 = Vertex(verts[0][0], verts[0][1], verts[0][2])
                uv0 = calculate_uv_for_point_in_triangle(verts[0], tri.verts[0], tri.verts[1], tri.verts[2], tri.tri)
                for i in range(0, len(verts) - 2):
                    vert1 = Vertex(verts[i + 1][0], verts[i + 1][1], verts[i + 1][2])
                    vert2 = Vertex(verts[i + 2][0], verts[i + 2][1], verts[i + 2][2])
                    uv1 = calculate_uv_for_point_in_triangle(verts[i + 1], tri.verts[0], tri.verts[1], tri.verts[2], tri.tri)
                    uv2 = calculate_uv_for_point_in_triangle(verts[i + 2], tri.verts[0], tri.verts[1], tri.verts[2], tri.tri)
                    newSegment.add_triangle(tri.batch.texIndex, tri.batch.flags, tri.tri.flags, vert0, vert1, vert2, uv0, uv1, uv2)
        newModel.segments.append(newSegment)
    newModel.bspTree.rootNode = get_bsp_node(splitData["root"], [0])[0]
    calculate_segment_bitfields(newModel)
    return newModel

def auto_split_model(model, numberOfSegments):
    modelAABB = model.get_bounding_box()
    minX = modelAABB[0][0]
    minY = modelAABB[0][1]
    minZ = modelAABB[0][2]
    maxX = modelAABB[1][0]
    maxY = modelAABB[1][1]
    maxZ = modelAABB[1][2]
    segmentBoundingBoxes = []
    splits = {}
    splits["root"] = split_segment_equally(segmentBoundingBoxes, SegmentAABB(minX, minY, minZ, maxX, maxY, maxZ), numberOfSegments, [1])
    return split_model(model, splits, segmentBoundingBoxes)

# -------- Test -------- #

if __name__ == '__main__':
    from import_obj import import_obj_model
    from export_obj import export_obj_model

    class TestArgs:
        def __init__(self):
            self.input = '../test_models/FrontEnd/FrontEnd.obj'
            self.output = '../test_models/FrontEnd/Out.obj'
            self.scale = 1

    args = TestArgs()
    model = import_obj_model(args)
    splits = json.loads(open('../test_models/FrontEnd/FrontEndSplits.json', 'r').read())
    validate_split_node(splits["root"])
    modelAABB = model.get_bounding_box()
    print("Model AABB = " + str(modelAABB))
    minX = modelAABB[0][0]
    minY = modelAABB[0][1]
    minZ = modelAABB[0][2]
    maxX = modelAABB[1][0]
    maxY = modelAABB[1][1]
    maxZ = modelAABB[1][2]
    segmentBoundingBoxes = []
    splits = {}
    splits["root"] = split_segment_equally(segmentBoundingBoxes, SegmentAABB(minX, minY, minZ, maxX, maxY, maxZ), 7, [1])
    #split_segment(segmentBoundingBoxes, SegmentAABB(minX, minY, minZ, maxX, maxY, maxZ), [1], splits["root"])
    print(splits)
    for segment in segmentBoundingBoxes:
        print(segment)
    newModel = split_model(model, splits, segmentBoundingBoxes)
    export_obj_model(newModel, args)

