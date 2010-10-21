from django.core.management.base import BaseCommand, CommandError
from cdr.models import CDR
import csv
import os

"""
By default the Master.csv format is,
$accountcode, $src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield

"""

def IntToDottedIP( intip ):
    octet = ''
    for exp in [3,2,1,0]:
        octet = octet + str(intip / ( 256 ** exp )) + "."
        intip = intip % ( 256 ** exp )
    return(octet.rstrip('.'))

def DottedIPToInt( dotted_ip ):
    exp = 3
    intip = 0
    for quad in dotted_ip.split('.'):
        intip = intip + (int(quad) * (256 ** exp))
        exp = exp - 1
    return(intip)


class Command(BaseCommand):
    args = '<filename1, filename2, ...>'
    help = "Import a specified CDR file \n---------------------------------\n" \
           "Filename should be provisioned in the following format : cdr_%IP%.csv \n" \
           "the %IP% will be used to define to which account the CDR belongs.\n\n" \
           "The file format have to follow the next sequence: \n" \
           "$accountcode, $src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield\n\n"

    def handle(self, *args, **options):
        x = 0
        for filepath in args:
            x = x + 1
            print "File #" + str(x) + " - " + filepath
            myext = filepath[-3:]
            if not myext == 'csv':
                raise CommandError('Wrong file type, only csv file are supported')
            
            filename = os.path.basename(filepath)
            filename_noext = filename[0:-4]
            fileIP = filename_noext.split('_')[1]
            
            print "IP : %s - IPtoInt : %d" %(fileIP, DottedIPToInt(fileIP))
            
            file = open(filepath)
            reader = csv.reader(file,delimiter=',', quotechar='"')
            
            rownum = 0
            for row in reader:
                try:
                    "$accountcode, $src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield"
                    accountcode = DottedIPToInt(fileIP)
                    #accountcode = row[0].encode("utf-8")
                    src = row[1].encode("utf-8")
                    dst = row[2].encode("utf-8")
                    dcontext = row[3].encode("utf-8")
                    clid = row[4].encode("utf-8")
                    channel = row[5].encode("utf-8")
                    dstchannel = row[6].encode("utf-8")
                    lastapp = row[7].encode("utf-8")
                    lastdata = row[8].encode("utf-8")
                    start = row[9].encode("utf-8")
                    answer = row[10].encode("utf-8")
                    end = row[11].encode("utf-8")
                    duration = row[12].encode("utf-8")
                    billsec = row[13].encode("utf-8")
                    disposition = row[14].encode("utf-8")
                    amaflags = 1
                    uniqueid = row[16].encode("utf-8")
                    userfield = row[17].encode("utf-8")
                    #TODO : disposition
                    print row
                    
                    if CDR.objects.filter(accountcode=accountcode, uniqueid=uniqueid) :
                        print "########### NOT INSERTED"
                    else :
                        print "########### INSERTED"
                        mycdr = CDR(src=src, dst=dst, calldate=start, clid=clid, dcontext=dcontext, channel=channel, dstchannel=dstchannel, lastapp=lastapp, lastdata=lastdata, duration=duration, billsec=billsec, disposition=1, amaflags=amaflags, accountcode=accountcode, uniqueid=uniqueid, userfield=userfield)
                        mycdr.save()
                        print mycdr
                    
                    print "======================================================="
                    print rownum
                    rownum = rownum + 1
                except:
                    #import pdb; pdb.set_trace()
                    raise
                    raise CommandError('CDR "%s" does not exist' % accountcode)
                
            
            """
            for acct_id in args:
                try:
                    cdr = CDR.objects.get(pk=int(acct_id))
                except CDR.DoesNotExist:
                    raise CommandError('CDR "%s" does not exist' % acct_id)
                

                cdr.dst = "TESTING"
                cdr.save()

                self.stdout.write('Successfully updated cdr "%s"\n' % acct_id)
            """
