from urllib.request import urlopen
from bs4 import BeautifulSoup, NavigableString
import csv
import jinja2
from datetime import datetime

DAY_MAPPING = {
    'July 1 - Schedule': 1,
    'July 2 - Schedule': 2,
    'July 3 - Schedule': 3,
    'July 4 - Schedule': 4,
}

ROOM_MAPPING = {
    'Main Events': 'main-events',
    'Community Stage': 'community-stage',
    'Grammy Museum Terrace': 'grammy-museum-terrace',
    'Petree Hall': 'petree-hall',
    'The Novo': 'the-novo',
    'JW-Diamond (VAPOLLO VIRTUAL STAGE)': 'jw-diamond',
    'JW-Diamond  (VAPOLLO VIRTUAL STAGE)': 'jw-diamond',
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

def is_cleared(description):
    ldesc = description.lower()
    if 'this room will be cleared' in ldesc:
        return True
    if 'this room will not be cleared' in ldesc:
        return False
    return None

def parse_event(node):
    day_text = node.parent.attrs['data-day']
    room_text = node.css.select_one('.timebar .channel .bold').text.strip()
    start = node.css.select_one('.timebar .start .bold').text.strip()
    datetime_start = datetime.strptime(start, '%I:%M %p')
    end = node.css.select_one('.timebar .end .bold').text.strip()
    datetime_end = datetime.strptime(end, '%I:%M %p')
    description = ''.join(t.text for t in node.css.select_one('.desc') if isinstance(t, NavigableString))
    return {
        'day': DAY_MAPPING.get(day_text),
        'title': node.css.select_one('.title').text.strip(),
        'room': ROOM_MAPPING.get(room_text, room_text),
        'time_start': '{:02d}{:02d}'.format(datetime_start.hour, datetime_start.minute),
        'time_end': '{:02d}{:02d}'.format(datetime_end.hour, datetime_end.minute),
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
        fieldnames = ['day', 'time_start', 'time_end', 'room', 'cleared', 'title', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

JINJA_ENV = jinja2.Environment(loader=jinja2.PackageLoader('ax_schedule_table'))

def write_schedule_table(events):
    template = JINJA_ENV.get_template('template.html')
    render = template.render(events=events)
    with open('schedule_table.html', 'w') as f:
        print(render, file=f)

if __name__ == '__main__':
    events = read_events_local()
    write_csv(events)
    write_schedule_table(e for e in events if e.get('day') == 1)