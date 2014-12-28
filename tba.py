#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  tba.py
#
#  Copyright 2014 Unknown <wm@Victor-Arch>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import print_function
from sys import argv
import requests
DISTRICTEVENTSURL = "http://www.thebluealliance.com/api/v2/district/%(district)s/%(year)s/events"
EVENTTEAMSURL =  "http://www.thebluealliance.com/api/v2/event/%(eventcode)s/teams"
HEADERS = {"X-TBA-App-Id":"brolliancebeta:distteams:1"}
def main():
    events = []
    if argv[1] == "district":
        r = requests.get(DISTRICTEVENTSURL % {"district":argv[2],"year":argv[3]}, headers = HEADERS)
        for event in r.json():
            events.append(event["key"])
    else:
        events = argv[1:]
    teams = []
    for event in events:
        r = requests.get(EVENTTEAMSURL % {"eventcode":event}, headers = HEADERS)
        for team in r.json():
            if team["team_number"] not in teams:
                teams.append(team["team_number"])
    for team in sorted(teams):
        print(team)
    return 0

if __name__ == '__main__':
    main()

