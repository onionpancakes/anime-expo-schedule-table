from urllib.request import urlopen
from bs4 import BeautifulSoup, NavigableString
import csv
import jinja2
from datetime import datetime

DAY_MAPPING = {
    'July 1 - Schedule': '1',
    'July 2 - Schedule': '2',
    'July 3 - Schedule': '3',
    'July 4 - Schedule': '4',
}

ROOM_MAPPING = {
    'Main Events': 'main-events',
    'Petree Hall': 'petree-hall',
    'Community Stage': 'community-stage',
    'JW-Diamond (VAPOLLO VIRTUAL STAGE)': 'jw-diamond',
    'JW-Diamond  (VAPOLLO VIRTUAL STAGE)': 'jw-diamond',
    'JW-Platinum': 'jw-platinum',
    'The Novo': 'the-novo',
    'Grammy Museum Terrace': 'grammy-museum-terrace',
    '402 AB': '402-AB',
    '403 AB': '403-AB',
    '404 AB': '404-AB',
    '406 AB': '406-AB',
    '408 AB': '408-AB',
    '409 AB': '409-AB',
    '411': '411',
    '511': '511',
    '515 A': '515-A',
    '515 B': '515-B',
}

# { (day, title, end): end_correct }
END_CORRECTION = {
    ('4', 'Horimiya: The Missing Pieces panel by Crunchyroll and Aniplex, Inc.', '11:20 PM'): '11:20 AM',
}

def is_cleared_prior(description):
    ldesc = description.lower()
    if 'this room will be cleared prior to this panel' in ldesc:
        return 'Y'
    if 'this room will not be cleared prior to this panel' in ldesc:
        return 'N'
    return '?'

def is_cleared_after(description):
    ldesc = description.lower()
    if 'this room will be cleared for the next panel' in ldesc:
        return 'Y'
    if 'this room will not be cleared after this panel' in ldesc:
        return 'N'
    if 'this room will not be cleared for the next panel' in ldesc:
        return 'N'
    return '?'

def parse_event(node):
    # Day
    day_text = node.parent.attrs['data-day']
    day = DAY_MAPPING.get(day_text)
    # Title
    title = node.css.select_one('.title').text.strip()
    # Room
    room_text = node.css.select_one('.timebar .channel .bold').text.strip()
    room = ROOM_MAPPING.get(room_text, room_text)
    # Start
    start = node.css.select_one('.timebar .start .bold').text.strip()
    start_datetime = datetime.strptime(start, '%I:%M %p')
    start_time = '{:02d}{:02d}'.format(start_datetime.hour, start_datetime.minute)
    # End
    end = node.css.select_one('.timebar .end .bold').text.strip()
    end_correct = END_CORRECTION.get((day, title, end), end)
    end_datetime = datetime.strptime(end_correct, '%I:%M %p')
    end_time = '{:02d}{:02d}'.format(end_datetime.hour, end_datetime.minute)
    # Description
    description = ''.join(t.text for t in node.css.select_one('.desc') if isinstance(t, NavigableString))
    return {
        'day': day,
        'title': title,
        'room': room,
        'start': start,
        'end': end,
        'start_time': start_time,
        'end_time': end_time,
        'description': description,
        'cleared_prior': is_cleared_prior(description),
        'cleared_after': is_cleared_after(description),
    }

def parse_ax_schedule_local(filepath='ax_schedule.html'):
    with open(filepath) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return [parse_event(e) for e in soup.css.select('.event')]

def parse_ax_schedule_web(url='https://www.anime-expo.org/ax/schedule-2023/'):
    with urlopen(url) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return [parse_event(e) for e in soup.css.select('.event')]

def write_parsed_events_csv(events, filepath='data/parsed_events.csv'):
    with open(filepath, 'w') as f:
        fieldnames = ['day', 'start', 'end', 'start_time', 'end_time', 'room', 'cleared_prior', 'cleared_after', 'title', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

def read_events():
    with open('data/parsed_events.csv') as f:
        yield from csv.DictReader(f)
    with open('data/community_events.csv') as f:
        yield from csv.DictReader(f)
    with open('data/ax_dance_events.csv') as f:
        yield from csv.DictReader(f)
    with open('data/beer_garden_events.csv') as f:
        yield from csv.DictReader(f)
    with open('data/lounge21_events.csv') as f:
        yield from csv.DictReader(f)

JINJA_ENV = jinja2.Environment(loader=jinja2.PackageLoader('ax_schedule_table'))

def write_schedule_table(events):
    events_by_day = {}
    for e in events:
        events_by_day.setdefault(e.get('day'), []).append(e)
    template = JINJA_ENV.get_template('template.html')
    for day in ['1','2','3','4']:
        render = template.render(day=day, events=events_by_day.get(day))
        with open(f'docs/day{day}.html'.format(day), 'w') as f:
            print(render, file=f)

if __name__ == '__main__':
    parsed_events = parse_ax_schedule_web()
    write_parsed_events_csv(parsed_events)
    # Generate schedule table
    events = read_events()
    write_schedule_table(events)