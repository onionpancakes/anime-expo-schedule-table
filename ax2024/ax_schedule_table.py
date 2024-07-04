from urllib.request import urlopen
from bs4 import BeautifulSoup, NavigableString
import csv
import jinja2
from datetime import datetime
import re
import textwrap

DAY_MAPPING = {
    'Day 1 - July 4': '1',
    'Day 2 - July 5': '2',
    'Day 3 - July 6': '3',
    'Day 4 - July 7': '4',
}

ROOM_MAPPING = {
    'Main Events': 'main-events',
    'Petree Hall': 'petree-hall',
    'JW-Diamond': 'jw-diamond',
    'JW-Platinum': 'jw-platinum',
    'AX Crossing Stage': 'ax-crossing-stage',
    'Community Stage': 'community-stage',
    'The Novo': 'the-novo',
    'Grammy Museum Terrace': 'grammy-museum-terrace',
    'Peacock Theater': 'peacock-theater',
    '402AB': '402-AB',
    '403AB': '403-AB',
    '404AB': '404-AB',
    '406AB': '406-AB',
    '408AB': '408-AB',
    '409AB': '409-AB',
    '411': '411',
    '511ABC': '511-ABC',
    # '511': '511',
    '515A': '515-A',
    '515B': '515-B',
    'AX Dance (Concourse Hall E)': 'ax-dance',
    'AX Dance': 'ax-dance',
    'Beer Garden': 'beer-garden',
    'Lounge 21': 'lounge21',
}

# { (day, title, end): end_correct }
END_CORRECTION = {
    ('1', 'Create Your Own Omamori Amulet & Envision Your Ideal Community!', '3:05 AM'): '3:05 PM',
    ('1', "Voices of the Night: Behind the Making of Ex and Bee - Nightfall's Coven", '4:05 AM'): '4:05 PM',
    ('2', "ATLUS Presents: The World of Metaphor: ReFantazio featuring Katsura Hashino & Shigenori Soejima", '11:20 PM'): '11:20 AM',
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
    if 'this room will be cleared after this panel' in ldesc:
        return 'Y'
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
    start_time = datetime.strptime(start, '%I:%M %p').strftime('%H%M')
    # End
    end = node.css.select_one('.timebar .end .bold').text.strip()
    end_correct = END_CORRECTION.get((day, title, end), end)
    end_time = datetime.strptime(end_correct, '%I:%M %p').strftime('%H%M')
    # Description
    description = ''.join(t.text for t in node.css.select_one('.desc') if isinstance(t, NavigableString))
    return {
        'day': day,
        'title': textwrap.shorten(title, 140, placeholder='...'),
        'room': room,
        'start': start,
        'end': end,
        'start_time': start_time,
        'end_time': end_time,
        'description': f"{title}\n\n{description}",
        'cleared_prior': is_cleared_prior(description),
        'cleared_after': is_cleared_after(description),
        'cancelled': 'CANCELED' in title or 'CANCELLED' in title
    }

def parse_ax_schedule_local(filepath='ax_schedule.html'):
    with open(filepath) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return [parse_event(e) for e in soup.css.select('.event')]

def parse_ax_schedule_web(url='https://www.anime-expo.org/ax/schedule-2024/'):
    with urlopen(url) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return [parse_event(e) for e in soup.css.select('.event')]

def write_parsed_events_csv(events, filepath='ax2024/data/parsed_events.csv'):
    with open(filepath, 'w') as f:
        fieldnames = ['day', 'start', 'end', 'start_time', 'end_time', 'room', 'cleared_prior', 'cleared_after', 'title', 'description', 'cancelled']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

# Activity events

ACTIVITY_EVENT_PATTERN = re.compile(r'(\d\d?:\d\d\s?(?:AM|PM))\s+-\s+(\d\d?:\d\d\s?(?:AM|PM))\s+-\s+(.+)')

def parse_activity_event(node, day, room):
    m = ACTIVITY_EVENT_PATTERN.match(node.text.strip())
    try:
        start_time = datetime.strptime(m.group(1), '%I:%M %p').strftime('%H%M')
    except:
        start_time = datetime.strptime(m.group(1), '%I:%M%p').strftime('%H%M')
    try:
        end_time = datetime.strptime(m.group(2), '%I:%M %p').strftime('%H%M')
    except:
        end_time = datetime.strptime(m.group(2), '%I:%M%p').strftime('%H%M')
    return {
        'day': day,
        'title': m.group(3),
        'room': room,
        'start': m.group(1),
        'end': m.group(2),
        'start_time': start_time,
        'end_time': end_time,
        'description': None,
        'cleared_prior': None,
        'cleared_after': None,
        'cancelled': None
    }

ACTIVITY_DAY_MAPPING = {
    'July 4 (DAY 1)': 1,
    'July 5 (DAY 2)': 2,
    'July 6 (DAY 3)': 3,
    'July 7 (DAY 4)': 4,
}

def parse_activity(url, room):
    with urlopen(url) as f:
        soup = BeautifulSoup(f, 'html.parser')
    day = None
    for e in soup.css.select('.section-group > *'):
        if e.text.strip() == '':
            continue
        elif e.text in ACTIVITY_DAY_MAPPING:
            day = ACTIVITY_DAY_MAPPING.get(e.text)
        elif ACTIVITY_EVENT_PATTERN.match(e.text):
            yield parse_activity_event(e, day, room)
        else:
            continue

# Schedule

def read_events():
    with open('ax2024/data/parsed_events.csv') as f:
        yield from (e for e in csv.DictReader(f) if e.get('cancelled') != 'True')
    #with open('ax2024/data/community_events.csv') as f:
    #    yield from csv.DictReader(f)
    #with open('ax2024/data/ax_dance_events.csv') as f:
    #    yield from csv.DictReader(f)
    #with open('ax2024/data/beer_garden_events.csv') as f:
    #    yield from csv.DictReader(f)
    #with open('ax2024/data/lounge21_events.csv') as f:
    #    yield from csv.DictReader(f)

JINJA_ENV = jinja2.Environment(loader=jinja2.PackageLoader('ax_schedule_table'))

def write_schedule_table(events):
    events_by_day = {}
    for e in events:
        events_by_day.setdefault(e.get('day'), []).append(e)
    template = JINJA_ENV.get_template('template.html')
    for day in ['1','2','3','4']:
        render = template.render(day=day, events=events_by_day.get(day), last_updated_time=datetime.now().strftime('%Y-%m-%d %H:%M'))
        with open(f'docs/2024/day{day}.html'.format(day), 'w') as f:
            print(render, file=f)

if __name__ == '__main__':
    parsed_events = parse_ax_schedule_web()
    write_parsed_events_csv(parsed_events, 'ax2024/data/parsed_events.csv')
    # Community Stage
    parsed_community_stage = parse_activity('https://www.anime-expo.org/activity/community-stage/', 'community-stage')
    write_parsed_events_csv(parsed_community_stage, 'ax2024/data/community_events.csv')
    # Ax Dance
    parsed_ax_dance = parse_activity('https://www.anime-expo.org/activity/ax-dance/', 'ax-dance')
    write_parsed_events_csv(parsed_ax_dance, 'ax2024/data/ax_dance_events.csv')
    # Beer Garden
    parsed_beer_garden = parse_activity('https://www.anime-expo.org/activity/beer-garden/', 'beer-garden')
    write_parsed_events_csv(parsed_beer_garden, 'ax2024/data/beer_garden_events.csv')
    # Lounge21
    parsed_lounge21 = parse_activity('https://www.anime-expo.org/activity/lounge-21/', 'lounge21')
    write_parsed_events_csv(parsed_lounge21, 'ax2024/data/lounge21_events.csv')
    # Generate schedule table
    events = read_events()
    write_schedule_table(events)