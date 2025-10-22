import os
import re
from pathlib import Path
from flask import send_from_directory, session
import lesson_generation as lg

# Define a function to create topic directories
def create_topic_directory(topic):
    """Create a directory for the current topic and return the path."""
    sanitized_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
    topic_dir = Path("outputFiles") / sanitized_topic
    topic_dir.mkdir(parents=True, exist_ok=True)
    
    # Update the global topic_directory in lesson_generation module
    lg.topic_directory = topic_dir
    
    return topic_dir

# Function to safely handle file downloads
def download_file(directory, filename):
    """Secure file download function."""
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        return str(e), 404

# Function to handle background tasks (simplified)
def run_background_task(task_func, *args, **kwargs):
    """
    Run a function in the background and track its status.
    In a real production app, use a proper task queue like Celery.
    """
    try:
        session['task_status'] = 'running'
        result = task_func(*args, **kwargs)
        session['task_status'] = 'complete'
        return result
    except Exception as e:
        session['task_status'] = 'failed'
        session['task_error'] = str(e)
        raise

# Function to get the current output directory
def get_output_directory():
    """Get the output directory for the current topic."""
    if session.get('topic'):
        sanitized_topic = re.sub(r'[^\w\s-]', '', session.get('topic')).strip().replace(' ', '_')
        return Path("outputFiles") / sanitized_topic
    return Path("outputFiles")

# AI-powered functions for auto-generation
def generate_learning_outcomes_from_topic(topic):
    """
    Generate learning outcomes from a topic using AI
    """
    if not topic:
        return ""
    
    prompt = f"""Generate 3–5 specific and measurable learning outcomes for a lesson on "{topic}".
    Important notes:
                Each learning outcome should:
                - Start with an action verb
                - Be specific and measurable
                - Focus on student understanding or skills
                - Be appropriate for a classroom setting

                Format the response as a simple list with one learning outcome per line.
                Do not include any explanations, introductions, or other text.
    """
    
    try:
        ai_outcomes = lg.ai_agent(prompt)
        
        # Clean up the response
        # Remove bullet points, numbering, etc.
        #ai_outcomes = re.sub(r'^\s*[\d\.\-\*]+\s*', '', ai_outcomes, flags=re.MULTILINE)
        ai_outcomes = ai_outcomes.strip()
        ai_outcomes = ai_outcomes.replace('<','&lt;').replace('>','&gt;')
        
        return ai_outcomes
    except Exception as e:
        print(f"Error generating learning outcomes: {str(e)}")
        return ""

def generate_topic_from_outcomes(learning_outcomes):
    """
    Generate a topic from learning outcomes using AI
    """
    if not learning_outcomes:
        return ""
    
    prompt = f"""Based on the following learning outcomes, suggest a concise and specific educational topic or lesson title:

{learning_outcomes}

Respond with ONLY the topic/title. Keep it short (under 10 words), specific, and appropriate for an educational setting.
Do not include any explanations or additional text."""
    
    try:
        topic = lg.ai_agent(prompt)
        
        # Clean up the response
        topic = topic.strip()
        
        # Remove any "Topic:" or similar prefixes
        topic = re.sub(r'^(Topic:|Title:)\s*', '', topic, flags=re.IGNORECASE)
        
        return topic
    except Exception as e:
        print(f"Error generating topic: {str(e)}")
        return ""
