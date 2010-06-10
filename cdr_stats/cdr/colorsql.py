import sys
from django.db import connection
#from time import *

class ColorSQLMiddleware:
    """
    Color SQL logging middleware.
    Prints a short summary (number of database queries and
    total time) for each request. Additionally it will print
    the raw SQL if any of the configurable tresholds are
    exceeded, in order to draw your attention to pages
    that trigger slow or too many queries.

    The available tresholds are:
    * Query count
    * Total Time (for all SQL queries)
    * Query Time (for individual SQL queries)

    We're trying to keep the output readable by modest use of ANSI color.  

    Example output
    ==============

    This is what you get for normal page views where
    no treshold was exceeded:
    ---------------------------------------------------------------------- 
     0.006s | 3 queries
    ---------------------------------------------------------------------- 

    This is what you get for page views where one or more 
    tresholds have been exceeded. Please note that in reality the
    SQL is *not* truncated. I did that by hand to keep this comment
    readable:
    ---------------------------------------------------------------------- 
    SELECT "django_session"."session_key","django_session"."session_data",
    FROM "django_session"
    WHERE ("django_session"."session_key" = '6495c82cf81b34dc0c4dbb91fc641
    
    SELECT "core_userprofile"."id","core_userprofile"."user_id","core_user
    FROM "core_userprofile" INNER JOIN "auth_user" AS "core_userprofile__u
    WHERE ("core_userprofile__user"."username" = 'sook') 
    
    SELECT "auth_user"."id","auth_user"."username","auth_user"."first_name
    f","auth_user"."is_active","auth_user"."is_superuser","auth_user"."las
    FROM "auth_user"
    WHERE ("auth_user"."id" = 55) 
    
    SELECT "auth_user"."id","auth_user"."username","auth_user"."first_name
    f","auth_user"."is_active","auth_user"."is_superuser","auth_user"."las
    FROM "auth_user"
    WHERE ("auth_user"."id" = 55) 
    
    SELECT "auth_message"."id","auth_message"."user_id","auth_message"."me
    FROM "auth_message"
    WHERE ("auth_message"."user_id" = 55) 
    ---------------------------------------------------------------------- 
     0.176s | 5 queries
    ---------------------------------------------------------------------- 


    Installation
    ============

    Simply put this into your middleware/ directory,
    into a file called "colorsql.py".

    Then edit your settings.py to enable the middleware:

    MIDDLEWARE_CLASSES = (
        ...
        'YOURPATH.colorsql.ColorSQLMiddleware',
        ...
    )

    Finally you may tweak the various options in
    settings.py, see below.


    Options in settings.py (with defaults)
    ======================================

    LOG_COLORSQL_ENABLE = True (boolean)
    -------------------
    True  == Enable the middleware (default)
    False == Disable the middleware, nothing will be printed

    LOG_COLORSQL_VERBOSE = False (boolean)
    --------------------
    True  == The SQL will always be printed.
    False == The SQL will only be printed if one of the tresholds is
             exceeded

    LOG_COLORSQL_WARN_TOTALTIME = 0.5 (float)
    ---------------------------
    If the total time for all db queries exceeds
    this value (in seconds) then the SQL will
    be printed and the measured time in the summary-
    line will be printed in YELLOW.

    LOG_COLORSQL_ALERT_TOTALTIME = 1.0 (float)
    ----------------------------
    If the total time for all db queries exceeds
    this value (in seconds) then the SQL will
    be printed and the measured time in the summary-
    line will be printed in RED.

    LOG_COLORSQL_WARN_TOTALCOUNT = 6 (integer)
    ----------------------------
    If the number of db queries exceeds this value
    then the SQL will be printed and the query-count
    in the summary line will be printed in YELLOW.

    LOG_COLORSQL_ALERT_TOTALCOUNT = 10 (integer)
    -----------------------------
    If the number of db queries exceeds this value
    then the SQL will be printed and the query-count
    in the summary line will be printed in RED.

    LOG_COLORSQL_WARN_TIME = 0.05 (float)
    ----------------------
    If the time for any individual db query exceeds
    this value (in seconds) then the SQL will be
    printed and the offending query be highlighted
    in YELLOW.

    LOG_COLORSQL_ALERT_TIME = 0.20 (float)
    -----------------------
    If the time for any individual db query exceeds
    this value (in seconds) then the SQL will be
    printed and the offending query be highlighted
    in RED.

    """
    def process_response ( self, request, response ):
        from django.conf import settings
        enable  = getattr( settings, 'LOG_COLORSQL_ENABLE', True )

        if False == enable:
            return response

        verbose = getattr( settings, 'LOG_COLORSQL_VERBOSE', False )

        timewarn  = getattr( settings, 'LOG_COLORSQL_WARN_TOTALTIME', 0.5 )
        timealert = getattr( settings, 'LOG_COLORSQL_ALERT_TOTALTIME', 1.0 )

        countwarn  = getattr( settings, 'LOG_COLORSQL_WARN_TOTALCOUNT', 6 )
        countalert = getattr( settings, 'LOG_COLORSQL_ALERT_TOTALCOUNT', 10 )

        qtimewarn = getattr( settings, 'LOG_COLORSQL_WARN_TIME', 0.05 )
        qtimealert = getattr( settings, 'LOG_COLORSQL_ALERT_TIME', 0.20 )

        # sanity checks...
        if qtimealert < qtimewarn:
            qtimewarn = qtimealert

        if countalert < countwarn:
            countwarn = countalert

        if timealert < timewarn:
            timewarn = timealert

        ttime = 0.0
        for q in connection.queries:
            if q.has_key('time') :
                time = float(q['time'])
            else :
                time = float(q['duration'])
            
            ttime = ttime + time
            if qtimewarn < time:
                verbose = True

        count = len(connection.queries)
        if timewarn <= ttime or countwarn <= count:
            verbose = True

        #if verbose:
            #print "\033[0;30;1m"
            #print "-" * 70,
            #print "\033[0m"

        i = 0
        for q in connection.queries:
            if q.has_key('time') :
                time = float(q['time'])
            else :
                time = float(q['duration'])

            if verbose or timewarn <= ttime or countwarn <= count:
                sql = q['sql']
                sql = sql.replace( ' FROM ', '\nFROM ' ).replace( ' WHERE ', '\nWHERE ' )

                tcolor = "\033[31m"
                ptime = "\033[7m %ss \033[0m" % ( time )
                if qtimealert > time:
                    tcolor = "\033[33m"
                if qtimewarn > time:
                    tcolor = "\033[30;1m"
                    ptime = ""

                print "%s%s" % ( tcolor, sql ),
                print "%s\033[1m%s\033[0m" % ( tcolor, ptime )
                i = i + 1
                if i < len(connection.queries):
                    print

        sys.stdout.write( "\033[0;30;1m" )
        print "-" * 70,
        print "\033[35;1m"

        time = ttime

        tcolor = "\033[31;1m"
        if timealert > time:
            tcolor = "\033[33;1m"
        if timewarn > time:
            tcolor = "\033[30;1m"

        ccolor = "\033[31;1m"
        if countalert > count:
            ccolor = "\033[33;1m"
        if countwarn > count:
            ccolor = "\033[30;1m"
        
        if (count > 0) :
            print "%s %.3fs \033[30;1m| %s%d queries\033[0m" % ( tcolor, time, ccolor, count )
            sys.stdout.write( "\033[0;30;1m" )
            print "-" * 70,
            print "\033[0m"

        return response
        
        
