/**
 * Worksheet Prompt Update Script
 * This script ensures that user selections in the worksheet form are properly reflected in the prompt textarea.
 */
function initWorksheetPromptUpdater() {
    console.log("Initializing worksheet prompt updater");
    
    function updatePrompt() {
        // Get values from form elements
        console.log("Updating worksheet prompt");
        const difficultyLevel = document.getElementById('difficultyLevel').value || 'moderate';
        const numActivities = document.getElementById('numActivities').value || '5';
        const subject = document.getElementById('subject').value || '';
        const studentLevel = document.getElementById('studentLevel').value || '';
        
        // Get topic from page
        const topicElement = document.querySelector('p.text-muted.mb-4 strong');
        const topic = topicElement ? topicElement.textContent.trim() : 'HTML';
        
        // Get checked activities
        const checkedTypes = [];
        document.querySelectorAll('input[name="worksheet_type"]:checked').forEach(function(checkbox) {
            if (checkbox.nextElementSibling && checkbox.nextElementSibling.textContent) {
                checkedTypes.push(checkbox.nextElementSibling.textContent.trim());
            }
        });
        const activityTypes = checkedTypes.length > 0 ? checkedTypes.join(', ') : 'practice exercises, assessment activities';
        
        // Build prompt text
        let promptText = `Create a ${difficultyLevel.toLowerCase()} level worksheet with ${numActivities} activities.\n\n`;
        
        if (subject && subject !== 'Select the subject') {
            promptText += `Subject area: ${subject}\n`;
        }
        
        if (studentLevel && studentLevel !== 'Select Level') {
            promptText += `For ${studentLevel} level students\n`;
        }
        
        promptText += `\nInclude the following types of activities: ${activityTypes}.\n\n`;
        promptText += `The worksheet should focus on the topic: ${topic}`;
        
        // Update textarea
        const textarea = document.getElementById('instructions');
        if (textarea) {
            textarea.value = promptText;
            
            // Visual feedback
            textarea.style.backgroundColor = '#e8f4ff';
            textarea.style.borderColor = '#0d6efd';
            setTimeout(function() {
                textarea.style.backgroundColor = '#f8f9fa';
                textarea.style.borderColor = '';
            }, 500);
            
            console.log("Prompt updated successfully");
        }
    }
    
    // Set up event listeners
    function setupEventListeners() {
        // For dropdowns
        document.querySelectorAll('#difficultyLevel, #numActivities, #subject, #studentLevel').forEach(function(select) {
            select.addEventListener('change', updatePrompt);
        });
        
        // For checkboxes
        document.querySelectorAll('input[name="worksheet_type"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', updatePrompt);
        });
        
        // Add update button
        try {
            const promptHeader = document.querySelector('.card-header .fa-pen-to-square').closest('.card-header');
            if (promptHeader) {
                const headerDiv = promptHeader.querySelector('.d-flex');
                
                const btn = document.createElement('button');
                btn.className = 'btn btn-sm btn-primary ms-2';
                btn.innerHTML = '<i class="fas fa-sync-alt"></i>';
                btn.title = "Refresh prompt with current selections";
                btn.type = "button";
                btn.onclick = function(e) {
                    e.preventDefault();
                    updatePrompt();
                };
                
                if (headerDiv) {
                    headerDiv.appendChild(btn);
                }
            }
        } catch (e) {
            console.error("Could not add update button:", e);
        }
        
        // Initial updates
        updatePrompt();
        setTimeout(updatePrompt, 500);
        setTimeout(updatePrompt, 1000);
    }
    
    // Initialize when DOM is fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupEventListeners);
    } else {
        setupEventListeners();
    }
}

// Auto-execute on page load
initWorksheetPromptUpdater();
