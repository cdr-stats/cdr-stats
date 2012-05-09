#!/bin/bash
#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public 
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
# 
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

func_identify_os() {
    # Identify Linux Distribution type
    if [ -f /etc/debian_version ] ; then
        DIST='DEBIAN'
        if [ "$(lsb_release -cs)" != "lucid" ] && [ "$(lsb_release -cs)" != "precise" ]; then
		    echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
		    exit 255
	    fi
    elif [ -f /etc/redhat-release ] ; then
        DIST='CENTOS'
        if [ "$(awk '{print $3}' /etc/redhat-release)" != "6.2" ] ; then
        	echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
        	exit 255
        fi
    else
        echo ""
        echo "This script is only intended to run on Ubuntu LTS 10.04 / 12.04 or CentOS 6.2"
        echo ""
        exit 1
    fi
}
