document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadArea = document.getElementById('uploadArea');
    const resumeFile = document.getElementById('resumeFile');
    const uploadedFile = document.getElementById('uploadedFile');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const removeFile = document.getElementById('removeFile');
    const analyzeButton = document.getElementById('analyzeButton');
    const resumeUploadForm = document.getElementById('resumeUploadForm');
    
    // Results Elements
    const initialMessage = document.getElementById('initialMessage');
    const loadingMessage = document.getElementById('loadingMessage');
    const resultsContainer = document.getElementById('resultsContainer');
    const scoreDisplay = document.getElementById('scoreDisplay');
    const atsScore = document.getElementById('atsScore');
    const scoreNeedle = document.getElementById('scoreNeedle');
    
    // Tab Elements
    const keyFindings = document.getElementById('keyFindings');
    const quickImprovements = document.getElementById('quickImprovements');
    const keywordsFound = document.getElementById('keywordsFound');
    const keywordsMissing = document.getElementById('keywordsMissing');
    const keywordProgress = document.getElementById('keywordProgress');
    const jobMatchProgress = document.getElementById('jobMatchProgress');
    const suggestedKeywords = document.getElementById('suggestedKeywords');
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('dragover');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('dragover');
    }
    
    // Handle file drop
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            handleFiles(files);
        }
    }
    
    // Handle file selection
    resumeFile.addEventListener('change', function() {
        if (this.files.length) {
            handleFiles(this.files);
        }
    });
    
    function handleFiles(files) {
        const file = files[0];
        
        // Check if file is PDF, DOC, or DOCX
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a PDF, DOC, or DOCX file.');
            return;
        }
        
        // Display file info
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        
        // Show uploaded file section
        uploadArea.classList.add('d-none');
        uploadedFile.classList.remove('d-none');
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return bytes + ' bytes';
        } else if (bytes < 1048576) {
            return (bytes / 1024).toFixed(1) + ' KB';
        } else {
            return (bytes / 1048576).toFixed(1) + ' MB';
        }
    }
    
    // Remove file
    removeFile.addEventListener('click', function() {
        resumeFile.value = '';
        uploadedFile.classList.add('d-none');
        uploadArea.classList.remove('d-none');
    });
    
    // Analyze resume using real API endpoint
    resumeUploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!resumeFile.files.length) {
            alert('Please upload a resume file.');
            return;
        }
        
        // Show loading message
        initialMessage.classList.add('d-none');
        loadingMessage.classList.remove('d-none');
        resultsContainer.classList.add('d-none');
        
        try {
            // Get job description if provided
            const jobDescription = document.getElementById('jobDescription').value;
            
            // Create form data to send files
            const formData = new FormData();
            formData.append('resume', resumeFile.files[0]);
            if (jobDescription) {
                formData.append('jobDescription', jobDescription);
            }
            
            // Call the real API endpoint for resume analysis
            const response = await fetch('/api/analyze_resume', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }
            
            const analysisData = await response.json();
            
            // Log the response for debugging
            console.log('ATS Analysis Response:', analysisData);
            
            // Display the results
            displayAnalysisResults(analysisData, jobDescription);
            
        } catch (error) {
            console.error('Error:', error);
            loadingMessage.classList.add('d-none');
            resultsContainer.classList.add('d-none');
            
            // Show error message
            initialMessage.classList.remove('d-none');
            initialMessage.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Error analyzing resume: ${error.message}
                </div>
                <div class="mt-3">
                    <h5>General Resume Improvement Tips:</h5>
                    <ul class="list-group">
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Add more industry-specific keywords to your resume</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Ensure your resume has clear section headings</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Quantify your achievements with numbers and metrics</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Include a skills section with both technical and soft skills</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Use a clean, ATS-friendly format without complex tables or graphics</li>
                    </ul>
                </div>
            `;
        }  
    });
    
    // Display analysis results
    function displayAnalysisResults(data, jobDescription) {
        try {
            // Hide loading, show results
            loadingMessage.classList.add('d-none');
            resultsContainer.classList.remove('d-none');
            scoreDisplay.classList.remove('d-none');
            
            console.log('Displaying analysis results:', data);
            
            // Ensure data has all required properties
            data = {
                score: data.score || 75,
                name: data.name || 'Not detected',
                contact: data.contact || { email: 'Not detected', phone: 'Not detected' },
                fileInfo: data.fileInfo || { format: 'Unknown', wordCount: '0' },
                keywords: data.keywords || { found: [], missing: [] },
                improvements: data.improvements || [],
                keyFindings: data.keyFindings || []
            };
            
            // Update ATS score
            const score = data.score;
            if (atsScore) atsScore.textContent = score;
            
            // Update score needle position and color
            // Convert score to degrees: 0 = -90deg, 100 = 90deg
            const degrees = -90 + (score * 1.8);
            if (scoreNeedle) {
                scoreNeedle.style.transform = `rotate(${degrees}deg)`;
                
                // Set color based on score
                let scoreColor = '#dc3545'; // Red for poor scores
                if (score >= 90) {
                    scoreColor = '#28a745'; // Green for excellent scores
                } else if (score >= 80) {
                    scoreColor = '#17a2b8'; // Blue for good scores
                } else if (score >= 70) {
                    scoreColor = '#ffc107'; // Yellow for fair scores
                }
                
                scoreNeedle.style.backgroundColor = scoreColor;
                if (atsScore) atsScore.style.color = scoreColor;
            }
            
            // Update resume name and contact info
            const detectedNameEl = document.getElementById('detectedName');
            if (detectedNameEl) detectedNameEl.textContent = data.name || 'Not detected';
            
            const contactInfoEl = document.getElementById('contactInfo');
            if (contactInfoEl) {
                contactInfoEl.textContent = 
                    `${data.contact.email !== 'Not detected' ? 'Email' : 'No email'}, ` +
                    `${data.contact.phone !== 'Not detected' ? 'Phone' : 'No phone'} detected`;
            }
            
            // Update file info
            const fileFormatEl = document.getElementById('fileFormat');
            if (fileFormatEl) fileFormatEl.textContent = data.fileInfo.format || 'Unknown';
            
            const wordCountEl = document.getElementById('wordCount');
            if (wordCountEl) wordCountEl.textContent = data.fileInfo.wordCount || '0';
            
            // Update keyword match percentage
            const foundKeywords = data.keywords.found || [];
            const missingKeywords = data.keywords.missing || [];
            const totalKeywords = foundKeywords.length + missingKeywords.length;
            const keywordMatch = totalKeywords > 0 ? Math.round((foundKeywords.length / totalKeywords) * 100) : 0;
            
            if (keywordProgress) keywordProgress.style.width = `${keywordMatch}%`;
            
            // Set progress bar color based on match percentage
            if (keywordProgress) {
                if (keywordMatch >= 80) {
                    keywordProgress.classList.remove('bg-warning', 'bg-danger');
                    keywordProgress.classList.add('bg-success');
                } else if (keywordMatch >= 50) {
                    keywordProgress.classList.remove('bg-success', 'bg-danger');
                    keywordProgress.classList.add('bg-warning');
                } else {
                    keywordProgress.classList.remove('bg-success', 'bg-warning');
                    keywordProgress.classList.add('bg-danger');
                }
            }
            
            // Add match percentage text
            const keywordMatchTextEl = document.getElementById('keywordMatchText');
            if (keywordMatchTextEl) keywordMatchTextEl.textContent = `${keywordMatch}%`;
            if (keywordProgress) keywordProgress.textContent = `${keywordMatch}%`;
            updateProgressBarColor('keywordProgress', keywordMatch);
            
            // Update job match section if job description provided
            if (jobDescription && jobDescription.trim()) {
                const jobMatch = calculateJobMatch(foundKeywords, missingKeywords);
                if (jobMatchProgress) {
                    jobMatchProgress.style.width = `${jobMatch}%`;
                    jobMatchProgress.textContent = `${jobMatch}%`;
                }
                const jobMatchSection = document.getElementById('jobMatchSection');
                if (jobMatchSection) jobMatchSection.classList.remove('d-none');
                updateProgressBarColor('jobMatchProgress', jobMatch);
            } else {
                const jobMatchSection = document.getElementById('jobMatchSection');
                if (jobMatchSection) jobMatchSection.classList.add('d-none');
            }
            
            // Display found and missing keywords
            displayKeywords(foundKeywords, missingKeywords);
            
            // Display key findings
            displayKeyFindings(data.keyFindings || []);
            
            // Display quick improvements
            displayQuickImprovements(data.improvements || []);
            
            // Update content analysis based on received data
            updateContentAnalysis(data);
        } catch (error) {
            console.error('Error displaying analysis results:', error);
            // Show a fallback message with suggestions
            initialMessage.classList.remove('d-none');
            loadingMessage.classList.add('d-none');
            resultsContainer.classList.add('d-none');
            scoreDisplay.classList.add('d-none');
            
            initialMessage.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    There was an issue displaying your ATS analysis results: ${error.message}
                </div>
                <div class="mt-3">
                    <h5>General Resume Improvement Tips:</h5>
                    <ul class="list-group">
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Add more industry-specific keywords to your resume</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Ensure your resume has clear section headings</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Quantify your achievements with numbers and metrics</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Include a skills section with both technical and soft skills</li>
                        <li class="list-group-item"><i class="bi bi-lightbulb me-2 text-warning"></i>Use a clean, ATS-friendly format without complex tables or graphics</li>
                    </ul>
                </div>
            `;
        }
    }
    
    // Display keywords found and missing in the resume
    function displayKeywords(foundKeywords, missingKeywords) {
        // Clear existing content
        keywordsFound.innerHTML = '';
        keywordsMissing.innerHTML = '';
        
        // Add found keywords
        if (foundKeywords && foundKeywords.length > 0) {
            foundKeywords.forEach(keyword => {
                const keywordElement = document.createElement('span');
                keywordElement.className = 'badge bg-success me-2 mb-2';
                keywordElement.textContent = keyword;
                keywordsFound.appendChild(keywordElement);
            });
        } else {
            keywordsFound.innerHTML = '<p class="text-muted">No keywords detected</p>';
        }
        
        // Add missing keywords
        if (missingKeywords && missingKeywords.length > 0) {
            missingKeywords.forEach(keyword => {
                const keywordElement = document.createElement('span');
                keywordElement.className = 'badge bg-secondary me-2 mb-2';
                keywordElement.textContent = keyword;
                keywordsMissing.appendChild(keywordElement);
            });
        } else {
            keywordsMissing.innerHTML = '<p class="text-muted">No missing keywords detected</p>';
        }
    }
    
    // Display key findings from analysis
    function displayKeyFindings(findings) {
        // Clear existing content
        keyFindings.innerHTML = '';
        
        if (findings && findings.length > 0) {
            findings.forEach(finding => {
                addFinding(finding.type, finding.text);
            });
        } else {
            // Default findings if none provided
            addFinding('info', 'Resume analysis complete');
            addFinding('info', 'See detailed results in each tab');
        }
    }
    
    // Display quick improvements
    function displayQuickImprovements(improvements) {
        // Clear existing content
        quickImprovements.innerHTML = '';
        
        console.log('Improvements data:', improvements);
        
        // Create an unordered list for improvements
        const ul = document.createElement('ul');
        ul.className = 'list-group';
        quickImprovements.appendChild(ul);
        
        if (improvements && improvements.length > 0) {
            // Use the provided improvements
            improvements.forEach(improvement => {
                const li = document.createElement('li');
                li.className = 'list-group-item list-group-item-action';
                li.innerHTML = `<i class="bi bi-lightbulb me-2 text-warning"></i>${improvement}`;
                ul.appendChild(li);
            });
        } else {
            // Default improvements if none provided
            const defaultImprovements = [
                'Add more industry-specific keywords to your resume to improve ATS matching',
                'Ensure your resume has clear section headings (Summary, Experience, Education, Skills)',
                'Quantify your achievements with numbers and metrics where possible',
                'Include a skills section with both technical and soft skills',
                'Make sure your contact information is clearly visible at the top of your resume',
                'Use a clean, ATS-friendly format without complex tables or graphics'
            ];
            
            defaultImprovements.forEach(improvement => {
                const li = document.createElement('li');
                li.className = 'list-group-item list-group-item-action';
                li.innerHTML = `<i class="bi bi-lightbulb me-2 text-warning"></i>${improvement}`;
                ul.appendChild(li);
            });
        }
    }
    
    // Calculate job match percentage based on keywords
    function calculateJobMatch(foundKeywords, missingKeywords) {
        const totalKeywords = foundKeywords.length + missingKeywords.length;
        if (totalKeywords === 0) return 50; // Default value
        
        const matchPercentage = Math.round((foundKeywords.length / totalKeywords) * 100);
        return matchPercentage;
    }
    
    // Generate key findings based on resume analysis with more accurate insights
    function generateKeyFindings(score, resumeData) {
        keyFindings.innerHTML = '';
        
        // Get job description for contextual findings
        const jobDescription = document.getElementById('jobDescription').value;
        const isJobSpecific = jobDescription.trim().length > 0;
        
        // Add score-based findings with more nuanced insights
        if (score < 70) {
            addFinding('warning', 'Your resume may be filtered out by ATS screening systems.');
            addFinding('warning', 'Critical ATS optimization issues were detected.');
            if (isJobSpecific) {
                addFinding('warning', 'Low relevance to the job description provided.');
            }
        } else if (score < 80) {
            addFinding('info', 'Your resume is partially ATS-optimized but needs improvement.');
            addFinding('warning', 'Some formatting and keyword issues may affect ATS parsing.');
            if (isJobSpecific) {
                addFinding('info', 'Moderate relevance to the job description provided.');
            }
        } else if (score < 90) {
            addFinding('info', 'Your resume is ATS-friendly with some room for improvement.');
            addFinding('success', 'Good use of industry-standard formatting and keywords.');
            if (isJobSpecific) {
                addFinding('success', 'Good relevance to the job description provided.');
            }
        } else {
            addFinding('success', 'Your resume is highly optimized for ATS systems.');
            addFinding('success', 'Excellent keyword usage, formatting and structure.');
            if (isJobSpecific) {
                addFinding('success', 'Excellent match to the job description provided.');
            }
        }
        
        // Add format findings with specific explanations
        if (!resumeData.format.hasProperHeadings) {
            addFinding('warning', 'Missing clear section headings (e.g., "Experience", "Education", "Skills") that ATS systems look for.');
        }
        
        if (!resumeData.format.hasBulletPoints) {
            addFinding('warning', 'Use bullet points for experience descriptions - they improve ATS parsing and readability.');
        }
        
        if (resumeData.format.usesTables) {
            addFinding('warning', 'Tables detected - many ATS systems cannot properly parse table structures. Use standard formatting instead.');
        }
        
        if (resumeData.format.hasImages) {
            addFinding('warning', 'Images, graphics, or charts detected - these are invisible to ATS systems and waste valuable space.');
        }
        
        if (resumeData.format.margins === 'too narrow') {
            addFinding('info', 'Margins appear too narrow - this can cause text to be cut off when scanned by some ATS systems.');
        }
        
        // Add content-specific findings
        if (!resumeData.content.hasMeasurableResults) {
            addFinding('info', 'Add quantifiable achievements with numbers (e.g., "Increased sales by 25%") to strengthen your experience section.');
        }
        
        if (!resumeData.content.usesActionVerbs) {
            addFinding('info', 'Use more action verbs (e.g., "implemented," "developed," "managed") to powerfully describe your contributions.');
        }
        
        if (!resumeData.content.hasDates) {
            addFinding('warning', 'Missing employment dates in your experience section. All roles should include month/year format.');
        }
        
        if (resumeData.content.spelling < 95) {
            addFinding('warning', 'Possible spelling errors detected. Even minor errors can significantly reduce your chances of an interview.');
        }
        
        if (resumeData.content.density === 'too dense') {
            addFinding('info', 'Content appears too dense. Increase white space and use bullets to improve readability.');
        }
        
        // Add section-specific findings
        if (!resumeData.sections.summary) {
            addFinding('info', 'Adding a tailored professional summary with relevant keywords would improve ATS matching.');
        }
        
        if (!resumeData.sections.projects && (resumeData.experience.years < 3)) {
            addFinding('info', 'For early-career professionals, adding a projects section can demonstrate skills when experience is limited.');
        }
        
        if (!resumeData.sections.certifications && isJobSpecific) {
            // Check if job description mentions certifications
            if (jobDescription.toLowerCase().includes('certif')) {
                addFinding('info', 'The job mentions certifications. Adding a certifications section could improve your match rate.');
            }
        }
        
        // Add keyword findings with specific metrics
        const keywordCount = resumeData.keywords.length;
        const missingKeywordCount = resumeData.missingKeywords.length;
        
        if (keywordCount < 10) {
            addFinding('warning', `Low keyword density detected (${keywordCount} keywords). Industry average is 15-20 for most roles.`);
        } else if (keywordCount > 25) {
            addFinding('info', `High keyword count detected (${keywordCount}). Ensure they are used naturally to avoid being flagged for keyword stuffing.`);
        }
        
        if (isJobSpecific && missingKeywordCount > 5) {
            addFinding('warning', `Missing ${missingKeywordCount} relevant keywords from the job description.`);
        }
        
        // Update resume metadata display
        document.getElementById('detectedName').textContent = resumeData.name || 'Not detected';
        document.getElementById('contactInfo').textContent = 
            `${resumeData.email ? 'Email' : 'No email'}, ${resumeData.phone ? 'Phone' : 'No phone'} detected`;
        document.getElementById('fileFormat').textContent = resumeData.fileFormat || 'Unknown';
        document.getElementById('wordCount').textContent = resumeData.wordCount || '0';
    }
    
    function addFinding(type, text) {
        const iconClass = {
            'success': 'bi-check-circle-fill text-success',
            'warning': 'bi-exclamation-triangle-fill text-warning',
            'info': 'bi-info-circle-fill text-info',
            'danger': 'bi-x-circle-fill text-danger'
        };
        
        const li = document.createElement('li');
        li.innerHTML = `<i class="bi ${iconClass[type]}"></i> ${text}`;
        keyFindings.appendChild(li);
    }
    
    function generateKeywords() {
        // Clear containers
        keywordsFound.innerHTML = '';
        keywordsMissing.innerHTML = '';
        suggestedKeywords.innerHTML = '';
        
        // Sample keywords for demo
        const foundKeywords = [
            'JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 
            'API Integration', 'Agile', 'Git', 'Problem Solving'
        ];
        
        const missingKeywords = [
            'TypeScript', 'Redux', 'AWS', 'Docker', 'CI/CD',
            'Unit Testing', 'MongoDB'
        ];
        
        const suggestedKeywordsList = [
            'Full Stack Development', 'RESTful APIs', 'Microservices',
            'Jest', 'Webpack', 'Performance Optimization'
        ];
        
        // Add found keywords
        foundKeywords.forEach(keyword => {
            const span = document.createElement('span');
            span.className = 'keyword keyword-found';
            span.textContent = keyword;
            keywordsFound.appendChild(span);
        });
        
        // Add missing keywords
        missingKeywords.forEach(keyword => {
            const span = document.createElement('span');
            span.className = 'keyword keyword-missing';
            span.textContent = keyword;
            keywordsMissing.appendChild(span);
        });
        
        // Add suggested keywords
        suggestedKeywordsList.forEach(keyword => {
            const span = document.createElement('span');
            span.className = 'keyword keyword-suggested';
            span.textContent = keyword;
            suggestedKeywords.appendChild(span);
        });
    }
    
    function generateQuickImprovements() {
        quickImprovements.innerHTML = '';
        
        const improvements = [
            'Add more industry-specific keywords like "TypeScript", "Redux", and "AWS" to increase your match rate.',
            'Quantify your achievements with metrics and numbers to stand out (e.g., "Increased performance by 40%").',
            'Ensure your job titles align with industry standards for better ATS recognition.'
        ];
        
        improvements.forEach(improvement => {
            const li = document.createElement('li');
            li.textContent = improvement;
            quickImprovements.appendChild(li);
        });
    }
    
    function updateContentAnalysis(resumeData) {
        // Update detected information with actual data
        document.getElementById('detectedName').textContent = resumeData.name || 'Not detected';
        
        // Check what contact info was found
        const contactTypes = [];
        if (resumeData.email) contactTypes.push('Email');
        if (resumeData.phone) contactTypes.push('Phone');
        if (resumeData.linkedin) contactTypes.push('LinkedIn');
        if (resumeData.website) contactTypes.push('Website');
        
        document.getElementById('contactInfo').textContent = contactTypes.length > 0 ? 
            contactTypes.join(', ') + ' detected' : 'No contact information detected';
        
        document.getElementById('fileFormat').textContent = resumeFile.files[0].type.includes('pdf') ? 'PDF' : 'Word Document';
        document.getElementById('wordCount').textContent = resumeData.wordCount || '~450';
        
        // Calculate section scores based on resume data
        const contactScore = calculateContactScore(resumeData);
        const experienceScore = calculateExperienceScore(resumeData);
        const educationScore = calculateEducationScore(resumeData);
        const skillsScore = calculateSkillsScore(resumeData);
        
        // Update progress bars
        document.getElementById('contactProgress').style.width = `${contactScore}%`;
        document.getElementById('contactProgress').textContent = `${contactScore}%`;
        document.getElementById('contactProgress').setAttribute('aria-valuenow', contactScore);
        
        document.getElementById('experienceProgress').style.width = `${experienceScore}%`;
        document.getElementById('experienceProgress').textContent = `${experienceScore}%`;
        document.getElementById('experienceProgress').setAttribute('aria-valuenow', experienceScore);
        
        document.getElementById('educationProgress').style.width = `${educationScore}%`;
        document.getElementById('educationProgress').textContent = `${educationScore}%`;
        document.getElementById('educationProgress').setAttribute('aria-valuenow', educationScore);
        
        document.getElementById('skillsProgress').style.width = `${skillsScore}%`;
        document.getElementById('skillsProgress').textContent = `${skillsScore}%`;
        document.getElementById('skillsProgress').setAttribute('aria-valuenow', skillsScore);
        
        // Update progress bar colors
        updateProgressBarColor('contactProgress', contactScore);
        updateProgressBarColor('experienceProgress', experienceScore);
        updateProgressBarColor('educationProgress', educationScore);
        updateProgressBarColor('skillsProgress', skillsScore);
        
        // Update feedback text based on actual resume content
        if (skillsScore < 60) {
            document.getElementById('skillsFeedback').textContent = 
                'Your skills section needs improvement. Consider adding more industry-specific technical skills and organizing them by category.';
        } else if (skillsScore < 80) {
            document.getElementById('skillsFeedback').textContent = 
                'Your skills section is good but could be enhanced by adding more keywords relevant to your target industry.';
        } else {
            document.getElementById('skillsFeedback').textContent = 
                'Your skills section is well-structured and includes a good range of technical and soft skills.';
        }
        
        // Experience feedback based on actual content
        if (experienceScore < 70) {
            document.getElementById('experienceFeedback').textContent = 
                'Your experience section could be improved by adding more quantifiable achievements and using more action verbs at the beginning of bullet points.';
        } else if (experienceScore < 85) {
            document.getElementById('experienceFeedback').textContent = 
                'Your experience section is good but could benefit from more specific metrics and achievements.';
        } else {
            document.getElementById('experienceFeedback').textContent = 
                'Your experience section effectively highlights your achievements with good use of action verbs and metrics.';
        }
        
        // Education feedback
        if (educationScore < 70) {
            document.getElementById('educationFeedback').textContent = 
                'Your education section needs more details such as GPA, relevant coursework, or academic achievements.';
        } else {
            document.getElementById('educationFeedback').textContent = 
                'Your education section is well-structured and includes relevant details.';
        }
        
        // Contact info feedback
        if (contactScore < 80) {
            document.getElementById('contactFeedback').textContent = 
                'Some contact information appears to be missing or not properly formatted.';
        } else {
            document.getElementById('contactFeedback').textContent = 
                'Your contact information is complete and well-formatted.';
        }
    }
    
    function updateProgressBarColor(elementId, score) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        // Remove existing color classes
        element.classList.remove('bg-success', 'bg-warning', 'bg-danger');
        
        // Add appropriate color class based on score
        if (score >= 80) {
            element.classList.add('bg-success');
        } else if (score >= 60) {
            element.classList.add('bg-warning');
        } else {
            element.classList.add('bg-danger');
        }
    }
    
    /**
     * Calculate contact information score based on resume data
     */
    function calculateContactScore(resumeData) {
        // Default score if no data is available
        if (!resumeData) return 70;
        
        let score = 0;
        
        // Check for email
        if (resumeData.contact && resumeData.contact.email && resumeData.contact.email !== 'Not detected') {
            score += 40;
        } else if (resumeData.email && resumeData.email !== 'Not detected') {
            score += 40;
        }
        
        // Check for phone
        if (resumeData.contact && resumeData.contact.phone && resumeData.contact.phone !== 'Not detected') {
            score += 40;
        } else if (resumeData.phone && resumeData.phone !== 'Not detected') {
            score += 40;
        }
        
        // Check for LinkedIn or other social profiles
        if (resumeData.linkedin || (resumeData.contact && resumeData.contact.linkedin)) {
            score += 10;
        }
        
        // Check for website or portfolio
        if (resumeData.website || (resumeData.contact && resumeData.contact.website)) {
            score += 10;
        }
        
        // Ensure score is between 0-100
        return Math.min(100, Math.max(50, score));
    }
    
    /**
     * Calculate experience section score based on resume data
     */
    function calculateExperienceScore(resumeData) {
        // Default score if no data is available
        if (!resumeData) return 70;
        
        let score = 60; // Base score
        
        // Check if experience section exists
        if (resumeData.sections && resumeData.sections.experience) {
            score += 10;
        }
        
        // Check if experience entries exist
        if (resumeData.experience) {
            score += 10;
            
            // If experience is an array and has entries
            if (Array.isArray(resumeData.experience) && resumeData.experience.length > 0) {
                score += 10;
                
                // Bonus for multiple experiences
                if (resumeData.experience.length > 1) {
                    score += 10;
                }
            }
        }
        
        // Ensure score is between 0-100
        return Math.min(100, Math.max(50, score));
    }
    
    /**
     * Calculate education section score based on resume data
     */
    function calculateEducationScore(resumeData) {
        // Default score if no data is available
        if (!resumeData) return 70;
        
        let score = 60; // Base score
        
        // Check if education section exists
        if (resumeData.sections && resumeData.sections.education) {
            score += 15;
        }
        
        // Check if education entries exist
        if (resumeData.education) {
            score += 15;
            
            // If education is an array and has entries
            if (Array.isArray(resumeData.education) && resumeData.education.length > 0) {
                score += 10;
            }
        }
        
        // Ensure score is between 0-100
        return Math.min(100, Math.max(50, score));
    }
    
    /**
     * Calculate skills section score based on resume data
     */
    function calculateSkillsScore(resumeData) {
        // Default score if no data is available
        if (!resumeData) return 70;
        
        let score = 60; // Base score
        
        // Check if skills section exists
        if (resumeData.sections && resumeData.sections.skills) {
            score += 10;
        }
        
        // Check if skills exist
        const skills = [];
        
        // Get skills from different possible locations in the data structure
        if (resumeData.skills && Array.isArray(resumeData.skills)) {
            skills.push(...resumeData.skills);
        } else if (resumeData.keywords && resumeData.keywords.found) {
            skills.push(...resumeData.keywords.found);
        }
        
        // Score based on number of skills
        if (skills.length >= 15) {
            score += 30;
        } else if (skills.length >= 10) {
            score += 20;
        } else if (skills.length >= 5) {
            score += 10;
        }
        
        // Ensure score is between 0-100
        return Math.min(100, Math.max(50, score));
    }
    
    // Resume Text Extraction using PDF.js and text analysis
    async function extractResumeText(file) {
        // Show a loading indicator while processing
        document.getElementById('loadingMessage').querySelector('p').textContent = 'Analyzing your resume... (Step 1/3: Extracting text)';
        
        return new Promise((resolve) => {
            // In a production app, we would use PDF.js or docx-parser to extract text
            // This is an improved extraction simulation with more reliable data
            
            const fileReader = new FileReader();
            
            fileReader.onload = function() {
                console.log("File loaded for ATS analysis");
                
                // In a real implementation, we'd extract text from the file and analyze it
                // Here we're using a more realistic simulation of what would be extracted
                
                const resumeData = {
                    name: 'Extracted Name',
                    email: 'extracted.email@example.com',
                    phone: '(555) 123-4567',
                    fileFormat: file.type === 'application/pdf' ? 'PDF' : 'Word',
                    wordCount: Math.floor(Math.random() * 300) + 400, // 400-700 words
                    sections: {
                        summary: Math.random() > 0.2, // 80% chance of having a summary
                        experience: true, // Always have experience
                        education: true,  // Always have education
                        skills: true,     // Always have skills
                        projects: Math.random() > 0.4, // 60% chance of having projects
                        certifications: Math.random() > 0.6 // 40% chance of having certifications
                    },
                    keywords: [],
                    missingKeywords: [],
                    format: {
                        hasProperHeadings: Math.random() > 0.1, // 90% chance
                        hasBulletPoints: Math.random() > 0.2,   // 80% chance
                        fontConsistency: Math.floor(Math.random() * 20) + 80, // 80-100%
                        usesTables: Math.random() > 0.7,  // 30% chance
                        hasImages: Math.random() > 0.9,   // 10% chance
                        margins: Math.random() > 0.2 ? 'appropriate' : 'too narrow', // 80% chance
                        fileSize: file.size
                    },
                    content: {
                        hasMeasurableResults: Math.random() > 0.4, // 60% chance
                        usesActionVerbs: Math.random() > 0.3,      // 70% chance
                        hasDates: Math.random() > 0.1,             // 90% chance
                        spelling: Math.floor(Math.random() * 15) + 85, // 85-100%
                        grammar: Math.floor(Math.random() * 15) + 85,  // 85-100%
                        density: Math.random() > 0.3 ? 'good' : 'too dense' // 70% chance
                    },
                    experience: {
                        years: Math.floor(Math.random() * 10) + 1, // 1-10 years
                        relevance: Math.floor(Math.random() * 30) + 70, // 70-100%
                        roles: [
                            'Software Engineer', 
                            'Web Developer', 
                            'Data Analyst', 
                            'Project Manager', 
                            'UX Designer'
                        ].sort(() => Math.random() - 0.5).slice(0, Math.floor(Math.random() * 3) + 1)
                    },
                    education: {
                        degree: ['Bachelor of Science', 'Master of Science', 'Bachelor of Arts'][Math.floor(Math.random() * 3)],
                        field: ['Computer Science', 'Information Technology', 'Engineering', 'Business'][Math.floor(Math.random() * 4)],
                        gpa: (Math.random() * 1.5 + 2.5).toFixed(1) // 2.5-4.0
                    }
                };
                
                // Generate industry-specific keywords based on common job requirements
                const allKeywords = [
                    // Technical skills
                    'JavaScript', 'React', 'Angular', 'Vue.js', 'Node.js', 'Python', 'Java', 'C#', 'C++',
                    'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'PHP', 'Ruby', 'Rails',
                    'HTML5', 'CSS3', 'SASS', 'LESS', 'Responsive Design', 'Bootstrap', 'Material UI',
                    'Git', 'GitHub', 'GitLab', 'CI/CD', 'Jenkins', 'Docker', 'Kubernetes', 'AWS', 'Azure',
                    'GCP', 'Cloud Architecture', 'Microservices', 'RESTful APIs', 'GraphQL', 'Redux',
                    'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch', 'Natural Language Processing',
                    'Computer Vision', 'Deep Learning', 'Artificial Intelligence', 'Big Data', 'Hadoop',
                    'Spark', 'Data Visualization', 'Power BI', 'Tableau', 'R', 'MATLAB',
                    
                    // Soft skills
                    'Project Management', 'Agile', 'Scrum', 'Kanban', 'JIRA', 'Confluence',
                    'Team Leadership', 'Communication', 'Problem Solving', 'Critical Thinking',
                    'Time Management', 'Collaboration', 'Customer Service', 'Presentation Skills',
                    'Research', 'Documentation', 'Technical Writing', 'Client Relations'
                ];
                
                // Randomly select keywords that are "found" in the resume (12-18)
                resumeData.keywords = allKeywords.sort(() => Math.random() - 0.5).slice(0, Math.floor(Math.random() * 6) + 12);
                
                // Randomly select keywords that are "missing" from the resume (5-10)
                resumeData.missingKeywords = allKeywords
                    .filter(keyword => !resumeData.keywords.includes(keyword))
                    .sort(() => Math.random() - 0.5)
                    .slice(0, Math.floor(Math.random() * 5) + 5);
                
                // Add job-specific keywords if job description is provided
                const jobDescription = document.getElementById('jobDescription').value;
                if (jobDescription.trim()) {
                    // For this demo, we'll extract words that appear to be skills or technologies
                    const words = jobDescription.match(/\b[A-Za-z][A-Za-z0-9+#-\.]+\b/g) || [];
                    const potentialKeywords = words.filter(word => {
                        return word.length > 3 && 
                               !['and', 'the', 'for', 'with', 'this', 'that', 'our', 'your'].includes(word.toLowerCase());
                    });
                    
                    // Add some of these to missing keywords
                    const jobKeywords = [...new Set(potentialKeywords)].slice(0, 8);
                    for (const keyword of jobKeywords) {
                        if (!resumeData.keywords.includes(keyword) && Math.random() > 0.3) {
                            resumeData.missingKeywords.push(keyword);
                        }
                    }
                }
                
                resolve(resumeData);
            };
            
            // Start reading the file as text
            if (file.type === 'application/pdf') {
                // For PDF, we'd typically use PDF.js, but here we're just simulating
                fileReader.readAsArrayBuffer(file);
            } else {
                // For Word docs, we'd use a docx parser
                fileReader.readAsText(file);
            }
        });
    }
    
    // Calculate overall ATS score based on resume data with improved accuracy
    function calculateATSScore(resumeData) {
        // Calculate individual component scores
        const contactScore = calculateContactScore(resumeData);
        const formatScore = calculateFormatScore(resumeData);
        const contentScore = calculateContentScore(resumeData);
        const keywordScore = calculateKeywordScore(resumeData);
        const experienceScore = calculateExperienceScore(resumeData);
        const educationScore = calculateEducationScore(resumeData);
        
        // Get job description for more accurate scoring
        const jobDescription = document.getElementById('jobDescription').value;
        let jobRelevanceMultiplier = 1.0;
        
        // If job description is provided, adjust scoring based on job relevance
        if (jobDescription.trim()) {
            // Check how well the resume keywords match job description
            const jobKeywords = extractKeywordsFromJobDescription(jobDescription);
            const matchingKeywords = resumeData.keywords.filter(keyword => 
                jobKeywords.some(jobKeyword => 
                    jobKeyword.toLowerCase().includes(keyword.toLowerCase()) || 
                    keyword.toLowerCase().includes(jobKeyword.toLowerCase())
                )
            );
            
            // Calculate relevance as a percentage of matching keywords
            const relevancePercentage = jobKeywords.length > 0 ? 
                (matchingKeywords.length / jobKeywords.length) : 0.5;
            
            // Adjust multiplier based on relevance (range: 0.8 to 1.2)
            jobRelevanceMultiplier = 0.8 + (relevancePercentage * 0.4);
        }
        
        // Weight the scores with more realistic weightings
        const weightedScore = (
            contactScore * 0.05 +       // Less important
            formatScore * 0.20 +        // Very important for ATS parsing
            contentScore * 0.25 +       // Important for humans reading the resume
            keywordScore * 0.30 +       // Most important for ATS matching
            experienceScore * 0.15 +    // Important for qualification
            educationScore * 0.05       // Less important for most roles
        ) * jobRelevanceMultiplier;
        
        // Return a more nuanced score (65-95 range is more realistic)
        let finalScore = Math.round(weightedScore);
        
        // Constrain score to a realistic range
        finalScore = Math.max(65, Math.min(finalScore, 95));
        
        return finalScore;
    }
    
    // Extract keywords from job description
    function extractKeywordsFromJobDescription(jobDescription) {
        const commonWords = new Set([
            'and', 'the', 'of', 'to', 'a', 'in', 'for', 'is', 'on', 'that', 'by', 
            'this', 'with', 'you', 'it', 'not', 'or', 'be', 'are', 'from', 'at', 'as', 
            'your', 'have', 'more', 'an', 'was', 'we', 'will', 'can', 'all', 'about',
            'our', 'which', 'their', 'has', 'would', 'what', 'they', 'if', 'when', 'up',
            'there', 'so', 'out', 'into', 'than', 'them', 'only', 'no', 'over', 'just',
            'may', 'should', 'such', 'where', 'each', 'its', 'these', 'does', 'do', 'how',
            'been', 'were', 'those', 'any', 'some', 'could', 'my', 'who', 'without'
        ]);
        
        // Extract words that look like skills, technologies, or job requirements
        const words = jobDescription.match(/\b[A-Za-z][A-Za-z0-9+#-\.]+\b/g) || [];
        
        // Filter out common words and short words
        const keywords = words.filter(word => {
            return word.length > 3 && 
                   !commonWords.has(word.toLowerCase()) &&
                   isNaN(word); // Filter out numbers
        });
        
        // Return unique keywords
        return [...new Set(keywords)];
    }
    
    // Calculate contact information score
    function calculateContactScore(resumeData) {
        let score = 0;
        
        // Check for essential contact information
        if (resumeData.name) score += 25;
        if (resumeData.email) score += 25;
        if (resumeData.phone) score += 25;
        if (resumeData.linkedin || resumeData.website) score += 25;
        
        return score;
    }
    
    // Calculate format score
    function calculateFormatScore(resumeData) {
        let score = 60; // Base score
        
        // Add points for good formatting
        if (resumeData.format) {
            if (resumeData.format.hasProperHeadings) score += 10;
            if (resumeData.format.hasBulletPoints) score += 10;
            if (resumeData.format.hasConsistentFormatting) score += 10;
            if (resumeData.format.hasProperSpacing) score += 5;
            if (!resumeData.format.hasImages) score += 5; // No images is better for ATS
        }
        
        return Math.min(score, 100); // Cap at 100
    }
    
    // Calculate content score
    function calculateContentScore(resumeData) {
        let score = 50; // Base score
        
        // Check for essential sections
        if (resumeData.sections) {
            if (resumeData.sections.summary) score += 10;
            if (resumeData.sections.experience) score += 10;
            if (resumeData.sections.education) score += 10;
            if (resumeData.sections.skills) score += 10;
            if (resumeData.sections.projects) score += 5;
        }
        
        // Check experience quality
        if (resumeData.experience && resumeData.experience.length > 0) {
            const hasMetrics = resumeData.experience.some(exp => exp.hasMetrics);
            const hasActionVerbs = resumeData.experience.some(exp => exp.hasActionVerbs);
            
            if (hasMetrics) score += 3;
            if (hasActionVerbs) score += 2;
        }
        
        return Math.min(score, 100); // Cap at 100
    }
    
    // Calculate keyword score
    function calculateKeywordScore(resumeData) {
        // Base score depends on number of skills
        let score = 60;
        
        if (resumeData.skills) {
            // More skills = higher score, up to a point
            if (resumeData.skills.length >= 5) score += 10;
            if (resumeData.skills.length >= 8) score += 10;
            if (resumeData.skills.length >= 12) score += 5;
            
            // Check for technical skills if it's a technical role
            const technicalRole = resumeData.jobTitle && (
                resumeData.jobTitle.toLowerCase().includes('developer') ||
                resumeData.jobTitle.toLowerCase().includes('engineer') ||
                resumeData.jobTitle.toLowerCase().includes('data') ||
                resumeData.jobTitle.toLowerCase().includes('tech')
            );
            
            if (technicalRole) {
                const technicalSkills = ['javascript', 'python', 'java', 'c#', 'c++', 
                                        'react', 'angular', 'vue', 'node', 'aws', 'azure',
                                        'sql', 'nosql', 'mongodb', 'docker', 'kubernetes'];
                
                const hasTechnicalSkills = resumeData.skills.some(skill => 
                    technicalSkills.includes(skill.toLowerCase())
                );
                
                if (hasTechnicalSkills) score += 15;
            }
        }
        
        return Math.min(score, 100); // Cap at 100
    }
    
    // Calculate experience score
    function calculateExperienceScore(resumeData) {
        let score = 60; // Base score
        
        if (resumeData.experience && resumeData.experience.length > 0) {
            // More experience entries = higher score
            if (resumeData.experience.length >= 2) score += 10;
            if (resumeData.experience.length >= 3) score += 5;
            
            // Check for quality indicators
            let qualityScore = 0;
            resumeData.experience.forEach(exp => {
                if (exp.hasMetrics) qualityScore += 5;
                if (exp.hasActionVerbs) qualityScore += 5;
                if (exp.bullets && exp.bullets >= 3) qualityScore += 5;
            });
            
            score += Math.min(qualityScore, 25); // Cap quality bonus at 25 points
        }
        
        return Math.min(score, 100); // Cap at 100
    }
    
    // Calculate education score
    function calculateEducationScore(resumeData) {
        let score = 70; // Base score
        
        if (resumeData.education && resumeData.education.length > 0) {
            // Check for quality indicators
            resumeData.education.forEach(edu => {
                if (edu.hasGPA) score += 10;
                if (edu.hasCourses) score += 10;
                if (edu.year) score += 5;
            });
        }
        
        return Math.min(score, 100); // Cap at 100
    }
    
    // Calculate job match percentage
    function calculateJobMatch(resumeData, jobDescription) {
        // In a real implementation, this would analyze the job description
        // and compare it with the resume content
        
        // For demo purposes, we'll return a simulated match percentage
        const jobDescLower = jobDescription.toLowerCase();
        let matchScore = 65; // Base score
        
        // Check if skills from resume appear in job description
        if (resumeData.skills) {
            let skillMatches = 0;
            resumeData.skills.forEach(skill => {
                if (jobDescLower.includes(skill.toLowerCase())) {
                    skillMatches++;
                }
            });
            
            // Add points based on percentage of skills that match
            const skillMatchPercentage = (skillMatches / resumeData.skills.length) * 100;
            matchScore += Math.min(skillMatchPercentage / 3, 25); // Max 25 points from skills
        }
        
        // Check if job title matches
        if (resumeData.jobTitle && jobDescLower.includes(resumeData.jobTitle.toLowerCase())) {
            matchScore += 10;
        }
        
        return Math.min(Math.round(matchScore), 100); // Cap at 100
    }
    
    // Generate suggested keywords from job description
    function generateSuggestedKeywords(resumeData, jobDescription) {
        // Clear container
        suggestedKeywords.innerHTML = '';
        
        // Common keywords by industry
        const commonKeywords = {
            tech: ['JavaScript', 'React', 'Node.js', 'Python', 'AWS', 'Cloud', 'API', 'Agile', 'CI/CD', 'Docker'],
            marketing: ['Digital Marketing', 'SEO', 'Social Media', 'Content Strategy', 'Analytics', 'Campaign Management'],
            finance: ['Financial Analysis', 'Accounting', 'Budgeting', 'Forecasting', 'Risk Management', 'Compliance'],
            healthcare: ['Patient Care', 'Electronic Health Records', 'HIPAA', 'Clinical', 'Medical', 'Healthcare'],
            general: ['Project Management', 'Leadership', 'Communication', 'Problem Solving', 'Team Collaboration']
        };
        
        // Extract potential keywords from job description
        const jobDescLower = jobDescription.toLowerCase();
        let suggestedKeywordsList = [];
        
        // Determine which industry keywords to check based on job description
        let relevantKeywords = [];
        if (jobDescLower.includes('developer') || jobDescLower.includes('engineer') || 
            jobDescLower.includes('software') || jobDescLower.includes('programming')) {
            relevantKeywords = relevantKeywords.concat(commonKeywords.tech);
        }
        
        if (jobDescLower.includes('market') || jobDescLower.includes('brand') || 
            jobDescLower.includes('content') || jobDescLower.includes('social media')) {
            relevantKeywords = relevantKeywords.concat(commonKeywords.marketing);
        }
        
        if (jobDescLower.includes('financ') || jobDescLower.includes('account') || 
            jobDescLower.includes('budget') || jobDescLower.includes('audit')) {
            relevantKeywords = relevantKeywords.concat(commonKeywords.finance);
        }
        
        if (jobDescLower.includes('health') || jobDescLower.includes('medical') || 
            jobDescLower.includes('patient') || jobDescLower.includes('clinical')) {
            relevantKeywords = relevantKeywords.concat(commonKeywords.healthcare);
        }
        
        // Always include general keywords
        relevantKeywords = relevantKeywords.concat(commonKeywords.general);
        
        // Filter out keywords that are already in the resume
        const resumeSkills = resumeData.skills ? resumeData.skills.map(skill => skill.toLowerCase()) : [];
        suggestedKeywordsList = relevantKeywords.filter(keyword => 
            jobDescLower.includes(keyword.toLowerCase()) && 
            !resumeSkills.includes(keyword.toLowerCase())
        );
        
        // Limit to 10 keywords
        suggestedKeywordsList = suggestedKeywordsList.slice(0, 10);
        
        // Add suggested keywords
        suggestedKeywordsList.forEach(keyword => {
            const span = document.createElement('span');
            span.className = 'keyword keyword-suggested';
            span.textContent = keyword;
            suggestedKeywords.appendChild(span);
        });
        
        // If no keywords were found, show a message
        if (suggestedKeywordsList.length === 0) {
            suggestedKeywords.innerHTML = '<p class="text-muted">No additional keywords suggested.</p>';
        }
    }
    
    // Generate keywords based on resume data
    function generateKeywords(resumeData) {
        // Clear containers
        keywordsFound.innerHTML = '';
        keywordsMissing.innerHTML = '';
        
        // Common industry keywords
        const industryKeywords = {
            tech: ['JavaScript', 'Python', 'Java', 'React', 'Angular', 'Node.js', 'AWS', 'Cloud', 'DevOps', 'CI/CD', 'Docker', 'Kubernetes', 'Agile', 'Scrum'],
            marketing: ['Digital Marketing', 'SEO', 'SEM', 'Social Media', 'Content Strategy', 'Analytics', 'Campaign Management', 'CRM', 'Email Marketing'],
            finance: ['Financial Analysis', 'Accounting', 'Budgeting', 'Forecasting', 'Risk Management', 'Compliance', 'Financial Reporting', 'Audit'],
            general: ['Project Management', 'Leadership', 'Communication', 'Problem Solving', 'Team Collaboration', 'Time Management', 'Critical Thinking']
        };
        
        // Determine industry based on job title or skills
        let relevantKeywords = [];
        const jobTitle = resumeData.jobTitle ? resumeData.jobTitle.toLowerCase() : '';
        
        if (jobTitle.includes('developer') || jobTitle.includes('engineer') || 
            jobTitle.includes('software') || jobTitle.includes('data')) {
            relevantKeywords = industryKeywords.tech;
        } else if (jobTitle.includes('market') || jobTitle.includes('brand') || 
                  jobTitle.includes('content') || jobTitle.includes('social')) {
            relevantKeywords = industryKeywords.marketing;
        } else if (jobTitle.includes('financ') || jobTitle.includes('account') || 
                  jobTitle.includes('budget') || jobTitle.includes('audit')) {
            relevantKeywords = industryKeywords.finance;
        } else {
            // Default to general keywords
            relevantKeywords = industryKeywords.general;
        }
        
        // Add found keywords from resume
        const foundKeywords = resumeData.skills || [];
        foundKeywords.forEach(keyword => {
            const span = document.createElement('span');
            span.className = 'keyword keyword-found';
            span.textContent = keyword;
            keywordsFound.appendChild(span);
        });
        
        // Add missing keywords (from relevant industry that aren't in resume)
        const resumeSkills = resumeData.skills ? resumeData.skills.map(skill => skill.toLowerCase()) : [];
        const missingKeywords = relevantKeywords.filter(keyword => 
            !resumeSkills.includes(keyword.toLowerCase())
        ).slice(0, 8); // Limit to 8 missing keywords
        
        missingKeywords.forEach(keyword => {
            const span = document.createElement('span');
            span.className = 'keyword keyword-missing';
            span.textContent = keyword;
            keywordsMissing.appendChild(span);
        });
    }
    
    // Generate key findings based on resume analysis
    function generateKeyFindings(score, resumeData) {
        keyFindings.innerHTML = '';
        
        // Add findings based on score and resume data
        if (score < 70) {
            addFinding('warning', 'Your resume may not pass ATS screening at many companies.');
            
            // Add specific findings based on resume data
            if (!resumeData.format || !resumeData.format.hasProperHeadings) {
                addFinding('warning', 'Standard section headings are missing or not easily recognized by ATS.');
            }
            
            if (resumeData.skills && resumeData.skills.length < 5) {
                addFinding('warning', 'Your resume contains too few keywords for ATS optimization.');
            }
            
            if (resumeData.format && resumeData.format.hasImages) {
                addFinding('warning', 'Images or graphics detected, which can interfere with ATS parsing.');
            }
            
            // Add detailed analysis findings
            if (resumeData.analysis) {
                if (resumeData.analysis.passiveVoice > 3) {
                    addFinding('warning', 'High use of passive voice detected. Use active voice for stronger impact.');
                }
                
                if (resumeData.analysis.spellingErrors > 0) {
                    addFinding('danger', `${resumeData.analysis.spellingErrors} spelling errors detected, which can significantly reduce ATS score.`);
                }
                
                if (resumeData.analysis.grammarIssues > 0) {
                    addFinding('danger', `${resumeData.analysis.grammarIssues} grammar issues detected, which can affect readability.`);
                }
                
                if (resumeData.analysis.dateFormat === 'inconsistent') {
                    addFinding('warning', 'Inconsistent date formatting detected. Standardize all dates (e.g., MM/YYYY).');
                }
                
                if (resumeData.analysis.bulletPointFormat === 'inconsistent') {
                    addFinding('warning', 'Inconsistent bullet point formatting detected. Standardize all bullet points.');
                }
                
                if (resumeData.analysis.actionVerbs && resumeData.analysis.actionVerbs.length < 3) {
                    addFinding('warning', 'Limited use of action verbs. Use more powerful action verbs to begin bullet points.');
                }
                
                if (!resumeData.analysis.metrics || resumeData.analysis.metrics.length === 0) {
                    addFinding('warning', 'No quantifiable achievements detected. Add metrics to demonstrate impact.');
                }
            }
        } else if (score < 85) {
            addFinding('info', 'Your resume is ATS-friendly but has room for improvement.');
            
            if (resumeData.format && resumeData.format.hasProperHeadings) {
                addFinding('success', 'Good use of industry-standard section headings.');
            }
            
            if (resumeData.experience && resumeData.experience.some(exp => !exp.hasMetrics)) {
                addFinding('info', 'Consider adding more quantifiable achievements to your experience section.');
            }
            
            if (resumeData.format && !resumeData.format.hasConsistentFormatting) {
                addFinding('warning', 'Inconsistent formatting detected, which may affect ATS parsing.');
            }
            
            // Add detailed analysis findings
            if (resumeData.analysis) {
                if (resumeData.analysis.passiveVoice > 0) {
                    addFinding('info', 'Some passive voice detected. Consider revising for stronger impact.');
                }
                
                if (resumeData.analysis.dateFormat === 'inconsistent') {
                    addFinding('info', 'Minor inconsistencies in date formatting. Standardize all dates for better parsing.');
                }
                
                if (resumeData.analysis.metrics && resumeData.analysis.metrics.length < 3) {
                    addFinding('info', 'Limited quantifiable achievements. Add more metrics to demonstrate impact.');
                }
            }
        } else {
            addFinding('success', 'Your resume is highly optimized for ATS systems.');
            addFinding('success', 'Excellent keyword usage and formatting.');
            
            if (resumeData.skills && resumeData.skills.length >= 8) {
                addFinding('success', 'Strong keyword density with relevant industry terms.');
            }
            
            if (resumeData.experience && resumeData.experience.every(exp => exp.hasMetrics)) {
                addFinding('success', 'Excellent use of metrics and achievements in experience section.');
            }
            
            // Add detailed analysis findings for high scores
            if (resumeData.analysis) {
                if (resumeData.analysis.actionVerbs && resumeData.analysis.actionVerbs.length >= 5) {
                    addFinding('success', 'Excellent use of varied action verbs throughout your experience section.');
                }
                
                if (resumeData.analysis.metrics && resumeData.analysis.metrics.length >= 3) {
                    addFinding('success', 'Strong use of quantifiable achievements to demonstrate impact.');
                }
                
                if (resumeData.analysis.passiveVoice === 0) {
                    addFinding('success', 'No passive voice detected. Active voice creates stronger impact.');
                }
                
                if (resumeData.analysis.spellingErrors === 0 && resumeData.analysis.grammarIssues === 0) {
                    addFinding('success', 'No spelling or grammar issues detected. Excellent proofreading.');
                }
            }
        }
        
        // Add common findings based on resume length
        if (resumeData.wordCount) {
            if (resumeData.wordCount < 300) {
                addFinding('info', 'Resume is quite short. Consider adding more details to key sections.');
            } else if (resumeData.wordCount > 700) {
                addFinding('info', 'Resume is on the longer side. Consider condensing for better readability.');
            } else {
                addFinding('success', 'Resume length is appropriate for your experience level.');
            }
        }
    }
    
    // Generate quick improvements based on resume analysis
    function generateQuickImprovements(resumeData, jobDescription) {
        quickImprovements.innerHTML = '';
        
        const improvements = [];
        
        // Check for missing keywords
        if (resumeData.skills && resumeData.skills.length < 8) {
            improvements.push('Add more industry-specific keywords to increase your match rate. Aim for at least 8-12 relevant skills.');
        }
        
        // Check for metrics in experience
        if (resumeData.experience && resumeData.experience.some(exp => !exp.hasMetrics)) {
            improvements.push('Quantify your achievements with metrics and numbers to stand out (e.g., "Increased performance by 40%").');
        }
        
        // Check for formatting issues
        if (resumeData.format) {
            if (!resumeData.format.hasProperHeadings) {
                improvements.push('Use standard section headings like "Experience," "Education," and "Skills" for better ATS recognition.');
            }
            
            if (!resumeData.format.hasConsistentFormatting) {
                improvements.push('Ensure consistent formatting throughout your resume (fonts, spacing, bullet points).');
            }
            
            if (resumeData.format.hasImages) {
                improvements.push('Remove images, graphics, and complex formatting that can interfere with ATS parsing.');
            }
        }
        
        // Add improvements based on detailed analysis
        if (resumeData.analysis) {
            if (resumeData.analysis.passiveVoice > 2) {
                improvements.push('Replace passive voice with active voice in your bullet points for stronger impact (e.g., "Was responsible for managing" → "Managed").');
            }
            
            if (resumeData.analysis.spellingErrors > 0) {
                improvements.push('Fix spelling errors in your resume. Even a single spelling mistake can significantly reduce your chances of getting an interview.');
            }
            
            if (resumeData.analysis.grammarIssues > 0) {
                improvements.push('Correct grammar issues in your resume. Proper grammar demonstrates attention to detail and professionalism.');
            }
            
            if (resumeData.analysis.dateFormat === 'inconsistent') {
                improvements.push('Standardize date formats throughout your resume (e.g., use "MM/YYYY" consistently) for better ATS parsing.');
            }
            
            if (resumeData.analysis.bulletPointFormat === 'inconsistent') {
                improvements.push('Ensure consistent bullet point formatting throughout your resume. Start each bullet with an action verb and maintain consistent punctuation.');
            }
            
            if (!resumeData.analysis.metrics || resumeData.analysis.metrics.length === 0) {
                improvements.push('Add specific metrics and numbers to quantify your achievements (e.g., "Increased sales by 30%" or "Managed a team of 15 developers").');
            }
            
            if (!resumeData.analysis.actionVerbs || resumeData.analysis.actionVerbs.length < 3) {
                improvements.push('Use more varied and powerful action verbs at the beginning of bullet points (e.g., "Spearheaded," "Orchestrated," "Transformed").');
            }
        }
        
        // Job description specific improvements
        if (jobDescription && jobDescription.trim()) {
            improvements.push('Tailor your resume keywords to match those in the job description for higher ATS match rates.');
            
            // Extract potential job title from job description
            const jobTitle = extractJobTitle(jobDescription);
            if (jobTitle && (!resumeData.jobTitle || !resumeData.jobTitle.toLowerCase().includes(jobTitle.toLowerCase()))) {
                improvements.push(`Consider aligning your job title with the target role ("${jobTitle}") to improve keyword matching.`);
            }
        }
        
        // Limit to top 5 most important improvements
        improvements.slice(0, 5).forEach(improvement => {
            const li = document.createElement('li');
            li.textContent = improvement;
            quickImprovements.appendChild(li);
        });
    }
    
    // Extract job title from job description
    function extractJobTitle(jobDescription) {
        // Common job title patterns
        const patterns = [
            /job title:\s*([\w\s]+)/i,
            /position:\s*([\w\s]+)/i,
            /role:\s*([\w\s]+)/i,
            /seeking\s+a?\s*([\w\s]+)/i,
            /hiring\s+a?\s*([\w\s]+)/i
        ];
        
        for (const pattern of patterns) {
            const match = jobDescription.match(pattern);
            if (match && match[1]) {
                return match[1].trim();
            }
        }
        
        // If no pattern matches, look for common job titles
        const commonTitles = [
            'Software Engineer', 'Software Developer', 'Frontend Developer', 'Backend Developer',
            'Full Stack Developer', 'Data Scientist', 'Data Analyst', 'Product Manager',
            'Project Manager', 'UX Designer', 'UI Designer', 'DevOps Engineer', 'QA Engineer',
            'Marketing Manager', 'Content Writer', 'Sales Representative', 'Financial Analyst'
        ];
        
        for (const title of commonTitles) {
            if (jobDescription.includes(title)) {
                return title;
            }
        }
        
        return null;
    }
});
