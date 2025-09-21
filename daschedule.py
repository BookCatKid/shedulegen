"""
Schedule Generator Core Module

This module provides functionality for generating SVG schedule layouts with:
- Regular day schedules (4 periods per day)
- X-Day schedules (8 shorter periods)
- Time slots and breaks
- Customizable class names and colors
- Embedded fonts for consistent rendering
- Automatic text sizing and wrapping

The generated schedules are designed for school/academic use with:
- Multiple schedule formats (regular days vs X-days)
- Office hours and breaks
- Lunch periods
- Configurable time slots
- Color-coded class periods
"""

from io import BytesIO
import base64
import svg
from PIL import ImageFont
from fonts import FONT_JOMHURIA_BASE64, FONT_INTER_BASE64
# import cairosvg

OTHER_HEIGHT = 140
CLASS_HEIGHT = 250
BREAK_HEIGHT = 80
TITLE_HEIGHT = 100
XDAY_CLASS_HEIGHT = ((OTHER_HEIGHT*3 + CLASS_HEIGHT*4 + BREAK_HEIGHT*2) - (3*BREAK_HEIGHT) - (2*OTHER_HEIGHT)) / 8

WIDTH = 450

XDAY_GAP = 65

START_X = 200
START_Y = 200

MAIN_OFFSET_X = XDAY_GAP + (WIDTH * 2)
MAIN_OFFSET_Y = TITLE_HEIGHT

TIMES_OFFSET_X = XDAY_GAP + WIDTH
TIMES_OFFSET_Y = TITLE_HEIGHT

XDAY_OFFSET_X = 0
XDAY_OFFSET_Y = TITLE_HEIGHT

STROKE_WIDTH = 4

BASE_CLASS_TEXT_SIZE = 50
BASE_OTHER_TEXT_SIZE = 40
BASE_TIMES_TEXT_SIZE = 45
BASE_TITLE_TEXT_SIZE = 150
BASE_DAY_NUMBERS_TEXT_SIZE = 100
BASE_ROOM_SIZE = 30

MAIN_FONT_FAMILY = "Inter"
TITLE_FONT_FAMILY = "Jomhuria"

CLASS_COLORS = {
    1: "#91DCFA",
    2: "#FEF59C",
    3: "#FFC4E7",
    4: "#E3B5FB",
    5: "#FF9795",
    6: "#A7F0D6",
    7: "#FDC688",
    8: "#CCCCCC"
}

#TITLE_TEXT = "Simon's 9th Grade Timetable"

#CLASSES = {
#    1: "Global History",
#    2: "Free",
#    3: "English I",
#    4: "Accelerated Physics",
#    5: "Foundations",
#    6: "Graphic Design",
#    7: "Spanish II",
#    8: "Math I (H)"
#}

TITLE_TEXT = "Upper School Timetable"

CLASSES = {
    "1": "Class 1",
    "2": "Class 2",
    "3": "Class 3",
    "4": "Class 4",
    "5": "Class 5",
    "6": "Class 6",
    "7": "Class 7",
    "8": "Class 8"
}

ROOMS = {
    "1": "Room 1",
    "2": "Room 2",
    "3": "Room 3",
    "4": "Room 4",
    "5": "Room 5",
    "6": "Room 6",
    "7": "Room 7",
    "8": "Room 8"
}

TEACHERS = {
    "1": "Teacher 1",
    "2": "Teacher 2",
    "3": "Teacher 3",
    "4": "Teacher 4",
    "5": "Teacher 5",
    "6": "Teacher 6",
    "7": "Teacher 7",
    "8": "Teacher 8"
}


FULL_WIDTH = WIDTH*6 + XDAY_GAP
CANVAS_WIDTH = START_X*2+FULL_WIDTH
CANVAS_HEIGHT = START_Y*2+(MAIN_OFFSET_Y+OTHER_HEIGHT*3+CLASS_HEIGHT*4+BREAK_HEIGHT*2)

FONT_STYLE = f'''<style>
@font-face {{
  font-family: "Jomhuria";
  src: url("data:font/ttf;base64,{FONT_JOMHURIA_BASE64}");
}}
@font-face {{
  font-family: "Inter";
  src: url("data:font/ttf;base64,{FONT_INTER_BASE64}");
}}
</style>
'''



def normalize_classes(classes):
    """
    Normalize the schedule dictionary:
    - Keys: period numbers (int or str)

    Args:
        classes (dict): Dictionary mapping period numbers to class names
    """

    classes_int = {int(k): v for k, v in classes.items()}

    return dict(sorted(classes_int.items()))


def measure_text_width(text, font_size, font_base64):
    """
    Measure text width using PIL with base64-encoded font data.

    Args:
        text (str): Text to measure
        font_size (int): Font size in pixels
        font_base64 (str): Base64-encoded font file data

    Returns:
        float: Text width in pixels

    Note:
        Uses PIL's ImageFont.truetype() with BytesIO to load font from base64 data.
        More accurate than SVG text measurement for layout calculations.
    """
    font = ImageFont.truetype(BytesIO(base64.b64decode(font_base64)), font_size)
    return font.getlength(text)


def split_text_two_lines(text):
    """
    Split text into two lines at the optimal word boundary.

    Args:
        text (str): Text to split

    Returns:
        list[str]: List containing 1-2 strings. Single item if no spaces found
                   or splitting not beneficial, two items for optimal split.

    Algorithm:
        - Finds midpoint of text
        - Locates nearest space before and after midpoint
        - Chooses split position closest to midpoint
        - Preserves word boundaries (never splits within words)
    """
    if " " not in text:
        return [text]
    mid = len(text) // 2
    left_space = text.rfind(" ", 0, mid)
    right_space = text.find(" ", mid)
    if left_space == -1 and right_space == -1:
        return [text]
    if left_space == -1:
        split_pos = right_space
    elif right_space == -1:
        split_pos = left_space
    else:
        split_pos = left_space if (mid - left_space) <= (right_space - mid) else right_space
    line1 = text[:split_pos].strip()
    line2 = text[split_pos+1:].strip()
    return [line1, line2]


def fit_text_to_width(text, max_width, base_size=50, min_size=8, font_base64=FONT_INTER_BASE64, allow_split=False):
    """
    Find optimal font size and text layout to fit within specified width.

    Args:
        text (str): Text to fit
        max_width (int): Maximum width in pixels
        base_size (int, optional): Starting font size to try. Defaults to 50.
        min_size (int, optional): Minimum allowed font size. Defaults to 8.
        font_base64 (str, optional): Base64 font data. Defaults to FONT_INTER_BASE64.
        allow_split (bool, optional): Whether to allow text splitting. Defaults to False.

    Returns:
        tuple: When allow_split=True: (font_size, list_of_lines)
               When allow_split=False: font_size (int)

    Strategy:
        1. Try base_size with single line
        2. If allow_split=True and text has spaces, try two-line layout
        3. Reduce font size until text fits or min_size reached
        4. Returns optimal font size and line arrangement
    """
    # Try one line first
    if measure_text_width(text, base_size, font_base64) <= max_width:
        return base_size, [text] if allow_split else base_size

    if allow_split and " " in text:
        lines = split_text_two_lines(text)
        # Now try to find the max font size that fits both lines
        font_size = base_size
        while font_size >= min_size:
            if all(measure_text_width(line, font_size, font_base64) <= max_width for line in lines):
                return font_size, lines
            font_size -= 1
        return min_size, lines
    else:
        # No split allowed or no spaces, just shrink single line
        font_size = base_size
        while font_size >= min_size:
            if measure_text_width(text, font_size, font_base64) <= max_width:
                return font_size, [text]
            font_size -= 1
        return min_size, [text]


def draw_day(x, y, daily_classes, classes, rooms, teachers):
    """
    Generate SVG elements for a single day column in the schedule.

    Args:
        x (int): X coordinate for column positioning
        y (int): Y coordinate for column positioning
        daily_classes (list[int]): List of 4 period numbers for this day [p1, p2, p3, p4]
        classes (dict): Mapping of period numbers to class names

    Returns:
        list: SVG elements (rectangles and text) representing the day column

    Layout:
        - 4 class periods with colored backgrounds based on CLASS_COLORS
        - Automatic text fitting with optional two-line splitting
        - Handles text positioning for single-line vs two-line layouts
        - Bottom section left white for additional content
    """
    elements = [
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT,
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[daily_classes[0]],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+CLASS_HEIGHT+BREAK_HEIGHT,
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[daily_classes[1]],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*2)+BREAK_HEIGHT,
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[daily_classes[2]],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+(BREAK_HEIGHT*2),
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[daily_classes[3]],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2),
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#FFFFFF",
            stroke_width=STROKE_WIDTH,
        ),
    ]

    text_content = str(classes[daily_classes[0]])
    font_size = fit_text_to_width(text_content, WIDTH - 20, base_size=BASE_CLASS_TEXT_SIZE, allow_split=True)
    if len(font_size[1]) == 2:
        elements.append(svg.Text(
            text=font_size[1][0],
            x=x + WIDTH / 2,
            y=y + OTHER_HEIGHT+CLASS_HEIGHT*0.35,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
        elements.append(svg.Text(
            text=font_size[1][1],
            x=x + WIDTH / 2,
            y=y + OTHER_HEIGHT+CLASS_HEIGHT*0.60,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
    else:
        elements.append(svg.Text(
            text=text_content,
            x=x + WIDTH / 2,
            y=y + OTHER_HEIGHT+CLASS_HEIGHT/2,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))

    elements.append(svg.Text(
        text=rooms[str(daily_classes[0])],
        x=x + WIDTH / 2,
        y=y + OTHER_HEIGHT+CLASS_HEIGHT*0.85,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    elements.append(svg.Text(
        text=teachers[str(daily_classes[0])],
        x=x + WIDTH / 2,
        y=y + OTHER_HEIGHT+CLASS_HEIGHT*0.15,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    text_content = str(classes[daily_classes[1]])
    font_size = fit_text_to_width(text_content, WIDTH - 20, base_size=BASE_CLASS_TEXT_SIZE, allow_split=True)
    if len(font_size[1]) == 2:
        elements.append(svg.Text(
            text=font_size[1][0],
            x=x + WIDTH / 2,
            y=y + OTHER_HEIGHT+(CLASS_HEIGHT*0.35)+CLASS_HEIGHT+BREAK_HEIGHT,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
        elements.append(svg.Text(
            text=font_size[1][1],
            x=x + WIDTH / 2,
            y=y + OTHER_HEIGHT+(CLASS_HEIGHT*0.60)+CLASS_HEIGHT+BREAK_HEIGHT,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
    else:
        elements.append(svg.Text(
            text=text_content,
            x=x + WIDTH / 2,
            y=y + OTHER_HEIGHT+(CLASS_HEIGHT/2)+CLASS_HEIGHT+BREAK_HEIGHT,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))

    elements.append(svg.Text(
        text=rooms[str(daily_classes[1])],
        x=x + WIDTH / 2,
        y=y + OTHER_HEIGHT+BREAK_HEIGHT+CLASS_HEIGHT*1.85,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    elements.append(svg.Text(
        text=teachers[str(daily_classes[1])],
        x=x + WIDTH / 2,
        y=y + OTHER_HEIGHT+BREAK_HEIGHT+CLASS_HEIGHT*1.15,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    text_content = str(classes[daily_classes[2]])
    font_size = fit_text_to_width(text_content, WIDTH - 20, base_size=BASE_CLASS_TEXT_SIZE, allow_split=True)
    if len(font_size[1]) == 2:
        elements.append(svg.Text(
            text=font_size[1][0],
            x=x + WIDTH / 2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*2.35)+BREAK_HEIGHT,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
        elements.append(svg.Text(
            text=font_size[1][1],
            x=x + WIDTH / 2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*2.60)+BREAK_HEIGHT,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
    else:
        elements.append(svg.Text(
            text=text_content,
            x=x + WIDTH / 2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT/2)+(CLASS_HEIGHT*2)+BREAK_HEIGHT,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))

    elements.append(svg.Text(
        text=rooms[str(daily_classes[2])],
        x=x + WIDTH / 2,
        y=y + (OTHER_HEIGHT*2)+BREAK_HEIGHT+CLASS_HEIGHT*2.85,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    elements.append(svg.Text(
        text=teachers[str(daily_classes[2])],
        x=x + WIDTH / 2,
        y=y + (OTHER_HEIGHT*2)+BREAK_HEIGHT+CLASS_HEIGHT*2.15,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    text_content = str(classes[daily_classes[3]])
    font_size = fit_text_to_width(text_content, WIDTH - 20, base_size=BASE_CLASS_TEXT_SIZE, allow_split=True)
    if len(font_size[1]) == 2:
        elements.append(svg.Text(
            text=font_size[1][0],
            x=x + WIDTH / 2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*3.35)+(BREAK_HEIGHT*2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
        elements.append(svg.Text(
            text=font_size[1][1],
            x=x + WIDTH / 2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*3.60)+(BREAK_HEIGHT*2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))
    else:
        elements.append(svg.Text(
            text=text_content,
            x=x + WIDTH / 2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT/2)+(CLASS_HEIGHT*3)+(BREAK_HEIGHT*2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=font_size[0],
            font_family=MAIN_FONT_FAMILY
        ))

    elements.append(svg.Text(
        text=rooms[str(daily_classes[3])],
        x=x + WIDTH / 2,
        y=y + (OTHER_HEIGHT*2)+(BREAK_HEIGHT*2)+CLASS_HEIGHT*3.85,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    elements.append(svg.Text(
        text=teachers[str(daily_classes[3])],
        x=x + WIDTH / 2,
        y=y + (OTHER_HEIGHT*2)+(BREAK_HEIGHT*2)+CLASS_HEIGHT*3.15,
        text_anchor="middle",
        dominant_baseline="central",
        font_size=BASE_ROOM_SIZE,
        font_family=MAIN_FONT_FAMILY
    ))

    return elements


def draw_sames(x, y):
    """
    Generate SVG elements for shared schedule components across all days.

    Args:
        x (int): X coordinate for positioning
        y (int): Y coordinate for positioning

    Returns:
        list: SVG elements for office hours, faculty meetings, breaks, and lunch periods

    Components:
        - Office Hours blocks (purple background)
        - Faculty Meeting block (purple background)
        - Break periods (blue background)
        - Lunch period (green background)
        - Study hall/office hours (gray background)
    """
    elements = [
        svg.Rect(
            x=x, y=y,
            width=WIDTH*2, height=OTHER_HEIGHT,
            stroke="black",
            fill="#AB91FA",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x+WIDTH*2, y=y,
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#AB91FA",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x+WIDTH*3, y=y,
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#AB91FA",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+CLASS_HEIGHT,
            width=WIDTH*4, height=BREAK_HEIGHT,
            stroke="black",
            fill="#00B6FF",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(CLASS_HEIGHT*2)+BREAK_HEIGHT,
            width=WIDTH*4, height=OTHER_HEIGHT,
            stroke="black",
            fill="#A8FA91",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+BREAK_HEIGHT,
            width=WIDTH*4, height=BREAK_HEIGHT,
            stroke="black",
            fill="#00B6FF",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Text(
            text='Office Hours',
            x=x + WIDTH,
            y=y + (OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Faculty Meeting',
            x=x + WIDTH*2.5,
            y=y + (OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Office Hours',
            x=x + WIDTH*3.5,
            y=y + (OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Break',
            x=x + WIDTH*2,
            y=y + OTHER_HEIGHT+CLASS_HEIGHT+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Lunch',
            x=x + WIDTH*2,
            y=y + OTHER_HEIGHT+(CLASS_HEIGHT*2)+BREAK_HEIGHT+(OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_CLASS_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Break',
            x=x + WIDTH*2,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+BREAK_HEIGHT+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Flex 1 or Flex 3',
            x=x+WIDTH*0.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.35),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Advisory',
            x=x+WIDTH*1.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.35),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Flex 2 or Flex 4',
            x=x+WIDTH*2.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.35),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='Assembly',
            x=x+WIDTH*3.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.35),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='and or office hours',
            x=x+WIDTH*0.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.65),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='and or office hours',
            x=x+WIDTH*1.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.65),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='and or office hours',
            x=x+WIDTH*2.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.65),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text='and or office hours',
            x=x+WIDTH*3.5,
            y=y + (OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.65),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        )
    ]

    return elements

def draw_times(x, y):
    """
    Generate SVG elements for the time schedule column.

    Args:
        x (int): X coordinate for positioning
        y (int): Y coordinate for positioning

    Returns:
        list: SVG elements showing time slots with gray backgrounds and white text

    Time Slots:
        - 7:50-8:20 AM (Office Hours)
        - 8:30-9:45 AM (Period 1)
        - 9:50-11:05 AM (Period 2)
        - 11:15 AM-12:30 PM (Period 3)
        - 1:15-2:30 PM (Period 4)
        - 2:30-3:15 PM (Study Hall)
    """
    elements = [
        svg.Rect(
            x=x, y=y,
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT,
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+CLASS_HEIGHT,
            width=WIDTH, height=BREAK_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+CLASS_HEIGHT+BREAK_HEIGHT,
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(CLASS_HEIGHT*2)+BREAK_HEIGHT,
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*2)+BREAK_HEIGHT,
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+BREAK_HEIGHT,
            width=WIDTH, height=BREAK_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+(BREAK_HEIGHT*2),
            width=WIDTH, height=CLASS_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2),
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#888888",
            stroke_width=STROKE_WIDTH,
        ),
        # -- TEXT --

        svg.Text(
            text="7:50 - 8:20 a.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="8:30 - 9:45 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(CLASS_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="9:45 - 9:55 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+CLASS_HEIGHT+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="9:55 - 11:10 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+CLASS_HEIGHT+BREAK_HEIGHT+(CLASS_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="11:10 - 11:50 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(CLASS_HEIGHT*2)+BREAK_HEIGHT+(OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="11:50 a.m. - 1:05 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*2)+BREAK_HEIGHT+(CLASS_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="1:05 - 1:15 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+BREAK_HEIGHT+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="1:15 - 2:30 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*3)+(BREAK_HEIGHT*2)+(CLASS_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
        svg.Text(
            text="2:30 - 3:15 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TIMES_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
            fill="#FFFFFF"
        ),
    ]

    return elements


def draw_xday(x, y, classes, free_period_name):
    """
    Generate SVG elements for X-Day schedule column (special schedule format).

    Args:
        x (int): X coordinate for positioning
        y (int): Y coordinate for positioning
        classes (dict): Mapping of period numbers to class names
        free_period_name (str): Name to replace 'Foundations' with

    Returns:
        list: SVG elements for X-Day schedule with shorter periods

    X-Day Format:
        - 8 shorter class periods (XDAY_CLASS_HEIGHT)
        - Office hours, breaks, and lunch periods
        - Different timing than regular days
        - All 8 periods fit in same vertical space as 4 regular periods
    """
    # Replace any class containing 'Foundations' with free_period_name
    classes = {k: (free_period_name if 'Foundations' in str(v) else v) for k, v in classes.items()}

    elements = [
        svg.Rect(
            x=x, y=y,
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#AB91FA",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT,
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[1],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+XDAY_CLASS_HEIGHT,
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[2],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*2),
            width=WIDTH, height=BREAK_HEIGHT,
            stroke="black",
            fill="#00B6FF",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*2)+BREAK_HEIGHT,
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[3],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*3)+BREAK_HEIGHT,
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[4],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*4)+BREAK_HEIGHT,
            width=WIDTH, height=BREAK_HEIGHT,
            stroke="black",
            fill="#00B6FF",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*4)+(BREAK_HEIGHT*2),
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[5],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*5)+(BREAK_HEIGHT*2),
            width=WIDTH, height=OTHER_HEIGHT,
            stroke="black",
            fill="#A8FA91",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*5)+(BREAK_HEIGHT*2),
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[6],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*6)+(BREAK_HEIGHT*2),
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[7],
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*7)+(BREAK_HEIGHT*2),
            width=WIDTH, height=BREAK_HEIGHT,
            stroke="black",
            fill="#00B6FF",
            stroke_width=STROKE_WIDTH,
        ),
        svg.Rect(
            x=x, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*7)+(BREAK_HEIGHT*3),
            width=WIDTH, height=XDAY_CLASS_HEIGHT,
            stroke="black",
            fill=CLASS_COLORS[8],
            stroke_width=STROKE_WIDTH,
        ),

        # -- TEXT --

        svg.Text(
            text="Office Hours",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY,
        ),
        svg.Text(
            text=classes[1],
            x=x + WIDTH / 2,
            y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[1], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="8:30 - 9:10 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[2],
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+XDAY_CLASS_HEIGHT+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[2], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="9:15 - 9:55 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+XDAY_CLASS_HEIGHT+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="Break 9:55 - 10:05 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*2)+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[3],
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*2)+BREAK_HEIGHT+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[3], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="10:05 - 10:45 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*2)+BREAK_HEIGHT+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[4],
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*3)+BREAK_HEIGHT+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[4], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="10:50 - 11:30 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*3)+BREAK_HEIGHT+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="Break 11:30 - 11:40 a.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*4)+BREAK_HEIGHT+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[5],
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[5], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="11:40 a.m. - 12:20 p.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*4)+(BREAK_HEIGHT*2)+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="Lunch",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*5)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_CLASS_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="12:20 - 1:00 p.m.",
            x=x+WIDTH/2, y=y+OTHER_HEIGHT+(XDAY_CLASS_HEIGHT*5)+(BREAK_HEIGHT*2)+(OTHER_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[6],
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*5)+(BREAK_HEIGHT*2)+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[6], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="1:00 - 1:40 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*5)+(BREAK_HEIGHT*2)+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[7],
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*6)+(BREAK_HEIGHT*2)+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[7], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="1:45 - 2:25 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*6)+(BREAK_HEIGHT*2)+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="Break 2:25 - 2:35 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*7)+(BREAK_HEIGHT*2)+(BREAK_HEIGHT/2),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text=classes[8],
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*7)+(BREAK_HEIGHT*3)+(XDAY_CLASS_HEIGHT*0.3),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=fit_text_to_width(classes[8], WIDTH-20, base_size=BASE_CLASS_TEXT_SIZE)[0],
            font_family=MAIN_FONT_FAMILY
        ),
        svg.Text(
            text="2:35 - 3:15 p.m.",
            x=x+WIDTH/2, y=y+(OTHER_HEIGHT*2)+(XDAY_CLASS_HEIGHT*7)+(BREAK_HEIGHT*3)+(XDAY_CLASS_HEIGHT*0.7),
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_OTHER_TEXT_SIZE,
            font_family=MAIN_FONT_FAMILY
        )
    ]

    return elements

def draw_titles(title):
    """
    Generate SVG elements for schedule title and day headers.

    Args:
        title (str): Main schedule title text

    Returns:
        list: SVG elements including background, main title, and day labels

    Elements:
        - White background rectangle
        - Main title (large, Jomhuria font)
        - Day labels: "X Day", "Day 1", "Day 2", "Day 3", "Day 4"
        - Positioned above the schedule grid
    """
    elements = [
        svg.Rect(
            fill="#FFFFFF",
            x=0, y=0,
            width=CANVAS_WIDTH, height=CANVAS_HEIGHT
        ),
        svg.Text(
            text=title,
            x=CANVAS_WIDTH/2, y=((START_Y + MAIN_OFFSET_Y) * 0.85) / 2,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_TITLE_TEXT_SIZE,
            font_family=TITLE_FONT_FAMILY
        ),
        svg.Text(
            text="X Day",
            x=START_X+(WIDTH*0.5), y=(START_Y+MAIN_OFFSET_Y)*0.85,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_DAY_NUMBERS_TEXT_SIZE,
            font_family=TITLE_FONT_FAMILY
        ),
        svg.Text(
            text="Day 1",
            x=START_X+MAIN_OFFSET_X+WIDTH*0.5, y=(START_Y+MAIN_OFFSET_Y)*0.85,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_DAY_NUMBERS_TEXT_SIZE,
            font_family=TITLE_FONT_FAMILY
        ),
        svg.Text(
            text="Day 2",
            x=START_X+MAIN_OFFSET_X+(WIDTH*1.5), y=(START_Y+MAIN_OFFSET_Y)*0.85,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_DAY_NUMBERS_TEXT_SIZE,
            font_family=TITLE_FONT_FAMILY
        ),
        svg.Text(
            text="Day 3",
            x=START_X+MAIN_OFFSET_X+(WIDTH*2.5), y=(START_Y+MAIN_OFFSET_Y)*0.85,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_DAY_NUMBERS_TEXT_SIZE,
            font_family=TITLE_FONT_FAMILY
        ),
        svg.Text(
            text="Day 4",
            x=START_X+MAIN_OFFSET_X+(WIDTH*3.5), y=(START_Y+MAIN_OFFSET_Y)*0.85,
            text_anchor="middle",
            dominant_baseline="central",
            font_size=BASE_DAY_NUMBERS_TEXT_SIZE,
            font_family=TITLE_FONT_FAMILY
        ),
    ]

    return elements

def create_svg(classes, rooms, teachers, title, free_period_name, exact_dimension=True):
    """
    Generate complete SVG schedule from class data and title.

    Args:
        classes (dict): Normalized class schedule mapping periods to names
        title (str): Schedule title text
        exact_dimension (bool, optional): Use exact pixel dimensions vs responsive.
                                        Defaults to True.

    Returns:
        str: Complete SVG markup with embedded fonts and schedule layout

    Layout:
        - X-Day column (left)
        - Times column
        - 4 regular day columns (Day 1-4)
        - Shared elements (office hours, breaks, etc.)
        - Embedded font styles for Inter and Jomhuria fonts

    Day Schedules:
        - Day 1: Periods [1,3,5,7]
        - Day 2: Periods [2,4,6,8]
        - Day 3: Periods [3,1,7,5]
        - Day 4: Periods [4,2,8,6]
    """
    canvas = svg.SVG(
        width=CANVAS_WIDTH if exact_dimension else "100%",
        height=CANVAS_HEIGHT if exact_dimension else "100%",
        preserveAspectRatio="xMidYMid meet",
        viewBox="0 0 " + str(CANVAS_WIDTH) + " " + str(CANVAS_HEIGHT),
        elements=draw_titles(title)+draw_day(START_X+MAIN_OFFSET_X, START_Y+MAIN_OFFSET_Y, [1,3,5,7], classes, rooms, teachers)+draw_day(START_X+MAIN_OFFSET_X+WIDTH, START_Y+MAIN_OFFSET_Y, [2,4,6,8], classes, rooms, teachers)+draw_day(START_X+MAIN_OFFSET_X+WIDTH+WIDTH, START_Y+MAIN_OFFSET_Y, [3,1,7,5], classes, rooms, teachers)+draw_day(START_X+MAIN_OFFSET_X+WIDTH+WIDTH+WIDTH, START_Y+MAIN_OFFSET_Y, [4,2,8,6], classes, rooms, teachers)+draw_sames(START_X+MAIN_OFFSET_X,START_Y+MAIN_OFFSET_Y)+draw_times(START_X+TIMES_OFFSET_X, START_Y+TIMES_OFFSET_Y)+draw_xday(START_X+XDAY_OFFSET_X, START_Y+XDAY_OFFSET_Y, classes, free_period_name)
    )
    return str(canvas).replace(">", ">" + FONT_STYLE, 1)

if __name__ == "__main__":
    classes = normalize_classes(CLASSES)
    if classes is None:
        raise ValueError("Invalid classes format")

    with open("file2.svg", "w", encoding="utf-8") as file:
        file.write(create_svg(classes, ROOMS, TEACHERS, TITLE_TEXT, "Study Period", True))

    # cairosvg.svg2png(url="file2.svg", write_to="file2.png")
