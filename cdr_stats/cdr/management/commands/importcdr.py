from django.core.management.base import BaseCommand, CommandError
from cdr.models import CDR

"""
By default the Master.csv format is,
$accountcode,$src, $dst, $dcontext, $clid, $channel, $dstchannel, $lastapp, $lastdata, $start, $answer, $end, $duration, $billsec, $disposition, $amaflags. $uniqueid, $userfield


Filename should be provisioned in this format : master_cdr_%IP%.csv
the %IP% will be used to define to which account the CDR belongs

"""


class Command(BaseCommand):
    args = '<filepath>'
    help = 'Import a specified CDR file'

    def handle(self, *args, **options):
        for acct_id in args:
            try:
                cdr = CDR.objects.get(pk=int(acct_id))
            except CDR.DoesNotExist:
                raise CommandError('CDR "%s" does not exist' % acct_id)
            

            cdr.dst = "TESTING"
            cdr.save()

            self.stdout.write('Successfully updated cdr "%s"\n' % acct_id)
