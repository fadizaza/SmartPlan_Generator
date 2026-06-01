import urllib.request
import requests


# Global dictionary to store prompt changes in memory
prompt_changes = {}

def read_file_contents(file_name):
    # First check if there are any in-memory changes
    if file_name in prompt_changes:
        return prompt_changes[file_name]
    # If no in-memory changes, read from file
    with open(file_name, 'r', encoding='utf-8') as file:
        contents = file.read()
    return contents

def read_text_file_from_url(url):
    """Reads text content from a given URL"""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error reading from URL {url}: {e}")
        return ""

def liveURL():
    url = "https://athkar-5bd89.web.app/vedcc/lessonGenerator/vedc"
    try:
        response = requests.head(url)
        return response.status_code < 400  # 400 and above typically indicate errors
    except requests.ConnectionError:
        return False

def clean_text(text):
    """Removes extra spaces and empty lines from the given text."""
    lines = text.split("\n")  # Split text into lines
    cleaned_lines = [" ".join(line.split()) for line in lines if line.strip()]  # Remove extra spaces and empty lines
    return "\n".join(cleaned_lines)  # Join the cleaned lines back into a single string

def extract_important_lines(text):
    """Extracts lines containing '!!!' from the text."""
    lines = text.split("\n")  # Split the text into lines
    important_lines = [line for line in lines if "!!!" in line]  # Filter lines containing '!!!'
    return important_lines

def center_window(window):
    """
    Centers a tkinter window on its parent window (or on the screen if no parent).
    
    Args:
        window: The tkinter window to center
    """
    window.update_idletasks()  # Make sure window size is updated
    
    # Get window dimensions
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    
    # If window has a parent, center on parent
    if window.master and window.master.winfo_toplevel() != window:
        parent = window.master.winfo_toplevel()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
    else:
        # Center on screen
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
    
    # Ensure window is not positioned offscreen
    x = max(0, x)
    y = max(0, y)
    
    # Set window position
    window.geometry(f"+{x}+{y}")