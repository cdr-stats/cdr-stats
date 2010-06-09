from django.db import connection
from django.conf import settings
import os

def terminal_width():
    """
    Function to compute the terminal width.
    WARNING: This is not my code, but I've been using it forever and
    I don't remember where it came from.
    """
    width = 0
    try:
        import struct, fcntl, termios
        s = struct.pack('HHHH', 0, 0, 0, 0)
        x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
        width = struct.unpack('HHHH', x)[1]
    except:
        pass
    if width <= 0:
        try:
            width = int(os.environ['COLUMNS'])
        except:
            pass
    if width <= 0:
        width = 80
    return width

class SqlPrintingMiddleware(object):
    """
    Middleware which prints out a list of all SQL queries done
    for each view that is processed.  This is only useful for debugging.
    """
    def process_response(self, request, response,log=False):
        import logging
        indentation = 2
        if len(connection.queries) > 0:
            width = terminal_width()
            total_time = 0.0
            for query in connection.queries:
                nice_sql = query['sql'].replace('"', '').replace(',',', ')
                sql = "\033[1;31m[%s]\033[0m %s" % (query['time'], nice_sql)
                total_time = total_time + float(query['time'])
                # while len(sql) > width-indentation:
                #     print "%s%s" % (" "*indentation, sql[:width-indentation])
                #     sql = sql[width-indentation:]
                # if 'SELECT `auth' not in sql and 'SELECT `django_session`.`session_key`' not in sql and sql.count('choice_7')==3:
                # if 'SELECT COUNT' in sql:
                if 'survey_' in sql or 'reporting_' in sql:
                    print "%s%s\n" % (" "*indentation, sql)
            replace_tuple = (" "*indentation, str(total_time))
            # if log:
            #     logging.debug("%s\033[1;32m[TOTAL TIME: %s seconds]\033[0m" % replace_tuple)
            # else:    
            print "%s\033[1;32m[TOTAL TIME: %s seconds]\033[0m" % replace_tuple
        return response
        
# INSERT INTO `survey_answer` (`trashed_at`,  `user_id`,  `question_id`,  `session_key`,  `text`,  `choice_id`,  `submission_date`,  `interview_uuid`,  `iphone_uuid`,  `user_agent`,  `interview_order`,  `level`,  `partial`) VALUES (None,  1,  350,  6d57966482e0600a28543f2005f08a81,  Peets,  1019,  2009-05-20 11:52:43,  6d57966482e0600a28543f2005f08a81,  ,  mozilla/5.0 (macintosh; u; intel mac os x 10.5; en-us; rv:1.9.0.10) gecko/2009042315 firefox/3.0.10,  None,  0,  False)        