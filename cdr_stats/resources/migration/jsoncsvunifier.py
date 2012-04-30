from parser import load_matrices
import json
matrix, reversed_matrix, code_to_name = load_matrices()
name_to_code = {}
for code in code_to_name :
    name_to_code[code_to_name[code]]=code

world_svg_paths = json.loads(open("world_svg_paths.json").read())

reconciliation= json.loads(open("reconciliation.json").read())


for code in reconciliation:
    name_to_code[reconciliation[code]]= code

world_svg_paths_by_code = {}
for country in world_svg_paths:
    code = name_to_code.get(country,None)
    if not  code:
        print country, code
    else :
        world_svg_paths_by_code[code]=world_svg_paths[country]

f = open('world_svg_paths_by_code.json','w')
f.write(json.dumps(world_svg_paths_by_code))
f.close()