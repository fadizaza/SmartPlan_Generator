// Progress animation script for worksheet generation
$(document).ready(function() {
    console.log("Worksheet loading fix loaded");
    
    // Progress simulation variables
    let progressInterval;
    let currentProgress = 0;
    
    // Function to simulate progress during worksheet generation
    window.startProgressSimulation = function() {
        clearInterval(progressInterval);
        currentProgress = 0;
        
        const progressSteps = [
            { threshold: 10, message: "Analyzing topic and requirements..." },
            { threshold: 25, message: "Planning worksheet structure..." },
            { threshold: 40, message: "Creating activities..." },
            { threshold: 60, message: "Formatting content..." },
            { threshold: 80, message: "Finalizing worksheet..." },
            { threshold: 95, message: "Almost done..." }
        ];
        
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
            $('#generation-progress').css('width', currentProgress + '%');
            $('#progress-status').text('Processing: ' + Math.round(currentProgress) + '%');
            
            // Update message based on progress thresholds
            for (let step of progressSteps) {
                if (currentProgress >= step.threshold && currentProgress < step.threshold + 5) {
                    $('#progress-status').text(step.message + ' (' + Math.round(currentProgress) + '%)');
                    break;
                }
            }
        }, 200);
    };
    
    // Override the default form submission
    $('#worksheetForm').submit(function(e) {
        e.preventDefault();
        
        // Reset and show loading modal
        $('#generation-progress').css('width', '0%');
        $('#progress-status').text('Processing: 0%');
        $('#loadingModal').modal('show');
        
        // Start progress animation
        startProgressSimulation();
        
        // Get form data
        const formData = new FormData(this);
        
        // Send AJAX request
        $.ajax({
            url: $(this).attr('action') || window.location.pathname,
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log("Server response:", response);
                
                // Complete the progress animation
                clearInterval(progressInterval);
                $('#generation-progress').css('width', '100%');
                $('#progress-status').text('Processing: 100%');
                
                // Wait a moment to show 100% completion before closing
                setTimeout(function() {
                    // Hide loading modal
                    $('#loadingModal').modal('hide');
                    
                    if (response.status === 'success') {
                        // Update success modal with download options
                        let downloadHtml = '';
                        let hasDownloadUrl = false;
                        
                        // Setup download buttons for different formats
                        if (response.file_path || response.docx_url) {
                            const docxUrl = response.file_path || response.docx_url;
                            if (docxUrl) {
                                downloadHtml += `<a href="${docxUrl}" class="btn btn-primary me-2 mb-2">
                                    <i class="fas fa-file-word"></i> Download DOCX
                                </a>`;
                                // Set the main download button as well
                                $('#downloadBtn').attr('href', docxUrl);
                                hasDownloadUrl = true;
                            }
                        }
                        
                        if (response.html_url) {
                            downloadHtml += `<a href="${response.html_url}" class="btn btn-info mb-2">
                                <i class="fas fa-file-code"></i> Download HTML
                            </a>`;
                            
                            // If no DOCX URL was set, use the HTML URL for main download button
                            if (!hasDownloadUrl) {
                                $('#downloadBtn').attr('href', response.html_url);
                                hasDownloadUrl = true;
                            }
                        }
                        
                        // If we have format-specific links, add them to the modal
                        if (downloadHtml) {
                            $('.modal-body', '#successModal').html(`
                                <p>Your worksheet has been generated successfully!</p>
                                <div class="d-flex flex-wrap mt-3">
                                    ${downloadHtml}
                                </div>
                            `);
                        }
                        
                        // Show success modal when we have any download URL
                        if (hasDownloadUrl) {
                            console.log("Setting download URLs completed");
                            // Show success modal
                            $('#successModal').modal('show');
                        } 
                    } else {
                        // Show error modal
                        const errorMsg = response.message || 'There was an error generating your worksheet.';
                        console.error("Error response:", errorMsg);
                        $('#errorMessage').text(errorMsg);
                        $('#errorModal').modal('show');
                    }
                }, 800);
            },
            error: function(xhr, status, error) {
                // Hide loading and show error
                clearInterval(progressInterval);
                $('#loadingModal').modal('hide');
                $('#errorMessage').text('Server error. Please try again.');
                $('#errorModal').modal('show');
                console.error("AJAX error:", status, error);
            }
        });
    });
});
