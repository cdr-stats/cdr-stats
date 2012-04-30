import json

height = 700
width=1200

def lolatoxy(point):
    lo = point[0]
    la = point[1]
    x = (lo+180) * (float(width) / 360.0)
    y = (180 - (la+90)) *  (float(height) / 180.0)
    return int(x),int(y)

def transform_to_json():
    world = json.loads(open("world.json").read())

    features= world["features"]
    res = {}
    for feature in features :
        path_list = []
        multipolygon= feature["geometry"]["coordinates"]
        for polygon in multipolygon:
            for path in polygon:
                svgpath ="M %s %s " % lolatoxy(path[0])
                for point in path[1:-1]:
                    svgpath += "L %s %s " % lolatoxy(point)
                svgpath += "Z"
                path_list.append(svgpath)
        res[feature["properties"]["name"]]=path_list


    #print res
    f = open("world_svg_paths.json",'w')
    f.write(json.dumps(res))
    f.close()
    return res

if __name__=="__main__":
    transform_to_json()