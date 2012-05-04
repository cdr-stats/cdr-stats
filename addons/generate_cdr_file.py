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
max_contact = 100
start_callerid = 71050000
start_phonenumber = 640200000

for it_name in test:
    count_contact = count_contact + 1
    duration = random.randint(1, 300)
    billsec = duration - random.randint(1, 10)
    callername = "%s%d" % (it_name, count_contact)
    print "%d, %s, %d, %d, %d, %s, %s" % (start_callerid, callername, start_phonenumber, duration, billsec, str(uuid.uuid1()), str(time.time()).split('.')[0])
    start_phonenumber = start_phonenumber + 1
    start_callerid = start_callerid + 1
    
    if count_contact > max_contact:
        exit()
    
