import sys
import argparse

sys.path.insert(0,'src')
from import_obj import import_obj_model
from export_obj import export_obj_model
from import_dkr_binary import import_dkr_level_binary
from export_dkr_level_binary import export_dkr_level_binary
from preview import preview_level
sys.path.insert(0,'..')

OBJ_EXTENSIONS = '.obj'
LEVEL_BINARY_EXTENSIONS = ('.bin', '.cbin')

def load_model(path):
    lowerPath = path.lower()
    if lowerPath.endswith(OBJ_EXTENSIONS):
        return import_obj_model(path)
    elif lowerPath.endswith(LEVEL_BINARY_EXTENSIONS):
        return import_dkr_level_binary(path)
    raise SystemExit('Invalid file path "' + path + '"; must end with .obj, .bin, or .cbin')

def preview_model(args):
    preview_level(load_model(args.input))

def convert_model(args):
    model = load_model(args.input)
    lowerPath = args.output.lower()
    if lowerPath.endswith(OBJ_EXTENSIONS):
        print('Converting to OBJ, Please wait...')
        return export_obj_model(model, args.output)
    elif lowerPath.endswith(LEVEL_BINARY_EXTENSIONS):
        print('Converting to Level Binary, Please wait...')
        return export_dkr_level_binary(model, args.output)

def main():
    parser = argparse.ArgumentParser(description='Convert/Preview DKR Levels')
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path', required=False)

    args = parser.parse_args()
    if args.output == None:
        preview_model(args)
    else:
        convert_model(args)
    

if __name__ == '__main__':
    main()