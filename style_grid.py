#!/usr/bin/env python3
"""Style A — Grille hebdomadaire modernisée (Poppins, cartes à ombre douce)."""
import os
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
WHITE = (255, 255, 255)
GOLD = (255, 210, 120)

TYPE_COLORS = {
    'CM': (167, 139, 250), 'TD': (255, 165, 92), 'TP': (96, 189, 232),
    'CM/TP': (129, 170, 230), 'EXAMEN': (231, 76, 60), 'PARTIEL': (231, 76, 60),
    'RATTRAPAGE': (46, 204, 113), 'TUTORAT': (241, 196, 15), 'default': (150, 150, 160),
}

SUBJECT_PALETTE = [
    (86, 148, 227), (230, 126, 60), (72, 191, 145), (198, 96, 185),
    (235, 168, 60), (94, 173, 210), (211, 84, 100), (140, 120, 220),
]
_subject_cache = {}

def subject_color(name: str):
    if not name:
        return (130, 130, 140)
    if name not in _subject_cache:
        idx = sum(ord(c) for c in name) % len(SUBJECT_PALETTE)
        _subject_cache[name] = SUBJECT_PALETTE[idx]
    return _subject_cache[name]

def _F(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, f"Poppins-{name}.ttf"), size)
    except Exception:
        return ImageFont.load_default()

def _gradient_bg(w, h, top=(24, 26, 46), bot=(40, 34, 66)):
    top_a, bot_a = np.array(top), np.array(bot)
    ys = np.linspace(0, 1, h).reshape(h, 1, 1)
    grad = top_a.reshape(1, 1, 3) + (bot_a - top_a).reshape(1, 1, 3) * ys
    arr = np.repeat(grad, w, axis=1).astype("uint8")
    return Image.fromarray(arr, "RGB")

def _soft_glow(img, cx, cy, r, color, alpha):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).ellipse([cx-r, cy-r, cx+r, cy+r], fill=color+(alpha,))
    ov = ov.filter(ImageFilter.GaussianBlur(r/2.2))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

def _rect(base, x, y, w, h, r, fill_rgba):
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill_rgba)
    return Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")

def _card_shadow(base, x, y, w, h, r, fill_rgba, alpha=70, blur=10):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x, y+4, x+w, y+h+4], radius=r, fill=(0, 0, 0, alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    base = Image.alpha_composite(base.convert("RGBA"), shadow)
    card = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill_rgba)
    return Image.alpha_composite(base, card).convert("RGB")

def wrap_text(text, font, max_width, draw):
    if not text:
        return []
    words, lines, cur = text.split(), [], []
    for w in words:
        t = ' '.join(cur + [w])
        bb = draw.textbbox((0, 0), t, font=font)
        if bb[2]-bb[0] <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    return lines

def fit_text_ellipsis(text, font, max_width, draw):
    """Tronque avec '…' en se basant sur la largeur réelle du texte rendu,
    jamais sur un nombre de caractères arbitraire (qui déborde selon la
    police/le zoom réel)."""
    if not text:
        return text
    bb = draw.textbbox((0, 0), text, font=font)
    if bb[2]-bb[0] <= max_width:
        return text
    for i in range(len(text)-1, 0, -1):
        candidate = text[:i].rstrip() + "…"
        bb = draw.textbbox((0, 0), candidate, font=font)
        if bb[2]-bb[0] <= max_width:
            return candidate
    return "…"

DAYS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
MONTHS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin",
             "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

def generate_grid_edt(group_label, week_events, monday, output):
    W, H = 1680, 1150
    PAD = 40
    HEADER_H = 152
    DAYCOL_W = 74
    FOOTER_H = 46
    START_H, END_H = 8, 19

    img = _gradient_bg(W, H)
    img = _soft_glow(img, W-140, 70, 340, (150, 120, 255), 30)
    draw = ImageDraw.Draw(img)

    # Header
    badge = f"EDT {group_label}"
    bf = _F("SemiBold", 18)
    bb = draw.textbbox((0, 0), badge, font=bf)
    bw = (bb[2]-bb[0]) + 30
    img = _rect(img, PAD, PAD, bw, 40, 20, (167, 139, 250, 255))
    draw = ImageDraw.Draw(img)
    draw.text((PAD+15, PAD+10), badge, font=bf, fill=(20, 14, 30))

    friday = monday + timedelta(days=4)
    date_str = f"Semaine du {monday.day} au {friday.day} {MONTHS_FR[friday.month]} {friday.year}" \
        if monday.month == friday.month else \
        f"Semaine du {monday.day} {MONTHS_FR[monday.month]} au {friday.day} {MONTHS_FR[friday.month]} {friday.year}"
    draw.text((PAD, PAD+52), date_str, font=_F("Black", 30), fill=WHITE)

    goat = "LE GOAT DE L'EDT"
    gf = _F("SemiBold", 14)
    gb = draw.textbbox((0, 0), goat, font=gf)
    gw = (gb[2]-gb[0]) + 26
    img = _rect(img, W-PAD-gw, PAD, gw, 34, 17, (255, 255, 255, 26))
    draw = ImageDraw.Draw(img)
    draw.text((W-PAD-gw+13, PAD+8), goat, font=gf, fill=WHITE)

    grid_top = HEADER_H
    grid_bottom = H - FOOTER_H
    grid_h = grid_bottom - grid_top
    day_w = (W - 2*PAD - DAYCOL_W) / 5
    hour_h = grid_h / (END_H - START_H)

    # Colonnes jours
    for i, day_name in enumerate(DAYS_FR):
        x = PAD + DAYCOL_W + i*day_w
        d = monday + timedelta(days=i)
        img = _rect(img, x, grid_top, day_w-6, 46, 12, (255, 255, 255, 18))
        draw = ImageDraw.Draw(img)
        label = f"{day_name} {d.day}"
        bb = draw.textbbox((0, 0), label, font=_F("SemiBold", 15))
        draw.text((x + (day_w-6-(bb[2]-bb[0]))/2, grid_top+13), label, font=_F("SemiBold", 15), fill=WHITE)

    grid_top2 = grid_top + 58
    grid_h2 = grid_bottom - grid_top2
    hour_h = grid_h2 / (END_H - START_H)

    for h in range(START_H, END_H+1):
        y = grid_top2 + (h-START_H)*hour_h
        draw.text((PAD, y-7), f"{h:02d}h", font=_F("Regular", 13), fill=(120, 122, 132, 170))
        draw.line([(PAD+DAYCOL_W, y), (W-PAD, y)], fill=(110, 112, 122, 40), width=1)

    for i in range(6):
        x = PAD + DAYCOL_W + i*day_w
        draw.line([(x, grid_top2), (x, grid_bottom)], fill=(110, 112, 122, 32), width=1)

    for day_idx, events in week_events.items():
        if day_idx >= 5:
            continue
        x0 = PAD + DAYCOL_W + day_idx*day_w

        # Répartition en "voies" par CLUSTER de vrai chevauchement temporel,
        # pas globalement pour toute la journée : un cours isolé le matin
        # garde toute la largeur même si 2 cours se chevauchent l'après-midi
        # (ex : les 2 options en parallèle).
        ordered = sorted(events, key=lambda e: (e['start'], e['end']))
        clusters = []
        for e in ordered:
            if clusters and e['start'] < clusters[-1]['max_end']:
                clusters[-1]['events'].append(e)
                clusters[-1]['max_end'] = max(clusters[-1]['max_end'], e['end'])
            else:
                clusters.append({'events': [e], 'max_end': e['end']})

        for cluster in clusters:
            lane_end = []
            for e in cluster['events']:
                placed = False
                for i, end_t in enumerate(lane_end):
                    if end_t <= e['start']:
                        e['_lane'] = i
                        lane_end[i] = e['end']
                        placed = True
                        break
                if not placed:
                    e['_lane'] = len(lane_end)
                    lane_end.append(e['end'])
            e_total_lanes = max(len(lane_end), 1)
            for e in cluster['events']:
                e['_total_lanes'] = e_total_lanes

        for e in ordered:
            total_lanes = e.get('_total_lanes', 1)
            lane_w = (day_w - 6) / total_lanes
            ci = e['course_info']
            sh = e['start'].hour + e['start'].minute/60
            eh = e['end'].hour + e['end'].minute/60
            sh, eh = max(sh, START_H), min(eh, END_H)
            if eh <= sh:
                continue
            y0 = grid_top2 + (sh-START_H)*hour_h
            y1 = grid_top2 + (eh-START_H)*hour_h
            block_h = y1 - y0
            if block_h < 8:
                continue

            col = subject_color(ci['matiere'])
            if ci.get('is_makeup'):
                col = TYPE_COLORS['RATTRAPAGE']
            pad = 3
            lane = e.get('_lane', 0)
            bx = x0 + lane*lane_w + pad
            by = y0 + pad
            bw2 = lane_w - 2*pad
            bh2 = block_h - 2*pad

            # Carte translucide (glass) mais grille assourdie juste au-dessus :
            # équilibre entre lisibilité et vivacité des couleurs.
            img = _card_shadow(img, bx, by, bw2, bh2, 10, col+(150,), alpha=60, blur=8)
            draw = ImageDraw.Draw(img)
            img = _rect(img, bx, by, 5, bh2, 3, (255, 255, 255, 220))
            draw = ImageDraw.Draw(img)

            tx = bx + 12
            ty = by + 7
            avail_w = bw2 - 18
            narrow = bw2 < 145

            # La taille de police suit la DURÉE réelle du cours (1h, 1h30, 2h,
            # 3h, 4h+) plutôt que sa hauteur en pixels : un cours de 2h est
            # nettement plus grand qu'un cours d'1h, de façon prévisible.
            duration_h = e.get('duration_hours', (eh - sh))
            if duration_h > 3.25:
                tier = "xl"
            elif duration_h > 2.25:
                tier = "big"
            elif duration_h > 1.6:
                tier = "mid"
            elif duration_h > 1.1:
                tier = "small"
            else:
                tier = "xs"
            if narrow and tier in ("xl", "big"):
                tier = "mid"  # colonne étroite (créneaux simultanés) : on limite la casse

            TIME_SZ  = {"xl": 20, "big": 17, "mid": 15, "small": 13, "xs": 12}
            SUB_SZ   = {"xl": 20, "big": 17, "mid": 15, "small": 13, "xs": 12}
            INFO_SZ  = {"xl": 16, "big": 14, "mid": 13, "small": 12, "xs": 11}
            LINE_GAP = {"xl": 26, "big": 22, "mid": 19, "small": 16, "xs": 14}
            SUB_LINES = {"xl": 3, "big": 3, "mid": 2, "small": 2, "xs": 1}

            f_time = _F("SemiBold", TIME_SZ[tier])
            f_sub  = _F("SemiBold", SUB_SZ[tier])
            f_info = _F("Regular", INFO_SZ[tier])
            f_room = _F("SemiBold", INFO_SZ[tier])
            line_gap = LINE_GAP[tier]

            time_txt = f"{e['start'].strftime('%H:%M')}–{e['end'].strftime('%H:%M')}"
            draw.text((tx, ty), time_txt, font=f_time, fill=WHITE)
            ty += line_gap + (4 if tier in ("xl", "big") else 0)

            type_txt = ci['type_cours'] or ''
            if type_txt and bw2 > 68:
                tbf = _F("SemiBold", 10 if tier in ("small", "xs") else 11)
                ttb = draw.textbbox((0, 0), type_txt, font=tbf)
                tw = (ttb[2]-ttb[0])+14
                th = 16 if tier in ("small", "xs") else 18
                badge_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(badge_ov).rounded_rectangle(
                    [bx+bw2-tw-6, by+6, bx+bw2-6, by+6+th], radius=8, fill=col+(255,))
                img = Image.alpha_composite(img.convert("RGBA"), badge_ov).convert("RGB")
                draw = ImageDraw.Draw(img)
                draw.text((bx+bw2-tw+1, by+8), type_txt, font=tbf, fill=(15, 12, 20))

            matiere = ci['matiere'] or (e.get('summary', '')[:24])
            if ci.get('is_cancelled'):
                matiere = f"ANNULÉ — {matiere}"

            if tier != "xs":
                for line in wrap_text(matiere, f_sub, avail_w, draw)[:SUB_LINES[tier]]:
                    draw.text((tx, ty), line, font=f_sub, fill=WHITE)
                    ty += line_gap
            else:
                line = wrap_text(matiere, f_sub, avail_w, draw)
                if line:
                    draw.text((tx, ty), line[0], font=f_sub, fill=WHITE)
                    ty += line_gap

            # Salle mise en valeur (couleur + gras), professeur en dessous —
            # affichés dès que l'espace vertical le permet, quelle que soit
            # la durée du cours (un cours d'1h30 doit montrer les deux, pas
            # seulement le nom de la matière).
            remaining = by + bh2 - ty
            if remaining > line_gap:
                loc = e.get('location', '')
                if loc:
                    loc_txt = fit_text_ellipsis(loc, f_room, avail_w, draw)
                    draw.text((tx, ty), loc_txt, font=f_room, fill=GOLD)
                    ty += line_gap
                    remaining -= line_gap

            if remaining > line_gap:
                prof = ci['professeur']
                if prof:
                    prof_txt = fit_text_ellipsis(prof, f_info, avail_w, draw)
                    draw.text((tx, ty), prof_txt, font=f_info, fill=(255, 255, 255, 175))
                    ty += line_gap
                    remaining -= line_gap

    # Footer — juste le total, plus de légende (les couleurs n'encodent plus
    # le type de cours ici, la légende n'avait donc plus d'utilité)
    all_events = [e for lst in week_events.values() for e in lst]
    total_h = sum(e['duration_hours'] for e in all_events)
    img = _rect(img, 0, grid_bottom, W, FOOTER_H, 0, (0, 0, 0, 90))
    draw = ImageDraw.Draw(img)
    draw.line([(PAD, grid_bottom), (W-PAD, grid_bottom)], fill=(255, 255, 255, 40), width=1)
    stat_txt = f"{len(all_events)} cours  ·  {total_h:.1f} h cette semaine"
    draw.text((PAD, grid_bottom+16), stat_txt, font=_F("SemiBold", 15), fill=GOLD)

    img.save(output, "PNG", optimize=True)
    return output
