from django.core.management.base import BaseCommand, CommandError
from cdr.models import CDR
from cdr.models import dic_disposition
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
        total_cdr_inserted = 0
        total_cdr_not_inserted = 0
        rownum = 0
        
        for filepath in args:
            x = x + 1
            #print "File #" + str(x) + " - " + filepath
            myext = filepath[-3:]
            if not myext == 'csv':
                raise CommandError('Wrong file type, only csv file are supported')
            
            filename = os.path.basename(filepath)
            filename_noext = filename[0:-4]
            fileIP = filename_noext.split('_')[1]
            IP_lastnum = '.' + fileIP.split('.')[3]
            #print "IP : %s - IPtoInt : %d" %(fileIP, DottedIPToInt(fileIP))
            file = open(filepath)
            reader = csv.reader(file,delimiter=',', quotechar='"')
            
            for row in reader:
                try:
                    "$accountcode, $src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield"
                    if (len(row)==0):
                        continue
                    #print row
                    accountcode = DottedIPToInt(fileIP)
                    #accountcode = row[0].encode("utf-8")
                    src = row[1].encode("utf-8")
                    if len(src) == 0:
                        src = IP_lastnum
                    dst = row[2].encode("utf-8")
                    dcontext = row[3].encode("utf-8")
                    clid = row[4].encode("utf-8")
                    if len(clid) == 0:
                        print IP_lastnum
                        clid = IP_lastnum
                    channel = row[5].encode("utf-8")
                    dstchannel = row[6].encode("utf-8")
                    lastapp = row[7].encode("utf-8")
                    lastdata = row[8].encode("utf-8")
                    start = row[9].encode("utf-8")
                    answer = row[10].encode("utf-8")
                    end = row[11].encode("utf-8")
                    duration = row[12].encode("utf-8")
                    billsec = row[13].encode("utf-8")
                    #TODO : disposition
                    disposition = dic_disposition[row[14].encode("utf-8")]
                    print "disposition : " + str(disposition)
                    #TODO : http://www.voip-info.org/wiki/view/Asterisk+Billing+amaflags
                    amaflags = 1
                    uniqueid = row[16].encode("utf-8")
                    userfield = row[17].encode("utf-8")
                    
                    if CDR.objects.filter(accountcode=accountcode, uniqueid=uniqueid):
                        #print "########### NOT INSERTED"
                        total_cdr_not_inserted = total_cdr_not_inserted + 1
                    else:
                        #print "########### INSERTED"
                        mycdr = CDR(src=src, dst=dst, calldate=start, clid=clid, dcontext=dcontext, channel=channel, dstchannel=dstchannel, lastapp=lastapp, lastdata=lastdata, duration=duration, billsec=billsec, disposition=disposition, amaflags=amaflags, accountcode=accountcode, uniqueid=uniqueid, userfield=userfield)
                        mycdr.save()
                        total_cdr_inserted = total_cdr_inserted + 1
                        
                    rownum = rownum + 1
                    
                except:
                    #import pdb; pdb.set_trace()
                    raise
                    raise CommandError('CDR "%s" does not exist' % rownum)
            
            self.stdout.write("\nCDR IMPORT RESULT:\n----------------------\n")
            self.stdout.write('Amount of parsed lines "%d"\n' % rownum)
            self.stdout.write('Successfully Inserted CDRs "%d"\n' % total_cdr_inserted)
            self.stdout.write('Not Inserted CDRs "%d"\n' % total_cdr_not_inserted)
            
            """
            for acct_id in args:
                try:
                    cdr = CDR.objects.get(pk=int(acct_id))
                except CDR.DoesNotExist:
                    raise CommandError('CDR "%s" does not exist' % acct_id)
                

                cdr.dst = "TESTING"
                cdr.save()

                
            """
