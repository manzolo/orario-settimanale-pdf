#!/usr/bin/env python3
"""
Genera orario.html da orario.csv

Formato CSV (intestazione obbligatoria):
  giorno,nome,attivita,inizio,fine[,note]

  giorno   : Lunedi | Martedi | Mercoledi | Giovedi | Venerdi | Sabato | Domenica
  nome     : nome del bambino (determina il colore)
  attivita : es. Danza, Pallavolo, Judo ...
  inizio   : HH:MM  oppure  mattina
  fine     : HH:MM  oppure  mattina
  note     : (opzionale) testo secondario nella cella
"""

import csv
import sys
from collections import defaultdict

# Ordine canonico dei giorni — vengono mostrati solo quelli presenti nel CSV
ALL_DAYS = ['Lunedi', 'Martedi', 'Mercoledi', 'Giovedi', 'Venerdi', 'Sabato', 'Domenica']
DAY_IT   = {
    'Lunedi': 'Lunedì', 'Martedi': 'Martedì', 'Mercoledi': 'Mercoledì',
    'Giovedi': 'Giovedì', 'Venerdi': 'Venerdì', 'Sabato': 'Sabato', 'Domenica': 'Domenica',
}
COLORS = {
    'Linda':    '#bfdbfe',
    'Mariel':   '#fbcfe8',
    'Vittoria': '#bbf7d0',
}
DEFAULT_COLOR = '#fef9c3'

STYLE = """
  @page { size: 297mm 210mm; margin: 10mm; }
  body {
    font-family: 'DejaVu Sans', Arial, sans-serif;
    margin: 0;
    background: #eef1f5;
  }
  h2 {
    text-align: center;
    margin: 8px 0 10px 0;
    color: #1e293b;
    font-weight: normal;
    font-size: 15px;
    letter-spacing: 3px;
    text-transform: uppercase;
  }
  table {
    border-collapse: separate;
    border-spacing: 3px;
    width: 100%;
  }
  th {
    background-color: #1e293b;
    color: #f1f5f9;
    font-weight: bold;
    font-size: 11px;
    padding: 8px 5px;
    border-radius: 6px;
    letter-spacing: 0.4px;
    border: none;
  }
  td {
    text-align: center;
    padding: 6px 4px;
    vertical-align: middle;
    word-wrap: break-word;
    border: none;
    font-size: 11px;
  }
  td.orario {
    font-weight: bold;
    font-size: 10px;
    color: #64748b;
    background: #dde3eb;
    border-radius: 5px;
    white-space: nowrap;
  }
  td.empty { background: transparent; }
  .name { font-weight: bold; font-size: 11px; color: #1e293b; }
  .time { font-size: 9px; color: #475569; }
"""


# ---------- utilità tempi ----------

def to_min(s):
    h, m = map(int, s.strip().split(':'))
    return h * 60 + m

def to_hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"

def round30(m):
    """Arrotonda al multiplo di 30 minuti più vicino."""
    return ((m + 15) // 30) * 30


# ---------- lettura CSV ----------

def load(path):
    timed, mattina = [], []
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): (v.strip() if v else '') for k, v in row.items()}
            if row['inizio'].lower() == 'mattina':
                mattina.append(row)
            else:
                row['s']  = to_min(row['inizio'])
                row['e']  = to_min(row['fine'])
                row['gs'] = round30(row['s'])
                row['ge'] = round30(row['e'])
                timed.append(row)
    return timed, mattina


# ---------- griglia temporale ----------

def build_slots(entries):
    bounds = sorted({e['gs'] for e in entries} | {e['ge'] for e in entries})
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]

def build_grid(entries, slots):
    grid = defaultdict(lambda: defaultdict(list))
    for e in entries:
        for s, end in slots:
            if e['gs'] <= s and e['ge'] >= end:
                grid[e['giorno']][s].append(e)
    return grid

def slot_is_used(slot_start, grid, active_days):
    return any(grid[d][slot_start] for d in active_days)


# ---------- assegnazione colonne per giorni con sovrapposizioni ----------

def compute_col_assignments(used_slots, grid, active_days):
    """
    Per ogni giorno con attività sovrapposte assegna ciascuna attività a una
    sotto-colonna: 0 (sinistra) alla più lunga, 1 (destra) all'altra.
    Restituisce { giorno: { id(attività): indice_colonna } }
    """
    day_cols = {}
    for day in active_days:
        assignments = {}
        for s, _ in used_slots:
            acts = grid[day][s]
            if len(acts) < 2:
                continue
            sorted_acts = sorted(acts, key=lambda a: -(a['ge'] - a['gs']))
            for i, a in enumerate(sorted_acts[:2]):
                if id(a) not in assignments:
                    assignments[id(a)] = i
        if assignments:
            day_cols[day] = assignments
    return day_cols


# ---------- calcolo rowspan ----------

def rowspan_simple(e, day, start_idx, used_slots, grid):
    count = 0
    for i in range(start_idx, len(used_slots)):
        s, _ = used_slots[i]
        if e in grid[day][s]:
            count += 1
        else:
            break
    return count

def rowspan_col(e, day, start_idx, used_slots, grid):
    count = 0
    for i in range(start_idx, len(used_slots)):
        s, _ = used_slots[i]
        if e in grid[day][s]:
            count += 1
        else:
            break
    return count


# ---------- rendering celle ----------

def color_for(e):
    return COLORS.get(e['nome'], DEFAULT_COLOR)

def cell_content(e):
    note = f'<br><span class="time">{e["note"]}</span>' if e.get('note') else ''
    return (f'<span class="name">{e["nome"]} {e["attivita"]}</span>'
            f'<br><span class="time">{e["inizio"]}–{e["fine"]}</span>{note}')

def make_td(e, rowspan, colspan=1):
    rs = f' rowspan="{rowspan}"' if rowspan > 1 else ''
    cs = f' colspan="{colspan}"' if colspan > 1 else ''
    return (
        f'<td style="background-color:{color_for(e)}; border-radius:8px;"{rs}{cs}>'
        f'{cell_content(e)}</td>'
    )

def render_day_cells(day, slot_idx, used_slots, grid, day_cols, skip):
    s, _ = used_slots[slot_idx]
    acts     = grid[day][s]
    is_split = day in day_cols

    # ── giorno NON diviso ─────────────────────────────────────────────────────
    if not is_split:
        if skip[day][0] > 0:
            skip[day][0] -= 1
            return []
        if not acts:
            return ['<td class="empty"></td>']
        e = acts[0]
        rowspan = rowspan_simple(e, day, slot_idx, used_slots, grid)
        skip[day][0] = rowspan - 1
        return [make_td(e, rowspan)]

    # ── giorno DIVISO (2 sotto-colonne) ───────────────────────────────────────
    day_assignments = day_cols[day]
    sk = skip[day]
    both_free = (sk[0] == 0 and sk[1] == 0)

    if not acts:
        if both_free:
            return ['<td class="empty" colspan="2"></td>']
        cells = []
        for c in range(2):
            if sk[c] > 0:
                sk[c] -= 1
            else:
                cells.append('<td class="empty"></td>')
        return cells

    assigned   = {day_assignments[id(a)]: a for a in acts if id(a) in day_assignments}
    unassigned = [a for a in acts if id(a) not in day_assignments]

    if both_free and not assigned and len(unassigned) == 1:
        e = unassigned[0]
        rowspan = rowspan_simple(e, day, slot_idx, used_slots, grid)
        sk[0] = rowspan - 1
        sk[1] = rowspan - 1
        return [make_td(e, rowspan, colspan=2)]

    cells = []
    for c in range(2):
        if sk[c] > 0:
            sk[c] -= 1
            continue
        if c in assigned:
            e = assigned[c]
            rowspan = rowspan_col(e, day, slot_idx, used_slots, grid)
            sk[c] = rowspan - 1
            cells.append(make_td(e, rowspan))
        elif unassigned and c == 0:
            e = unassigned[0]
            rowspan = rowspan_simple(e, day, slot_idx, used_slots, grid)
            sk[c] = rowspan - 1
            cells.append(make_td(e, rowspan))
        else:
            cells.append('<td class="empty"></td>')
    return cells


# ---------- generazione HTML ----------

def generate(entries, mattina, out='orario.html'):
    # Solo i giorni effettivamente presenti nel CSV, nell'ordine canonico
    days_in_data = {e['giorno'] for e in entries} | {e['giorno'] for e in mattina}
    active_days  = [d for d in ALL_DAYS if d in days_in_data]

    slots    = build_slots(entries)
    grid     = build_grid(entries, slots)
    used     = [(s, e) for s, e in slots if slot_is_used(s, grid, active_days)]
    day_cols = compute_col_assignments(used, grid, active_days)

    skip = {d: [0, 0] if d in day_cols else [0] for d in active_days}

    lines = [f'<!DOCTYPE html>\n<html lang="it">\n<head>\n<meta charset="UTF-8">'
             f'\n<style>{STYLE}</style>\n</head>\n<body>'
             f'\n<h2>Orario Settimanale</h2>\n<table>\n  <thead>\n    <tr>'
             f'\n      <th>Orario</th>']

    for d in active_days:
        ncols = 2 if d in day_cols else 1
        cs = f' colspan="{ncols}"' if ncols > 1 else ''
        lines.append(f'      <th{cs}>{DAY_IT[d]}</th>')
    lines.append('    </tr>\n  </thead>\n  <tbody>')

    # Riga Mattina
    if mattina:
        by_day = defaultdict(list)
        for e in mattina:
            by_day[e['giorno']].append(e)

        lines.append('    <tr>')
        lines.append('      <td class="orario">Mattina</td>')
        for d in active_days:
            cs = ' colspan="2"' if d in day_cols else ''
            events = by_day.get(d, [])
            if not events:
                lines.append(f'      <td class="empty"{cs}></td>')
            elif len(events) == 1:
                e = events[0]
                note_html = f'<br><span class="time">{e["note"]}</span>' if e.get('note') else ''
                lines.append(
                    f'      <td style="background-color:{color_for(e)}; border-radius:8px;"{cs}>'
                    f'<span class="name">{e["nome"]} {e["attivita"]}</span>{note_html}</td>'
                )
            else:
                # Più eventi mattina nello stesso giorno: celle impilate
                divs = []
                for i, e in enumerate(events):
                    mb = ' margin-bottom:2px;' if i < len(events) - 1 else ''
                    note_html = f'<br><span class="time">{e["note"]}</span>' if e.get('note') else ''
                    divs.append(
                        f'<div style="background-color:{color_for(e)};{mb} padding:5px 4px; border-radius:6px;">'
                        f'<span class="name">{e["nome"]} {e["attivita"]}</span>{note_html}</div>'
                    )
                lines.append(
                    f'      <td style="padding:3px; vertical-align:top;"{cs}>'
                    + '\n        '.join([''] + divs)
                    + '\n      </td>'
                )
        lines.append('    </tr>')

    # Righe orarie
    for i, (slot_start, slot_end) in enumerate(used):
        label = f'{to_hhmm(slot_start)}–{to_hhmm(slot_end)}'
        row_cells = [f'      <td class="orario">{label}</td>']
        for d in active_days:
            tds = render_day_cells(d, i, used, grid, day_cols, skip)
            row_cells.extend(f'      {td}' for td in tds)
        lines.append('    <tr>\n' + '\n'.join(row_cells) + '\n    </tr>')

    lines.append('  </tbody>\n</table>\n</body>\n</html>')

    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'✓ {out} generato da {path}')


# ---------- main ----------

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'orario.csv'
    entries, mattina = load(path)
    generate(entries, mattina)
