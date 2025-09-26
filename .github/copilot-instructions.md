# SmartPlan Web Application - AI Agent Instructions

## Project Architecture Overview

SmartPlan is a Flask-based web application for generating educational materials using AI. Key components:

- `app.py`: Main Flask application with route handlers and user authentication
- `lesson_generation.py`: Core generation logic and AI integration
- `models.py`: Database models and user management
- `web_utils.py`: Helper functions for web-specific operations

### Core Components and Data Flow

1. User Authentication (`models.py`, `app.py`):
   - SQLite database with User model
   - Login/signup flows in `/login` and `/signup` routes

2. Content Generation Flow:
   - Learning outcomes definition → Topic selection/generation → Material generation
   - Each generation type (worksheet, questions, etc.) follows the pattern:
     ```python
     @app.route('/<type>', methods=['GET', 'POST'])
     @login_required
     def handler():
         # 1. Get user input/parameters
         # 2. Call lesson_generation.<type> function
         # 3. Save outputs in user's directory
         # 4. Return file download/preview links
     ```

3. File Organization:
   - User files stored in `outputFiles/<username>/<topic>/`
   - Templates in `templates/` (HTML) and `word templates/` (DOCX)
   - PowerPoint templates in `powerpoint templates/`

## Key Integration Points

1. Google AI API Integration:
   - Uses Gemini 1.5 Flash model
   - API calls made in `lesson_generation.py:ai_agent()`
   - Requires valid API key in environment/config

2. Document Generation:
   - DOCX: Uses `python-docx` with templates in `word templates/`
   - PPTX: Uses `python-pptx` with themes in `powerpoint templates/`
   - HTML: Dynamic generation with embedded styles

## Development Workflows

### Setup and Running

1. Create and activate virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Initialize database:
   ```powershell
   python init_db.py
   ```

3. Run development server:
   ```powershell
   python app.py
   ```

### Adding New Generation Features

1. Create route handler in `app.py`
2. Add generation function in `lesson_generation.py`
3. Create HTML template in `templates/`
4. Update navigation in `templates/base.html`

## Project-Specific Conventions

1. AI Generation Pattern:
   ```python
   def create_X(custom_prompt=None, output_formats=None):
       # 1. Build default prompt if custom_prompt not provided
       # 2. Call ai_agent() for content generation
       # 3. Process response into required formats (DOCX/HTML)
       # 4. Return paths in standardized dictionary format
   ```

2. File Output Format:
   - Return dictionary with format-specific paths:
     ```python
     {
         'docx_path': 'path/to/file.docx',
         'html_path': 'path/to/file.html'
     }
     ```

3. User File Organization:
   - All generated files go under `outputFiles/<username>/<topic>/`
   - Sanitized topic names used for directories
   - HTML responses saved alongside DOCX/PPTX files

## Template System

1. HTML Templates:
   - Base template: `templates/base.html`
   - Each feature has dedicated template
   - Uses Jinja2 templating engine

2. Document Templates:
   - Word templates in `word templates/`
   - PowerPoint themes in `powerpoint templates/`
   - Template selection handled through UI

Remember to validate file paths and ensure proper directory permissions when working with file operations.