// Main JavaScript for Berojgar - Job Application Assistant

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Resume upload preview
    const resumeInput = document.getElementById('resume');
    const resumePreview = document.getElementById('resumePreview');
    
    if (resumeInput && resumePreview) {
        resumeInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const fileName = file.name;
                resumePreview.innerHTML = `
                    <div class="alert alert-success">
                        <i class="bi bi-file-earmark-pdf me-2"></i>
                        <strong>${fileName}</strong> uploaded successfully
                    </div>`;
                
                // Extract resume data if possible
                if (window.FileReader) {
                    extractResumeData(file);
                }
            }
        });
    }

    // Job search form
    const jobSearchForm = document.getElementById('jobSearchForm');
    if (jobSearchForm) {
        jobSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            searchJobs();
        });
    }

    // Resume matcher form
    const matcherForm = document.getElementById('uploadForm');
    if (matcherForm) {
        matcherForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await matchResumeToJob();
        });
    }

    // Initialize job search results if we're on the search page
    if (document.getElementById('jobSearchResults')) {
        // Check if there are search params in the URL
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('query');
        const location = urlParams.get('location');
        
        if (query || location) {
            // Fill the form with the search params
            if (document.getElementById('jobQuery')) {
                document.getElementById('jobQuery').value = query || '';
            }
            if (document.getElementById('jobLocation')) {
                document.getElementById('jobLocation').value = location || '';
            }
            
            // Trigger the search
            searchJobs();
        }
    }
});

// Function to search for jobs
async function searchJobs() {
    const query = document.getElementById('jobQuery').value;
    const location = document.getElementById('jobLocation').value;
    const resumeInput = document.getElementById('resume');
    const resultsContainer = document.getElementById('jobSearchResults');
    const loadingSpinner = document.getElementById('searchLoading');
    
    if (!resultsContainer) return;
    
    // Validate input
    if (!query.trim()) {
        showToast('Please enter a job title, skill, or keyword', 'warning');
        return;
    }
    
    // Show loading spinner with message
    if (loadingSpinner) {
        loadingSpinner.style.display = 'flex';
        const loadingMessage = loadingSpinner.querySelector('.loading-message') || document.createElement('p');
        loadingMessage.className = 'loading-message text-center mt-2';
        loadingMessage.textContent = 'Searching for genuine job opportunities...';
        if (!loadingSpinner.querySelector('.loading-message')) {
            loadingSpinner.appendChild(loadingMessage);
        }
    }
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    try {
        // Using the new API endpoint with POST method
        const apiUrl = '/api/jobs/search';
        
        // Prepare the request data
        const requestData = {
            query: query,
            location: location,
            resume_data: null
        };
        
        // If resume is uploaded, extract skills and other data
        if (resumeInput && resumeInput.files.length > 0) {
            try {
                const resumeFile = resumeInput.files[0];
                // This is a placeholder - in a real app you'd extract skills from the resume
                // For now, add some common skills as an example
                requestData.resume_data = {
                    skills: ['JavaScript', 'Python', 'React', 'SQL', 'Communication', 'Teamwork']
                };
                console.log('Added resume data to request:', requestData.resume_data);
            } catch (error) {
                console.error('Error processing resume:', error);
            }
        }
        
        // Set a timeout to show a message if the search takes too long
        const timeoutId = setTimeout(() => {
            if (loadingSpinner && loadingSpinner.style.display === 'flex') {
                const loadingMessage = loadingSpinner.querySelector('.loading-message');
                if (loadingMessage) {
                    loadingMessage.textContent = 'Still searching... Finding genuine opportunities takes a moment.';
                }
            }
        }, 5000);
        
        // Make API request to search for jobs using POST method
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        clearTimeout(timeoutId);
        const data = await response.json();
        
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
        if (data.success && data.jobs && data.jobs.length > 0) {
            // Filter out jobs with invalid URLs or missing essential data
            const validJobs = data.jobs.filter(job => {
                return job.title && job.company && job.url && 
                       (job.url.startsWith('http://') || job.url.startsWith('https://'));
            });
            
            if (validJobs.length === 0) {
                showNoJobsMessage(resultsContainer, query, location);
                return;
            }
            
            // Group jobs by source
            const jobsBySource = {};
            validJobs.forEach(job => {
                if (!jobsBySource[job.source]) {
                    jobsBySource[job.source] = [];
                }
                jobsBySource[job.source].push(job);
            });
            
            // Create a header for the results
            const resultsHeader = document.createElement('div');
            resultsHeader.className = 'results-header mb-4';
            resultsHeader.innerHTML = `
                <h3 class="mb-3">Found ${validJobs.length} genuine jobs matching "${query}"</h3>
                <div class="d-flex flex-wrap gap-2 mb-3">
                    ${Object.keys(jobsBySource).map(source => 
                        `<span class="badge bg-secondary">${source}: ${jobsBySource[source].length} jobs</span>`
                    ).join('')}
                </div>
                <p class="text-muted">Jobs are sorted by match score based on your resume</p>
            `;
            resultsContainer.appendChild(resultsHeader);
            
            // Display job results
            validJobs.forEach(job => {
                const matchClass = job.match_score >= 80 ? 'match-high' : 
                                  job.match_score >= 60 ? 'match-medium' : 'match-low';
                
                // Format job title and company for display
                const title = sanitizeHTML(job.title);
                const company = sanitizeHTML(job.company);
                const location = sanitizeHTML(job.location || 'Remote');
                
                // Create skills badges
                let skillsHtml = '';
                if (job.skills && job.skills.length > 0) {
                    skillsHtml = `<div class="skills-container mt-2">
                        ${job.skills.slice(0, 5).map(skill => 
                            `<span class="badge bg-light text-dark me-1">${sanitizeHTML(skill)}</span>`
                        ).join('')}
                        ${job.skills.length > 5 ? `<span class="badge bg-light text-dark">+${job.skills.length - 5} more</span>` : ''}
                    </div>`;
                }
                
                // Format job description
                let description = job.description || 'No description available.';
                description = description.substring(0, 180) + (description.length > 180 ? '...' : '');
                
                // Format posted date
                const postedDate = job.posted_date || 'Recently posted';
                
                // Verify application URL
                const applicationUrl = job.application_url || job.url || '#';
                const hasValidUrl = applicationUrl && (applicationUrl.startsWith('http://') || applicationUrl.startsWith('https://'));
                
                const jobCard = document.createElement('div');
                jobCard.className = 'card job-card mb-3';
                jobCard.setAttribute('data-source', job.source);
                jobCard.setAttribute('data-job-id', job.id);
                
                // Add remote badge if job is remote
                const remoteBadge = job.is_remote ? 
                    `<span class="badge bg-success me-2">Remote</span>` : '';
                
                // Add new badge if job is posted within last 3 days
                const isNew = job.posted_date_timestamp && 
                              (Date.now()/1000 - job.posted_date_timestamp) < 3 * 24 * 60 * 60;
                const newBadge = isNew ? 
                    `<span class="badge bg-danger me-2">New</span>` : '';
                
                jobCard.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="job-title mb-1">${title}</h5>
                                <p class="company-name mb-2">${company}</p>
                                <div class="d-flex flex-wrap mb-2">
                                    <span class="job-location me-3">
                                        <i class="bi bi-geo-alt me-1"></i>${location}
                                    </span>
                                    <span class="job-type me-3">
                                        <i class="bi bi-briefcase me-1"></i>${job.job_type || 'Full-time'}
                                    </span>
                                    <span class="job-source">
                                        <i class="bi bi-globe me-1"></i>${job.source}
                                    </span>
                                </div>
                                ${skillsHtml}
                            </div>
                            <span class="job-match ${matchClass}">
                                ${job.match_score}% Match
                            </span>
                        </div>
                        <p class="job-description mt-2">${description}</p>
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <div>
                                ${newBadge}
                                ${remoteBadge}
                                <span class="badge bg-light text-dark me-2">${postedDate}</span>
                                ${job.salary ? `<span class="badge bg-light text-dark">${sanitizeHTML(job.salary)}</span>` : ''}
                            </div>
                            <div>
                                <button class="btn btn-sm ${hasValidUrl ? 'btn-outline-primary' : 'btn-outline-secondary'} me-2 apply-btn" 
                                        data-job-id="${job.id}" 
                                        data-job-url="${applicationUrl}"
                                        ${!hasValidUrl ? 'disabled' : ''}>
                                    ${hasValidUrl ? 'Apply Now' : 'No Link Available'}
                                </button>
                                <button class="btn btn-sm btn-primary view-btn" 
                                        data-job-id="${job.id}"
                                        data-bs-toggle="modal" 
                                        data-bs-target="#jobDetailModal">
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                resultsContainer.appendChild(jobCard);
            });
            
            // Add event listeners to the apply buttons
            document.querySelectorAll('.apply-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const jobId = this.getAttribute('data-job-id');
                    const jobUrl = this.getAttribute('data-job-url');
                    applyToJob(jobId, jobUrl);
                });
            });
            
            // Add event listeners to the view buttons
            document.querySelectorAll('.view-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const jobId = this.getAttribute('data-job-id');
                    viewJobDetails(jobId);
                });
            });
            
            // Add filter controls
            addJobFilters(resultsContainer, jobsBySource);
        } else {
            // No jobs found
            showNoJobsMessage(resultsContainer, query, location);
        }
    } catch (error) {
        console.error('Error searching for jobs:', error);
        
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
        
        // Show error message
        resultsContainer.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Error</h4>
                <p>There was an error searching for jobs. Please try again later.</p>
                <hr>
                <p class="mb-0">Technical details: ${error.message || 'Unknown error'}</p>
            </div>
        `;
    }
}

// Function to show no jobs message
function showNoJobsMessage(container, query, location) {
    container.innerHTML = `
        <div class="alert alert-info">
            <h4 class="alert-heading">No jobs found</h4>
            <p>We couldn't find any jobs matching "${sanitizeHTML(query)}" ${location ? `in "${sanitizeHTML(location)}"` : ''}.</p>
            <hr>
            <p class="mb-0">Try these tips:</p>
            <ul>
                <li>Check your spelling</li>
                <li>Try more general keywords</li>
                <li>Try different keywords</li>
                <li>Upload your resume for better matches</li>
                <li>Remove location filter for remote opportunities</li>
            </ul>
        </div>
    `;
}

// Function to add job filters
function addJobFilters(container, jobsBySource) {
    // Create filter container
    const filterContainer = document.createElement('div');
    filterContainer.className = 'job-filters mb-4';
    filterContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">Filter Results</h5>
            <button class="btn btn-sm btn-outline-secondary reset-filters">Reset Filters</button>
        </div>
        <div class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Source</label>
                <select class="form-select form-select-sm" id="sourceFilter">
                    <option value="">All Sources</option>
                    ${Object.keys(jobsBySource).map(source => 
                        `<option value="${source}">${source} (${jobsBySource[source].length})</option>`
                    ).join('')}
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Job Type</label>
                <select class="form-select form-select-sm" id="jobTypeFilter">
                    <option value="">All Types</option>
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                    <option value="Freelance">Freelance</option>
                    <option value="Internship">Internship</option>
                </select>
            </div>
            <div class="col-md-4">
                <label class="form-label">Match Score</label>
                <select class="form-select form-select-sm" id="matchScoreFilter">
                    <option value="">Any Match</option>
                    <option value="80">High Match (80%+)</option>
                    <option value="60">Medium Match (60%+)</option>
                </select>
            </div>
        </div>
    `;
    
    // Insert filter container before the job cards
    const resultsHeader = container.querySelector('.results-header');
    if (resultsHeader && resultsHeader.nextSibling) {
        container.insertBefore(filterContainer, resultsHeader.nextSibling);
    } else {
        container.appendChild(filterContainer);
    }
    
    // Add event listeners to filters
    const sourceFilter = document.getElementById('sourceFilter');
    const jobTypeFilter = document.getElementById('jobTypeFilter');
    const matchScoreFilter = document.getElementById('matchScoreFilter');
    const resetButton = container.querySelector('.reset-filters');
    
    // Function to apply filters
    function applyFilters() {
        const sourceValue = sourceFilter.value;
        const jobTypeValue = jobTypeFilter.value;
        const matchScoreValue = parseInt(matchScoreFilter.value) || 0;
        
        // Get all job cards
        const jobCards = container.querySelectorAll('.job-card');
        
        // Filter job cards
        jobCards.forEach(card => {
            const source = card.getAttribute('data-source');
            const jobType = card.querySelector('.job-type').textContent.trim().replace('\n', '').replace(/^[\s\S]*\bi\b[\s\S]*\b/, '');
            const matchScore = parseInt(card.querySelector('.job-match').textContent) || 0;
            
            const sourceMatch = !sourceValue || source === sourceValue;
            const jobTypeMatch = !jobTypeValue || jobType.includes(jobTypeValue);
            const matchScoreMatch = matchScore >= matchScoreValue;
            
            if (sourceMatch && jobTypeMatch && matchScoreMatch) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Count visible jobs
        const visibleJobs = Array.from(jobCards).filter(card => card.style.display !== 'none').length;
        
        // Update results header
        const resultsHeader = container.querySelector('.results-header h3');
        if (resultsHeader) {
            const originalText = resultsHeader.getAttribute('data-original-text') || resultsHeader.textContent;
            if (!resultsHeader.getAttribute('data-original-text')) {
                resultsHeader.setAttribute('data-original-text', originalText);
            }
            
            if (sourceValue || jobTypeValue || matchScoreValue) {
                resultsHeader.textContent = `Showing ${visibleJobs} filtered jobs`;
            } else {
                resultsHeader.textContent = originalText;
            }
        }
    }
    
    // Add event listeners
    sourceFilter.addEventListener('change', applyFilters);
    jobTypeFilter.addEventListener('change', applyFilters);
    matchScoreFilter.addEventListener('change', applyFilters);
    
    // Reset filters
    resetButton.addEventListener('click', function() {
        sourceFilter.value = '';
        jobTypeFilter.value = '';
        matchScoreFilter.value = '';
        applyFilters();
    });
}

// Helper function to sanitize HTML
function sanitizeHTML(text) {
    if (!text) return '';
    return text.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Function to apply to a job
async function applyToJob(jobId, jobUrl) {
    const resumeInput = document.getElementById('resume');
    
    if (!resumeInput || !resumeInput.files[0]) {
        showToast('Please upload your resume first', 'error');
        return;
    }
    
    try {
        // Show loading toast
        showToast('Submitting your application...', 'info');
        
        // Convert resume to base64
        const resumeBase64 = await fileToBase64(resumeInput.files[0]);
        
        // Make API request to apply to the job
        const response = await fetch('/apply_job', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_id: jobId,
                resume_file: resumeBase64
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Application submitted successfully!', 'success');
            
            // Check if we need to redirect to an external application page
            if (data.redirect_url) {
                // Show toast with redirection message
                showToast('Redirecting to the official application page...', 'info');
                
                // Open the application URL in a new tab
                setTimeout(() => {
                    window.open(data.redirect_url, '_blank');
                }, 1500);
            }
            
            // Update the dashboard if it exists
            if (document.getElementById('dashboardStats')) {
                updateDashboardStats();
            }
        } else {
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error applying to job:', error);
        showToast('Error submitting application. Please try again.', 'error');
    }
}

// Function to view job details
async function viewJobDetails(jobId) {
    const modalBody = document.querySelector('#jobDetailModal .modal-body');
    const modalFooter = document.querySelector('#jobDetailModal .modal-footer');
    
    if (!modalBody) return;
    
    // Show loading spinner
    modalBody.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Loading job details...</p>
        </div>
    `;
    
    try {
        // Make API request to get job details
        const response = await fetch(`/job_details/${encodeURIComponent(jobId)}`);
        const data = await response.json();
        
        if (data.success && data.job) {
            const job = data.job;
            
            // Check if this is a real job from an external source
            const isRealJob = jobId.startsWith('indeed_') || 
                              jobId.startsWith('linkedin_') || 
                              jobId.startsWith('github_') || 
                              jobId.startsWith('google_') || 
                              jobId.startsWith('rss_');
            
            // Format requirements as a list
            const requirementsList = job.requirements && job.requirements.length > 0 ?
                `<ul class="requirements-list">
                    ${job.requirements.map(req => `<li>${req}</li>`).join('')}
                </ul>` : '';
            
            // Format skills as badges
            const skillsBadges = job.skills && job.skills.length > 0 ?
                `<div class="skills-container">
                    ${job.skills.map(skill => `<span class="badge bg-light text-dark me-2 mb-2">${skill}</span>`).join('')}
                </div>` : '';
            
            // Format matching skills if available
            const matchingSkillsSection = job.matching_skills && job.matching_skills.length > 0 ?
                `<div class="job-detail-section mb-4">
                    <h5 class="section-title">Your Matching Skills</h5>
                    <div class="matching-skills-container">
                        ${job.matching_skills.map(skill => 
                            `<span class="badge bg-success text-white me-2 mb-2">${skill}</span>`
                        ).join('')}
                    </div>
                    <p class="mt-2 text-muted">These skills from your resume match the job requirements</p>
                </div>` : '';
            
            // Update modal content
            modalBody.innerHTML = `
                <div class="job-detail-header mb-4">
                    <h3 class="job-title">${job.title}</h3>
                    <p class="company-name">${job.company}</p>
                    <div class="d-flex flex-wrap mb-3">
                        <span class="job-location me-3">
                            <i class="bi bi-geo-alt me-1"></i>${job.location}
                        </span>
                        <span class="job-type me-3">
                            <i class="bi bi-briefcase me-1"></i>${job.job_type || 'Full-time'}
                        </span>
                        <span class="job-source me-3">
                            <i class="bi bi-globe me-1"></i>${job.source}
                        </span>
                        <span class="job-date">
                            <i class="bi bi-calendar me-1"></i>Posted ${job.posted_date || 'Recently'}
                        </span>
                    </div>
                    ${job.salary ? `<div class="salary-badge mb-3"><i class="bi bi-cash me-1"></i>${job.salary}</div>` : ''}
                    ${job.match_score ? `<div class="match-score-badge mb-3"><i class="bi bi-check-circle me-1"></i>${job.match_score}% Match with your resume</div>` : ''}
                </div>
                
                ${matchingSkillsSection}
                
                <div class="job-detail-section mb-4">
                    <h5 class="section-title">Job Description</h5>
                    <p>${job.description}</p>
                </div>
                
                ${job.requirements && job.requirements.length > 0 ? `
                <div class="job-detail-section mb-4">
                    <h5 class="section-title">Requirements</h5>
                    ${requirementsList}
                </div>` : ''}
                
                ${job.skills && job.skills.length > 0 ? `
                <div class="job-detail-section mb-4">
                    <h5 class="section-title">Skills</h5>
                    ${skillsBadges}
                </div>` : ''}
                
                <div class="job-detail-section">
                    <h5 class="section-title">How to Apply</h5>
                    ${isRealJob ? 
                        `<p>Click the Apply button below to be redirected to the official job listing. Our system will attempt to auto-fill the application form for you if you've uploaded your resume.</p>` :
                        `<p>Click the Apply button below to submit your application. Make sure you have uploaded your resume for the best results.</p>`
                    }
                </div>
            `;
            
            // Update modal footer with apply button
            modalFooter.innerHTML = `
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary apply-modal-btn" data-job-id="${job.id}" data-job-url="${job.url}">
                    <i class="bi bi-send me-1"></i>Apply Now
                </button>
            `;
            
            // Add event listener to the apply button
            document.querySelector('.apply-modal-btn').addEventListener('click', function() {
                const jobId = this.getAttribute('data-job-id');
                const jobUrl = this.getAttribute('data-job-url');
                applyToJob(jobId, jobUrl);
                
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('jobDetailModal'));
                if (modal) {
                    modal.hide();
                }
            });
        } else {
            // Job not found
            modalBody.innerHTML = `
                <div class="alert alert-warning text-center">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Job details not found.
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching job details:', error);
        
        // Show error message
        modalBody.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Error loading job details. Please try again later.
            </div>
        `;
    }
}

// Function to match resume to job
async function matchResumeToJob() {
    const resumeInput = document.getElementById('resume');
    const jobLink = document.getElementById('job_link');
    const loadingElement = document.getElementById('loading');
    const resultElement = document.getElementById('result');
    
    if (!resumeInput || !resumeInput.files[0] || !jobLink || !jobLink.value) {
        showToast('Please upload your resume and provide a job link', 'error');
        return;
    }
    
    // Show loading spinner
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
    if (resultElement) {
        resultElement.style.display = 'none';
    }
    
    try {
        // Convert resume to base64
        const resumeBase64 = await fileToBase64(resumeInput.files[0]);
        
        // Make API request to match resume to job
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                resume: resumeBase64,
                job_description: jobLink.value
            })
        });
        
        const data = await response.json();
        
        // Hide loading spinner
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Display results
        if (resultElement) {
            resultElement.style.display = 'block';
            
            let resultHtml = '';
            if (data.match_score !== undefined) {
                resultHtml += '<strong>Match Score: ' + Math.round(data.match_score * 100) + '%</strong>';
            }
            
            if (data.match_score === 0) {
                if (data.missing_skills && data.missing_skills.length > 0) {
                    resultHtml += '<br><br><b>Missing Skills:</b><ul>' +
                        data.missing_skills.map(skill => '<li>' + skill + '</li>').join('') + '</ul>';
                }
                if (data.tips && data.tips.length > 0) {
                    resultHtml += '<br><b>Tips to Improve Your Resume:</b><ul>' +
                        data.tips.map(tip => '<li>' + tip + '</li>').join('') + '</ul>';
                }
            } else if (data.status) {
                resultHtml += '<br><span>' + data.status + '</span>';
            } else if (data.error) {
                resultHtml += '<br><span style="color:red">Error: ' + data.error + '</span>';
            } else {
                resultHtml += '<br>Unexpected response.';
            }
            
            resultElement.innerHTML = resultHtml;
        }
    } catch (error) {
        console.error('Error matching resume to job:', error);
        
        // Hide loading spinner
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
        
        // Show error message
        if (resultElement) {
            resultElement.style.display = 'block';
            resultElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error: ${error.message || 'An unexpected error occurred'}
                </div>
            `;
        }
    }
}

// Helper function to convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// Function to show toast notifications
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast';
    
    // Set toast content based on type
    let iconClass = 'bi-info-circle';
    let headerClass = 'bg-primary';
    
    if (type === 'success') {
        iconClass = 'bi-check-circle';
        headerClass = 'bg-success';
    } else if (type === 'error') {
        iconClass = 'bi-exclamation-triangle';
        headerClass = 'bg-danger';
    } else if (type === 'warning') {
        iconClass = 'bi-exclamation-circle';
        headerClass = 'bg-warning';
    }
    
    toast.innerHTML = `
        <div class="toast-header ${headerClass} text-white">
            <i class="bi ${iconClass} me-2"></i>
            <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close btn-close-white" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Add event listener to close button
    const closeButton = toast.querySelector('.btn-close');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            toast.remove();
        });
    }
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Function to extract resume data (for future use)
function extractResumeData(file) {
    // This would normally use a resume parsing API or service
    // For now, we'll just log that we would extract data
    console.log('Would extract data from resume:', file.name);
}
