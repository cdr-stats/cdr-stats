from geojsontosvg import transform_to_json
from parser import load_matrices
from collections import OrderedDict
import json
res = transform_to_json()
matrix, reversed_matrix,csv_code_to_name = load_matrices()

from_csv = csv_code_to_name.values()
from_json = res.keys()

#print len(from_csv),from_csv
from_csv = [unicode(name,errors='ignore') for name in from_csv]

unmapped_csv_stats = sorted(list(set(from_csv) - set(from_json)))

csv_name_to_code=OrderedDict()
for code in csv_code_to_name:
    csv_name_to_code[unicode(csv_code_to_name[code],errors="ignore")]=code
print "name_to_code keys", sorted(csv_name_to_code.keys())
json_names = sorted(from_json)
import sys
#line = sys.stdin.readline()
res = OrderedDict()
entered_letter = ""
while unmapped_csv_stats:
    unmapped_stat = unmapped_csv_stats[0]
    print "Match for :", unmapped_stat , ("or beginning letter")
    i=1
    print "0 : not found"
    if entered_letter !="":
        show_list= filter(lambda x:x.lower().startswith(entered_letter),json_names)
    else:
        show_list = json_names
    for name in show_list :
        print  i, ":", name ,
        i+=1
    print 
    value = sys.stdin.readline()
    try:
        print "value ", value
        value=int(value)
        print "value entered" , value
        entered_letter=""
        if i==0:
            code = "NOTFOUND"
        else :
            print csv_name_to_code
            code= csv_name_to_code[unmapped_stat]
        res[code]=show_list[value-1]
        print "res"
        for r in res :
            print r, csv_code_to_name[r], res[r]
        print "-------------"
        f = open('reconciliation.json','w')
        f.write(json.dumps(res))
        f.close()
        unmapped_csv_stats = unmapped_csv_stats[1:]
    except ValueError, e:
        print "the exception : ", type(e)
        entered_letter=value.strip()
        print "letter entered", entered_letter



#print code_to_name
#print line
