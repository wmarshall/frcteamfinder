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
from __future__ import print_function, division
import sys, pickle
from os import path
import requests
DISTRICTEVENTSURL = "http://www.thebluealliance.com/api/v2/district/%(district)s/%(year)s/events"
EVENTTEAMSURL =  "http://www.thebluealliance.com/api/v2/event/%(eventkey)s/teams"
TEAMEVENTSURL = "http://www.thebluealliance.com/api/v2/team/%(teamkey)s/events"
TEAMEVENTMATCHESURL = "http://www.thebluealliance.com/api/v2/team/%(teamkey)s/event/%(eventkey)s/matches"
TEAMEVENTAWARDSURL = "http://www.thebluealliance.com/api/v2/team/%(teamkey)s/event/%(eventkey)s/awards"
HEADERS = {"X-TBA-App-Id":"brolliancebeta:rankings:1"}

COMMANDS = {"list", "avg", "rank"}

def tba_get(path):
    return requests.get(path, headers = HEADERS)

class Team(object):
    max_quals_avg = 0
    max_elims_avg = 0
    def __init__(self, team_key):
        self.team_key = team_key
        self.team_number = int(team_key[3:])
        self.quals_tot = 0
        self.quals_played = 0
        self.elims_tot = 0
        self.elims_played = 0
        self.ca_count = 0
        self.ei_count = 0
        self.rookie_count = 0
        self.other_count = 0

    def __str__(self):
        return ",".join([str(self.team_number), str(self.norm_quals_avg()), \
            str(self.norm_elims_avg()), str(self.ca_count), \
            str(self.ei_count), str(self.rookie_count), str(self.other_count), \
            str(self.ranking_score())])

    def populate_data(self):
        events = []
        r = tba_get(TEAMEVENTSURL % {"teamkey" : self.team_key})
        for event in r.json():
            events.append(event["key"])
        for event in events:
            r = tba_get(TEAMEVENTMATCHESURL % {"teamkey" : self.team_key, "eventkey" : event})
            for match in r.json():
                if self.team_key in match["alliances"]["blue"]["teams"]:
                    alliance = "blue"
                else:
                    alliance = "red"
                if match["comp_level"] == "qm":
                    self.quals_tot += match["alliances"][alliance]["score"]
                    self.quals_played += 1
                else:
                    self.elims_tot += match["alliances"][alliance]["score"]
                    self.elims_played += 1
            r = tba_get(TEAMEVENTAWARDSURL % {"teamkey" : self.team_key, "eventkey" : event})
            for award in r.json():
                if "Regional Engineering Inspiration Award" in award["name"]:
                    self.ei_count += 1
                elif "Regional Chairman's Award" in award["name"]:
                    self.ca_count += 1
                elif "Rookie" in award["name"]:
                    self.rookie_count += 1
                else:
                    self.other_count += 1
        if self.quals_avg() > Team.max_quals_avg:
            Team.max_quals_avg = self.quals_avg()
        if self.elims_avg() > Team.max_elims_avg:
            Team.max_elims_avg = self.elims_avg()


    def quals_avg(self):
        return self.quals_tot / self.quals_played

    def elims_avg(self):
        try:
            return self.elims_tot / self.elims_played
        except:
            return 0

    def norm_quals_avg(self):
        return self.quals_avg() / Team.max_quals_avg

    def norm_elims_avg(self):
        return self.elims_avg() / Team.max_elims_avg

    def ranking_score(self):
        return 0.2 * self.norm_quals_avg() + \
            0.5 * self.norm_elims_avg() + \
            0.1 * self.ei_count + \
            0.15 * self.ca_count + \
            0.03 * self.rookie_count + \
            0.02 * self.other_count


class NoSuchCommand(Exception):
    pass

def usage():
    print("usage: tba.py <list|avg|rank> [district] <eventcode1> ... <eventcoden>")

def get_teams(eventcodes):
    teams = {}
    for event in eventcodes:
        eventteams = {}
        if path.exists(event+".teams"):
            with open(event+".teams", 'r') as f:
               eventteams = pickle.load(f)
        else:
            r = tba_get(EVENTTEAMSURL % {"eventkey" : event})
            for team in r.json():
                if team["key"] not in teams:
                    eventteams[team["key"]] = Team(team["key"])
            with open(event+".teams", 'w') as f:
                    pickle.dump(eventteams, f)
        teams.update(eventteams)

    return teams


def main():
    command = sys.argv[1]
    if command not in COMMANDS:
        raise NoSuchCommand(command)
    district = sys.argv[3] if sys.argv[2] == "district" else None
    year = sys.argv[4] if district else None
    events = []
    if district:
        r = requests.get(DISTRICTEVENTSURL % {"district":district,"year":year}, headers = HEADERS)
        for event in r.json():
            events.append(event["key"])
    else:
        events = sys.argv[2:]
    teams = get_teams(events)

    if command == "list":
        for team in sorted(teams.values(), lambda x, y : cmp(x.team_number, y.team_number)):
            print(team.team_number)
    elif command == "avg":
        for team in sorted(teams.values(), lambda x, y : cmp(x.team_number, y.team_number)):
            team.populate_data()
            print(team)
    elif command == "rank":
        for i, team in enumerate(teams.values()):
            print("%.02d%%" % (i+1/len(teams)))
            team.populate_data()
        for team in sorted(teams.values(), lambda x, y : cmp(x.ranking_score(), y.ranking_score()), reverse = True):
            print(team)

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except NoSuchCommand as e:
        print("Invalid command {}" % e.message, sys.stderr)
        usage()
        sys.exit(1)


