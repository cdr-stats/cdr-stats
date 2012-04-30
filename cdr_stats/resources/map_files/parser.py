from collections import OrderedDict
import csv
import json
import requests
import time
from collections import defaultdict
def load_matrices():
    reader = csv.reader(open('global_migrant_origin_database_version_4.csv', 'rU'), delimiter=',')
    row = reader.next()
    state_codes  = row[2:]
    i=0
    matrix = {}
    code_to_name_temp = {}
    for row in reader:
        code_to_name_temp[row[1]]=row[0]
        matrix[row[1]]={}
        dict= matrix[row[1]]
        j=0
        for val in row[2:] :
            dict[state_codes[j]] = val
            j=j+1

        i=i+1

    name_to_code = {}
    for code in code_to_name_temp :
        name_to_code[code_to_name_temp[code]]=code
    sorted_names = sorted(name_to_code.keys())
    code_to_name = OrderedDict()
    for name in sorted_names:
        code_to_name[name_to_code[name]]=name
        
    f = open("name_to_code.json",'w')
    f.write(json.dumps(name_to_code))
    f.close()

    reversed_matrix = defaultdict(lambda: {})
    for fro in matrix :
        for to in matrix[fro]:
            reversed_matrix[to][fro]=matrix[fro][to]
    return matrix, reversed_matrix,code_to_name

#print code_to_name

def get_sorted_tuples(matrix,country, code_to_name,size=20):
    country_data = matrix[country]
    temp = [(key,country_data[key]) for key in country_data ]
    temp2 = sorted(temp, key=lambda tuple: -int(tuple[1]))
    i=0
    res=[]
    for tuple in temp2:
        if i<size:
            res.append((tuple[0],code_to_name[tuple[0]] , tuple[1]))
        i+=1
    return res


def geolocalize_the_world():
    f = open("geoloc.json","w")
    res ={}
    for code in code_to_name:
        country = code_to_name[code]
        country =  country.replace(' ','+')
        #print country
        r = requests.get("http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=true" %  country)
        res[code]=json.loads(r.content)
        time.sleep(0.15)
        #print res[code]
    f.write(json.dumps(res))
    f.close()


if __name__ =="__main__":
    matrix, reversed_matrix, code_to_name = load_matrices()


    f = open('code_to_name.json','w')

    code_to_name["WSAHARA"]="Western Sahara",

    f.write(json.dumps(code_to_name))
    f.close()
    print get_sorted_tuples(matrix,"MEX", code_to_name)
    print get_sorted_tuples(reversed_matrix,"MEX",code_to_name)


