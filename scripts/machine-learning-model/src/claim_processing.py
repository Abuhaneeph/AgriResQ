import spacy
from spacy.matcher import Matcher
from dateparser import parse  # For parsing natural language dates
from datetime import datetime, timedelta

# Load pre-trained spaCy model
nlp = spacy.load("en_core_web_sm")

# Define a pattern matcher for Event Types
matcher = Matcher(nlp.vocab)
event_patterns = [
    [{"LOWER": "rain"}],
    [{"LOWER": "rains"}],  # plural form
    [{"LOWER": "drought"}],
    [{"LOWER": "flood"}],
    [{"LOWER": "floods"}],  # plural form
    [{"LOWER": "storm"}],
    [{"LOWER": "storms"}],  # plural form
    [{"LOWER": "hailstorm"}],
    [{"LOWER": "wildfire"}],
    [{"LOWER": "wildfires"}],  # plural form
    [{"LOWER": "unknown"}, {"LOWER": "disaster"}],
    [{"LOWER": "unclassified"}]
]
matcher.add("EVENT_TYPE", event_patterns)

# Define severity patterns
severity_patterns = [
    [{"LOWER": "heavy"}],
    [{"LOWER": "mild"}],
    [{"LOWER": "severe"}],
    [{"LOWER": "intense"}],
    [{"LOWER": "light"}],
    [{"LOWER": "moderate"}],
    [{"LOWER": "strong"}],  # additional severity
    [{"LOWER": "extreme"}]  # additional severity
]
matcher.add("SEVERITY", severity_patterns)

# Time-related phrase to days mapping
TIME_PHRASES_TO_DAYS = {
    'today': 1,
    'yesterday': 1,
    'tomorrow': 1,
    'this week': 7,
    'last week': 7,
    'next week': 7,
    'this month': 30,
    'last month': 30,
    'next month': 30,
    'recently': 3,
    'past few days': 3,
    'past week': 7,
    'last few days': 3
}

# Function to normalize date text to actual dates
def normalize_date(date_text, base_date=None):
    """
    Normalize date text to a specific date format with improved handling of relative dates.
    """
    if base_date is None:
        base_date = datetime.now()
    
    if not date_text:
        return base_date.strftime('%Y-%m-%d')
    
    # Preprocess relative date expressions
    date_text = date_text.lower().strip()
    
    # Handle specific relative date cases
    if date_text == 'today':
        return base_date.strftime('%Y-%m-%d')
    if date_text == 'yesterday':
        return (base_date - timedelta(days=1)).strftime('%Y-%m-%d')
    if date_text == 'tomorrow':
        return (base_date + timedelta(days=1)).strftime('%Y-%m-%d')
    if date_text == 'this month':
        return base_date.replace(day=1).strftime('%Y-%m-%d')
    if date_text == 'last month':
        first_day_of_current_month = base_date.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        return last_day_of_previous_month.replace(day=1).strftime('%Y-%m-%d')
    if date_text == 'next month':
        first_day_of_next_month = (base_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        return first_day_of_next_month.strftime('%Y-%m-%d')
    
    # Use dateparser for complex cases
    try:
        parsed_date = parse(date_text, settings={
            'RELATIVE_BASE': base_date,
            'PREFER_DATES_FROM': 'past',
            'PREFER_DAY_OF_MONTH': 'first'
        })
        if parsed_date:
            return parsed_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error parsing date: {e}")
    
    return base_date.strftime('%Y-%m-%d')

# Function to extract claim details with enhanced parsing
def extract_claim_details(text):
    doc = nlp(text)

    # Initialize extracted details
    event_type = "Other"
    severity = "Unknown"
    date = None
    location = None
    base_date = datetime.now()
    days = 7  # Default days for event window

    # Use spaCy's NER for date and location
    for ent in doc.ents:
        if ent.label_ == "DATE":
            date = ent.text
        if ent.label_ == "GPE":  # Geo-Political Entity
            location = ent.text

    # Map predefined time phrases to days
    for phrase, num_days in TIME_PHRASES_TO_DAYS.items():
        if phrase in text.lower():
            days = num_days
            break

    # Identify event type and severity using matcher
    matches = matcher(doc)
    for match_id, start, end in matches:
        match_id_str = nlp.vocab.strings[match_id]
        if match_id_str == "EVENT_TYPE":
            event_type = doc[start:end].text
        elif match_id_str == "SEVERITY":
            severity = doc[start:end].text

    # Normalize the date
    normalized_date = normalize_date(date, base_date)

    # Handle specific event cases (e.g., drought)
    if event_type == 'drought':
        days = max(days, 7)
        if 'this month' in text.lower() or 'month' in text.lower():
            days = 30

    # Reject very short-term claims for long-duration events
    if days <= 1 and event_type in ['drought', 'flood']:
        event_type = "Insufficient Data"
        severity = "Unassessable"

    # Return extracted details
    return {
        "Claim": text,
        "Event Type": event_type,
        "Severity": severity,
        "Date": normalized_date,
        "Location": location,
        "Days": days
    }

# Main function to process claims
def process_claims_from_text(input_text):
    if isinstance(input_text, str):
        return [extract_claim_details(input_text)]
    elif isinstance(input_text, list):
        return [extract_claim_details(claim) for claim in input_text]
    else:
        raise ValueError("Input must be a string or a list of strings.")
