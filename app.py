# This file is part of the Lesson Generation Web App.

import os
import re
import datetime
import io
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, session, flash, Markup
from werkzeug.utils import secure_filename
import jinja2

load_dotenv()
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
import os.path
import html

# Import existing modules (adapting as needed).
import lesson_generation as lg
from web_utils import create_topic_directory, download_file, generate_learning_outcomes_from_topic, generate_topic_from_outcomes

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add nl2br filter for converting newlines to <br> tags
@app.template_filter('nl2br')
def nl2br(value):
    if value:
        return jinja2.utils.markupsafe.Markup(value.replace('\n', '<br>'))
    return ""

# Add context processor to provide datetime to all templates
@app.context_processor
def inject_now():
    now = datetime.datetime.now()
    return {
        'now': now,
        'current_date': now.strftime('%B %d, %Y')
    }

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputFiles'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to get user-specific output folder
def get_user_output_folder():
    if current_user.is_authenticated:
        user_folder = os.path.join(OUTPUT_FOLDER, current_user.username)
        os.makedirs(user_folder, exist_ok=True)
        return user_folder
    return OUTPUT_FOLDER

# Color scheme (from original app)
colors = {
    'primary': '#1BACDF',
    'secondary': '#4CAF50',
    'background': '#F5F5F5',
    'text': '#212121',
    'accent': '#FF4081',
    'hover': '#1976D2',
    'card_bg': '#FFFFFF',
    'shadow': '#E0E0E0',
    'light_text': '#757575',
    'divider': '#EEEEEE',
    'header_bg': '#E3F2FD'
}

# Helper function to escape HTML special characters in learning outcomes
def escape_learning_outcomes(text):
    if not text:
        return ""
    # Replace < and > with their HTML entities
    escaped_text = text.replace('<', '&lt;').replace('>', '&gt;')
    return escaped_text

# Routes
@app.route('/')
@login_required
def index():
    # Reset the topic if starting fresh
    session['topic'] = session.get('topic', '')
    session['learning_outcomes'] = session.get('learning_outcomes', '')
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    # Pass current topic to the template
    return render_template('index.html', 
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/learning_outcomes', methods=['GET', 'POST'])
@login_required
def learning_outcomes():
    if request.method == 'POST':
        topic = request.form.get('topic', '')
        learning_outcomes = request.form.get('learning_outcomes', '')
        
        # Update session variables
        session['topic'] = topic
        session['learning_outcomes'] = learning_outcomes
        
        # Get user-specific session and update it
        user_session = lg.get_user_session(current_user.id)
        user_session.topic = topic
        user_session.learning_outcomes = learning_outcomes
        
        # Set user-specific directory
        if current_user.is_authenticated:
            user_folder = os.path.join(OUTPUT_FOLDER, current_user.username)
            user_session.user_directory = user_folder
            os.makedirs(user_folder, exist_ok=True)
            print(f"Set user_directory to: {user_folder}")
        
        # Create directory for this topic
        if topic:
            create_topic_directory(topic)
            
        return redirect(url_for('index'))
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('learning_outcomes.html', 
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/api/check_file_content', methods=['GET'])
@login_required
def api_check_file_content():
    """Check if the current user has uploaded file content available and return it"""
    try:
        user_session = lg.get_user_session(current_user.id)
        has_file_content = hasattr(user_session, 'fileContent') and user_session.fileContent
        
        response = {
            'status': 'success',
            'hasFileContent': bool(has_file_content)
        }
        
        # Include the actual file content if available
        if has_file_content:
            response['fileContent'] = user_session.fileContent
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to check file content: {str(e)}'
        }), 500

@app.route('/questions', methods=['GET', 'POST'])
@login_required
def questions():
    if not session.get('topic'):
        return redirect(url_for('learning_outcomes'))
        
    if request.method == 'POST':
        # Get form data
        subject = request.form.get('subject')
        student_level = request.form.get('student_level')
        question_types = request.form.getlist('question_type')
        additional_notes = request.form.get('additional_notes', '')
        difficulty_levels = {}
        sub_question_counts = {}
        
        # Get output format preferences
        output_formats = {
            'docx': request.form.get('format_docx') == 'true',
            'html': request.form.get('format_html') == 'true'
        }
        
        # Ensure at least one format is selected (default to DOCX if none)
        if not any(output_formats.values()):
            output_formats['docx'] = True
            
        # Process each selected question type
        for q_type in question_types:
            difficulty_levels[q_type] = request.form.get(f'difficulty_{q_type}', 'Easy')
            sub_question_counts[q_type] = request.form.get(f'count_{q_type}', '5')
            print(f"Processing question type: {q_type}, count: {sub_question_counts[q_type]}, difficulty: {difficulty_levels[q_type]}")
        

        # Build the prompt
        user_session = lg.get_user_session(current_user.id)
        has_file_content = hasattr(user_session, 'fileContent') and user_session.fileContent
               
        prompt = f"You are an experienced and creative {subject} teacher "
        prompt += f"designing engaging assessment questions for {student_level} students\n"
        prompt += f"Your goal is to help students understand a given {session.get('topic', '')} in a simple and age-appropriate way.\n"
        prompt += f"Use clear, student-friendly language and practical examples that make complex ideas easy to grasp."
        if not has_file_content:
            prompt += f"\nBase your questions on the provided learning outcomes: \n{session.get('learning_outcomes', '')}for that topic.\n"
        prompt += "Generate questions according to the following specifications:\n"
        for q_type in question_types:
            prompt += f"Question Type: {q_type}, Difficulty: {difficulty_levels[q_type]}, Count: {sub_question_counts[q_type]}\n"
        prompt = prompt.replace('mcq', 'multiple choice questions')
       
        
        if has_file_content:
            prompt += "\nUse the below contents only to create your questions:\n"
            prompt += user_session.fileContent + "\n"
        # Call the existing question generation function but adapt for web context
        prompt += """
        consider the following notes while creating the questions:\n
            - Ensure the questions are aligned with the learning outcomes, encourage curiosity, and include relatable real-world examples (such as chatbots, robots, or games when appropriate).
            - Provide clear, concise question wording suitable for primary learners.
            - Reply only with the questions, no additional text.
            - Format the questions appropriately based on their type (e.g., list options for multiple choice).
            - Provide the correct answer for each question at the end of the question.
        """
        if additional_notes:
            prompt += f"- {additional_notes}\n"
        
         # Debug: Print the constructed prompt
        try:
            # Generate questions in a background thread and return a job ID
            # In a real app, use a task queue like Celery
            session['generation_status'] = 'running'
            result = lg.create_questions(
                custom_prompt=prompt,
                output_formats=output_formats,
                user_id=current_user.id
            )
            session['generation_status'] = 'completed'
              # Check if result is a dictionary or string (backward compatibility)
            if isinstance(result, dict):
                session['generated_file'] = result.get('docx_path', '')
                
                # Get paths for different formats
                docx_path = result.get('docx_path', '')
                html_path = result.get('html_path', '')
                
                # Create response with all available URLs
                response = {
                    'status': 'success',
                    'message': 'Questions generated successfully'
                }
                
                if docx_path:
                    docx_basename = os.path.basename(docx_path)
                    response['docx_url'] = url_for('download_file', filename=docx_basename)
                    # Default file_url is the DOCX for backward compatibility
                    response['file_url'] = response['docx_url']
                    print(f"DOCX file: {docx_path} → {response['docx_url']}")
                
                if html_path:
                    html_basename = os.path.basename(html_path)
                    response['html_url'] = url_for('download_file', filename=html_basename)
                    print(f"HTML file: {html_path} → {response['html_url']}")
                
                return jsonify(response)
            else:
                # Legacy handling for backward compatibility
                session['generated_file'] = result
                
                # Get the filename from the result path
                file_basename = os.path.basename(result)
                
                # Print debug information about the file paths
                print(f"Generated file path: {result}")
                print(f"Extracted filename: {file_basename}")
                print(f"Download URL: {url_for('download_file', filename=file_basename)}")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Questions generated successfully',
                    'file_url': url_for('download_file', filename=file_basename)
                })
        except Exception as e:
            session['generation_status'] = 'failed'
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate questions: {str(e)}'
            })
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('questions.html',
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/worksheet', methods=['GET', 'POST'])
@login_required
def worksheet():
    if not session.get('topic'):
        return redirect(url_for('learning_outcomes'))
        
    if request.method == 'POST':
        # Handle worksheet generation
        subject = request.form.get('subject', '')
        studentLevel = request.form.get('student_level', '')
        difficultyLevel = request.form.get('difficulty_level', '')
        numActivities = request.form.get('num_activities', '')
        activities = request.form.get('custom_prompt', '')
        additional_notes = request.form.get('additional_notes', '')
        
       
        user_session = lg.get_user_session(current_user.id)
        has_file_content = hasattr(user_session, 'fileContent') and user_session.fileContent
        #if has_file_content:
        #   instructions += "\nUse the following content mainly to create your lesson plan:\n"
        #   instructions += user_session.fileContent + "\n"
        
        # Check for alternative field names that might be used by frontend
                
       
        
        # If still empty, build a default prompt
        
        
        custom_prompt = f"You are an experienced {subject} teacher.\n"
        custom_prompt += f"Create a worksheet for {studentLevel} students.\n"
        custom_prompt += f"The worksheet should be at {difficultyLevel} difficulty level.\n"
        custom_prompt += f"You should create {numActivities} activities."
        custom_prompt += activities + "\n"
        if not has_file_content:
            custom_prompt += f"The worksheet should focus on the topic: {session.get('topic', '')}\n"
            custom_prompt += f"The worksheet should cover the following Learning Outcomes:\n{session.get('learning_outcomes', '')}\n"
        if additional_notes:
            custom_prompt += f"""
        notes:
            - {additional_notes}
        """
        if has_file_content:
            custom_prompt += "\nUse the below contents only to create your worksheet:\n"
            custom_prompt += user_session.fileContent + "\n"
        
        # Get output format preferences
        output_formats = {
            'docx': request.form.get('format_docx') == 'true',
            'html': request.form.get('format_html') == 'true'
        }
        
        # Log the output format values for debugging
        #print(f"Output formats - DOCX: {output_formats['docx']}, HTML: {output_formats['html']}")
        
        # Ensure at least one format is selected (default to DOCX if none)
        if not any(output_formats.values()):
            output_formats['docx'] = True
            print("No output formats selected, defaulting to DOCX")
        
        try:
            # Call the existing worksheet generation function with format preferences and user_id
            session['generation_status'] = 'running'
            result = lg.create_worksheet(custom_prompt=custom_prompt, output_formats=output_formats, user_id=current_user.id)
            session['generation_status'] = 'completed'
            
            # Check if result is a dictionary (new format) or string (old format)
            response = {
                'status': 'success',
                'message': 'Worksheet generated successfully'
            }
            
            if isinstance(result, dict):
                # Handle dictionary result (similar to questions and lesson_plan routes)
                if result.get('file_path') or result.get('docx_path'):
                    file_path = result.get('file_path') or result.get('docx_path')
                    if file_path:
                        file_basename = os.path.basename(file_path)
                        response['file_path'] = url_for('download_file', filename=file_basename)
                        response['file_url'] = response['file_path']  # For backwards compatibility
                
                # HTML handling if present
                if result.get('html_path'):
                    html_path = result.get('html_path')
                    html_basename = os.path.basename(html_path)
                    response['html_url'] = url_for('download_file', filename=html_basename)
                    
                    # If no other file_url set, use the HTML URL
                    if not response.get('file_url'):
                        response['file_url'] = response['html_url']
            elif result:  # Handle string result (old format)
                file_basename = os.path.basename(result)
                response['file_url'] = url_for('download_file', filename=file_basename)
                response['file_path'] = response['file_url']  # For consistency
            else:
                # Handle None result
                raise ValueError("Worksheet generation did not produce any output files")
            
            return jsonify(response)
        except Exception as e:
            session['generation_status'] = 'failed'
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate worksheet: {str(e)}'
            })
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('worksheet.html',
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/lesson_plan', methods=['GET', 'POST'])
@login_required
def lesson_plan():
    if not session.get('topic'):
        return redirect(url_for('learning_outcomes'))
        
    if request.method == 'POST':
        # Handle lesson plan generation
        instructions = request.form.get('instructions', '')
        
        rules = '''
        It is very important that you follow these rules:
        - Begin every section above with the marker "!!!".
        - Present the sections immediately without any introductory explanation or comments.
        '''
        # Append formatting rules to the instructions
        instructions += "\n" + rules
       
        user_session = lg.get_user_session(current_user.id)
        has_file_content = hasattr(user_session, 'fileContent') and user_session.fileContent
        if has_file_content:
            instructions += "\nUse the following content mainly to create your lesson plan:\n"
            instructions += user_session.fileContent + "\n"

        # Get selected sections
       
        output_formats_str = request.form.get('output_formats', '')
        try:
            output_formats = json.loads(output_formats_str) if output_formats_str else {}
        except:
            # Default if JSON parsing fails
            output_formats = {}
              # Check for individual format checkboxes (backwards compatibility)
        if not output_formats:
            output_formats = {
                'docx': request.form.get('format_docx') == 'true',
                'html': request.form.get('format_html') == 'true',
            }
        
        # Ensure at least one format is selected (default to DOCX if none)
        if not output_formats or not any(output_formats.values()):
            output_formats = {'docx': True, 'html': True}
            
        
        
            
        try:
            # Call the existing lesson plan generation function with the enhanced instructions
            session['generation_status'] = 'running'
            result = lg.create_lesson_plan(custom_prompt=instructions, output_formats=output_formats, user_id=current_user.id)
            session['generation_status'] = 'completed'
              # Check if result is a dictionary (new format) or string (old format)
            response = {
                'status': 'success',
                'message': 'Lesson plan generated successfully'
            }
            
            if isinstance(result, dict):
                # Process different output formats                # DOCX handling
                if output_formats.get('docx', True) and (result.get('file_path') or result.get('docx_path')):
                    docx_path = result.get('file_path') or result.get('docx_path')
                    docx_basename = os.path.basename(docx_path)
                    response['docx_url'] = url_for('download_file', filename=docx_basename)
                    # Set as default download if no specific format is requested
                    response['file_url'] = response['docx_url']
                
                # HTML handling
                if output_formats.get('html', False) and result.get('html_path'):
                    html_path = result.get('html_path')
                    html_basename = os.path.basename(html_path)
                    response['html_url'] = url_for('download_file', filename=html_basename)
                    # If HTML was the only format requested, make it the default download
                    if output_formats.get('html', False) and not output_formats.get('docx', False):
                        response['file_url'] = response['html_url']
                  # Ensure we have at least one file URL
                if not response.get('file_url') and (response.get('docx_url') or response.get('html_url')):
                    response['file_url'] = response.get('docx_url') or response.get('html_url')
            else:
                # Legacy handling for string result
                file_basename = os.path.basename(result)
                file_url = url_for('download_file', filename=file_basename)
                response['file_url'] = file_url
            
            return jsonify(response)
        except Exception as e:
            session['generation_status'] = 'failed'
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate lesson plan: {str(e)}'
            })
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('lesson_plan.html',
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/presentation', methods=['GET', 'POST'])
@login_required
def presentation():
    if not session.get('topic'):
        return redirect(url_for('learning_outcomes'))
        
    if request.method == 'POST':        # Handle presentation generation
              
        # Get additional parameters from the form
        subject = request.form.get('subject', '')
        audience = request.form.get('audience', '')
        num_slides = request.form.get('numSlides', '')
        content_length = request.form.get('contentLength', '')
        theme = request.form.get('theme', '')
        additional_notes = request.form.get('additional_notes', '')
       
        try:
            user_session = lg.get_user_session(current_user.id)
            has_file_content = hasattr(user_session, 'fileContent') and user_session.fileContent
            # Build enhanced instructions
            enhanced_instructions = ""
            # If custom prompt is provided, use it
            enhanced_instructions += f"You are an expert {subject} teacher teaching {audience} students.\n"
            enhanced_instructions += f"you have to create a {num_slides} slides for a presentation.\n"
            enhanced_instructions += f"Each slide should have a {content_length.lower()} amount of text.\n"
            if not has_file_content:
                enhanced_instructions += f"the slides should cover the following topic:\n{session.get('topic', '')}\n"
                enhanced_instructions += f"the slides should cover the following learning outcomes:\n{session.get('learning_outcomes', '')}\n"
       
            
            if has_file_content:
                enhanced_instructions += "\nUse the following content to create your presentation slides:\n"
                enhanced_instructions += user_session.fileContent + "\n"
        except Exception as e:
            flash(f"Error reading directories: {str(e)}", "danger")
        
        enhanced_instructions += '''
        notes:
            - Begin every slide with the marker "!!!".
            - the marker "!!!" should be followed by the slide title without new line.
            - Present the slides immediately without any introductory explanation or comments.
            - Each slide should have a title and bullet points.
            - Use simple language suitable for the audience.
            - Include relevant examples and analogies to explain complex concepts.
            - Ensure the content is engaging and interactive.
            - Use consistent formatting and style throughout the presentation.
            '''
        if additional_notes:
            enhanced_instructions += f"- {additional_notes}\n"
                
                # Reset global sections variable before generating a new presentation
            
        
        
        lg.sections = None  # Reset sections to ensure new generation
                
            # Print debug info
            #
            # Call the presentation generation function with user_id
        result = lg.create_presentation(custom_prompt=enhanced_instructions, 
                                          theme_name=theme,
                                          user_id=current_user.id)
            
        return jsonify({
                'status': 'success',
                'message': 'Presentation generated successfully',
                'file_url': url_for('download_file', filename=os.path.basename(result))
            })
        
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('presentation.html',
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/revision', methods=['GET', 'POST'])
@login_required
def revision():
    if not session.get('topic'):
        return redirect(url_for('learning_outcomes'))
        
    if request.method == 'POST':
        # Handle revision material generation
        prompt = request.json.get('instructions', '') if request.is_json else request.form.get('instructions', '')
        
        # Get output format preferences
        output_formats = request.json.get('output_formats', {}) if request.is_json else {}
        
        # Make sure the output formats are properly formatted for the backend function
        if output_formats and isinstance(output_formats, dict):
            # Ensure boolean values (they might come as "true"/"false" strings from frontend)
            for key in output_formats:
                if isinstance(output_formats[key], str):
                    output_formats[key] = output_formats[key].lower() == 'true'
        else:
            # Default if no formats specified
            output_formats = {
                'docx': True,
                'html': request.json.get('format_html', 'false').lower() == 'true' if request.is_json else False
            }
            
            # Check for individual format checkboxes if coming from form
            if not request.is_json:
                output_formats['html'] = request.form.get('format_html') == 'true'
        
        try:
            # Call the existing revision generation function
            user_session = lg.get_user_session(current_user.id)
            has_file_content = hasattr(user_session, 'fileContent') and user_session.fileContent
            if has_file_content:
                prompt += "\nUse the following content mainly to create your revision:\n"
                prompt += user_session.fileContent + "\n"
            session['generation_status'] = 'running'
            result = lg.create_revision(custom_prompt=prompt, output_formats=output_formats, user_id=current_user.id)
            session['generation_status'] = 'completed'
            
            # Initialize response dictionary
            response = {
                'status': 'success',
                'message': 'Revision materials generated successfully'
            }
            
            # Check if result is a dictionary (new format) or string (old format)
            if isinstance(result, dict):
                # Handle DOCX path
                if result.get('docx_path'):
                    docx_basename = os.path.basename(result['docx_path'])
                    response['file_url'] = url_for('download_file', filename=docx_basename)
                
                # Handle HTML path
                if result.get('html_path'):
                    html_basename = os.path.basename(result['html_path'])
                    response['html_url'] = url_for('download_file', filename=html_basename)
            else:
                # Legacy handling for string result
                file_basename = os.path.basename(result)
                response['file_url'] = url_for('download_file', filename=file_basename)
            
            return jsonify(response)
        except Exception as e:
            session['generation_status'] = 'failed'
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate revision materials: {str(e)}'
            })
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('revision.html',
                          topic=session.get('topic', ''),
                          learning_outcomes=session.get('learning_outcomes', ''),
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/files')
@login_required
def files():
    # List generated files for the current user
    user_folder = get_user_output_folder()
    
    # If topic is specified, look in the topic folder
    topic_dir = None
    if session.get('topic'):
        sanitized_topic = re.sub(r'[^\w\s-]', '', session.get('topic')).strip().replace(' ', '_')
        topic_dir = Path(user_folder) / sanitized_topic
    else:
        topic_dir = Path(user_folder)
    
    files = []
    if topic_dir.exists():
        for file in topic_dir.iterdir():
            if file.is_file():
                files.append({
                    'name': file.name,
                    'path': file.relative_to(Path(OUTPUT_FOLDER)),
                    'size': f"{file.stat().st_size / 1024:.1f} KB",
                    'modified': datetime.datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
    
    # Escape the learning outcomes for proper display
    escaped_learning_outcomes = escape_learning_outcomes(session.get('learning_outcomes', ''))
    
    return render_template('files.html',
                          topic=session.get('topic', ''),
                          files=files,
                          escaped_learning_outcomes=escaped_learning_outcomes,
                          colors=colors)

@app.route('/download/<path:filename>')
def download_file(filename):
    """Securely handle file download with improved path handling."""
    print(f"Download request for file: {filename}")
    
    # URL decode the filename in case it contains special characters
    decoded_filename = os.path.basename(filename)
    print(f"Decoded filename: {decoded_filename}")
    
    try:
        # Get user folder
        user_folder = get_user_output_folder() if current_user.is_authenticated else OUTPUT_FOLDER
        
        # Get topic directory if a topic is set in the session
        topic_directory = None
        if session.get('topic'):
            sanitized_topic = re.sub(r'[^\w\s-]', '', session.get('topic')).strip().replace(' ', '_')
            topic_directory = os.path.join(user_folder, sanitized_topic)
        
        # Look for the file in various locations, starting with the most specific
        
        # 1. Look in current topic directory first
        if topic_directory and os.path.exists(topic_directory):
            file_path = os.path.join(topic_directory, decoded_filename)
            print(f"Checking in topic directory: {file_path}")
            if os.path.isfile(file_path):
                print(f"Found in topic directory: {topic_directory}")
                return send_from_directory(topic_directory, decoded_filename, as_attachment=True)
        
        # 2. Look directly in user's folder
        direct_file_path = os.path.join(user_folder, decoded_filename)
        print(f"Checking in user directory: {direct_file_path}")
        if os.path.isfile(direct_file_path):
            print(f"Found in user directory: {user_folder}")
            return send_from_directory(user_folder, decoded_filename, as_attachment=True)
            
        # 3. Try all possible subfolders under user's folder (exhaustive search)
        print("Performing exhaustive search...")
        for root, dirs, files in os.walk(user_folder):
            if decoded_filename in files:
                rel_dir = os.path.relpath(root, app.root_path)
                abs_path = os.path.join(root, decoded_filename)
                print(f"File found in: {abs_path}")
                return send_from_directory(root, decoded_filename, as_attachment=True)
            
        # 4. Check in OUTPUT_FOLDER as a last resort (for backwards compatibility)
        fallback_path = os.path.join(OUTPUT_FOLDER, decoded_filename)
        print(f"Checking fallback path: {fallback_path}")
        if os.path.isfile(fallback_path):
            print(f"Found in OUTPUT_FOLDER: {fallback_path}")
            return send_from_directory(OUTPUT_FOLDER, decoded_filename, as_attachment=True)
                
        # If we got here, the file wasn't found anywhere
        print(f"File not found anywhere: {decoded_filename}")
        return f"File {decoded_filename} not found. Please try again or contact support.", 404
        
    except Exception as e:
        print(f"Error in download_file: {str(e)}")
        return f"Error downloading file: {str(e)}", 500
# New API endpoints for auto-generation
@app.route('/api/generate_outcomes', methods=['POST'])
@login_required
def api_generate_outcomes():
    """Generate learning outcomes from a topic using AI"""
    topic = request.json.get('topic', '')
    
    if not topic:
        return jsonify({
            'status': 'error',
            'message': 'Topic is required'
        }), 400
        
    try:
        # Call the AI function to generate outcomes
        learning_outcomes = generate_learning_outcomes_from_topic(topic)
        
        # Update session variables
        session['topic'] = topic
        session['learning_outcomes'] = learning_outcomes
           
        # Get user session and clear file content
        user_session = lg.get_user_session(current_user.id)
        user_session.fileContent = None
        session['fileContent'] = None  # Clear any uploaded file content
        
        
        
        
        # Update global variables in lesson_generation
        lg.topic = topic
        lg.learning_outcomes = learning_outcomes
        
        return jsonify({
            'status': 'success',
            'learning_outcomes': learning_outcomes
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate learning outcomes: {str(e)}'
        }), 500

@app.route('/api/generate_topic', methods=['POST'])
@login_required
def api_generate_topic():
    """Generate a topic from learning outcomes using AI"""
    learning_outcomes = request.json.get('learning_outcomes', '')
    
    if not learning_outcomes:
        return jsonify({
            'status': 'error',
            'message': 'Learning outcomes are required'
        }), 400
        
    try:
        # Call the AI function to generate a topic
        topic = generate_topic_from_outcomes(learning_outcomes)
        
        # Update session variables
        session['topic'] = topic
        session['learning_outcomes'] = learning_outcomes
        user_session = lg.get_user_session(current_user.id)
        user_session.fileContent = None
        session['fileContent'] = None  # Clear any uploaded file content
        
        
        # Update global variables in lesson_generation
        lg.topic = topic
        lg.learning_outcomes = learning_outcomes
        
        return jsonify({
            'status': 'success',
            'topic': topic
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate topic: {str(e)}'
        }), 500

@app.route('/status')
def status():
    # Return the current generation status
    return jsonify({
        'status': session.get('generation_status', 'idle')
    })

@app.route('/install_pdf_support')
def install_pdf_support():
    try:
        # Run the install_pdf_support.bat file
        subprocess.Popen([r'cmd.exe', '/c', 'install_pdf_support.bat'], shell=False)
        return jsonify({
            'status': 'success',
            'message': 'PDF support installation initiated.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/presentation/preview', methods=['POST'])
@login_required
def preview_presentation():
    if not session.get('topic'):
        return jsonify({
            'status': 'error',
            'message': 'No topic has been selected.'
        })
    
    try:
        # Get form data
        subject = request.form.get('subject', '')
        audience = request.form.get('audience', '')
        num_slides = request.form.get('numSlides', '')
        content_length = request.form.get('contentLength', '')
        theme = request.form.get('theme', '')
        
        # Build enhanced instructions
        enhanced_instructions = ""
        enhanced_instructions += f"You are an expert {subject} teacher. You are teaching {audience} students.\n"
        enhanced_instructions += f"Create a {num_slides} slide presentation.\n"
        enhanced_instructions += f"Each slide should have a {content_length.lower()} amount of text.\n"
        enhanced_instructions += f"the presentation should cover the following topic:\n{session.get('topic', '')}\n"
        enhanced_instructions += f"the slides should cover the following learning outcomes:\n{session.get('learning_outcomes', '')}\n"
        enhanced_instructions += '''
            - each slide should start with a "!!!" format.
            - give me the slides directly without explination at the begining of your response.
            '''
        
        # Generate AI response using the user session
        ai_response = generate_ai_response_only(enhanced_instructions, current_user.id)
        
        return jsonify({
            'status': 'success',
            'content': ai_response
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate AI response: {str(e)}'
        })

@app.route('/presentation/save-response', methods=['POST'])
@login_required
def save_ai_response():
    if not session.get('topic'):
        return jsonify({
            'status': 'error',
            'message': 'No topic has been selected.'
        })
    
    try:
        data = request.json
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'status': 'error',
                'message': 'No content provided.'
            })
        
        # Get user session and update it with the content
        user_session = lg.get_user_session(current_user.id)
        topic = user_session.topic or session.get('topic', '')
        user_directory = user_session.user_directory
        
        # Determine output directory
        if user_directory and topic:
            sanitized_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
            output_dir = os.path.join(user_directory, sanitized_topic)
            os.makedirs(output_dir, exist_ok=True)
        else:
            # Fallback to user folder
            user_folder = get_user_output_folder()
            output_dir = os.path.join(user_folder, 'HTML')
            os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, 'AIresponse.txt')
        
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Update user session with the content
        user_session.sections = content
        
        return jsonify({
            'status': 'success',
            'message': 'AI response saved successfully.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to save AI response: {str(e)}'
        })

@app.route('/presentation/load-response', methods=['GET'])
@login_required
def load_ai_response():
    if not session.get('topic'):
        return jsonify({
            'status': 'error',
            'message': 'No topic has been selected.'
        })
    
    try:
        # Get user session
        user_session = lg.get_user_session(current_user.id)
        topic = user_session.topic or session.get('topic', '')
        user_directory = user_session.user_directory
        
        # Determine output directory
        if user_directory and topic:
            sanitized_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
            output_dir = os.path.join(user_directory, sanitized_topic)
        else:
            # Fallback to user folder
            output_dir = get_user_output_folder()
        
        output_file = os.path.join(output_dir, 'AIresponse.txt')
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update user session with the loaded content
            user_session.sections = content
            
            return jsonify({
                'status': 'success',
                'content': content
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No saved response found.'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to load AI response: {str(e)}'
        })

def generate_ai_response_only(prompt, user_id):
    """Generate AI response without creating the PowerPoint presentation.
    
    Args:
        prompt (str): The prompt to generate content.
        user_id: The ID of the current user.
        
    Returns:
        str: The AI generated content.
    """
    try:
        # Get user session
        user_session = lg.get_user_session(user_id)
        user_session.topic = session.get('topic', '')
        user_session.learning_outcomes = session.get('learning_outcomes', '')
        
        # Set user-specific directory if not already set
        if not user_session.user_directory:
            user_folder = get_user_output_folder()
            user_session.user_directory = user_folder
        
        # Add the formatting rules for slides
        rules = '''
        - each slide should start with a "!!!" format.
        - give me the slides directly without explanation at the beginning of your response.
        '''
        full_prompt = prompt + "\n" + rules
        
        # Get AI response using the user session system
        ai_response = lg.get_ai_response(full_prompt, user_id=user_id)
        
        return ai_response
    except Exception as e:
        app.logger.error(f"Error generating AI response: {str(e)}")
        raise

@app.route('/about')
def about():
    """Display the About Us page"""
    return render_template('about.html', colors=colors)

# Routes for authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            error = 'Invalid username or password. Please try again.'
        else:
            # Update last login time
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()
            
            # Log in the user
            login_user(user, remember=remember)
            
            # Redirect to the page they were trying to access or to the home page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
    
    return render_template('login.html', error=error, colors=colors)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    error = None
    success = None
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        else:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                error = 'Username already exists. Please choose another one.'
            elif User.query.filter_by(email=email).first():
                error = 'Email already registered. Please use another email or login.'
            else:
                # Create new user
                new_user = User(
                    name=name,
                    email=email,
                    username=username
                )
                new_user.set_password(password)
                
                # Add to database
                db.session.add(new_user)
                db.session.commit()
                
                # Create user-specific folder
                user_folder = os.path.join(OUTPUT_FOLDER, username)
                os.makedirs(user_folder, exist_ok=True)
                
                success = 'Account created successfully! You can now log in.'
    
    return render_template('signup.html', error=error, success=success, colors=colors)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home_view():
    """Display all folders in the user's directory."""
    # Get the user-specific directory using the helper function
    user_dir = get_user_output_folder()
    
    # Ensure the directory exists
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    # Get all folders in the directory
    folders = []
    try:
        for item in os.listdir(user_dir):
            item_path = os.path.join(user_dir, item)
            if os.path.isdir(item_path):
                # Get folder stats
                folder_stats = os.stat(item_path)
                modified_time = datetime.datetime.fromtimestamp(folder_stats.st_mtime)
                
                # Count files in the folder
                file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                
                folders.append({
                    'name': item,
                    'path': item_path,
                    'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_count': file_count
                })
    except Exception as e:
        flash(f"Error reading directories: {str(e)}", "danger")
    
    # Sort folders by modified time (newest first)
    folders.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('home.html', folders=folders, colors=colors)

# Modify the create_topic_directory function in web_utils.py from within app.py
def create_topic_directory(topic):
    """Create a directory for the given topic within user's folder."""
    sanitized_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
    
    # Get user-specific base directory
    if current_user.is_authenticated:
        base_dir = os.path.join(OUTPUT_FOLDER, current_user.username)
    else:
        base_dir = OUTPUT_FOLDER
    
    os.makedirs(base_dir, exist_ok=True)
    
    # Create topic directory within user directory
    topic_dir = os.path.join(base_dir, sanitized_topic)
    os.makedirs(topic_dir, exist_ok=True)
    
    return topic_dir

@app.route('/api/user-folders')
@login_required
def get_user_folders():
    """API endpoint to get all folders in the user's directory or within a specific folder."""
    # Get the user-specific directory using the helper function
    user_dir = get_user_output_folder()
    
    # Check if we're looking for subfolders within a specific folder
    parent_folder = request.args.get('folder', '')
    
    # Determine the current directory to explore
    if parent_folder:
        current_dir = os.path.join(user_dir, parent_folder)
        # For security, ensure we're still within the user's directory
        if not os.path.normpath(current_dir).startswith(os.path.normpath(user_dir)):
            return jsonify({
                'status': 'error',
                'message': "Access denied: Cannot access directories outside user space"
            })
    else:
        current_dir = user_dir
    
    # Ensure the directory exists
    if not os.path.exists(current_dir):
        os.makedirs(current_dir, exist_ok=True)
    
    # Get all folders in the directory
    folders = []
    try:
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                # Get folder stats
                folder_stats = os.stat(item_path)
                modified_time = datetime.datetime.fromtimestamp(folder_stats.st_mtime)
                
                # Count files in the folder
                file_count = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
                
                # Create relative path from user directory
                rel_path = os.path.relpath(item_path, user_dir)
                
                folders.append({
                    'name': item,
                    'path': rel_path,
                    'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'file_count': file_count
                })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Error reading directories: {str(e)}"
        })
    
    # Sort folders by modified time (newest first)
    folders.sort(key=lambda x: x['modified'], reverse=True)
    
    # Add breadcrumb information for navigation
    breadcrumbs = []
    if parent_folder:
        parts = parent_folder.split(os.sep)
        cumulative_path = ""
        breadcrumbs.append({'name': 'Home', 'path': ''})
        
        for i, part in enumerate(parts):
            if part:  # Skip empty parts
                if cumulative_path:
                    cumulative_path = os.path.join(cumulative_path, part)
                else:
                    cumulative_path = part
                    
                breadcrumbs.append({'name': part, 'path': cumulative_path})
    else:
        # Just add home when at root
        breadcrumbs.append({'name': 'Home', 'path': ''})
    
    return jsonify({
        'status': 'success',
        'folders': folders,
        'breadcrumbs': breadcrumbs,
        'current_folder': parent_folder
    })

@app.route('/api/folder-files')
@login_required
def get_folder_files():
    """API endpoint to get files within a specific folder."""
    # Get the user-specific directory using the helper function
    user_dir = get_user_output_folder()
    
    # Get the folder path from query parameters
    folder_path = request.args.get('folder', '')
    
    # Determine the directory to explore
    if folder_path:
        target_dir = os.path.join(user_dir, folder_path)
        # For security, ensure we're still within the user's directory
        if not os.path.normpath(target_dir).startswith(os.path.normpath(user_dir)):
            return jsonify({
                'status': 'error',
                'message': "Access denied: Cannot access files outside user space"
            })
    else:
        target_dir = user_dir
    
    # Check if directory exists
    if not os.path.exists(target_dir):
        return jsonify({
            'status': 'error',
            'message': f"Folder not found: {folder_path}"
        })
    
    # Get all files in the directory
    files = []
    try:
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            if os.path.isfile(item_path):
                # Get file stats
                file_stats = os.stat(item_path)
                modified_time = datetime.datetime.fromtimestamp(file_stats.st_mtime)
                size_kb = file_stats.st_size / 1024
                
                # Determine file type based on extension
                file_type = "File"
                extension = os.path.splitext(item)[1].lower()
                
                if extension == '.docx':
                    file_type = "Word Document"
                elif extension == '.pptx':
                    file_type = "PowerPoint"
                elif extension == '.pdf':
                    file_type = "PDF"
                elif extension == '.txt':
                    file_type = "Text"
                elif extension == '.html':
                    file_type = "HTML"
                
                files.append({
                    'name': item,
                    'path': os.path.join(folder_path, item) if folder_path else item,
                    'size': f"{size_kb:.1f} KB",
                    'modified': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': file_type
                })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Error reading files: {str(e)}"
        })
    
    # Sort files by modified time (newest first)
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({
        'status': 'success',
        'files': files,
        'folder': folder_path
    })

# Add escape function as a Jinja filter for easier use in templates
@app.template_filter('escape_html')
def escape_html_filter(text):
    return escape_learning_outcomes(text)

@app.route('/api/process_topic_file', methods=['POST'])
@login_required
def api_process_topic_file():
    """Process uploaded file and extract topic and learning outcomes"""
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file uploaded'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No file selected'
        }), 400
    
    try:
        # Extract content from uploaded file
        file_content = lg.extract_content(file)
        
        # Get user session and store file content
        user_session = lg.get_user_session(current_user.id)
        user_session.fileContent = file_content
        
        # Generate topic and learning outcomes from file content
        topic_prompt = f"""Based on the following information, suggest a concise and specific educational topic or lesson title:
        \n\n{file_content[:2000]}
        Important notes:
            - Respond with ONLY the topic/title. Keep it short (under 10 words), specific, and appropriate for an educational setting.
            - Do not include any explanations or additional text."""
        topic = lg.ai_agent(topic_prompt).strip().strip('"').strip("'")
        
        outcomes_prompt = f"""Generate 3-5 clear and concise learning outcomes based on the following information:
                \n\n{file_content[:2000]}\n
            Important notes:
                Each learning outcome should:
                - Start with an action verb
                - Be specific and measurable
                - Focus on student understanding or skills
                - Be appropriate for a classroom setting
                
                Format the response as a simple list with one learning outcome per line.
                Do not include any explanations, introductions, or other text."""
        learning_outcomes = lg.ai_agent(outcomes_prompt).strip()
        learning_outcomes = learning_outcomes.replace('<','&lt;').replace('>','&gt;')
        
        # Update session
        session['topic'] = topic
        session['learning_outcomes'] = learning_outcomes
        user_session.topic = topic
        user_session.learning_outcomes = learning_outcomes
        
        return jsonify({
            'status': 'success',
            'topic': topic,
            'learning_outcomes': learning_outcomes
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to process file: {str(e)}'
        }), 500

if __name__ == '__main__':
    try:
        # Create the database tables if they don't already exist
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
        
        # Print startup message
        print("=" * 50)
        print("Starting Lesson Generator Web Application")
        print("=" * 50)
        print(f"Server running at: http://127.0.0.1:5000")
        print("Press CTRL+C to quit")
        print("=" * 50)
        
        # Run the Flask application
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting the application: {str(e)}")
        print(f"Exception details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting the application: {str(e)}")
        print(f"Exception details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

