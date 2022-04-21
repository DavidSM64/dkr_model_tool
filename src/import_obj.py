import os.path
from model import *
from PIL import Image, ImageOps

def split_obj_line(line):
    if line.startswith('#!dkr'):
        line = line[line.index(' ')+1:]
    elif '#' in line:
        line = line[:line.index('#')]
    line = line.strip()
    if(len(line) == 0):
        return []
    return line.split(' ')

def load_and_add_texture(model, imgPath, originalTexIndex, flipTexture = False):
    tex = Image.open(imgPath).convert('RGBA')
    if flipTexture:
        tex = ImageOps.flip(tex)
    width, height = tex.size
    model.textures.append(TextureNode(tex, width, height, TEX_FORMAT_RGBA16, 0, originalTexIndex))

def load_materials(basePath, matPath, model, matToTexIndex):
    matPath = basePath + '/' + matPath
    if not os.path.exists(matPath):
        raise SystemExit('Error: Material file "' + matPath + '" does not exist!')

    originalTexIndex = -1
    numTextures = 0
    curIndex = -1
    curMatName = ''
    curMatPath = ''
    curMatHasTexture = False
    shouldFlipTexture = False
    matText = open(matPath, "r").read().split("\n")
    for line in matText:
        parts = split_obj_line(line)
        if(len(parts) > 0):
            mtlCmd = parts[0]
            if mtlCmd == 'newmtl':
                if curIndex > -1:
                    if not curMatHasTexture:
                        matToTexIndex[curMatName] = -1
                    else:
                        matToTexIndex[curMatName] = numTextures
                        numTextures += 1
                        load_and_add_texture(model, curMatPath, originalTexIndex, shouldFlipTexture)
                curMatName = parts[1]
                curIndex += 1
                curMatHasTexture = False
                curMatPath = ''
                originalTexIndex = -1
            elif mtlCmd == 'map_Kd':
                if not curMatHasTexture:
                    curMatHasTexture = True
                    curMatPath = basePath + "/" + parts[1]
                    shouldFlipTexture = False
            elif mtlCmd == 'vanilla_tex':
                originalTexIndex = int(parts[1])
                decompPath = get_decomp_path()
                if decompPath != None:
                    vanillaTexImgPath, vanillaTexProperties = get_vanilla_texture_image_path(decompPath, originalTexIndex)
                    if vanillaTexImgPath != None:
                        curMatPath = vanillaTexImgPath
                        curMatHasTexture = True
                        shouldFlipTexture = vanillaTexProperties["flipped-image"]
    if not curMatHasTexture:
        matToTexIndex[curMatName] = -1
    else:
        matToTexIndex[curMatName] = numTextures
        numTextures += 1
        load_and_add_texture(model, curMatPath, originalTexIndex)

DEFAULT_BATCH_FLAGS = 0x10
DEFAULT_TRIANGLE_FLAGS = 0x00

def import_obj_model(args):
    model = Model3D()

    objText = open(args.input, "r").read().split("\n")

    # There is at-least a single segment
    model.segments.append(Model3DSegment())

    setSegmentCount = False
    currentSegment = 0
    loadedMaterials = False
    curMatName = ''
    matToTexIndex = {}
    curTextureIndex = -1
    curVertexIndex = 0
    curUVIndex = 0

    vertices = []
    uvs = []
    bspNodes = None

    for line in objText:
        parts = split_obj_line(line)
        if(len(parts) > 0):
            objCmd = parts[0]
            # Standard commands
            if objCmd == 'v':
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                # Vertex colors are not standard.
                r = g = b = a = 255
                if len(parts) == 7 or len(parts) == 8:
                    try:
                        r = float(parts[4]) * 255
                        g = float(parts[5]) * 255
                        b = float(parts[6]) * 255
                        try:
                            a = float(parts[7]) * 255
                        except:
                            a = 255
                    except:
                        pass
                vertices.append(Vertex(x * args.scale, y * args.scale, z * args.scale, r, g, b, a))
                curVertexIndex += 1
            elif objCmd == 'vt':
                uvs.append(UV(float(parts[1]), float(parts[2])))
                curUVIndex += 1
            elif objCmd == 'vn':
                pass # Currently does nothing
            elif objCmd == 'f':
                if len(parts) > 5:
                    raise SystemExit("Error: This importer does not support faces with more than 4 vertices.")
                #try:
                isQuad = len(parts) == 5
                vertexIndices = []
                uvIndices = []
                for i in range(1, len(parts)):
                    subParts = parts[i].split('/')
                    vertIndex = int(subParts[0]) - 1
                    uvIndex = int(subParts[1]) - 1
                    vertexIndices.append(vertIndex)
                    uvIndices.append(uvIndex)
                vert0 = vertices[vertexIndices[0]]
                vert1 = vertices[vertexIndices[1]]
                vert2 = vertices[vertexIndices[2]]
                uv0 = uvs[uvIndices[0]]
                uv1 = uvs[uvIndices[1]]
                uv2 = uvs[uvIndices[2]]
                model.segments[currentSegment].add_triangle(curTextureIndex, DEFAULT_BATCH_FLAGS, DEFAULT_TRIANGLE_FLAGS, vert0, vert1, vert2, uv0, uv1, uv2)
                if isQuad:
                    vert3 = vertices[vertexIndices[3]]
                    uv3 = uvs[uvIndices[3]]
                    model.segments[currentSegment].add_triangle(curTextureIndex, DEFAULT_BATCH_FLAGS, DEFAULT_TRIANGLE_FLAGS, vert0, vert2, vert3, uv0, uv2, uv3)
                #except:
                #    print("Warning: Failed to load a triangle. Obj file might be corrupted!")
            elif objCmd == 'mtllib':
                if loadedMaterials:
                    raise SystemExit("Error: A material library has already been defined for this obj file!")
                basePath = '.'
                if '/' in args.input:
                    basePath = args.input[:args.input.rindex('/')]
                load_materials(basePath, parts[1], model, matToTexIndex)
                loadedMaterials = True
            elif objCmd == 'usemtl':
                curTextureIndex = matToTexIndex[parts[1]]
            elif objCmd == 'o':
                pass # Currently does nothing
            elif objCmd == 'g': 
                pass # Currently does nothing
            elif objCmd == 's': 
                pass # Currently does nothing
            # Custom commands
            elif objCmd == 'vertex_color':
                colorString = ' '.join(parts[1:])
                vertices[len(vertices) - 1].color.set_from_string(colorString)
            elif objCmd == 'number_of_segments':
                if setSegmentCount:
                    raise SystemExit("Error: Already set number of segments!")
                setSegmentCount = True
                segCount = int(parts[1])
                while len(model.segments) < segCount:
                    model.segments.append(Model3DSegment())
            elif objCmd == 'bsp_tree_start':
                bspNodes = []
            elif objCmd == 'bsp_tree_node':
                if bspNodes == None:
                    raise SystemExit('Error: `bsp_tree_node` command executed before `bsp_tree_start`.')
                leftIndex = int(parts[1])
                rightIndex = int(parts[2])
                splitAxis = parts[3].upper()
                if splitAxis != 'X' and splitAxis != 'Y' and splitAxis != 'Z':
                    raise SystemExit('Error: Invalid Axis "' + parts[3] + '". Should either be X, Y, or Z')
                segment = int(parts[4])
                splitValue = int(parts[5])
                bspNodes.append(BspTreeNode(splitAxis, splitValue, segment, leftIndex, None, rightIndex, None))
            elif objCmd == 'bsp_tree_end':
                for i in range(0, len(bspNodes)):
                    if bspNodes[i].leftIndex != -1:
                        bspNodes[i].left = bspNodes[bspNodes[i].leftIndex]
                    if bspNodes[i].rightIndex != -1:
                        bspNodes[i].right = bspNodes[bspNodes[i].rightIndex]
                model.bspTree.rootNode = bspNodes[0]
                bspNodes = None
            elif objCmd == 'segment_mask':
                model.bspTree.bitfields.append(int(parts[1], 0))
            elif objCmd == 'segment':
                if not setSegmentCount:
                    raise SystemExit("Must have a `number_of_segments` command before using `segment` command!")
                currentSegment = int(parts[1])
            # Unknown command
            else:
                print('Unimplemented command: ' + objCmd)
    return model
