import datetime

def format_transcript(transcript_data, meeting_name="Meeting Transcript"):
    """Formats the raw transcript data into a human-readable string with speaker grouping."""
    if not transcript_data or 'data' not in transcript_data:
        return "Transcript data is empty or invalid."

    lines = [f"# {meeting_name}\n"]
    last_speaker = None

    for entry in transcript_data['data']:
        speaker = entry.get('speaker', 'Unknown Speaker')
        text = entry.get('text', '')
        start_time_seconds = entry.get('startTime', 0)

        # Format timestamp as HH:MM:SS
        timestamp = str(datetime.timedelta(seconds=int(start_time_seconds)))

        # If speaker changes, add their name as a header for better grouping
        if speaker != last_speaker:
            lines.append(f"\n**{speaker}**")
            last_speaker = speaker
        
        # Add the text with its timestamp
        lines.append(f"[{timestamp}] {text}")

    formatted_lines = lines
    return "\n".join(formatted_lines)

def format_highlights(highlights_data: dict) -> str:
    """Formats the highlights data into a readable string."""
    if not highlights_data or not highlights_data.get('highlights'):
        return "AI Notes (Highlights):\n\nNo highlights were generated for this meeting."

    formatted_lines = ["AI Notes (Highlights):\n"]
    for note in highlights_data['highlights']:
        text = note.get('text', 'No content')
        start_time = note.get('timestamp', 0)
        seconds = int(start_time)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        timestamp = f"{hours:02}:{minutes:02}:{seconds:02}"
        formatted_lines.append(f"- [{timestamp}] {text}")
    
    return "\n".join(formatted_lines)
