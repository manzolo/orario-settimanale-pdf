#!/usr/bin/env python3
"""
Genera orario.html da orario.csv come calendario settimanale compatto.
"""

import csv
import html
import sys
from collections import defaultdict

ALL_DAYS = ['Lunedi', 'Martedi', 'Mercoledi', 'Giovedi', 'Venerdi', 'Sabato', 'Domenica']
DAY_IT = {
    'Lunedi': 'Lunedì', 'Martedi': 'Martedì', 'Mercoledi': 'Mercoledì',
    'Giovedi': 'Giovedì', 'Venerdi': 'Venerdì', 'Sabato': 'Sabato', 'Domenica': 'Domenica',
}
COLORS = {
    'Linda': '#bfdbfe',
    'Mariel': '#fbcfe8',
    'Vittoria': '#bbf7d0',
}
DEFAULT_COLOR = '#fef9c3'

SVG_W = 1123
SVG_H = 794
MARGIN = 22
TITLE_H = 40
HEADER_H = 46
MORNING_H = 72
TIME_W = 86
GRID_PAD = 10


def to_min(s):
    h, m = map(int, s.strip().split(':'))
    return h * 60 + m


def to_hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def round15(m):
    return ((m + 7) // 15) * 15


def color_for(entry):
    return entry.get('colore') or COLORS.get(entry['nome'], DEFAULT_COLOR)


def hex_to_rgb(color):
    color = color.lstrip('#')
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb


def mix(color, target, amount):
    base = hex_to_rgb(color)
    other = hex_to_rgb(target)
    mixed = tuple(int(base[i] * (1 - amount) + other[i] * amount) for i in range(3))
    return rgb_to_hex(mixed)


def card_fill(color):
    return mix(color, '#ffffff', 0.15)


def card_stroke(color):
    return mix(color, '#94a3b8', 0.35)


def esc(text):
    return html.escape(str(text), quote=False)


def load(path):
    timed, morning = [], []
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): (v.strip() if v else '') for k, v in row.items()}
            if row.get('stampa', '').lower() == 'no':
                continue
            if row['inizio'].lower() == 'mattina':
                morning.append(row)
                continue
            row['s'] = to_min(row['inizio'])
            row['e'] = to_min(row['fine'])
            row['gs'] = round15(row['s'])
            row['ge'] = round15(row['e'])
            timed.append(row)
    return timed, morning


def active_days(entries, morning):
    days = {e['giorno'] for e in entries} | {e['giorno'] for e in morning}
    return [d for d in ALL_DAYS if d in days]


def assign_lanes(day_entries):
    lanes_end = []
    lane_count = 1
    for entry in sorted(day_entries, key=lambda e: (e['gs'], e['ge'])):
        lane = None
        for i, end in enumerate(lanes_end):
            if end <= entry['gs']:
                lane = i
                lanes_end[i] = entry['ge']
                break
        if lane is None:
            lane = len(lanes_end)
            lanes_end.append(entry['ge'])
        overlaps = 1
        for other in day_entries:
            if other is entry:
                continue
            if other['gs'] < entry['ge'] and other['ge'] > entry['gs']:
                overlaps += 1
        entry['lane'] = lane
        entry['lane_count'] = max(entry.get('lane_count', 1), overlaps)
        lane_count = max(lane_count, len(lanes_end), overlaps)
    for entry in day_entries:
        entry['lane_count'] = lane_count


def text_block(lines, x, y, size, weight='400', fill='#1e293b', dy=0):
    parts = [f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="{weight}" fill="{fill}" font-family="DejaVu Sans, Arial, sans-serif">']
    for i, line in enumerate(lines):
        delta = 0 if i == 0 else dy
        parts.append(f'<tspan x="{x}" dy="{delta}">{esc(line)}</tspan>')
    parts.append('</text>')
    return ''.join(parts)


def fit_font_size(text, width, maximum, minimum):
    estimate = width / max(1, len(text) * 0.62)
    return max(minimum, min(maximum, int(estimate)))


def left_text_block(lines, x, y, size, weight='400', fill='#1e293b', dy=0):
    parts = [f'<text x="{x}" y="{y}" text-anchor="start" font-size="{size}" font-weight="{weight}" fill="{fill}" font-family="DejaVu Sans, Arial, sans-serif">']
    for i, line in enumerate(lines):
        delta = 0 if i == 0 else dy
        parts.append(f'<tspan x="{x}" dy="{delta}">{esc(line)}</tspan>')
    parts.append('</text>')
    return ''.join(parts)


def split_activity(activity):
    parts = activity.split(None, 1)
    if len(parts) == 2 and len(activity) > 8:
        return parts
    return [activity]


def render_event_card(svg, entry, x, y, w, h):
    base = color_for(entry)
    fill = card_fill(base)
    stroke = card_stroke(base)
    accent = mix(base, '#ffffff', 0.05)
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.2" filter="url(#shadow)"/>')
    accent_w = max(24, min(w - 20, w * 0.58))
    svg.append(f'<rect x="{x + 10}" y="{y + 8}" width="{accent_w}" height="5" rx="3" fill="{accent}" opacity="0.95"/>')

    pad_x = 12
    inner_w = max(20, w - pad_x * 2)
    center_x = x + w / 2
    top_y = y + 16

    name = entry['nome']
    activity = entry['attivita']
    time_label = f'{entry["inizio"]}-{entry["fine"]}'
    note = entry.get('note')

    strip = h < 50
    compact = w < 150 or h < 64
    tiny = w < 112 or h < 50

    if strip:
        title_lines = [name, activity]
        title_size = fit_font_size(max(title_lines, key=len), inner_w, 12, 10)
        time_size = 10
        svg.append(text_block(title_lines, center_x, y + 16, title_size, weight='700', dy=11))
        svg.append(text_block([time_label], center_x, y + h - 8, time_size, fill='#475569'))
        return

    if tiny:
        compact_w = max(18, w - 16)
        name_size = fit_font_size(name, compact_w, 10, 9)
        activity_lines = split_activity(activity)
        activity_size = fit_font_size(max(activity_lines, key=len), compact_w, 12, 10)
        time_size = 10
        svg.append(text_block([name], center_x, y + 17, name_size, weight='700', fill='#334155'))
        svg.append(text_block(activity_lines, center_x, y + 31, activity_size, weight='700', dy=12))
        svg.append(text_block([time_label], center_x, y + h - 8, time_size, fill='#475569'))
        return

    if compact:
        compact_w = max(20, w - 20)
        name_size = fit_font_size(name, compact_w, 11, 10)
        activity_lines = split_activity(activity)
        activity_size = fit_font_size(max(activity_lines, key=len), compact_w, 13, 11)
        time_size = 11
        svg.append(text_block([name], center_x, y + 19, name_size, weight='700', fill='#334155'))
        svg.append(text_block(activity_lines, center_x, y + 35, activity_size, weight='700', dy=13))
        extra_y = 35 + 13 * (len(activity_lines) - 1)
        svg.append(text_block([time_label], center_x, y + extra_y + 18, time_size, fill='#475569'))
        if note and h >= 78:
            svg.append(text_block([note], center_x, y + extra_y + 31, 9, fill='#64748b'))
        return

    name_size = fit_font_size(name, inner_w, 11 if h < 76 else 12, 10)
    activity_size = fit_font_size(activity, inner_w, 15 if h > 92 else 13, 11)
    time_size = max(12, activity_size - 1)
    note_size = max(9, time_size - 1)

    svg.append(text_block([name.upper()], center_x, top_y, name_size, weight='700', fill='#334155'))
    svg.append(text_block([activity], center_x, top_y + 20, activity_size, weight='700'))
    svg.append(text_block([time_label], center_x, top_y + 44, time_size, fill='#475569'))
    if note and h >= 84:
        svg.append(text_block([note], center_x, top_y + 60, note_size, fill='#64748b'))


def render_svg(entries, morning, out):
    days = active_days(entries, morning)
    if not days:
        days = ALL_DAYS[:5]

    by_day = defaultdict(list)
    for entry in entries:
        by_day[entry['giorno']].append(entry)
    for day in days:
        assign_lanes(by_day[day])

    min_time = min((e['gs'] for e in entries), default=14 * 60)
    max_time = max((e['ge'] for e in entries), default=20 * 60)
    if min_time == max_time:
        max_time += 60

    top = MARGIN
    grid_x = MARGIN + TIME_W + 10
    grid_y = top + TITLE_H + HEADER_H + 8
    if morning:
        grid_y += MORNING_H + 18
    grid_w = SVG_W - grid_x - MARGIN
    grid_h = SVG_H - grid_y - MARGIN - 10
    day_w = grid_w / len(days)
    minute_h = grid_h / (max_time - min_time)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">',
        '<defs>',
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.10"/>',
        '</filter>',
        '</defs>',
        f'<rect width="{SVG_W}" height="{SVG_H}" fill="#edf2f7"/>',
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{SVG_W - 2 * MARGIN}" height="{SVG_H - 2 * MARGIN}" rx="28" fill="#f8fafc"/>',
        text_block(['ORARIO SETTIMANALE'], SVG_W / 2, top + 22, 17, weight='500', fill='#334155'),
    ]

    header_y = top + TITLE_H
    svg.append(f'<rect x="{grid_x}" y="{grid_y - 6}" width="{grid_w}" height="{grid_h + 6}" rx="0" fill="#ffffff" stroke="#dbe4ee" stroke-width="1.2"/>')
    for i, day in enumerate(days):
        x = grid_x + i * day_w
        chip_x = x + 6
        chip_w = day_w - 12
        svg.append(f'<rect x="{chip_x}" y="{header_y}" width="{chip_w}" height="{HEADER_H}" rx="16" fill="#233047"/>')
        svg.append(text_block([DAY_IT[day]], x + day_w / 2, header_y + 29, 15, weight='700', fill='#f8fafc'))

    if morning:
        morning_y = top + TITLE_H + HEADER_H + 16
        svg.append(f'<rect x="{MARGIN + 2}" y="{morning_y}" width="{TIME_W - 6}" height="{MORNING_H}" rx="18" fill="#e2e8f0"/>')
        svg.append(text_block(['Mattina'], MARGIN + (TIME_W - 2) / 2, morning_y + 42, 13, weight='700', fill='#64748b'))
        morning_by_day = defaultdict(list)
        for entry in morning:
            morning_by_day[entry['giorno']].append(entry)
        for i, day in enumerate(days):
            cell_x = grid_x + i * day_w
            items = morning_by_day[day]
            if not items:
                continue
            inner_x = cell_x + GRID_PAD / 2
            inner_y = morning_y
            inner_w = day_w - GRID_PAD
            stack_h = (MORNING_H - 6 * (len(items) - 1)) / len(items)
            for idx, entry in enumerate(items):
                y = inner_y + idx * (stack_h + 6)
                fill = card_fill(color_for(entry))
                stroke = card_stroke(color_for(entry))
                svg.append(f'<rect x="{inner_x}" y="{y}" width="{inner_w}" height="{stack_h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1" filter="url(#shadow)"/>')
                lines = [f'{entry["nome"]} {entry["attivita"]}']
                if entry.get('note'):
                    lines.append(entry['note'])
                svg.append(text_block(lines, inner_x + inner_w / 2, y + stack_h / 2 - (7 if len(lines) > 1 else -4), 12, weight='700', dy=16))

    for minute in range(min_time, max_time + 1, 15):
        y = grid_y + (minute - min_time) * minute_h
        if minute < max_time:
            if minute % 60 == 0:
                svg.append(f'<line x1="{grid_x}" y1="{y}" x2="{grid_x + grid_w}" y2="{y}" stroke="#d5deea" stroke-width="1.2"/>')
            elif minute % 30 == 0:
                svg.append(f'<line x1="{grid_x}" y1="{y}" x2="{grid_x + grid_w}" y2="{y}" stroke="#eef3f8" stroke-width="0.8"/>')
        if minute < max_time and minute % 60 == 0:
            label = to_hhmm(minute)
            svg.append(text_block([label], MARGIN + TIME_W / 2, y + 6, 13, weight='800', fill='#334155'))

    for i in range(len(days) + 1):
        x = grid_x + i * day_w
        svg.append(f'<line x1="{x}" y1="{grid_y}" x2="{x}" y2="{grid_y + grid_h}" stroke="#dde5ef" stroke-width="1"/>')

    for i, day in enumerate(days):
        day_x = grid_x + i * day_w
        for entry in by_day[day]:
            lanes = max(1, entry['lane_count'])
            lane_gap = 4 if lanes > 1 else 0
            usable_w = day_w - GRID_PAD * 2 - lane_gap * (lanes - 1)
            lane_w = usable_w / lanes
            box_x = day_x + GRID_PAD + (lane_w + lane_gap) * entry['lane']
            box_y = grid_y + (entry['gs'] - min_time) * minute_h + 2
            box_w = lane_w
            duration = entry['ge'] - entry['gs']
            min_height = 48 if duration <= 30 else 32
            box_h = max(min_height, duration * minute_h - 4)
            render_event_card(svg, entry, box_x, box_y, box_w, box_h)

    svg.append('</svg>')
    html_doc = '\n'.join([
        '<!DOCTYPE html>',
        '<html lang="it">',
        '<head>',
        '<meta charset="UTF-8">',
        '<style>@page { size: A4 landscape; margin: 0; } body { margin: 0; }</style>',
        '</head>',
        '<body>',
        '\n'.join(svg),
        '</body>',
        '</html>',
    ])
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f'✓ {out} generato da {path}')


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'orario.csv'
    out = path.replace('.csv', '.html') if path.endswith('.csv') else path + '.html'
    entries, morning = load(path)
    render_svg(entries, morning, out)
