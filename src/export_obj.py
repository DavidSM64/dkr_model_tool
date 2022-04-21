from pathlib import Path
from model import *

def special_cmd(cmd, value=None):
    if value == None:
        return '#!dkr ' + cmd + '\n'
    return '#!dkr ' + cmd + ' ' + str(value) + '\n'

def export_obj_model(model, args):
    if not args.output.lower().endswith('.obj'):
        args.output += '.obj'

    objName = args.output[:-4]
    if '/' in objName:
        objName = objName[objName.rindex('/')+1:]

    objTxt = 'o ' + objName + '\n\n'
    objTxt += export_geometry_with_materials(model, objName, args.output[:-(len(objName)+4)], args.output[:-4]+".mtl", args.scale, True)

    open(args.output, 'w').write(objTxt)

def write_bsp_tree_node(textRef, node):
    if node == None:
        return
    cmdValue =  str(node.leftIndex) + ' ' + str(node.rightIndex) + ' ' + str(node.splitAxis) + ' ' + str(node.segmentNumber) + ' ' + str(node.splitValue)
    textRef[0] += special_cmd('bsp_tree_node', cmdValue)
    write_bsp_tree_node(textRef, node.left)
    write_bsp_tree_node(textRef, node.right)

def export_geometry_with_materials(model, objName, basePath, mtlPath, scale, exportColors=False):
    if basePath == '':
        basePath = '.'

    mtlTxt = ''
    Path(basePath + "/" + objName + "/").mkdir(parents=True, exist_ok=True)
    texIndex = 0
    for texture in model.textures:
        mtlTxt += 'newmtl ' + texture.name + '\n'
        mtlPngPath = objName + "/" + texture.name + '.png'
        texture.tex.save(basePath + "/" + mtlPngPath)
        if mtlPngPath.startswith("./"):
            mtlPngPath = mtlPngPath[2:]
        if texture.originalTexIndex != -1:
            mtlTxt += special_cmd('vanilla_tex', texture.originalTexIndex)
        mtlTxt += 'map_Kd ' + mtlPngPath + '\n'
        if texIndex < len(model.textures):
            mtlTxt += '\n'
        texIndex += 1

    open(mtlPath, 'w').write(mtlTxt)

    objTxt = 'mtllib ' + objName + '.mtl\n\n'

    numSegments = len(model.segments)

    objTxt += special_cmd('number_of_segments', numSegments)

    if numSegments > 1:
        objTxt += special_cmd('bsp_tree_start')
        bspTextRef = ['']
        write_bsp_tree_node(bspTextRef, model.bspTree.rootNode)
        objTxt += bspTextRef[0]
        objTxt += special_cmd('bsp_tree_end')
        for i in range(0, len(model.segments)):
            objTxt += special_cmd('segment_mask', hex(model.bspTree.bitfields[i]))
    else:
        # Write blank bsp tree and segment mask.
        objTxt += special_cmd('bsp_tree_start')
        objTxt += special_cmd('bsp_tree_node', '-1 -1 X 0 0')
        objTxt += special_cmd('bsp_tree_end')
        objTxt += special_cmd('segment_mask', 1)

    objTxt += '\n'

    segmentCount = 0
    segmentVertOffset = 0
    uvIndex = 0
    lastTexIndex = -1
    for segment in model.segments:
        objTxt += 'g segment_' + str(segmentCount) + '\n'
        objTxt += special_cmd('segment', segmentCount)
        for i in range(0, len(segment.vertices)):
            vert = segment.vertices[i]
            objTxt += 'v ' + str(vert.x / scale) + ' ' + str(vert.y / scale) + ' ' + str(vert.z / scale) + '\n'
            if exportColors:
                objTxt += special_cmd('vertex_color',  vert.color.as_hex_string())
        for i in range(0, len(segment.batches)):
            bat = segment.batches[i]
            if(bat.texIndex != lastTexIndex):
                objTxt += 'usemtl ' + model.textures[bat.texIndex].name + '\n'
                lastTexIndex = bat.texIndex
            numTris = bat.numTriangles
            vertsStartIndex = segmentVertOffset + bat.vertOffset
            trisStartIndex = bat.triOffset
            for j in range(0, numTris):
                tri = segment.triangles[trisStartIndex + j]
                objTxt += 'vt ' + str(tri.uv0.u) + ' ' + str(tri.uv0.v) + '\n'
                objTxt += 'vt ' + str(tri.uv1.u) + ' ' + str(tri.uv1.v) + '\n'
                objTxt += 'vt ' + str(tri.uv2.u) + ' ' + str(tri.uv2.v) + '\n'
                fv0 = str(vertsStartIndex + (tri.vi0) + 1) + '/' + str(uvIndex + 1)
                fv1 = str(vertsStartIndex + (tri.vi1) + 1) + '/' + str(uvIndex + 2)
                fv2 = str(vertsStartIndex + (tri.vi2) + 1) + '/' + str(uvIndex + 3)
                #print(str(i) + ',' + str(j) + ':' + str(fv0) + ' = ' + str(vertsStartIndex) + ' + ' + str(tri.vi0) + ' + 1')
                objTxt += 'f ' + fv0 + ' ' + fv1 + ' ' + fv2 + '\n'
                uvIndex += 3
        segmentCount += 1
        segmentVertOffset += len(segment.vertices)
        if segmentCount < len(model.segments):
            objTxt += '\n'
    return objTxt

def export_geometry_only(model, scale):
    objTxt = ''
    segmentCount = 0
    segmentVertOffset = 0
    for segment in model.segments:
        objTxt += 'g segment_' + str(segmentCount) + '\n'
        for i in range(0, len(segment.vertices)):
            vert = segment.vertices[i]
            objTxt += 'v ' + str(vert.x / scale) + ' ' + str(vert.y / scale) + ' ' + str(vert.z / scale) + '\n'
        for i in range(0, len(segment.batches)):
            bat = segment.batches[i]
            numTris = bat.numTriangles
            vertsStartIndex = segmentVertOffset + bat.vertOffset
            trisStartIndex = bat.triOffset
            for j in range(0, numTris):
                tri = segment.triangles[trisStartIndex + j]
                objTxt += 'f ' + str(vertsStartIndex + tri.vi0 + 1) + ' ' + str(vertsStartIndex + tri.vi1 + 1) + ' ' + str(vertsStartIndex + tri.vi2 + 1) + '\n'
        segmentCount += 1
        segmentVertOffset += len(segment.vertices)
        if segmentCount < len(model.segments):
            objTxt += '\n'
    return objTxt
