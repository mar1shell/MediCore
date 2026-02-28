#!/usr/bin/env python3
"""
Render the MedRound architecture diagram as a PNG using matplotlib.
Matches the Excalidraw specification exactly:
  - Zone 1: INPUT LAYER  (y=0..480)
  - Zone 2: PROCESSING LAYER  (y=540..1000)
  - Zone 3: OUTPUT LAYER  (y=1080..1340)
  - Zone 4: BACKEND API (FastAPI) + FRONTEND (React/Vite)  (y=1380..1580)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
import numpy as np

# ── Canvas ──────────────────────────────────────────────────────────────────
# Coordinate space: x ∈ [0, 960], y ∈ [-90, 1600]  (y increases down)
# We give a generous right margin so the key connection arrow label fits.
XMAX = 980
YMIN = -90
YMAX = 1600

fig, ax = plt.subplots(figsize=(20, 34))
ax.set_xlim(0, XMAX)
ax.set_ylim(YMIN, YMAX)
ax.invert_yaxis()          # y increases downward
ax.axis('off')
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# ── Palette ──────────────────────────────────────────────────────────────────
C = {
    'blue_fill':      '#a5d8ff',
    'blue_stroke':    '#1971c2',
    'purple_fill':    '#e599f7',
    'purple_stroke':  '#9c36b5',
    'indigo_fill':    '#d0bfff',
    'indigo_stroke':  '#7048e8',
    'orange_fill':    '#ffe8cc',
    'orange_stroke':  '#fd7e14',
    'red_fill':       '#ffc9c9',
    'red_stroke':     '#e03131',
    'green_fill':     '#b2f2bb',
    'green_stroke':   '#2f9e44',
    'gray_fill':      '#e9ecef',
    'gray_stroke':    '#868e96',
    'dark':           '#1e1e1e',
    'white':          '#ffffff',
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def box(ax, x, y, w, h, fill, stroke,
        text='', fontsize=14, lw=2, ls='solid',
        alpha=1.0, tc=None, bold=False, radius=8,
        mono=False, zorder=2):
    """Rounded rectangle + centred label."""
    if tc is None:
        tc = C['dark']
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f'round,pad=0,rounding_size={radius}',
        facecolor=fill, edgecolor=stroke,
        linewidth=lw, linestyle=ls,
        alpha=alpha, zorder=zorder,
    )
    ax.add_patch(patch)
    if text:
        ff = 'monospace' if mono else 'DejaVu Sans'
        ax.text(x + w / 2, y + h / 2, text,
                ha='center', va='center',
                fontsize=fontsize,
                color=tc,
                fontweight='bold' if bold else 'normal',
                fontfamily=ff,
                zorder=zorder + 1,
                multialignment='center',
                linespacing=1.45)


def zone(ax, x, y, w, h, fill, stroke, label, fontsize=14):
    """Dashed zone background + label."""
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0,rounding_size=10',
        facecolor=fill, edgecolor=stroke,
        linewidth=2.5, linestyle='dashed',
        alpha=0.25, zorder=1,
    )
    ax.add_patch(patch)
    ax.text(x + 15, y + 15, label,
            ha='left', va='top',
            fontsize=fontsize, color=stroke,
            fontweight='bold', zorder=2)


def arrow(ax, x1, y1, x2, y2, color, lw=2.5, ls='-',
          label='', loff=(0, 0), rad=0.0, dashed=False):
    """Annotated arrow (straight or curved)."""
    style = '--' if dashed else ls
    conn = f'arc3,rad={rad}'
    ax.annotate(
        '',
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle='->', color=color, lw=lw,
            linestyle=style,
            connectionstyle=conn,
        ),
        zorder=4,
    )
    if label:
        mx = (x1 + x2) / 2 + loff[0]
        my = (y1 + y2) / 2 + loff[1]
        ax.text(mx, my, label,
                ha='center', va='center',
                fontsize=10, color=color, zorder=5,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=color, linewidth=1.0, alpha=0.97))


# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
ax.text(490, -55,
        'MedRound — Critical Information Cross-Validation',
        ha='center', va='center',
        fontsize=24, fontweight='bold', color=C['dark'], zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# ZONE BACKGROUNDS  (drawn first — behind everything)
# ══════════════════════════════════════════════════════════════════════════════
zone(ax, 20,    0, 920, 480, '#e7f5ff', C['gray_stroke'],   'INPUT LAYER',     fontsize=14)
zone(ax, 20,  540, 920, 460, '#fff4e6', C['orange_stroke'], 'PROCESSING LAYER', fontsize=14)
zone(ax, 20, 1080, 920, 260, '#ebfbee', C['green_stroke'],  'OUTPUT LAYER',    fontsize=14)
zone(ax, 20, 1380, 920, 200, '#f8f9fa', C['gray_stroke'],
     'BACKEND API (FastAPI) + FRONTEND (React / Vite)',      fontsize=14)

# ══════════════════════════════════════════════════════════════════════════════
# ZONE 1 — INPUT LAYER
# ══════════════════════════════════════════════════════════════════════════════

# ── LEFT PATH: Chart Upload ──────────────────────────────────────────────────
box(ax, 60, 60, 220, 80, C['blue_fill'], C['blue_stroke'],
    'Doctor\nUploads PDF Chart', fontsize=14, bold=True)

box(ax, 60, 220, 220, 100, C['purple_fill'], C['purple_stroke'],
    'Mistral OCR 3\nPDF / Image Extraction\nHandwritten Notes', fontsize=13)

box(ax, 60, 400, 220, 120, C['indigo_fill'], C['indigo_stroke'],
    'Chart Data\n{ allergies: [...]\n  medications: [...]\n  diagnosis: \'...\' }',
    fontsize=12, mono=False)

# ── RIGHT PATH: Voice Session ────────────────────────────────────────────────
box(ax, 620, 60, 240, 100, C['blue_fill'], C['blue_stroke'],
    'Doctor\nVerbal Monologue\n(Verdict + Prescription)', fontsize=14, bold=True)

box(ax, 620, 240, 240, 110, C['purple_fill'], C['purple_stroke'],
    'ElevenLabs\nVoice Agent\nMedical Context Biasing\n(Chart-Aware)', fontsize=13)

box(ax, 620, 420, 240, 110, C['indigo_fill'], C['indigo_stroke'],
    'Spoken Data\n{ allergies: [...]\n  medications: [...]\n  diagnosis: \'...\' }',
    fontsize=12, mono=False)

# ══════════════════════════════════════════════════════════════════════════════
# ZONE 2 — PROCESSING LAYER
# ══════════════════════════════════════════════════════════════════════════════
box(ax, 330, 580, 280, 100, C['purple_fill'], C['purple_stroke'],
    'Mistral Large LLM\nEntity Extraction\n+ Synonym Checking', fontsize=14)

box(ax, 270, 750, 400, 120, C['orange_fill'], C['orange_stroke'],
    'Cross-Reference Engine\nStep 1: Exact Match\nStep 2: Abbreviation Map\nStep 3: LLM Synonym Check',
    fontsize=13)

box(ax, 290, 940, 360, 90, C['red_fill'], C['red_stroke'],
    'Discrepancy Flags\nRED: Critical (allergy + med conflict)\nYELLOW: Medium (diagnosis mismatch)',
    fontsize=13, tc='#6b0000')

# ══════════════════════════════════════════════════════════════════════════════
# ZONE 3 — OUTPUT LAYER  (3-column UI)
# ══════════════════════════════════════════════════════════════════════════════
box(ax, 50, 1120, 210, 180, C['green_fill'], C['green_stroke'],
    'Chart Data\nAllergies\nMedications\nDiagnosis', fontsize=14)

box(ax, 340, 1120, 260, 180, C['red_fill'], C['red_stroke'],
    'FLAGS\n[RED] CRITICAL MISMATCH\nChart: aspirin allergy\nDoctor: prescribed aspirin!\n[Dismiss]  [Add to Note]',
    fontsize=13, tc='#6b0000')

box(ax, 680, 1120, 210, 180, C['green_fill'], C['green_stroke'],
    'Spoken Data\nAllergies\nMedications\nDiagnosis', fontsize=14)

# ══════════════════════════════════════════════════════════════════════════════
# ZONE 4 — BACKEND API + FRONTEND
# ══════════════════════════════════════════════════════════════════════════════
endpoints = [
    (40,  'POST /upload-chart\nMistral OCR'),
    (260, 'POST /extract-entities\nMistral LLM'),
    (480, 'WS /voice-session\nElevenLabs Agent'),
    (700, 'POST /cross-reference\nDiscrepancy Engine'),
]
for bx, txt in endpoints:
    box(ax, bx, 1430, 200, 80, C['gray_fill'], C['gray_stroke'],
        txt, fontsize=12, mono=True, radius=5)

# ══════════════════════════════════════════════════════════════════════════════
# ARROWS
# ══════════════════════════════════════════════════════════════════════════════

# Zone 1 — LEFT PATH
arrow(ax, 170, 140, 170, 220, C['blue_stroke'])           # PDF Upload → OCR
arrow(ax, 170, 320, 170, 400, C['purple_stroke'])         # OCR → Chart Data

# Zone 1 — RIGHT PATH
arrow(ax, 740, 160, 740, 240, C['blue_stroke'])           # Doctor Voice → ElevenLabs
arrow(ax, 740, 350, 740, 420, C['purple_stroke'])         # ElevenLabs → Spoken Data

# KEY CONNECTION — Chart Data feeds ElevenLabs as context (dashed, orange)
arrow(ax, 280, 460, 620, 340, C['orange_stroke'],
      lw=2.5, dashed=True,
      label='chart context\n(grounding)',
      loff=(0, -18), rad=-0.25)

# Zone 1 → Zone 2: into Mistral LLM
arrow(ax, 170, 520, 370, 580, C['indigo_stroke'],
      lw=2.5, rad=-0.15, label='raw text', loff=(-20, -14))
arrow(ax, 740, 530, 570, 580, C['indigo_stroke'],
      lw=2.5, rad=0.15, label='transcript', loff=(20, -14))

# Zone 2 internal
arrow(ax, 470, 680, 470, 750, C['orange_stroke'], lw=2.5)    # LLM → Cross-Ref
arrow(ax, 470, 870, 470, 940, C['red_stroke'],    lw=2.5)    # Cross-Ref → Flags

# Zone 2 → Zone 3
arrow(ax, 470, 1030, 470, 1120, C['red_stroke'],  lw=2.5)   # Flags → FLAGS UI

# ══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════════════════
legend_items = [
    mpatches.Patch(facecolor=C['blue_fill'],   edgecolor=C['blue_stroke'],   label='Doctor Input'),
    mpatches.Patch(facecolor=C['purple_fill'], edgecolor=C['purple_stroke'], label='AI / ML Model'),
    mpatches.Patch(facecolor=C['indigo_fill'], edgecolor=C['indigo_stroke'], label='Structured Data'),
    mpatches.Patch(facecolor=C['orange_fill'], edgecolor=C['orange_stroke'], label='Cross-Reference'),
    mpatches.Patch(facecolor=C['red_fill'],    edgecolor=C['red_stroke'],    label='Flags / Alerts'),
    mpatches.Patch(facecolor=C['green_fill'],  edgecolor=C['green_stroke'],  label='Output UI'),
    mpatches.Patch(facecolor=C['gray_fill'],   edgecolor=C['gray_stroke'],   label='API Endpoints'),
]
ax.legend(handles=legend_items, loc='lower right',
          fontsize=10, framealpha=0.97, edgecolor='#ced4da',
          title='Component Types', title_fontsize=11,
          bbox_to_anchor=(0.99, 0.01),
          ncol=1, borderpad=0.9, labelspacing=0.55)

# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════
plt.tight_layout(pad=0.4)
output_path = '/home/theslender/coding_stuff/MediCore/MedRound_architecture.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none', format='png')
print(f'Saved PNG → {output_path}')
plt.close()
