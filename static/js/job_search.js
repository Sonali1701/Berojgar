/**
 * Berojgar Job Search JavaScript
 * Handles job search functionality, resume upload, and job details display
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const jobSearchForm = document.getElementById('jobSearchForm');
    const jobQueryInput = document.getElementById('jobQuery');
    const jobLocationInput = document.getElementById('jobLocation');
    const resumeInput = document.getElementById('resume');
    const searchLoading = document.getElementById('searchLoading');
    const jobSearchResults = document.getElementById('jobSearchResults');
    const jobDetailModal = new bootstrap.Modal(document.getElementById('jobDetailModal'));
    const modalBody = document.querySelector('#jobDetailModal .modal-body');
    
    // Resume data storage
    let resumeFile = null;
    let resumeData = null;
    
    // Event listeners
    jobSearchForm.addEventListener('submit', handleJobSearch);
    resumeInput.addEventListener('change', handleResumeUpload);
    
    /**
     * Handle job search form submission
     */
    function handleJobSearch(e) {
        e.preventDefault();
        
        const query = jobQueryInput.value.trim();
        const location = jobLocationInput.value.trim();
        
        if (!query) {
            showAlert('Please enter a job title, keyword, or company name', 'warning');
            return;
        }
        
        // Show loading spinner
        searchLoading.style.display = 'flex';
        jobSearchResults.innerHTML = '';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('query', query);
        formData.append('location', location);
        
        // Add resume if available
        if (resumeFile) {
            formData.append('resume', resumeFile);
        }
        
        // Add debug logging
        console.log('Sending job search request with query:', query, 'location:', location);
        
        // Send search request
        fetch('/api/jobs/search', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Job search response status:', response.status);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Error response text:', text);
                    throw new Error(`Server error: ${response.status} - ${text || 'No error details'}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading spinner
            searchLoading.style.display = 'none';
            
            // Log the response data for debugging
            console.log('Job search response data:', data);
            
            // Check if data has the expected structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid response format');
            }
            
            // Handle both possible response formats
            const jobs = data.jobs || (Array.isArray(data) ? data : []);
            
            // Display results
            renderJobResults(jobs);
        })
        .catch(error => {
            console.error('Job search error:', error);
            searchLoading.style.display = 'none';
            showAlert(`Error searching for jobs: ${error.message}. Please try again.`, 'danger');
            
            // Show fallback message and empty results
            jobSearchResults.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        ${error.message}
                        <p class="mt-2 mb-0">Please try a different search term or check your internet connection.</p>
                    </div>
                </div>
            `;
        });
    }
    
    /**
     * Handle resume file upload
     */
    function handleResumeUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Check file type
        if (file.type !== 'application/pdf') {
            showAlert('Please upload a PDF file', 'warning');
            resumeInput.value = '';
            return;
        }
        
        // Store file for later use
        resumeFile = file;
        
        // Show preview
        const previewElement = document.getElementById('resumePreview');
        previewElement.innerHTML = `
            <div class="alert alert-success mt-2">
                <i class="bi bi-file-earmark-check me-2"></i>
                Resume uploaded: <strong>${file.name}</strong> (${formatFileSize(file.size)})
                <button type="button" class="btn-close float-end" id="removeResume"></button>
            </div>
        `;
        
        // Add remove button functionality
        document.getElementById('removeResume').addEventListener('click', function() {
            resumeInput.value = '';
            resumeFile = null;
            previewElement.innerHTML = '';
        });
        
        // Extract resume data for better job matching
        extractResumeData(file);
    }
    
    /**
     * Extract resume data for better job matching
     */
    function extractResumeData(file) {
        const formData = new FormData();
        formData.append('resume', file);
        
        fetch('/api/resume/parse', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            resumeData = data;
            console.log('Resume data extracted:', resumeData);
        })
        .catch(error => {
            console.error('Error extracting resume data:', error);
        });
    }
    
    /**
     * Render job search results
     */
    function renderJobResults(jobs) {
        jobSearchResults.innerHTML = '';
        
        if (!jobs || jobs.length === 0) {
            jobSearchResults.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle me-2"></i>
                        No jobs found matching your search criteria. Try different keywords or location.
                    </div>
                </div>
            `;
            return;
        }
        
        console.log(`Rendering ${jobs.length} jobs`);
        
        // Initialize global job cache if it doesn't exist
        if (!window.jobCache) {
            window.jobCache = {};
        }
        
        // Create a container for all jobs
        const jobsContainer = document.createElement('div');
        jobsContainer.className = 'job-listings';
        jobSearchResults.appendChild(jobsContainer);
        
        jobs.forEach(job => {
            // Skip jobs with missing essential data
            if (!job.title && !job.company) {
                console.warn('Skipping job with missing title and company');
                return;
            }
            
            // Add job to global cache for quick lookup
            window.jobCache[job.id] = job;
            
            // Create a job card container
            const jobCard = document.createElement('div');
            jobCard.className = 'card mb-3 job-card horizontal-job-card';
            
            // Add some styling for horizontal cards
            jobCard.style.border = '1px solid #e0e0e0';
            jobCard.style.borderRadius = '8px';
            jobCard.style.transition = 'transform 0.2s, box-shadow 0.2s';
            jobCard.style.overflow = 'hidden';
            
            // Ensure job has a description
            const description = job.description || 'No description available';
            
            // Clean and prepare the description for display
            let cleanDescription = description;
            
            // Remove HTML tags if present
            cleanDescription = cleanDescription.replace(/<[^>]*>/g, ' ');
            
            // Replace common HTML entities
            cleanDescription = cleanDescription.replace(/&nbsp;/g, ' ')
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"')
                .replace(/&#39;/g, "'");
            
            // Remove extra whitespace
            cleanDescription = cleanDescription.replace(/\s+/g, ' ').trim();
            
            // Create truncated description
            const truncatedDescription = truncateText(cleanDescription, 150);
            
            // Determine job match class and text
            let matchClass = '';
            let matchText = '';
            
            if (job.match_score !== undefined) {
                if (job.match_score >= 80) {
                    matchClass = 'bg-success';
                    matchText = 'Strong Match';
                } else if (job.match_score >= 60) {
                    matchClass = 'bg-info';
                    matchText = 'Good Match';
                } else if (job.match_score >= 40) {
                    matchClass = 'bg-warning';
                    matchText = 'Fair Match';
                } else {
                    matchClass = 'bg-secondary';
                    matchText = 'Low Match';
                }
            }
            
            // Ensure job has a URL, or create a Google search URL
            const jobUrl = job.url || `https://www.google.com/search?q=${encodeURIComponent(job.title + ' ' + job.company + ' job apply')}`;
            
            // Format job type and posted date
            const jobType = job.job_type || 'Full-time';
            const postedDate = job.posted_date || 'Recently';
            
            // Create card content with horizontal layout
            jobCard.innerHTML = `
                <div class="row g-0">
                    <div class="col-md-8">
                        <div class="card-body">
                            ${job.match_score !== undefined ? `<span class="badge ${matchClass} position-absolute top-0 end-0 m-2">${job.match_score}% ${matchText}</span>` : ''}
                            <h5 class="card-title">${job.title || 'Untitled Position'}</h5>
                            <h6 class="card-subtitle mb-2 text-muted">${job.company || 'Unknown Company'}</h6>
                            <p class="card-text small">
                                <i class="bi bi-geo-alt me-1"></i> ${job.location || 'Remote/Various'}
                                <span class="ms-2"><i class="bi bi-calendar me-1"></i> ${postedDate}</span>
                                <span class="ms-2"><i class="bi bi-briefcase me-1"></i> ${jobType}</span>
                            </p>
                            <div class="card-text description">${truncatedDescription}</div>
                            
                            <div class="skills-container mt-2">
                                ${job.skills && job.skills.length > 0 ? 
                                    job.skills.slice(0, 5).map(skill => `<span class="badge bg-light text-dark me-1 mb-1">${skill}</span>`).join('') : 
                                    ''
                                }
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 d-flex align-items-center justify-content-center" style="background-color: #f8f9fa; padding: 15px;">
                        <div class="text-center">
                            <button class="btn btn-outline-primary mb-2 w-100" onclick="showJobDetails('${job.id}')">View Details</button>
                            <a href="${jobUrl}" class="btn btn-primary w-100 apply-now-btn" target="_blank" data-job-id="${job.id}">Apply Now</a>
                        </div>
                    </div>
                </div>
            `;
            
            // Add hover effect
            jobCard.addEventListener('mouseenter', () => {
                jobCard.style.transform = 'translateY(-5px)';
                jobCard.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
            });
            
            jobCard.addEventListener('mouseleave', () => {
                jobCard.style.transform = 'translateY(0)';
                jobCard.style.boxShadow = 'none';
            });
            
            // Append the job card to the container
            jobsContainer.appendChild(jobCard);
        });
    }
    
    /**
     * View job details in modal
     */
    function viewJobDetails(jobId) {
        console.log(`Viewing details for job ID: ${jobId}`);
        
        // Show loading in modal
        modalBody.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-3">Loading job details...</p>
            </div>
        `;
        
        // Show modal
        jobDetailModal.show();
        
        // Try to get job from cache first
        let cachedJob = null;
        if (window.jobCache && window.jobCache[jobId]) {
            console.log('Found job in cache:', window.jobCache[jobId]);
            cachedJob = window.jobCache[jobId];
        }
        
        // Fetch job details from API
        fetch(`/api/jobs/${jobId}`)
            .then(response => response.json())
            .then(data => {
                // Get the job data
                const job = data.job || (cachedJob || {});
                console.log('Displaying job details:', job);
                
                // Store in cache
                if (!window.jobCache) window.jobCache = {};
                window.jobCache[jobId] = job;
                
                // Format skills
                const skills = job.skills || [];
                let skillsHTML = '';
                
                if (skills.length > 0) {
                    skillsHTML = `
                        <div class="job-skills mb-3">
                            <h6>Skills:</h6>
                            <div>
                                ${skills.map(skill => `<span class="badge bg-light text-dark me-1 mb-1">${skill}</span>`).join(' ')}
                            </div>
                        </div>
                    `;
                }
                
                // Format job type and other metadata
                const metadataHTML = `
                    <div class="job-metadata mb-4">
                        <span class="badge bg-primary me-2"><i class="bi bi-briefcase me-1"></i>${job.job_type || 'Full-time'}</span>
                        <span class="badge bg-info me-2"><i class="bi bi-clock me-1"></i>${job.posted_date || 'Recently'}</span>
                        <span class="badge bg-secondary"><i class="bi bi-link-45deg me-1"></i>${job.source || 'Job Board'}</span>
                    </div>
                `;
                
                // Ensure job has a URL, or create a Google search URL
                const jobUrl = job.url || `https://www.google.com/search?q=${encodeURIComponent((job.title || '') + ' ' + (job.company || '') + ' job apply')}`;
                
                // Update modal content
                modalBody.innerHTML = `
                    <div class="job-detail-header mb-4">
                        <h3>${job.title || 'Job Title'}</h3>
                        <h5 class="text-muted">${job.company || 'Company'}</h5>
                        <p class="location mb-2">
                            <i class="bi bi-geo-alt"></i> ${job.location || 'Remote/Various'}
                        </p>
                        ${metadataHTML}
                    </div>
                    
                    ${skillsHTML}
                    
                    <div class="job-description mb-4">
                        <h6>Description:</h6>
                        <div class="description-content">
                            ${formatJobDescription(job.description || job.full_description || 'No description available')}
                        </div>
                    </div>
                    
                    <div class="text-center mt-4">
                        <a href="${jobUrl}" target="_blank" class="btn btn-primary apply-now-btn" data-job-id="${job.id}">
                            <i class="bi bi-box-arrow-up-right me-2"></i>Apply Now
                        </a>
                    </div>
                `;
            })
            .catch(error => {
                console.error('Error fetching job details:', error);
                
                // If we have a cached job, use that instead
                if (cachedJob) {
                    console.log('Using cached job data as fallback');
                    // Recursively call this function with the cached job
                    viewJobDetails(jobId);
                    return;
                }
                
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Failed to load job details. Please try again.
                    </div>
                `;
            });
    }
    
    /**
     * Format job description with proper HTML
     */
    function formatJobDescription(description) {
        if (!description) return '<p>No description available</p>';
        
        // Convert line breaks to paragraphs
        let formatted = description.replace(/\n{2,}/g, '</p><p>').replace(/\n/g, '<br>');
        formatted = '<p>' + formatted + '</p>';
        
        // Convert bullet points
        formatted = formatted.replace(/•\s/g, '<li>').replace(/\*\s/g, '<li>');
        if (formatted.includes('<li>')) {
            formatted = formatted.replace(/<p>(<li>.*?)<\/p>/g, '<ul>$1</ul>');
        }
        
        return formatted;
    }
    
    /**
     * Truncate text to a specified length and add ellipsis
     */
    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    /**
     * Sanitize HTML to prevent XSS attacks
     */
    function sanitizeHTML(html) {
        if (!html) return '';
        const temp = document.createElement('div');
        temp.textContent = html;
        return temp.innerHTML;
    }
    
    /**
     * Format file size in human-readable format
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Set up global event handlers
     */
    function setupGlobalEventHandlers() {
        // Add event delegation for all Apply Now buttons
        document.addEventListener('click', function(e) {
            // Check if the clicked element is an Apply Now button or its child
            const applyButton = e.target.closest('.apply-now-btn');
            if (!applyButton) return;
            
            const url = applyButton.getAttribute('href');
            const jobId = applyButton.getAttribute('data-job-id');
            
            // If URL is missing or placeholder, prevent default action
            if (url === '#' || !url || url === 'undefined') {
                e.preventDefault();
                
                // Try to get the job from cache first
                if (window.jobCache && window.jobCache[jobId] && window.jobCache[jobId].url && 
                    window.jobCache[jobId].url !== '#' && window.jobCache[jobId].url !== 'undefined') {
                    // Open the URL from cache
                    window.open(window.jobCache[jobId].url, '_blank');
                } else {
                    // If not in cache, try to fetch from API
                    fetch(`/api/jobs/${jobId}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.job && data.job.url && data.job.url !== '#') {
                                // If we got a valid URL, open it
                                window.open(data.job.url, '_blank');
                            } else {
                                // Try to construct a Google search URL
                                const job = window.jobCache[jobId] || data.job || {};
                                const searchUrl = `https://www.google.com/search?q=${encodeURIComponent((job.title || '') + ' ' + (job.company || '') + ' job apply')}`;
                                window.open(searchUrl, '_blank');
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching job URL:', error);
                            alert('Could not retrieve application link. Please try again later.');
                        });
                }
            }
        });
    }
    
    // Call the setup function when the DOM is loaded
    setupGlobalEventHandlers();
    
    /**
     * Show alert message
     */
    function showAlert(message, type = 'info') {
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        jobSearchResults.innerHTML = '';
        jobSearchResults.appendChild(alertElement);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertElement.classList.remove('show');
            setTimeout(() => alertElement.remove(), 300);
        }, 5000);
    }
});

// Add custom CSS for job cards
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        .job-card {
            position: relative;
            transition: transform 0.2s, box-shadow 0.2s;
            overflow: hidden;
        }
        
        .job-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        .job-card .card-title {
            font-weight: 600;
            line-height: 1.3;
        }
        
        .job-card .description {
            font-size: 0.9rem;
            color: #555;
            max-height: 80px;
            overflow: hidden;
        }
        
        .job-card .location {
            font-size: 0.85rem;
            color: #666;
        }
        
        .job-card .source {
            font-size: 0.8rem;
        }
        
        .job-skills .badge {
            margin-right: 5px;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .match-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 4px 8px;
            border-radius: 20px;
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            z-index: 1;
        }
        
        .job-detail-header {
            border-bottom: 1px solid #eee;
            padding-bottom: 15px;
        }
        
        .job-metadata .badge {
            padding: 6px 10px;
            font-weight: 500;
        }
        
        .description-content {
            font-size: 0.95rem;
            line-height: 1.6;
            color: #333;
        }
        
        .description-content ul {
            padding-left: 20px;
        }
        
        #searchLoading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 0;
        }
    `;
    document.head.appendChild(style);
});
