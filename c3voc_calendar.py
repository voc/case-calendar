#! /usr/bin/env python3

import argparse
import datetime

import yaml
import gantt

class C3VOCCalendar:
    resources = {}

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

    def is_resource_known(self, resource_name):
        return resource_name in self.resources

    def create_unique_gantt_resource(self, resource_name):
        if not self.is_resource_known(resource_name):
            resource = gantt.Resource(resource_name)
            self.resources[resource_name] = resource

    def create_resourses_from_event(self, event_details):
        """Create a unique Gantt resource for all resources in the event.

        This makes sure we only have 1 Gantt resource for all the occurences of a resource over all the events
        """
        for room_case in event_details['room cases']:
            self.create_unique_gantt_resource(room_case)

        for audio_case in event_details['audio cases']:
            self.create_unique_gantt_resource(audio_case)

    def retrieve_resources_for_event(self, event_details):
        """Read the resources from the evernt details and return a list of the Gantt resources for the event"""

        necessary_resources = []

        for room_case in event_details['room cases']:
            resource = self.resources[room_case]
            necessary_resources.append(resource)

        for audio_case in event_details['audio cases']:
            resource = self.resources[audio_case]
            necessary_resources.append(resource)

        return necessary_resources


    def create_event_as_gantt_task(self, event_name, event_details):
        """Create a Gantt task  for the event and assign the resources"""

        # parse the start time into a datetime and find the length of the event in days
        start_date = event_details['start']
        end_date = event_details['end']
        duration = end_date - start_date

        days = duration.days

        # Retrieve a list of the resources assigned to this event
        resources = self.retrieve_resources_for_event(event_details)

        # Create the task
        task = gantt.Task(name = event_name,
                          start = start_date,
                          duration = days,
                          resources = resources)

        return task


    def create_calendar(self):
        """Iterate over the parsed YAML calendar file and add the "resources" to the project. An event is a task and
        the audio cases and room cases are resources
        """

        for event_name, event_details in self.calendar.items():
            # First gather the resources
            self.create_resourses_from_event(event_details)

            # Create the task and assign the resources
            event = self.create_event_as_gantt_task(event_name = event_name, event_details = event_details)

            # Add the task to the project
            self.gantt_project.add_task(event)

    def export_calendar(self, svg_name):
        """Create an SVG from Gantt project for the current year"""
        today = datetime.date.today()
        start_date = today
        start_date = start_date.replace(day = 1)
        start_date = start_date.replace(month = 1)

        end_date = today
        end_date = end_date.replace(month = 12)
        end_date = end_date.replace(day = 31)

        self.gantt_project.make_svg_for_resources(filename = svg_name,
                                                  today = today,
                                                  start = start_date,
                                                  end = end_date)


    def main(self, arguments):
        """The main application function, this is where it all starts properly"""
        if self.load_yaml_file(arguments.calendar_yaml_file):
            self.gantt_project = gantt.Project(name='C3VOC')

            self.create_calendar()

            self.export_calendar(arguments.calendar_svg_file)

        else:
            print("""Failure while trying to load the YAML file, please check error message, fix the problem and try again""")

        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("calendar_yaml_file", help="YAML file to use as source for the calendar")
    parser.add_argument("calendar_svg_file", help="SVG file to use as output for the calendar")
    args = parser.parse_args()

    calendar = C3VOCCalendar()
    result = calendar.main(args)

    exit(result)
