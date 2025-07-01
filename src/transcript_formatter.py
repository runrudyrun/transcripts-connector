import datetime

def format_transcript(transcript_data, meeting_name="Meeting Transcript"):
    """Formats the raw transcript data into a human-readable string."""
    if not transcript_data or 'data' not in transcript_data:
        return "Transcript data is empty or invalid."

    lines = [f"# {meeting_name}\n"]

    for entry in transcript_data['data']:
        speaker = entry.get('speaker', 'Unknown Speaker')
        text = entry.get('text', '')
        start_time_seconds = entry.get('startTime', 0)

        # Format timestamp as HH:MM:SS
        timestamp = str(datetime.timedelta(seconds=int(start_time_seconds)))

        lines.append(f"**[{timestamp}] {speaker}:** {text}")

    return "\n".join(lines)
