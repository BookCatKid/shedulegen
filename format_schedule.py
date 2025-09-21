import json

# --------------------------------
# CONFIGURATION
# --------------------------------

INPUT_FILE = "events_monday_by_calendar.json"
OUTPUT_FILE = "formatted_schedule.json"

def parse_event_summary(summary):
    """
    Parses an event title to extract the class name and period number.
    - If the details part starts with "digit*", the class name becomes "Foundations".
    - Otherwise, the class name is everything before " - ".
    - Period number is extracted from the "Block #" pattern.
    Example 1: "Graphic Design - 6 Block 6" -> ("Graphic Design", "6")
    Example 2: "US History - 7* Block 7" -> ("Foundations", "7")
    Returns (class_name, period_number) on success, or (None, None) on failure.
    """
    if " - " not in summary:
        return None, None

    original_class_name, details_part = summary.split(" - ", 1)
    original_class_name = original_class_name.strip()
    details_part = details_part.strip()

    # First, find the required "Block #" to get the period number
    lower_details = details_part.lower()
    keyword = "block "
    if keyword not in lower_details:
        return None, None

    start_index = lower_details.find(keyword) + len(keyword)
    period_string_part = details_part[start_index:].strip()
    if not period_string_part:
        return None, None

    potential_period = period_string_part.split()[0]
    if not potential_period.isdigit():
        return None, None
    period_number = potential_period

    # Now, determine the final class name based on the special rule
    # Check if the details part (e.g., "7* Block 7") starts with a digit and an asterisk
    if len(details_part) >= 2 and details_part[0].isdigit() and details_part[1] == '*':
        final_class_name = "Foundations"
    else:
        final_class_name = original_class_name

    return final_class_name, period_number


def format_room_name(location):
    """
    Adds a prefix to the room name if it's a 2 or 3-digit number.
    - 3 digits -> "USQuad ###"
    - 2 digits -> "VASC ##"
    """
    location_str = str(location or "").strip()
    if location_str.isdigit():
        if len(location_str) == 3:
            return f"USQuad {location_str}"
        elif len(location_str) == 2:
            return f"VASC {location_str}"
    return location_str


def format_schedule_for_events(events):
    """
    Given a list of calendar events, return (formatted_schedule_dict, unrecognized_events_list).
    """
    formatted_schedule = {}
    unrecognized_events = []
    for event in events:
        summary = event.get("summary")
        if not summary:
            continue
        class_name, period = parse_event_summary(summary)
        if class_name is None or period is None:
            unrecognized_events.append(summary)
            continue
        raw_location = event.get("location", "")
        room = format_room_name(raw_location)
        if period not in formatted_schedule:
            formatted_schedule[period] = {
                "name": [],
                "room": []
            }
        formatted_schedule[period]["name"].append(class_name)
        formatted_schedule[period]["room"].append(room)
    return formatted_schedule, unrecognized_events


def main():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            all_schedules = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not read '{INPUT_FILE}'.")
        return
    selected_email = input("Enter the email address for the schedule you want to format: ").strip()
    if selected_email not in all_schedules:
        print(f"\nError: Email '{selected_email}' not found in the input file.")
        return
    student_events = all_schedules[selected_email]
    print(f"\nProcessing {len(student_events)} events for {selected_email}...")
    formatted_schedule, unrecognized_events = format_schedule_for_events(student_events)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(formatted_schedule, f, ensure_ascii=False, indent=4)
    print(f"\nSuccessfully converted the schedule for {selected_email}.")
    print(f"Formatted data saved to '{OUTPUT_FILE}'.")
    if unrecognized_events:
        print("\n--- The following events could not be parsed and were SKIPPED ---")
        for title in unrecognized_events:
            print(f"  - {title}")


if __name__ == "__main__":
    main()
