// Sidebar Generation Status Script
$(document).ready(function() {
    console.log("Worksheet sidebar status script loaded");

    // Set up initial state
    function initSidebarStatus() {
        $('#sidebar-spinner').hide();
        $('#sidebar-progress-status').text('Ready to generate');
        $('#sidebar-generation-progress').css('width', '0%');
    }

    // Initialize the sidebar status
    initSidebarStatus();

    // Override the startProgressSimulation function to update the sidebar
    const originalStartProgressSimulation = window.startProgressSimulation || function() {};
    window.startProgressSimulation = function() {
        // Call the original function if it exists
        if (originalStartProgressSimulation) {
            originalStartProgressSimulation();
        }

        // Reset sidebar progress
        $('#sidebar-spinner').show();
        $('#sidebar-generation-progress')
            .removeClass('bg-danger bg-success')
            .addClass('progress-bar-animated progress-bar-striped')
            .css('width', '0%');
        
        let currentProgress = 0;
        let progressInterval;
        
        const progressSteps = [
            { threshold: 10, message: "Analyzing topic and requirements..." },
            { threshold: 25, message: "Planning worksheet structure..." },
            { threshold: 40, message: "Creating activities..." },
            { threshold: 60, message: "Formatting content..." },
            { threshold: 80, message: "Finalizing worksheet..." },
            { threshold: 95, message: "Almost done..." }
        ];
        
        // Clear any existing interval
        clearInterval(progressInterval);
        
        progressInterval = setInterval(function() {
            // Increase progress but slow down as it approaches 95%
            if (currentProgress < 30) {
                currentProgress += 2;
            } else if (currentProgress < 60) {
                currentProgress += 1.5;
            } else if (currentProgress < 80) {
                currentProgress += 0.8;
            } else if (currentProgress < 95) {
                currentProgress += 0.3;
            }
            
            if (currentProgress >= 95) {
                currentProgress = 95;  // Cap at 95%, will go to 100% when complete
                clearInterval(progressInterval);
            }
            
            // Update the progress bar
            $('#sidebar-generation-progress').css('width', currentProgress + '%');
            
            // Update message based on progress thresholds
            for (let step of progressSteps) {
                if (currentProgress >= step.threshold && currentProgress < step.threshold + 5) {
                    $('#sidebar-progress-status').text(step.message + ' (' + Math.round(currentProgress) + '%)');
                    break;
                }
            }
        }, 200);
        
        // Store interval for clearing later
        window.sidebarProgressInterval = progressInterval;
    };

    // Listen for AJAX events to update the sidebar status
    $(document).ajaxSend(function(event, jqXHR, settings) {
        if (settings.url.includes('worksheet')) {
            // Reset and prepare sidebar for worksheet generation
            $('#sidebar-spinner').show();
            $('#sidebar-progress-status').text('Starting generation...');
            $('#sidebar-generation-progress')
                .removeClass('bg-danger bg-success')
                .addClass('progress-bar-animated progress-bar-striped')
                .css('width', '0%');
        }
    });

    $(document).ajaxSuccess(function(event, jqXHR, settings, data) {
        if (settings.url.includes('worksheet')) {
            // Complete the progress animation on the sidebar
            clearInterval(window.sidebarProgressInterval);
            $('#sidebar-generation-progress').css('width', '100%');
            
            if (data.status === 'success') {
                $('#sidebar-spinner').hide();
                $('#sidebar-progress-status').text('Worksheet generated successfully!');
                $('#sidebar-generation-progress')
                    .removeClass('progress-bar-animated progress-bar-striped')
                    .addClass('bg-success');
            } else {
                $('#sidebar-spinner').hide();
                $('#sidebar-progress-status').text('Error: Generation failed');
                $('#sidebar-generation-progress')
                    .removeClass('progress-bar-animated progress-bar-striped')
                    .addClass('bg-danger')
                    .css('width', '0%');
            }
        }
    });

    $(document).ajaxError(function(event, jqXHR, settings) {
        if (settings.url.includes('worksheet')) {
            // Reset sidebar status on error
            clearInterval(window.sidebarProgressInterval);
            $('#sidebar-spinner').hide();
            $('#sidebar-progress-status').text('Error: Generation failed');
            $('#sidebar-generation-progress')
                .removeClass('progress-bar-animated progress-bar-striped')
                .addClass('bg-danger')
                .css('width', '0%');
        }
    });
});
