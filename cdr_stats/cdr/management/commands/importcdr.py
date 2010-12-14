from django.core.management.base import BaseCommand, CommandError
from cdr.models import *
import csv
import os

"""
By default the Master.csv format is,
$accountcode, $src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield

"""

class Command(BaseCommand):
    """
    Import and asterisk cdr.csv file into the datebase. This is useful if you do not wish to save your asterisk data to a database in case failure.
    """
    
    
    args = '<filename1, filename2, ...>'
    help = """
        Import a specified CDR file \n
        ---------------------------------\n
        Import an Asterisk cdr.csv file into the call account system. \n
        The file format have to follow the next sequence: \n
        $accountcode, $src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield
        \n\n"""
    
    def handle(self, *args, **options):
        x = 0
        total_cdr_inserted = 0
        total_cdr_not_inserted = 0
        rownum = 0
        
        for filepath in args:
            x = x + 1
            myext = filepath[-3:]
            if not myext == 'csv':
                raise CommandError('Wrong file type, only csv file are supported')
            
            filename = os.path.basename(filepath)
            file = open(filepath)
            reader = csv.reader(file,delimiter=',', quotechar='"')
            
            for row in reader:
                try:
                    if (len(row)==0):
                        continue
                    accountcodetxt = row[0].encode("utf-8")
                    accountcodes = AccountCode.objects.filter(accountcode = accountcodetxt)
                    if accountcodes:
                        accountcode = accountcodes[0]
                    else:
                        accountcode = AccountCode(accountcode=accountcodetxt, description ="Newly created")
                        accountcode.save()
                    
                    kwargs = {}
                    kwargs['accountcode'] = accountcode
                    kwargs['src'] = row[1].encode("utf-8")
                    kwargs['dst'] = row[2].encode("utf-8")
                    kwargs['dcontext'] = row[3].encode("utf-8")
                    kwargs['clid'] = row[4].encode("utf-8")
                    kwargs['channel'] = row[5].encode("utf-8")
                    kwargs['dstchannel'] = row[6].encode("utf-8")
                    kwargs['lastapp'] = row[7].encode("utf-8")
                    kwargs['lastdata'] = row[8].encode("utf-8")
                    kwargs['start'] = row[9].encode("utf-8") 
                    kwargs['answered'] = row[10].encode("utf-8") if len(row[10]) > 14 else None
                    kwargs['end'] = row[11].encode("utf-8")
                    kwargs['duration'] = row[12].encode("utf-8")
                    kwargs['billsec'] = row[13].encode("utf-8")
                    kwargs['disposition'] = dic_disposition.get(row[14].encode("utf-8"),10)
                    kwargs['amaflags'] = dic_amaflags.get(row[15].encode("utf-8"),4)
                    kwargs['uniqueid'] = row[16].encode("utf-8")
                    kwargs['userfield'] = row[17].encode("utf-8")
                    
                    if CDR.objects.filter(accountcode=accountcode, uniqueid=kwargs['uniqueid']):
                        print "########### NOT INSERTED"
                        total_cdr_not_inserted = total_cdr_not_inserted + 1
                    else:
                        mycdr = CDR(**kwargs)
                        mycdr.save()
                        total_cdr_inserted = total_cdr_inserted + 1
                        
                    rownum = rownum + 1
                    
                except:
                    #import pdb; pdb.set_trace()
                    raise
                    raise CommandError('CDR "%s" does not exist' % rownum)
            
            print "CDR IMPORT RESULT:\n----------------------\n"
            print "Amount of parsed lines: {0}".format(rownum)
            print "Successfully Inserted CDRs: {0}".format(total_cdr_inserted)
            print "Not Inserted CDRs: {0}".format(total_cdr_not_inserted)
            
