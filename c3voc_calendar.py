#! /usr/bin/env python3

import argparse
import datetime
import urllib.request
import json

import yaml
import gantt
import re

from dateutil.relativedelta import relativedelta
from collections import OrderedDict


class ColourWheel:
    """Class that will return an endless aount of colors from a color wheel based on C3VOC green (#28C3AB)

    Source: http://paletton.com/#uid=c3d0p3G0S0kprGteZQMkBLdvfCm-Rrp
    """

    colours = ['#28C3AB', '#28C3A9', '#386FC8', '#FFB534', '#FF8634', '#78E1D0', '#83A8E3', '#FFD488', '#FFB888',
               '#4AD1BA', '#5888D4', '#FFC35B', '#FF9D5B', '#04B799', '#1556BC', '#FFA506', '#FF6B06', '#008A73',
               '#DA8B00', '#DA5800']

    def __init__(self):
        self.list_iterator = iter(self.colours)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            colour = next(self.list_iterator)

            return colour
        except:
            self.list_iterator = iter(self.colours)
            colour = next(self.list_iterator)

            return colour


class C3VOCCalendar:
    """A class representing the C3VOC calendar. It parses various data sources and then exports them as a GANTT chart in SVG form"""
    resources = {}
    calendar = {}

    def __init__(self):
        self.create_unique_gantt_resource('Unassigned')

    def load_yaml_file(self, yaml_file_name):
        """Loads the requested YAML file and tries to parse it into a datastructure"""
        try:
            with open(yaml_file_name, 'r') as stream:
                try:
                    self.calendar = yaml.safe_load(stream)
                    return True
                except yaml.YAMLError as yaml_exception:
                    print(yaml_exception)
        except OSError as open_error:
            print(open_error)

        return False


    def is_event_were_interested_in(self, event_start_date, calendar_year):
        if calendar_year:
            return event_start_date.year == int(calendar_year)
        else:
            today = datetime.date.today()
            first_of_the_year = today.replace(month=1)
            first_of_the_year = first_of_the_year.replace(day=1)

            return event_start_date >= first_of_the_year

    def load_json_url(self, json_url, calendar_year):
        """Downloads a json file from the supplied URL and reads into the format as defined by the YAML file loader"""
        try:
            with urllib.request.urlopen(json_url) as url:
                events = json.loads(url.read().decode())
                #print(events)

                for source_name, source_event in events["voc_events"].items():

                    event_date = datetime.datetime.strptime(source_event["start_date"], "%Y-%m-%d").date()

                    if self.is_event_were_interested_in(event_date, calendar_year):
                        event = dict()
                        event["start"] = event_date
                        event["end"] = datetime.datetime.strptime(source_event["end_date"], "%Y-%m-%d").date()

                        room_cases = []
                        audio_cases = []

                        #temp_cases = []
                        #
                        #for case in source_event["cases"]:
                        #    if "/" in case:
                        #        temp = case.split('/')
                        #        for thing in temp:
                        #            temp_cases.append(thing)
                        #
                        #    if "+" in case:
                        #        temp = case.split('+')
                        #        for thing in temp:
                        #            temp_cases.append(thing)

                        #for case in temp_cases:
                        for case in source_event["cases"]:
                            case = case.replace('?', '')
                            if case == '@@CASE@@' or case == '':
                                continue
                            
                            if case in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                                room_cases.append(case)
                            elif case[0] == "A":
                                audio_cases.append(case.upper())
                            elif case[0] == "S":
                                room_cases.append(case.upper())
                            elif case.upper() in ["NEIN", "?", "X", "XX", "-"]:
                                # These values are considered as non-assigned cases
                                continue
                            else:
                                room_cases.append(case.upper())


                        event["room cases"] = room_cases
                        event["audio cases"] = audio_cases

                        self.calendar[source_name] = event

                if len(self.calendar) > 0:
                    #print("Calendar = %s" % str(self.calendar))

                    print("Calendar = %s" % json.dumps(self.calendar, indent=2, cls=JSONEncoder))
                    return True

        except Exception as e:
            import traceback
            print("""Received an exception: %s\nTraceback: %s""" % (str(e), traceback.format_exc()))

        return False


    def is_resource_known(self, resource_name):
        return resource_name in self.resources

    def create_unique_gantt_resource(self, resource_name):
        if not self.is_resource_known(resource_name):
            resource = gantt.Resource(resource_name)
            self.resources[resource_name] = resource
            print('created resource', resource_name)

    def create_resourses_from_event(self, event_details):
        """Create a unique Gantt resource for all resources in the event.

        This makes sure we only have 1 Gantt resource for all the occurences of a resource over all the events
        """
        if 'room cases' in event_details:
            for room_case in event_details['room cases']:
                self.create_unique_gantt_resource(room_case)

        if 'audio cases' in event_details:
            for audio_case in event_details['audio cases']:
                self.create_unique_gantt_resource(audio_case)

    def retrieve_resources_for_event(self, event_details):
        """Read the resources from the evernt details and return a list of the Gantt resources for the event"""

        necessary_resources = []

        if 'room cases' in event_details:
            for room_case in event_details['room cases']:
                resource = self.resources[room_case]
                necessary_resources.append(resource)

        if 'audio cases' in event_details:
            for audio_case in event_details['audio cases']:
                resource = self.resources[audio_case]
                necessary_resources.append(resource)

        if len(necessary_resources) == 0:
            resource = self.resources['Unassigned']
            necessary_resources.append(resource)

        return necessary_resources


    def create_event_as_gantt_task(self, event_name, event_details, colour):
        """Create a Gantt task  for the event and assign the resources"""

        # parse the start time into a datetime and find the length of the event in days
        start_date = event_details['start']
        end_date = event_details['end']
        duration = end_date - start_date

        # Retrieve a list of the resources assigned to this event
        resources = self.retrieve_resources_for_event(event_details)

        # Create the task
        task = gantt.Task(name = event_name,
                          start = start_date,
                          duration = duration.days + 1,
                          resources = resources,
                          color = colour)

        return task


    def create_calendar(self, sort_by_date = False):
        """Iterate over the parsed YAML calendar file and add the "resources" to the project. An event is a task and
        the audio cases and room cases are resources
        """

        colours = ColourWheel()


        # from https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/
        convert = lambda text: int(text) if text.isdigit() else text
        def sort_case(x):
            first_case = x[1]['room cases'][0] if len(x[1]['room cases']) > 0 else ''
            result = [ convert(c) for c in re.split('([0-9]+)', first_case) ]
            #print('sort key', x[0], result)
            return result
        def sort_date_case(x):
            first_case = x[1]['room cases'][0] if len(x[1]['room cases']) > 0 else ''
            return [ str(x[1]['start']), first_case ]

        sorted_calendar = OrderedDict(sorted(self.calendar.items(), key=(sort_date_case if sort_by_date else sort_case)))

        for event_name, event_details in sorted_calendar.items():
            print(event_name, event_details)
            # First gather the resources
            self.create_resourses_from_event(event_details)

            # Create the task and assign the resources
            event = self.create_event_as_gantt_task(event_name = event_name, event_details = event_details, colour = next(colours))

            # Add the task to the project
            self.gantt_project.add_task(event)

    def export_calendar_year(self, svg_name, year):
        """Create an SVG from Gantt project for the current year"""
        today = datetime.date.today()
        start_date = today
        start_date = start_date.replace(day = 1)
        start_date = start_date.replace(month = 1)

        end_date = today
        end_date = end_date.replace(month = 12)
        end_date = end_date.replace(day = 31)

        if year:
            start_date = start_date.replace(year = int(year))
            end_date = end_date.replace(year=int(year))

        self.gantt_project.make_svg_for_resources(
            filename = 'resources-'+svg_name,
            today = today,
            start = start_date,
            end = end_date,
            one_line_for_tasks = True,
        )
        self.gantt_project.make_svg_for_tasks(
            filename = svg_name,
            today = today,
            start = start_date, end = end_date,
        )

    def export_calendar_monthly(self, year, svg_prefix, svg_suffix):
        """Create an SVG from Gantt project for the current year"""

        # Yes, 14, this is where the range stops
        # we also create the chart for January of next year (month=13)
        for month in range(1,14):
            self.export_calendar_month(year, month, svg_prefix, svg_suffix)
        

    def export_calendar_month(self, year, month, svg_prefix, svg_suffix):
        """Create an SVG from Gantt project for the selected month of year"""

        cases_svg_name = "resources-%s%02d%s" % (svg_prefix, month, svg_suffix)
        event_svg_name = "%s%02d%s" % (svg_prefix, month, svg_suffix)


        today = datetime.date.today()
        if not(year):
            year = today.year

        # allow simple preview to next year
        if month > 12:
            month = month % 12
            year += 1
 
        # Base the start and end dates on today
        start_date = datetime.date(year, month, 1) + relativedelta(day=1)
        end_date = start_date + relativedelta(day=1, months=+1, days=-1)

        self.gantt_project.make_svg_for_resources(
            filename = cases_svg_name,
            today = today,
            start = start_date, end = end_date,
            one_line_for_tasks = True,
        )
        self.gantt_project.make_svg_for_tasks(
            filename = event_svg_name,
            today = today,
            start = start_date, end = end_date,
        )


    def main(self, arguments):
        """The main application function, this is where it all starts properly"""
        generate_output = False

        calendar_year = None
        if arguments.calendar_year:
            calendar_year = arguments.calendar_year.strip()

        if arguments.calendar_yaml_file:
            if self.load_yaml_file(arguments.calendar_yaml_file.strip()):
                generate_output = True
            else:
                print("""Failure while trying to load the YAML file, please check error message, fix the problem and try again""")
        elif arguments.calendar_json_url:
            if self.load_json_url(arguments.calendar_json_url.strip(), calendar_year):
                generate_output = True
            else:
                print("""Loading the JSON file from %s failed. Please check the supplied URL""" % (arguments.calendar_json_url))
        else:
            print("""The supplied combination of parameters is not sufficient to do something. Please review""")

        if generate_output:
            gantt.define_not_worked_days([])
            self.gantt_project = gantt.Project(name='C3VOC')

            self.create_calendar(not(arguments.calendar_monthly))

            if arguments.calendar_monthly:
                self.export_calendar_monthly(calendar_year, arguments.calendar_monthly_prefix, arguments.calendar_monthly_suffix)
            else:
                self.export_calendar_year(arguments.calendar_svg_file.strip(), calendar_year)

            return True

        return False

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date): 
            return obj.__str__()
        #if isinstance(obj, method-wrapper): 
        #    return obj.__str__
        return json.JSONEncoder.default(self, obj)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", help="YAML file to use as source for the calendar", dest="calendar_yaml_file", action="store")
    parser.add_argument("-o", help="SVG file to use as output for the calendar", dest="calendar_svg_file", action="store")
    parser.add_argument("-u", help="URL to download JSON from", dest="calendar_json_url", action="store")
    parser.add_argument("-y", help="Year to create chart for, current year if not supplied", dest="calendar_year", action="store")
    parser.add_argument("-m", help="Create monthly files", dest="calendar_monthly", action="store_true")
    parser.add_argument("-p", help="Monthly file prefix", dest="calendar_monthly_prefix", action="store")
    parser.add_argument("-s", help="Monthly file suffix", dest="calendar_monthly_suffix", action="store")


    args = parser.parse_args()

    calendar = C3VOCCalendar()
    result = calendar.main(args)

    exit(result)
