import json
from geojsontosvg import lolatoxy
from parser import get_sorted_tuples, load_matrices
from collections import OrderedDict
import math
code_to_xy={}
def create_country_json(country_code,matrix,ccode_to_coordinates,file_prefix="in"):
    sorted_tuples= get_sorted_tuples(matrix,country_code,code_to_name,10)
    res=OrderedDict()
    from_point=[0,0]
    from_point[0],from_point[1] = ccode_to_coordinates[country_code]["lng"], ccode_to_coordinates[country_code]["lat"]
    code_to_xy[country_code]= lolatoxy(from_point)

    for tuple in sorted_tuples:
        code, name, migration = tuple
        point=[0,0]
        point[0], point[1]= (ccode_to_coordinates[code]["lng"], ccode_to_coordinates[code]["lat"])
        xy_from = lolatoxy(from_point)
        xy_to = lolatoxy(point)
        middle_point = (abs(xy_from[0]+xy_to[0])/2 , abs(xy_from[1]+xy_to[1])/2)
        middle_point = list(middle_point)
        d = math.sqrt(math.pow(xy_from[0]-xy_to[0],2)+math.pow(xy_to[1]-xy_from[1],2))
        try:
            xm = middle_point[0]
            ym = middle_point[1]
            d_div = 5.0
            p = (xy_from[0] - xy_to[0])/((xy_from[1] - xy_to[1])*1.0)
            alpha = math.atan(p)

            x1 = xm + math.cos(alpha) * d/d_div
            y1 = ym - math.sin(alpha) * d/d_div
            x2 = xm - math.cos(alpha) * d/d_div
            y2 = ym + math.sin(alpha) * d/d_div
            if y1 > y2:
                x1, y1 = x2,y2
        except Exception, e:
            print e
            x1 = middle_point[0]
            y1 = middle_point[1]-d/d_div
        svg_path = "M %s %s" %(lolatoxy(from_point)) + " Q %s %s "% (x1,y1) +"%s %s" %(lolatoxy(point))
        #print svg_path
        res[code]=(svg_path,name, migration)
    f = open('generated/'+file_prefix+country_code+".json","w")
    print '/generated/'+file_prefix+country_code+".json"
    f.write(json.dumps(res))
    f.close()


geoloc_data = json.loads(open('geoloc.json').read())

matrix, reversed_matrix,code_to_name = load_matrices()
wrong = []
ccode_to_coordinates = {}
for code in geoloc_data :
    try:
        ccode_to_coordinates[code]=geoloc_data[code]['results'][0]['geometry']['location']
    except Exception,e :
        wrong.append(code)
        print "wrong", wrong


for country_code in matrix :
    create_country_json(country_code,matrix,ccode_to_coordinates)
    create_country_json(country_code,reversed_matrix,ccode_to_coordinates,"out")

f = open("code_to_coordinates.json",'w')
f.write(json.dumps(code_to_xy))
f.close()