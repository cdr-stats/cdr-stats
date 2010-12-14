from django.core.management.base import BaseCommand, CommandError
from cdr.models import CDR

class Command(BaseCommand):
    args = '<acct_id acct_id ...>'
    help = 'Update the specified CDR'

    def handle(self, *args, **options):
        for acct_id in args:
            try:
                cdr = CDR.objects.get(pk=int(acct_id))
            except CDR.DoesNotExist:
                raise CommandError('CDR "%s" does not exist' % acct_id)
            

            cdr.dst = "TESTING"
            cdr.save()

            self.stdout.write('Successfully updated cdr "%s"\n' % acct_id)
