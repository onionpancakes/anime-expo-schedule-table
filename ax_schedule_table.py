from urllib.request import urlopen
from bs4 import BeautifulSoup, NavigableString
import csv
import jinja2
from datetime import datetime
import itertools

DAY_MAPPING = {
    'July 1 - Schedule': 1,
    'July 2 - Schedule': 2,
    'July 3 - Schedule': 3,
    'July 4 - Schedule': 4,
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
    (4, 'Horimiya: The Missing Pieces panel by Crunchyroll and Aniplex, Inc.', '11:20 PM'): '11:20 AM',
}

def is_cleared(description):
    ldesc = description.lower()
    if 'this room will be cleared' in ldesc:
        return True
    if 'this room will not be cleared' in ldesc:
        return False
    return None

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
        'start_time': start_time,
        'end_time': end_time,
        'description': description,
        'cleared': is_cleared(description)
    }

def read_events_local(filename='ax_events.html'):
    with open('ax_schedule.html') as f:
        soup = BeautifulSoup(f, 'html.parser')
    return [parse_event(e) for e in soup.css.select('.event')]

def read_events_web(url='https://www.anime-expo.org/ax/schedule-2023/'):
    with urlopen(AX_SCHEDULE_URL) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return [parse_event(e) for e in soup.css.select('.event')]

def write_csv(events, filename='schedule_table.csv'):
    with open(filename, 'w') as f:
        fieldnames = ['day', 'start_time', 'end_time', 'room', 'cleared', 'title', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

JINJA_ENV = jinja2.Environment(loader=jinja2.PackageLoader('ax_schedule_table'))

def write_schedule_table(events):
    events_by_day = {d:list(ev) for d, ev in itertools.groupby(events, key=lambda x: x.get('day'))}
    template = JINJA_ENV.get_template('template.html')
    for day in [1,2,3,4]:
        render = template.render(events=events_by_day.get(day))
        with open(f'schedule_table/day{day}.html'.format(day), 'w') as f:
            print(render, file=f)

if __name__ == '__main__':
    events = read_events_local()
    write_csv(events)
    write_schedule_table(events)