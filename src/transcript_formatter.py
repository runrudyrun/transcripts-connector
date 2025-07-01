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

    return "\n".join(lines)
