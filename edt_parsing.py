#!/usr/bin/env python3
"""Parsing iCal Hyperplanning -> événements exploitables (réutilisé/affiné
depuis edt_bot_final.py : extraction matière/prof/type déjà solide)."""
import re
from datetime import datetime, timedelta

try:
    import pytz
    PARIS = pytz.timezone("Europe/Paris")
except ImportError:
    PARIS = None

SPECIAL_EVENTS = {
    'annulé': 'ANNULÉ', 'annule': 'ANNULÉ', 'canceled': 'ANNULÉ',
    'tutorat': 'TUTORAT',
    'examen': 'EXAMEN', 'partiel': 'PARTIEL',
    'seconde chance': 'RATTRAPAGE', '2nde chance': 'RATTRAPAGE', '2è chance': 'RATTRAPAGE',
    'rattrapage': 'RATTRAPAGE',
    'soutenance': 'SOUTENANCE',
    'contrôle': 'CONTROLE', 'controle': 'CONTROLE',
}

def fix_text_encoding(text):
    if not text:
        return text
    text = re.sub(r'd\?([a-zA-Zé])', r"d'\1", text)
    text = re.sub(r'l\?([a-zA-Zé])', r"l'\1", text)
    text = re.sub(r'n\?([a-zA-Zé])', r"n'\1", text)
    text = re.sub(r's\?([a-zA-Zé])', r"s'\1", text)
    text = re.sub(r'¿', "'", text)
    text = text.replace('\\,', ',').replace('\\n', ' ').replace('\n', ' ')
    return text.strip()

def utc_to_paris(dt_naive_utc: datetime) -> datetime:
    """Convertit un datetime naïf (supposé UTC, tel que fourni par Hyperplanning)
    en heure de Paris, DST géré par pytz (fiable toute l'année)."""
    if PARIS is None:
        return dt_naive_utc
    import pytz
    aware_utc = pytz.utc.localize(dt_naive_utc)
    return aware_utc.astimezone(PARIS).replace(tzinfo=None)

def parse_ical_datetime(dt_string):
    try:
        dt_clean = dt_string.strip()
        if ';' in dt_clean:
            dt_clean = dt_clean.split(';')[-1]
        is_utc = dt_clean.endswith('Z')
        dt_clean = dt_clean.replace('Z', '')

        if 'T' in dt_clean and len(dt_clean) >= 15:
            date_part, time_part = dt_clean.split('T')
            year, month, day = int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8])
            hour, minute = int(time_part[:2]), int(time_part[2:4])
            second = int(time_part[4:6]) if len(time_part) >= 6 else 0
            dt = datetime(year, month, day, hour, minute, second)
            return utc_to_paris(dt) if is_utc else dt

        elif len(dt_clean) == 8:
            return datetime(int(dt_clean[:4]), int(dt_clean[4:6]), int(dt_clean[6:8]))
    except Exception:
        pass
    return None

def detect_special_event(summary, description=""):
    text = (summary + " " + description).lower()
    for keyword, label in SPECIAL_EVENTS.items():
        if keyword in text:
            return label
    return None

def extract_course_info(summary, description=""):
    info = {
        'type_cours': '', 'matiere': '', 'professeur': '', 'groupe': '',
        'special_event': None, 'is_tutorat': False, 'is_makeup': False, 'is_cancelled': False,
    }
    if not summary:
        return info

    summary = fix_text_encoding(summary)
    description = fix_text_encoding(description)

    special = detect_special_event(summary, description)
    info['special_event'] = special
    if special == 'ANNULÉ':
        info['is_cancelled'] = True
    if special == 'RATTRAPAGE':
        info['is_makeup'] = True
    if 'tutorat' in summary.lower():
        info['is_tutorat'] = True
        info['type_cours'] = 'Tutorat'

    if description:
        m = re.search(r'Matière\s*:\s*([^\n\\]+)', description, re.IGNORECASE)
        if m:
            raw = re.split(r'\\n|<br|Enseignant|Salle', m.group(1).strip(), flags=re.IGNORECASE)[0].strip()
            info['matiere'] = fix_text_encoding(raw)
        m = re.search(r'Enseignant\s*:\s*([^\n\\]+)', description, re.IGNORECASE)
        if m:
            raw = re.split(r'\\n|Salle\s*:', m.group(1).strip())[0].strip()
            info['professeur'] = fix_text_encoding(raw)
        if not info['is_tutorat']:
            m = re.search(r'Type\s*:\s*([\w/]+)', description, re.IGNORECASE)
            if m:
                info['type_cours'] = m.group(1).upper()

    if not info['matiere'] or not info['professeur']:
        parts = [p.strip() for p in summary.split(' - ')]
        if len(parts) >= 3:
            # dernier élément = type si court (CM, TD, TP, CM/TP...)
            if not info['type_cours'] and not info['is_tutorat'] and len(parts[-1]) <= 6:
                info['type_cours'] = parts[-1].upper()
            # groupe(s) en tête si présent
            start_idx = 0
            if parts[0].startswith('Gr'):
                info['groupe'] = parts[0]
                start_idx = 1
            middle = parts[start_idx:-1] if info['type_cours'] else parts[start_idx:]
            if middle:
                if not info['matiere']:
                    info['matiere'] = fix_text_encoding(middle[0])
                if not info['professeur'] and len(middle) > 1:
                    info['professeur'] = fix_text_encoding(middle[-1])

    return info

def fetch_and_parse_ics(ical_text: str) -> list:
    """Parse un flux iCal Hyperplanning en liste d'événements structurés."""
    events = []
    current_event = {}
    in_event = False
    current_field = None
    field_value = []

    for line in ical_text.split('\n'):
        line = line.rstrip('\r')
        if line.startswith(' ') or line.startswith('\t'):
            if current_field and field_value:
                field_value.append(line.strip())
            continue

        if current_field and field_value:
            value = ' '.join(field_value)
            if current_field == 'DTSTART':
                dt = parse_ical_datetime(value)
                if dt:
                    current_event['start'] = dt
            elif current_field == 'DTEND':
                dt = parse_ical_datetime(value)
                if dt:
                    current_event['end'] = dt
            elif current_field == 'SUMMARY':
                current_event['summary'] = value
            elif current_field == 'LOCATION':
                current_event['location'] = value
            elif current_field == 'DESCRIPTION':
                current_event['description'] = value
            current_field = None
            field_value = []

        if line == 'BEGIN:VEVENT':
            in_event = True
            current_event = {}
        elif line == 'END:VEVENT' and in_event:
            if 'start' in current_event and 'end' in current_event:
                events.append(current_event)
            in_event = False
            current_event = {}
        elif in_event and ':' in line:
            field_name = line.split(':', 1)[0].split(';')[0]
            field_content = line.split(':', 1)[1]
            if field_name in ('DTSTART', 'DTEND', 'SUMMARY', 'LOCATION', 'DESCRIPTION'):
                current_field = field_name
                field_value = [field_content]

    for event in events:
        summary = event.get('summary', '')
        description = event.get('description', '')
        event['course_info'] = extract_course_info(summary, description)
        duration = event['end'] - event['start']
        event['duration_hours'] = duration.total_seconds() / 3600

    return events

def filter_for_group(events: list, group_label: str) -> list:
    """Un événement est pertinent pour un groupe si : pas de préfixe Gr* du
    tout (cours commun / CM) OU si le préfixe correspond au groupe demandé."""
    out = []
    for e in events:
        summary = e.get('summary', '')
        has_group_prefix = bool(re.match(r'^\s*Gr[A-Za-z0-9]+', summary))
        if not has_group_prefix:
            out.append(e)
        elif group_label and re.search(rf'\bGr{re.escape(group_label)}\b', summary):
            out.append(e)
    return out

def filter_events_for_week(events: list, monday) -> dict:
    from collections import defaultdict
    week_events = defaultdict(list)
    week_end = monday + timedelta(days=6)
    for event in events:
        d = event['start'].date()
        if monday <= d <= week_end:
            idx = (d - monday).days
            if 0 <= idx < 7:
                week_events[idx].append(event)
    for day in week_events:
        week_events[day].sort(key=lambda x: x['start'])
    return dict(week_events)
