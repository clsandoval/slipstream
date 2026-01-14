#!/usr/bin/env python3
"""Generate visual diagram of all 5 dashboard states."""

from PIL import Image, ImageDraw, ImageFont
import os

# Canvas dimensions
WIDTH = 2400
HEIGHT = 1600

# Colors - Aquatic Minimalism palette
SLATE_900 = (15, 23, 42)
SLATE_800 = (30, 41, 59)
SLATE_700 = (51, 65, 85)
SLATE_400 = (148, 163, 184)
WHITE = (248, 250, 252)
GREEN_500 = (34, 197, 94)
BLUE_500 = (59, 130, 246)
SKY_400 = (56, 189, 248)
BLACK = (0, 0, 0)

# Font paths
FONT_DIR = "/home/clsandoval/.claude/plugins/cache/anthropic-agent-skills/document-skills/f23222824449/skills/canvas-design/canvas-fonts"

def load_fonts():
    return {
        'mono_bold': ImageFont.truetype(f"{FONT_DIR}/JetBrainsMono-Bold.ttf", 72),
        'mono_giant': ImageFont.truetype(f"{FONT_DIR}/JetBrainsMono-Bold.ttf", 120),
        'mono_medium': ImageFont.truetype(f"{FONT_DIR}/JetBrainsMono-Regular.ttf", 36),
        'mono_small': ImageFont.truetype(f"{FONT_DIR}/JetBrainsMono-Regular.ttf", 24),
        'sans_bold': ImageFont.truetype(f"{FONT_DIR}/Outfit-Bold.ttf", 28),
        'sans_regular': ImageFont.truetype(f"{FONT_DIR}/Outfit-Regular.ttf", 22),
        'sans_title': ImageFont.truetype(f"{FONT_DIR}/Outfit-Bold.ttf", 18),
        'sans_large': ImageFont.truetype(f"{FONT_DIR}/Outfit-Bold.ttf", 48),
    }

def draw_voice_indicator(draw, x, y, status='listening'):
    """Draw voice indicator dot with label."""
    color = GREEN_500 if status == 'listening' else SLATE_400
    draw.ellipse([x, y, x+12, y+12], fill=color)
    fonts = load_fonts()
    draw.text((x + 20, y - 3), status.capitalize(), fill=SLATE_400, font=fonts['sans_regular'])

def draw_sparkline(draw, x, y, width, height):
    """Draw a simple sparkline graph."""
    import random
    random.seed(42)
    points = []
    for i in range(20):
        px = x + (width * i / 19)
        py = y + height - (random.random() * 0.6 + 0.2) * height
        points.append((px, py))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=SKY_400, width=3)

def draw_state_sleeping(draw, x, y, w, h, fonts):
    """SLEEPING state - minimal clock on black."""
    # Background
    draw.rectangle([x, y, x+w, y+h], fill=BLACK)

    # State label
    draw.text((x + 20, y + 15), "SLEEPING", fill=SLATE_700, font=fonts['sans_title'])

    # Clock centered
    clock_text = "02:34"
    bbox = draw.textbbox((0, 0), clock_text, font=fonts['mono_bold'])
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + h // 2 - 30), clock_text, fill=SLATE_700, font=fonts['mono_bold'])

def draw_state_standby(draw, x, y, w, h, fonts):
    """STANDBY state - ready to swim."""
    # Background
    draw.rectangle([x, y, x+w, y+h], fill=SLATE_900)

    # State label
    draw.text((x + 20, y + 15), "STANDBY", fill=SLATE_400, font=fonts['sans_title'])

    # Clock
    clock_text = "14:32"
    bbox = draw.textbbox((0, 0), clock_text, font=fonts['mono_bold'])
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + 80), clock_text, fill=WHITE, font=fonts['mono_bold'])

    # Ready message
    msg = "Ready to swim"
    bbox = draw.textbbox((0, 0), msg, font=fonts['sans_bold'])
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + 170), msg, fill=SLATE_400, font=fonts['sans_bold'])

    # Voice indicator
    draw_voice_indicator(draw, x + w - 130, y + h - 35, 'listening')

def draw_state_swimming(draw, x, y, w, h, fonts):
    """SWIMMING state - giant stroke rate."""
    # Background
    draw.rectangle([x, y, x+w, y+h], fill=SLATE_900)

    # State label
    draw.text((x + 20, y + 15), "SWIMMING", fill=SKY_400, font=fonts['sans_title'])

    # Timer at top
    timer = "5:00"
    bbox = draw.textbbox((0, 0), timer, font=fonts['mono_medium'])
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + 50), timer, fill=WHITE, font=fonts['mono_medium'])

    # Giant stroke rate
    rate = "54"
    bbox = draw.textbbox((0, 0), rate, font=fonts['mono_giant'])
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2 - 30, y + 90), rate, fill=WHITE, font=fonts['mono_giant'])

    # /min label and trend
    draw.text((x + (w + tw) // 2 - 20, y + 100), "/min", fill=SLATE_400, font=fonts['sans_regular'])
    draw.text((x + (w + tw) // 2 - 20, y + 130), "↔", fill=WHITE, font=fonts['sans_bold'])

    # Sparkline
    draw_sparkline(draw, x + 40, y + 210, w - 80, 40)

    # Voice indicator
    draw_voice_indicator(draw, x + w - 130, y + h - 35, 'listening')

def draw_state_resting(draw, x, y, w, h, fonts):
    """RESTING state - expanded info."""
    # Background
    draw.rectangle([x, y, x+w, y+h], fill=SLATE_900)

    # State label
    draw.text((x + 20, y + 15), "RESTING", fill=GREEN_500, font=fonts['sans_title'])

    # Header row
    draw.text((x + 25, y + 45), "6:00", fill=WHITE, font=fonts['mono_medium'])
    draw.text((x + 25, y + 85), "SESSION", fill=SLATE_400, font=fonts['sans_title'])

    draw.text((x + w - 100, y + 45), "REST", fill=WHITE, font=fonts['sans_bold'])
    draw.text((x + w - 100, y + 75), "0:45", fill=SLATE_400, font=fonts['mono_small'])

    # Divider
    draw.line([(x + 20, y + 115), (x + w - 20, y + 115)], fill=SLATE_700, width=1)

    # Two columns
    col1_x = x + 25
    col2_x = x + w // 2 + 10

    draw.text((col1_x, y + 125), "LAST INTERVAL", fill=SLATE_400, font=fonts['sans_title'])
    draw.text((col1_x, y + 148), "Avg: 52 /min", fill=WHITE, font=fonts['sans_regular'])
    draw.text((col1_x, y + 172), "Est: 324m", fill=WHITE, font=fonts['sans_regular'])
    draw.text((col1_x, y + 196), "Strokes: 180", fill=WHITE, font=fonts['sans_regular'])

    draw.text((col2_x, y + 125), "NEXT UP", fill=SLATE_400, font=fonts['sans_title'])
    draw.text((col2_x, y + 148), "Interval 2/4", fill=WHITE, font=fonts['sans_regular'])
    draw.text((col2_x, y + 172), "4:00 duration", fill=WHITE, font=fonts['sans_regular'])

    # Coach message box
    draw.rectangle([x + 20, y + 230, x + w - 20, y + 275], fill=SLATE_800, outline=None)
    draw.text((x + 30, y + 243), "COACH:", fill=SLATE_400, font=fonts['sans_title'])
    draw.text((x + 95, y + 243), "Ready when you are!", fill=WHITE, font=fonts['sans_regular'])

    # Voice indicator
    draw_voice_indicator(draw, x + 25, y + h - 35, 'listening')

def draw_state_summary(draw, x, y, w, h, fonts):
    """SUMMARY state - session complete."""
    # Background
    draw.rectangle([x, y, x+w, y+h], fill=SLATE_900)

    # State label
    draw.text((x + 20, y + 15), "SUMMARY", fill=SLATE_400, font=fonts['sans_title'])

    # Title
    title = "Session Complete"
    bbox = draw.textbbox((0, 0), title, font=fonts['sans_large'])
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y + 50), title, fill=WHITE, font=fonts['sans_large'])

    # Stats grid 2x2
    stats = [
        ("DURATION", "6:00"),
        ("DISTANCE", "324m"),
        ("STROKES", "180"),
        ("AVG RATE", "52/min"),
    ]

    positions = [
        (x + 40, y + 130),
        (x + w // 2 + 20, y + 130),
        (x + 40, y + 210),
        (x + w // 2 + 20, y + 210),
    ]

    for i, (label, value) in enumerate(stats):
        px, py = positions[i]
        draw.text((px, py), label, fill=SLATE_400, font=fonts['sans_title'])
        draw.text((px, py + 25), value, fill=WHITE, font=fonts['mono_medium'])

def main():
    # Create canvas
    img = Image.new('RGB', (WIDTH, HEIGHT), SLATE_800)
    draw = ImageDraw.Draw(img)
    fonts = load_fonts()

    # Title
    title = "SLIPSTREAM DASHBOARD STATES"
    draw.text((60, 40), title, fill=WHITE, font=fonts['sans_large'])

    # Subtitle
    subtitle = "Poolside swim coach interface • 5 adaptive layouts"
    draw.text((60, 100), subtitle, fill=SLATE_400, font=fonts['sans_regular'])

    # Layout dimensions for each state
    state_w = 440
    state_h = 320
    padding = 40
    start_y = 160

    # Row 1: SLEEPING, STANDBY, SWIMMING
    draw_state_sleeping(draw, 60, start_y, state_w, state_h, fonts)
    draw_state_standby(draw, 60 + state_w + padding, start_y, state_w, state_h, fonts)
    draw_state_swimming(draw, 60 + 2 * (state_w + padding), start_y, state_w, state_h, fonts)

    # Row 2: RESTING (wide), SUMMARY
    resting_w = state_w + 200
    draw_state_resting(draw, 60, start_y + state_h + padding, resting_w, state_h, fonts)
    draw_state_summary(draw, 60 + resting_w + padding, start_y + state_h + padding, state_w + 160, state_h, fonts)

    # State flow arrows and labels at bottom
    flow_y = HEIGHT - 100
    draw.text((60, flow_y), "State Flow:", fill=SLATE_400, font=fonts['sans_bold'])

    flow_text = "SLEEPING → STANDBY → SWIMMING ↔ RESTING → SUMMARY"
    draw.text((200, flow_y), flow_text, fill=SKY_400, font=fonts['mono_small'])

    flow_desc = "(no connection)    (connected)     (active swimming)  (rest periods)   (session end)"
    draw.text((200, flow_y + 35), flow_desc, fill=SLATE_400, font=fonts['sans_regular'])

    # Save
    output_path = "/home/clsandoval/cs/slipstream/dashboard/dashboard-states.png"
    img.save(output_path, 'PNG', quality=95)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
