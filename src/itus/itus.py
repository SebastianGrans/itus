
import argparse
from datetime import datetime
from datetime import timedelta


from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


def make_quay_query(quay_id, num_departures, time_range):
    query = gql(
f"""
{{
    quay(
        id: "{quay_id}"
    ) {{
        estimatedCalls(
            numberOfDepartures: {num_departures}
            timeRange: {time_range}
            omitNonBoarding: true
        ) {{
            quay {{
                name
            }}
            realtime
            aimedArrivalTime
            expectedArrivalTime
            serviceJourney {{
                line {{
                    publicCode
                }}
            }}
            destinationDisplay {{
                frontText
            }}
        }}
    }}
}}""")
    return query



def send_query(query):

    transport = AIOHTTPTransport(
        url="https://api.entur.io/journey-planner/v3/graphql",
        headers={
            "Content-Type": "application/json",
            "ET-Client-Name:": "grans-consoleapp"
        }
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)
    result = client.execute(query)
    
    return result

def data_from_call(call):
    """A quay query returns a list calls. A call is a nested dictionary with information about a departure.
    This function extracts the relevant fields into a single layer dictionary.

    Args:
        call (dict): 

    Returns:
        call_data: Dictionary containing information about a specific departure.
    """
    
    datetime_fmt = "%Y-%m-%dT%H:%M:%S%z"

    data = {
        "platform_name": call['quay']['name'],
        "realtime": call['realtime'],
        "line_nr": call['serviceJourney']['line']['publicCode'],
        "line_name": call['destinationDisplay']['frontText'], 
        "aimed_arrival_time": datetime.strptime(
                call['aimedArrivalTime'],
                datetime_fmt
            ).replace(tzinfo=None),
        "expected_arrival_time": datetime.strptime(
                call['expectedArrivalTime'],
                datetime_fmt
            ).replace(tzinfo=None)
    }

    return data


def print_quay_table(data):

    if len(data) == 0:
        return
    # First we determine the minimum width of each field by 
    # finding the longest field.    
    # This can probably fail if line_nr is Null/None
    max_line_nr_width = -1
    for el in data:
        length = len(el['line_nr'])
        if length > max_line_nr_width:
            max_line_nr_width = length

    max_line_name_width = -1
    for el in data:
        length = len(el['line_name'])
        if length > max_line_name_width:
            max_line_name_width = length
    
    platform_name = data[0]['platform_name']
    
    # Example time table line.
    # +-Gløshaugen---------------------------------------------+
    # | 3 Hallset via sentrum       c:a 13 min (14:43 / 14:40) |
    
    line_width = (
        2 + max_line_nr_width + 1 + max_line_name_width + 
        8 + 10 + 1 + 15 + 2 
    )
   
    # The dashes except for beginning +- and ending -+ 
    header_padding = '-'*(line_width - 4 - len(platform_name))
    footer_padding = '-'*(line_width - 4)
        
    header = f"+-{platform_name}{header_padding}-+"
    footer = f"+-{footer_padding}-+"
    
    now = datetime.now()

    print(header)
    for el in data:
        expected = el['expected_arrival_time']
        expected_str = expected.strftime("%H:%M")
        aimed = el['aimed_arrival_time']
        aimed_str = aimed.strftime("%H:%M")
        dt = int((expected-now).seconds/60)
        minutes = ' '*10
        if dt <= 15:
            minutes = f"{dt:2d} min"
            if not el['realtime']:
                minutes = "c:a " + minutes
            else:
                minutes = "    " + minutes


        string = (
            f"| {el['line_nr']:>{max_line_nr_width}} "
            f"{el['line_name']:{max_line_name_width}}"
            f"{' '*8}"
            f"{minutes} "
            f"({expected_str} / {aimed_str}) |"
        )
        print(string)
    print(footer)

def stop_query(
        stop_id,
        num_departures, 
        time_range,
        lines=None
    ):
    """Query for upcoming departures from a specific stop.

    Args:
        stop_id (str): The stop id that can be found at https://stoppested.entur.org/
        num_departures (int): How many departures into the future to query for.
        time_range (int): How many seconds into the future to query for.
        lines (List[str], optional): A whitelist of which lines to present. Defaults to None and displays all lines stopping at that platform.
        
    Returns:
        results: A dictionary with an entry for each platform at that stop. Each dictionary entry contains a list of departure data.
    """
   
    # First get all the quays at the stop
    query = gql(
f'''{{
    stopPlace(
        id: "{stop_id}"
    ) {{
        quays {{
            id
        }}
    }}
}}''') 

    result = send_query(query)
    quays = [el['id'] for el in result['stopPlace']['quays']]

    results = {}

    for quay_id in quays:
        results[quay_id] = quay_query(quay_id, num_departures=num_departures, time_range=time_range, lines=lines)

    return results

def quay_query(
        quay_id,
        num_departures, 
        time_range,
        lines=None
    ):
    """Query for upcoming departures from a specific platform with id `quay_id`.
        
        Note: It is called quay to stay consistent with the Journey Planner API that Entur provides.

    Args:
        quay_id (str): The platform id (aka. quay id) that can be found at https://stoppested.entur.org/
        num_departures (int): How many departures into the future to query for.
        time_range (int): How many seconds into the future to query for.
        lines (List[str], optional): A whitelist of which lines to present. Defaults to None and displays all lines stopping at that platform.
        
    Returns:
        results: A list of upcoming departures.
    """

    query = make_quay_query(quay_id, num_departures, time_range)
    results = send_query(query)

    if lines is not None:
        print("Line filtering is not implemented yet...")
        # TODO: Filter out lines

    calls = results['quay']['estimatedCalls']
    departure_data = []
    for call in calls:
        departure_data.append(data_from_call(call))

    return departure_data

def main():
    # process_stop_query("NSR:StopPlace:44085",  num_departures=5, time_range=3600)

    # exit() 


    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-s', '--stop',
        metavar='stop_id',
        nargs='+', # Require at least one.
        help="The stop id according to the national stop registry. E.g. NSR:StopPlace:44085. Find it at https://stoppested.entur.org/"
    )
    parser.add_argument(
        '-p', '--platform',
        metavar='platform_id',
        nargs='+', # Require at least one.
        help="The quay id according to the national stop registry. E.g. NSR:Quay:75708. Find it at https://stoppested.entur.org/"
    )
    # parser.add_argument(
    #     '-l', '--line', '--lines',
    #     metavar='line_id',
    #     nargs='+' # Require at least one.
    # )

    parser.add_argument(
        '-n',
        metavar='value',
        type=int,
        default=5,
        help="Number of upcoming departures to look up. \nDefault is 5."
        # Fix to positive ints only
        # https://stackoverflow.com/a/39947874
    )
    parser.add_argument(
        '-tr', '--time_range',
        metavar='HH:MM',
        type=str,
        default='01:00',
        help='How long into the into the future we look for departures. \nDefaults to 1 hour.'
    )
    args = parser.parse_args()

    if not args.stop and not args.platform:
        print("No stop or platform specified.")
        parser.print_help()
        exit()

    # Parse the time into seconds.
    t = datetime.strptime("01:01", "%H:%M")
    args.time_range = timedelta(hours=t.hour, minutes=t.minute).seconds

    if args.stop:
        for stop_id in args.stop:
            data = stop_query(stop_id, num_departures=args.n, time_range=args.time_range)
            for quay_id in data:
                print_quay_table(data[quay_id])

    if args.platform:
        for quay_id in args.platform:
            departure_data = quay_query(quay_id, num_departures=args.n, time_range=args.time_range)
            print_quay_table(departure_data)




if __name__ == "__main__":
    main()
    
        
