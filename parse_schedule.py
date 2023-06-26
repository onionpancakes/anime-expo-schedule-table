from urllib.request import urlopen
from bs4 import BeautifulSoup, NavigableString
import csv

DAY_MAPPING = {
    'July 1 - Schedule': 1,
    'July 2 - Schedule': 2,
    'July 3 - Schedule': 3,
    'July 4 - Schedule': 4,
}

ROOM_MAPPING = {
    'JW-Diamond  (VAPOLLO VIRTUAL STAGE)': 'JW-Diamond (VAPOLLO VIRTUAL STAGE)'
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
    description = ''.join(t.text for t in node.css.select_one('.desc') if isinstance(t, NavigableString))
    return {
        'day': DAY_MAPPING.get(day_text),
        'title': node.css.select_one('.title').text.strip(),
        'room': ROOM_MAPPING.get(room_text, room_text),
        'start': node.css.select_one('.timebar .start .bold').text.strip(),
        'end': node.css.select_one('.timebar .end .bold').text.strip(),
        'description': description,
        'cleared': is_cleared(description)
    }

AX_SCHEDULE_URL = 'https://www.anime-expo.org/ax/schedule-2023/'

if __name__ == '__main__':
    with urlopen(AX_SCHEDULE_URL) as f:
        soup = BeautifulSoup(f, 'html.parser')

    events = [parse_event(e) for e in soup.css.select('.event')]

    with open('schedule.csv', 'w') as f:
        fieldnames = ['day', 'start', 'end', 'room', 'cleared', 'title', 'description']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)