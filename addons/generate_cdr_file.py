import sys, string 
import namegen
import uuid
import random
import time

# Use namegen : https://github.com/amnong/namegen


#CallerID, CallerName, Destination, Duration, BillSec, hangupcauseID, uuid, StartDate
#1773500, Erik, 640234009, 50, 45, 16, 3e308846-9036-11e1-964f-000c296bd875, 1327521966

test = namegen.NameGenerator()
count_contact = 0
max_contact = 10000
start_callerid = 81050000
start_phonenumber = 650200000

for it_name in test:
    count_contact = count_contact + 1
    duration = random.randint(1, 300)
    billsec = duration - random.randint(1, 10)
    callername = "%s%d" % (it_name, count_contact)
    hangupcause_id = random.randint(15, 17)
    timestamp = int(str(time.time()).split('.')[0])
    timestamp = timestamp - random.randint(1, 86400)
    
    print "%d, %s, %d, %d, %d, %d, %s, %d" % (start_callerid, callername, start_phonenumber, duration, billsec, hangupcause_id, str(uuid.uuid1()), timestamp)
    start_phonenumber = start_phonenumber + 1
    start_callerid = start_callerid + 1
    
    if count_contact >= max_contact:
        exit()
    
