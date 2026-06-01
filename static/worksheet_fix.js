// This script is designed to fix worksheet prompt updating issue
document.addEventListener('DOMContentLoaded', function() {
    console.log("Worksheet fix script loaded");
    
    // Simple no-jQuery function to update prompt when selections change
    function updateWorksheetPrompt() {
        var difficultyLevel = document.getElementById('difficultyLevel').value || 'moderate';
        var numActivities = document.getElementById('numActivities').value || '5';
        var subject = document.getElementById('subject').value || '';
        var studentLevel = document.getElementById('studentLevel').value || '';
        var topic = document.querySelector('p.text-muted.mb-4 strong') ? 
                   document.querySelector('p.text-muted.mb-4 strong').textContent : 'HTML';
        
        // Get selected worksheet types
        var selectedTypes = [];
        document.querySelectorAll('input[name="worksheet_type"]:checked').forEach(function(checkbox) {
            selectedTypes.push(checkbox.nextElementSibling.textContent.trim());
        });
        var worksheetTypes = selectedTypes.length > 0 ? selectedTypes.join(', ') : 'practice exercises, assessment activities';
        
        // Build the prompt template
        var promptTemplate = `Create a ${difficultyLevel.toLowerCase()} level worksheet with ${numActivities} activities.\n\n`;
        
        if (subject && subject !== 'Select the subject') {
            promptTemplate += `Subject area: ${subject}\n`;
        }
        
        if (studentLevel && studentLevel !== 'Select Level') {
            promptTemplate += `For ${studentLevel} level students\n`;
        }
        
        promptTemplate += `\nInclude the following types of activities: ${worksheetTypes}.\n\n`;
        promptTemplate += `The worksheet should focus on the topic: ${topic}`;
        
        // Update textarea
        var instructionsTextarea = document.getElementById('instructions');
        if (instructionsTextarea) {
            instructionsTextarea.value = promptTemplate;
            console.log("Prompt updated successfully");
            
            // Visual feedback
            instructionsTextarea.style.backgroundColor = "#e8f4ff";
            instructionsTextarea.style.borderColor = "#0d6efd";
            setTimeout(function() {
                instructionsTextarea.style.backgroundColor = "#f8f9fa";
                instructionsTextarea.style.borderColor = "";
            }, 500);
        } else {
            console.error("Could not find instructions textarea");
        }
    }
    
    // Add an update button next to the prompt heading
    function addUpdateButton() {
        var promptHeaders = document.querySelectorAll('.card-header');
        var promptHeader = null;
        
        // Find the header with the worksheet prompt heading
        promptHeaders.forEach(function(header) {
            if (header.textContent.includes('Worksheet Prompt')) {
                promptHeader = header;
            }
        });
        
        if (promptHeader) {
            var button = document.createElement('button');
            button.className = 'btn btn-sm btn-outline-primary ms-2';
            button.innerHTML = '<i class="fas fa-sync-alt"></i> Update Prompt';
            button.onclick = function(e) {
                e.preventDefault();
                updateWorksheetPrompt();
            };
            
            // Find the heading element and append the button
            var heading = promptHeader.querySelector('h5');
            if (heading) {
                heading.appendChild(button);
            } else {
                promptHeader.appendChild(button);
            }
        }
    }
    
    // Setup event listeners
    function setupEventListeners() {
        var selects = ['subject', 'studentLevel', 'difficultyLevel', 'numActivities'];
        selects.forEach(function(id) {
            var element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', updateWorksheetPrompt);
            }
        });
        
        document.querySelectorAll('input[name="worksheet_type"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', updateWorksheetPrompt);
        });
    }
    
    // Main initialization
    function init() {
        console.log("Initializing worksheet prompt fix");
        addUpdateButton();
        setupEventListeners();
        
        // Initial update and delayed update for reliability
        updateWorksheetPrompt();
        setTimeout(updateWorksheetPrompt, 500);
    }
    
    // Run initialization
    init();
});
