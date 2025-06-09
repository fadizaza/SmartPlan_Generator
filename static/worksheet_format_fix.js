// Worksheet output format handling
$(document).ready(function() {
    console.log("Worksheet format fix script loaded");
    
    // Access progressInterval from the global scope
    let progressInterval = window.progressInterval;
    
    // Ensure at least one format is always selected
    $('#format_docx, #format_html').on('change', function() {
        if (!$('#format_docx').is(':checked') && !$('#format_html').is(':checked')) {
            $(this).prop('checked', true);
            alert("At least one output format must be selected.");
        }
    });
    
    // Override the form submission to ensure correct format handling
    $('#worksheetForm').off('submit').on('submit', function(e) {
        e.preventDefault();
        
        // Reset progress indicators
        $('#top-progress-bar').css('width', '0%');
        $('#progress-percentage').text('0%');
        $('#top-progress-status').text('Starting generation...');
        $('#sidebar-generation-progress').css('width', '0%');
        $('#sidebar-progress-status').text('Processing: 0%');
        $('#sidebar-progress-spinner').show();
        $('#sidebar-success-message').hide();
        
        // Start progress animation
        if (typeof startProgressSimulation === 'function') {
            startProgressSimulation();
        }
        
        // Create a new FormData object
        const formData = new FormData(this);
        
        // Get the checkbox states
        const docxChecked = $('#format_docx').is(':checked');
        const htmlChecked = $('#format_html').is(':checked');
        
        // Remove any existing values
        formData.delete('format_docx');
        formData.delete('format_html');
        
        // Add the correct values
        formData.append('format_docx', docxChecked ? 'true' : 'false');
        formData.append('format_html', htmlChecked ? 'true' : 'false');
        
        console.log("DOCX format:", docxChecked ? 'true' : 'false');
        console.log("HTML format:", htmlChecked ? 'true' : 'false');
        
        // Send AJAX request
        $.ajax({
            url: window.location.href,
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log("Server response:", response);
                
                // Complete the progress animation
                clearInterval(progressInterval);
                $('#top-progress-bar, #sidebar-generation-progress').css('width', '100%');
                $('#progress-percentage').text('100%');
                $('#top-progress-status').text('Completed!');
                $('#sidebar-progress-status').text('Processing: 100%');
                
                // Wait a moment to show 100% completion before updating UI
                setTimeout(function() {
                    // Hide top progress bar with animation
                    $('#top-progress-container').fadeOut(500);
                    
                    if (response.status === 'success') {
                        // Always show success in the sidebar when status is success
                        $('#sidebar-progress-spinner').hide();
                        $('#sidebar-success-message').show();
                        
                        // Setup download buttons for different formats
                        const $downloadButtons = $('#sidebar-download-buttons');
                        $downloadButtons.empty(); // Clear existing buttons
                        
                        let hasDownloadLink = false;
                        
                        // Check and add DOCX download link
                        if (response.file_path || response.docx_url) {
                            const docxUrl = response.file_path || response.docx_url;
                            $downloadButtons.append(`
                                <a href="${docxUrl}" class="btn btn-primary mb-2">
                                    <i class="fas fa-file-word me-2"></i> Download DOCX
                                </a>
                            `);
                            // Set the main download link
                            $('#sidebar-download-link').attr('href', docxUrl);
                            hasDownloadLink = true;
                        }
                        
                        // Check and add HTML download link
                        if (response.html_url) {
                            $downloadButtons.append(`
                                <a href="${response.html_url}" class="btn btn-info">
                                    <i class="fas fa-file-code me-2"></i> Download HTML
                                </a>
                            `);
                            // If no DOCX URL was set, use HTML for main download link
                            if (!hasDownloadLink) {
                                $('#sidebar-download-link').attr('href', response.html_url);
                            }
                        }
                        
                        // Always update the sidebar UI to success state
                        $('#sidebar-spinner').hide();
                        $('#sidebar-progress-status').text('Worksheet generated successfully!');
                        $('#sidebar-generation-progress').removeClass('progress-bar-animated').addClass('bg-success');
                        
                    } else {
                        // Only show error for actual error responses
                        const errorMsg = response.message || 'There was an error generating your worksheet.';
                        console.error("Error response:", errorMsg);
                        $('#sidebar-progress-spinner').hide();
                        $('#sidebar-progress-status').text('Error: ' + errorMsg);
                        $('#sidebar-generation-progress').removeClass('progress-bar-animated').addClass('bg-danger');
                        
                        // Show error modal
                        $('#errorMessage').text(errorMsg);
                        $('#errorModal').modal('show');
                    }                
                }, 800);
            },
            error: function(xhr, status, error) {
                // Show error in sidebar and hide top progress
                $('#top-progress-container').fadeOut(500);
                $('#sidebar-progress-spinner').hide();
                $('#sidebar-progress-status').text('Error: Server error. Please try again.');
                $('#sidebar-generation-progress').css('width', '100%').removeClass('progress-bar-animated').addClass('bg-danger');
                console.error("AJAX error:", status, error);
                
                // Show error modal
                $('#errorMessage').text('Server error. Please try again.');
                $('#errorModal').modal('show');
            }
        });
    });
});
