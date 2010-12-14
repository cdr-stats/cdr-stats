import datetime
from django.core.management.base import BaseCommand, CommandError
from cdr.models import CDR


class Command(BaseCommand):
    args = '<Time Zone offset as integer, ie +10>'
    help = """"
            Updates all CDR time feilds with this Time Zone offset. \n 
            Usefull if your Asterisk config file is set to use GMT\n
            """

    def handle(self, *args, **options):
        try:
            offset = datetime.timedelta(hours=int(args[0]))
        except:
            print "\nInput Error\n###################\nCould not convert Time Zone value into an integer, only pass values such as +10 or -2\n\n"
            raise
        
        cdrlen = CDR.objects.all().count()
        cnt = percent = 0
        print "Modifing {0} records".format(cdrlen)
        for cdr in CDR.objects.all():
            cnt +=1
            if cnt > (cdrlen/10):
                cnt = 0
                percent += 10
                print " {0} %".format(percent)
            cdr.start += offset
            if cdr.answered: cdr.answered += offset
            if cdr.end: cdr.end += offset
            cdr.save()

