from numpy import array, dot
from util import *
from model import *

class LevelModel3DSegment:
    def __init__(self):
        self.batches = []
        self.vertices = []
        self.triangles = []
        self.bbox = None

    def _new_batch(self, texIndex=-1, batchFlags=0):
        newBatch = Model3DBatch(texIndex, batchFlags)
        if len(self.batches) > 0:
            prevBatch = self.batches[-1]
            newBatch.vertOffset = prevBatch.vertOffset + prevBatch.numVertices
            newBatch.triOffset = prevBatch.triOffset + prevBatch.numTriangles
        self.batches.append(newBatch)

    def _check_batch_for_vertex_index(self, vertex):
        batch = self.batches[-1]
        if batch.numVertices == 0:
            return -1

        for i in range(0, batch.numVertices):
            if self.vertices[batch.vertOffset + i] == vertex:
                return i

        return -1

    def _add_vertices_to_batch(self, texIndex, batchFlags, verts):
        numberOfNewVertices = 3
        vertIndices = [-1, -1, -1]

        for i in range(0, 3):
            vertIndices[i] = self._check_batch_for_vertex_index(verts[i])
            if vertIndices[i] > -1:
                numberOfNewVertices -= 1

        if self.batches[-1].numVertices + numberOfNewVertices > MAX_NUM_VERTS_PER_BATCH:
            self._new_batch(texIndex, batchFlags)
            vertIndices = [-1, -1, -1] # reset indices

        for i in range(0, 3):
            if vertIndices[i] == -1:
                vertIndices[i] = len(self.vertices) - self.batches[-1].vertOffset
                self.vertices.append(verts[i])
                self.batches[-1].numVertices += 1

        return vertIndices

    def _check_if_texindex_or_flags_changed(self, texIndex, batchFlags):
        curBatch = self.batches[-1]
        return curBatch.texIndex != texIndex or curBatch.flags != batchFlags

    def add_triangle(self, texIndex, batchFlags, flags, vert0, vert1, vert2, uv0, uv1, uv2):
        if len(self.batches) == 0 or self._check_if_texindex_or_flags_changed(texIndex, batchFlags) or self.batches[-1].numTriangles == MAX_NUM_TRIS_PER_BATCH:
            self._new_batch(texIndex, batchFlags)
        indices = self._add_vertices_to_batch(texIndex, batchFlags, [vert0, vert1, vert2])
        self.triangles.append(Triangle(flags, indices[0], indices[1], indices[2], uv0, uv1, uv2))
        self.batches[-1].numTriangles += 1
        
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
        if self.bbox != None:
            return self.bbox

        maxPos = [-999999, -999999, -999999]
        minPos = [999999, 999999, 999999]

        for vert in self.vertices:
            minPos[0] = min(minPos[0], vert.x)
            minPos[1] = min(minPos[1], vert.y)
            minPos[2] = min(minPos[2], vert.z)
            maxPos[0] = max(maxPos[0], vert.x)
            maxPos[1] = max(maxPos[1], vert.y)
            maxPos[2] = max(maxPos[2], vert.z)

        self.bbox = (minPos, maxPos)

        return self.bbox

    def get_bounding_box_size(self):
        bbox = self.get_bounding_box()
        x = bbox[1][0] - bbox[0][0]
        y = bbox[1][1] - bbox[0][1]
        z = bbox[1][2] - bbox[0][2]
        return (x, y, z)

    def get_center(self):
        bbox = self.get_bounding_box()
        x = bbox[0][0] + ((bbox[1][0] - bbox[0][0]) // 2)
        y = bbox[0][1] + ((bbox[1][1] - bbox[0][1]) // 2)
        z = bbox[0][2] + ((bbox[1][2] - bbox[0][2]) // 2)
        return (x, y, z)

    def is_point_within_bbox(self, x, y, z):
        bbox = self.get_bounding_box()
        return (x >= bbox[0][0] and x < bbox[1][0]) and (y >= bbox[0][1] and y < bbox[1][1]) and (z >= bbox[0][2] and z < bbox[1][2])

class BspTreeNode:
    def __init__(self, splitAxis, splitValue, segmentToRender, leftIndex = -1, left = None, rightIndex = -1, right = None):
        self.splitAxis = splitAxis
        self.splitValue = splitValue
        self.segmentNumber = segmentToRender
        self.leftIndex = leftIndex
        self.left = left
        self.rightIndex = rightIndex
        self.right = right
    
    def __str__(self):
        return '{ axis: ' + self.splitAxis + ', value: ' + str(self.splitValue) \
            + ', left: ' + str(self.left) + ', right: ' + str(self.right) + ' }'

    def __repr__(self):
        return self.__str__()

class BspTree:
    def __init__(self):
        self.rootNode = None
        self.bitfields = []

class LevelModel3D:
    def __init__(self):
        self.segments = []
        self.textures = []
        self.hasTrianglesWithoutATexture = False
        self.bspTree = BspTree()
        self.bbox = None
        self.type = "LEVEL"

    def get_bounding_box(self):
        if self.bbox != None:
            return self.bbox

        maxPos = [-999999, -999999, -999999]
        minPos = [999999, 999999, 999999]

        for segment in self.segments:
            segBox = segment.get_bounding_box()
            minPos[0] = min(minPos[0], segBox[0][0])
            minPos[1] = min(minPos[1], segBox[0][1])
            minPos[2] = min(minPos[2], segBox[0][2])
            maxPos[0] = max(maxPos[0], segBox[1][0])
            maxPos[1] = max(maxPos[1], segBox[1][1])
            maxPos[2] = max(maxPos[2], segBox[1][2])

        self.bbox = (minPos, maxPos)

        return self.bbox

