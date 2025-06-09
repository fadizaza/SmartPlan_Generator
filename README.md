# SmartPlan Web Application

SmartPlan is a web-based AI-powered lesson planning application that helps educators create comprehensive teaching materials including lesson plans, worksheets, presentations, and assessment questions.

## Features

- **Learning Outcomes**: Define learning objectives for your lessons
- **Questions Generator**: Create various types of assessment questions
- **Worksheet Generator**: Generate student worksheets
- **Lesson Plan Creator**: Design comprehensive lesson plans
- **Presentation Generator**: Create PowerPoint presentations
- **Revision Materials**: Generate revision materials for students

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Document Generation**: python-docx, python-pptx
- **APIs**: Google API integration for AI capabilities

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```
   cd "lesson gen folder\Lesson Generator_with pptx_vedc_desktop"
   ```

3. **Create and activate a virtual environment (recommended)**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install the dependencies**
   ```
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```
   python app.py
   ```

6. **Access the web application**
   Open your browser and go to: http://127.0.0.1:5000/

## Usage

1. **Start by setting a topic and learning outcomes**
   - Click on "Add Learning Outcomes / Topic" from the home page
   - Enter your topic and learning outcomes
   - Save and continue

2. **Generate teaching materials**
   - Choose the type of material you want to create (Questions, Worksheet, etc.)
   - Customize the options as needed
   - Click Generate
   - Download the generated files

3. **Access your files**
   - Click on "View Files" to see all generated materials
   - Download or access files from this page

## Deployment

This application can be deployed to various platforms:

### Heroku
```
heroku create your-app-name
git push heroku main
```

### PythonAnywhere
1. Upload the files to PythonAnywhere
2. Create a new web app with Flask
3. Configure the WSGI file to point to your app.py

### Docker
A Dockerfile is included for containerized deployment.

## Converting from Desktop to Web

This application was converted from a desktop Tkinter application to a web application. The conversion involved:

1. Replacing Tkinter UI with Flask routes and HTML templates
2. Adapting file handling for web context
3. Creating a responsive Bootstrap UI
4. Implementing AJAX for asynchronous operations
5. Adding server-side session management

## Credits

Original desktop application created for ACTVET (Abu Dhabi Center for Technical and Vocational Education and Training).
