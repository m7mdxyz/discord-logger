import os
import json
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

# Add a context processor to make the current year available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Helper function to load JSON log files
def load_json_log(filename):
    """
    Safely load and parse JSON log files.
    
    Args:
        filename (str): Name of the JSON file to load
        
    Returns:
        list: Parsed JSON data or empty list if file is missing or malformed
    """
    try:
        filepath = os.path.join('data', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Helper function to format timestamps
def format_timestamp(timestamp_str):
    """
    Format ISO timestamp to a more readable format.
    
    Args:
        timestamp_str (str): ISO timestamp string
        
    Returns:
        str: Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except (ValueError, AttributeError):
        return timestamp_str

# Helper function to calculate summary statistics
def get_summary_stats():
    """
    Calculate summary statistics from all log files.
    
    Returns:
        dict: Dictionary containing summary statistics
    """
    deleted_msgs = load_json_log('deleted_messages_log.json')
    edited_msgs = load_json_log('edited_messages_log.json')
    voice_activity = load_json_log('voice_channel_log.json')
    member_activity = load_json_log('member_log.json')
    
    # Find the most recent event across all logs
    all_events = []
    all_events.extend([(event['timestamp'], 'deleted') for event in deleted_msgs])
    all_events.extend([(event['timestamp'], 'edited') for event in edited_msgs])
    all_events.extend([(event['timestamp'], 'voice') for event in voice_activity])
    all_events.extend([(event['timestamp'], 'member') for event in member_activity])
    
    most_recent = "No events recorded"
    if all_events:
        all_events.sort(reverse=True)
        most_recent = format_timestamp(all_events[0][0])
    
    return {
        'total_entries': len(deleted_msgs) + len(edited_msgs) + len(voice_activity) + len(member_activity),
        'last_logged_event': most_recent
    }

# Route for the homepage
@app.route('/')
def index():
    """
    Render the homepage with summary statistics.
    """
    stats = get_summary_stats()
    return render_template('index.html', stats=stats)

# Route for deleted messages log
@app.route('/deleted-messages')
def deleted_messages():
    """
    Render the deleted messages log page.
    """
    messages = load_json_log('deleted_messages_log.json')
    # Format timestamps for display
    for msg in messages:
        msg['formatted_timestamp'] = format_timestamp(msg['timestamp'])
        msg['formatted_original_sent_at'] = format_timestamp(msg['original_sent_at'])
    return render_template('deleted_messages.html', messages=messages)

# Route for edited messages log
@app.route('/edited-messages')
def edited_messages():
    """
    Render the edited messages log page.
    """
    messages = load_json_log('edited_messages_log.json')
    # Format timestamps for display
    for msg in messages:
        msg['formatted_timestamp'] = format_timestamp(msg['timestamp'])
        msg['formatted_original_sent_at'] = format_timestamp(msg['original_sent_at'])
    return render_template('edited_messages.html', messages=messages)

# Route for voice channel activity log
@app.route('/voice-activity')
def voice_activity():
    """
    Render the voice channel activity log page.
    """
    activities = load_json_log('voice_channel_log.json')
    # Format timestamps for display
    for activity in activities:
        activity['formatted_timestamp'] = format_timestamp(activity['timestamp'])
    return render_template('voice_activity.html', activities=activities)

# Route for member activity log
@app.route('/member-activity')
def member_activity():
    """
    Render the member activity log page.
    """
    activities = load_json_log('member_log.json')
    # Format timestamps for display
    for activity in activities:
        activity['formatted_timestamp'] = format_timestamp(activity['timestamp'])
    return render_template('member_activity.html', activities=activities)

if __name__ == '__main__':
    app.run(debug=True)
