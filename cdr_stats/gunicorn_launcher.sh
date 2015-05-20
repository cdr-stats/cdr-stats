#!/bin/bash
set -e
LOGFILE=/var/log/cdr-stats/gunicorn_cdr_stats.log
LOGDIR=$(dirname $LOGFILE)

# The number of workers is number of worker processes that will serve requests.
# You can set it as low as 1 if you’re on a small VPS.
# A popular formula is 1 + 2 * number_of_cpus on the machine (the logic being,
# half of the processess will be waiting for I/O, such as database).
NUM_WORKERS=1

# user/group to run as
USER=cdr_stats
GROUP=cdr_stats

# cd /usr/share/virtualenvs/cdr-stats
# source bin/activate
source /opt/miniconda/envs/cdr-stats/bin/activate /opt/miniconda/envs/cdr-stats
cd /usr/share/cdrstats

test -d $LOGDIR || mkdir -p $LOGDIR

#Execute unicorn
exec gunicorn cdr_stats.wsgi:application -b 127.0.0.1:8123 -w $NUM_WORKERS --timeout=300 \
    --user=$USER --group=$GROUP --log-level=debug \
    --log-file=$LOGFILE 2>>$LOGFILE