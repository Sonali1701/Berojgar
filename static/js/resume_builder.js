document.addEventListener('DOMContentLoaded', function() {
    // Template selection
    const templateCards = document.querySelectorAll('.template-card');
    const selectedTemplateText = document.getElementById('selected-template');
    const downloadButton = document.getElementById('download-resume');
    let selectedTemplate = '';

    // Tab navigation
    const nextButtons = document.querySelectorAll('.next-tab');
    const prevButtons = document.querySelectorAll('.prev-tab');
    
    // Add entry buttons
    const addEducationBtn = document.getElementById('add-education');
    const addExperienceBtn = document.getElementById('add-experience');
    const addProjectBtn = document.getElementById('add-project');
    
    // Generate resume button
    const generateResumeBtn = document.getElementById('generate-resume');
    
    // Resume preview container
    const resumePreview = document.getElementById('resume-preview');
    
    // Initialize Bootstrap tabs
    const resumeTabs = document.getElementById('resumeTabs');
    const tabList = [].slice.call(resumeTabs.querySelectorAll('button'));
    
    // Add input event listeners to all form fields for real-time preview updates
    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('input', function() {
            updateResumePreview();
        });
    });
    
    // Template selection
    templateCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove selected class from all cards
            templateCards.forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            this.classList.add('selected');
            this.classList.add('template-selected-animation');
            
            // Update selected template text
            selectedTemplate = this.dataset.template;
            selectedTemplateText.textContent = selectedTemplate.charAt(0).toUpperCase() + selectedTemplate.slice(1);
            
            // Enable download button
            downloadButton.disabled = false;
            
            // Update preview
            updateResumePreview();
            
            // Remove animation class after animation completes
            setTimeout(() => {
                this.classList.remove('template-selected-animation');
            }, 500);
        });
    });
    
    // Tab navigation
    nextButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Find current active tab
            const activeTab = document.querySelector('.tab-pane.active');
            const activeTabId = activeTab.id;
            
            // Find index of current tab
            const currentIndex = tabList.findIndex(tab => tab.getAttribute('aria-controls') === activeTabId);
            
            // Activate next tab if it exists
            if (currentIndex < tabList.length - 1) {
                const nextTab = tabList[currentIndex + 1];
                const tab = new bootstrap.Tab(nextTab);
                tab.show();
            }
            
            // Update preview
            updateResumePreview();
        });
    });
    
    prevButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Find current active tab
            const activeTab = document.querySelector('.tab-pane.active');
            const activeTabId = activeTab.id;
            
            // Find index of current tab
            const currentIndex = tabList.findIndex(tab => tab.getAttribute('aria-controls') === activeTabId);
            
            // Activate previous tab if it exists
            if (currentIndex > 0) {
                const prevTab = tabList[currentIndex - 1];
                const tab = new bootstrap.Tab(prevTab);
                tab.show();
            }
            
            // Update preview
            updateResumePreview();
        });
    });
    
    // Add education entry
    addEducationBtn.addEventListener('click', function() {
        const educationContainer = document.getElementById('education-container');
        const newEntry = document.createElement('div');
        newEntry.className = 'education-entry mb-4 p-3 border rounded';
        newEntry.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Degree</label>
                    <input type="text" class="form-control" name="degree[]" placeholder="Bachelor of Science in Computer Science">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Institution</label>
                    <input type="text" class="form-control" name="institution[]" placeholder="University of Technology">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Location</label>
                    <input type="text" class="form-control" name="eduLocation[]" placeholder="New York, NY">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Graduation Date</label>
                    <input type="text" class="form-control" name="graduationDate[]" placeholder="May 2022">
                </div>
                <div class="col-12">
                    <label class="form-label">Description (Optional)</label>
                    <textarea class="form-control" name="eduDescription[]" rows="2" placeholder="GPA: 3.8/4.0, Dean's List, Relevant coursework..."></textarea>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger mt-2 remove-entry">Remove</button>
        `;
        educationContainer.appendChild(newEntry);
        
        // Add event listener to remove button
        newEntry.querySelector('.remove-entry').addEventListener('click', function() {
            newEntry.remove();
            updateResumePreview();
        });
    });
    
    // Add experience entry
    addExperienceBtn.addEventListener('click', function() {
        const experienceContainer = document.getElementById('experience-container');
        const newEntry = document.createElement('div');
        newEntry.className = 'experience-entry mb-4 p-3 border rounded';
        newEntry.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Job Title</label>
                    <input type="text" class="form-control" name="expTitle[]" placeholder="Software Engineer">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Company</label>
                    <input type="text" class="form-control" name="company[]" placeholder="Tech Solutions Inc.">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Location</label>
                    <input type="text" class="form-control" name="expLocation[]" placeholder="San Francisco, CA">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Employment Period</label>
                    <input type="text" class="form-control" name="employmentPeriod[]" placeholder="Jan 2020 - Present">
                </div>
                <div class="col-12">
                    <label class="form-label">Responsibilities & Achievements</label>
                    <textarea class="form-control" name="expDescription[]" rows="4" placeholder="• Developed and maintained web applications using React and Node.js&#10;• Improved application performance by 40% through code optimization&#10;• Collaborated with cross-functional teams to deliver features on time"></textarea>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger mt-2 remove-entry">Remove</button>
        `;
        experienceContainer.appendChild(newEntry);
        
        // Add event listener to remove button
        newEntry.querySelector('.remove-entry').addEventListener('click', function() {
            newEntry.remove();
            updateResumePreview();
        });
    });
    
    // Add project entry
    addProjectBtn.addEventListener('click', function() {
        const projectContainer = document.getElementById('project-container');
        const newEntry = document.createElement('div');
        newEntry.className = 'project-entry mb-4 p-3 border rounded';
        newEntry.innerHTML = `
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Project Name</label>
                    <input type="text" class="form-control" name="projectName[]" placeholder="E-commerce Platform">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Technologies Used</label>
                    <input type="text" class="form-control" name="technologies[]" placeholder="React, Node.js, MongoDB, AWS">
                </div>
                <div class="col-12">
                    <label class="form-label">Project URL (Optional)</label>
                    <input type="url" class="form-control" name="projectUrl[]" placeholder="https://github.com/username/project">
                </div>
                <div class="col-12">
                    <label class="form-label">Description</label>
                    <textarea class="form-control" name="projectDescription[]" rows="3" placeholder="• Developed a full-stack e-commerce platform with user authentication and payment processing&#10;• Implemented responsive design and optimized for mobile devices&#10;• Integrated with third-party APIs for shipping and inventory management"></textarea>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger mt-2 remove-entry">Remove</button>
        `;
        projectContainer.appendChild(newEntry);
        
        // Add event listener to remove button
        newEntry.querySelector('.remove-entry').addEventListener('click', function() {
            newEntry.remove();
            updateResumePreview();
        });
    });
    
    // Add event listeners to initial remove buttons
    document.querySelectorAll('.remove-entry').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.education-entry, .experience-entry, .project-entry').remove();
            updateResumePreview();
        });
    });
    
    // Generate resume
    generateResumeBtn.addEventListener('click', function() {
        updateResumePreview();
        
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'alert alert-success mt-3';
        successMessage.innerHTML = '<strong>Success!</strong> Your resume has been generated. You can now download it.';
        
        // Add to DOM
        const formCard = document.querySelector('.card-body');
        formCard.insertBefore(successMessage, formCard.firstChild);
        
        // Remove after 5 seconds
        setTimeout(() => {
            successMessage.remove();
        }, 5000);
        
        // Scroll to preview
        document.getElementById('resume-preview').scrollIntoView({ behavior: 'smooth' });
    });
    
    // Download resume
    downloadButton.addEventListener('click', function() {
        const resumeContent = document.getElementById('resume-preview');
        
        // Configure html2pdf options
        const options = {
            margin: 10,
            filename: `${selectedTemplate}_resume.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };
        
        // Generate PDF
        html2pdf().set(options).from(resumeContent).save();
    });
    
    // Update resume preview based on form data
    function updateResumePreview() {
        if (!selectedTemplate) {
            resumePreview.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-file-earmark-text display-1 text-muted"></i>
                    <p class="mt-3">Select a template and fill in your details to see a preview of your resume</p>
                </div>
            `;
            return;
        }
        
        // Get form data
        const fullName = document.getElementById('fullName').value || 'Your Name';
        const jobTitle = document.getElementById('jobTitle').value || 'Professional Title';
        const email = document.getElementById('email').value || 'email@example.com';
        const phone = document.getElementById('phone').value || '(123) 456-7890';
        const location = document.getElementById('location').value || 'City, State';
        const website = document.getElementById('website').value || 'linkedin.com/in/yourprofile';
        const summary = document.getElementById('summary').value || 'Professional summary goes here...';
        
        // Get skills
        const technicalSkills = document.getElementById('technicalSkills').value || '';
        const softSkills = document.getElementById('softSkills').value || '';
        const languages = document.getElementById('languages').value || '';
        const certifications = document.getElementById('certifications').value || '';
        
        // Create skills HTML
        let skillsHtml = '';
        
        if (technicalSkills) {
            const techSkillsArray = technicalSkills.split(',').map(skill => skill.trim());
            skillsHtml += '<div class="mb-2"><strong>Technical Skills:</strong><div>';
            techSkillsArray.forEach(skill => {
                skillsHtml += `<span class="skill-badge technical-skill">${skill}</span>`;
            });
            skillsHtml += '</div></div>';
        }
        
        if (softSkills) {
            const softSkillsArray = softSkills.split(',').map(skill => skill.trim());
            skillsHtml += '<div class="mb-2"><strong>Soft Skills:</strong><div>';
            softSkillsArray.forEach(skill => {
                skillsHtml += `<span class="skill-badge soft-skill">${skill}</span>`;
            });
            skillsHtml += '</div></div>';
        }
        
        if (languages) {
            const languagesArray = languages.split(',').map(lang => lang.trim());
            skillsHtml += '<div class="mb-2"><strong>Languages:</strong><div>';
            languagesArray.forEach(lang => {
                skillsHtml += `<span class="skill-badge language-skill">${lang}</span>`;
            });
            skillsHtml += '</div></div>';
        }
        
        if (certifications) {
            skillsHtml += `<div class="mb-2"><strong>Certifications:</strong><div>${certifications}</div></div>`;
        }
        
        // Get education entries
        let educationHtml = '';
        const educationEntries = document.querySelectorAll('.education-entry');
        
        educationEntries.forEach(entry => {
            const degree = entry.querySelector('[name="degree[]"]').value || 'Degree';
            const institution = entry.querySelector('[name="institution[]"]').value || 'Institution';
            const eduLocation = entry.querySelector('[name="eduLocation[]"]').value || 'Location';
            const graduationDate = entry.querySelector('[name="graduationDate[]"]').value || 'Graduation Date';
            const eduDescription = entry.querySelector('[name="eduDescription[]"]').value || '';
            
            educationHtml += `
                <div class="mb-3">
                    <div><strong>${degree}</strong></div>
                    <div>${institution}, ${eduLocation}</div>
                    <div><em>${graduationDate}</em></div>
                    ${eduDescription ? `<div class="mt-1">${eduDescription}</div>` : ''}
                </div>
            `;
        });
        
        // Get experience entries
        let experienceHtml = '';
        const experienceEntries = document.querySelectorAll('.experience-entry');
        
        experienceEntries.forEach(entry => {
            const expTitle = entry.querySelector('[name="expTitle[]"]').value || 'Job Title';
            const company = entry.querySelector('[name="company[]"]').value || 'Company';
            const expLocation = entry.querySelector('[name="expLocation[]"]').value || 'Location';
            const employmentPeriod = entry.querySelector('[name="employmentPeriod[]"]').value || 'Employment Period';
            const expDescription = entry.querySelector('[name="expDescription[]"]').value || '';
            
            experienceHtml += `
                <div class="mb-3">
                    <div><strong>${expTitle}</strong></div>
                    <div>${company}, ${expLocation}</div>
                    <div><em>${employmentPeriod}</em></div>
                    ${expDescription ? `<div class="mt-1">${expDescription}</div>` : ''}
                </div>
            `;
        });
        
        // Get project entries
        let projectsHtml = '';
        const projectEntries = document.querySelectorAll('.project-entry');
        
        projectEntries.forEach(entry => {
            const projectName = entry.querySelector('[name="projectName[]"]').value || 'Project Name';
            const technologies = entry.querySelector('[name="technologies[]"]').value || 'Technologies';
            const projectUrl = entry.querySelector('[name="projectUrl[]"]').value || '';
            const projectDescription = entry.querySelector('[name="projectDescription[]"]').value || '';
            
            projectsHtml += `
                <div class="mb-3">
                    <div>
                        <strong>${projectName}</strong>
                        ${projectUrl ? `<a href="${projectUrl}" target="_blank" class="ms-2"><i class="bi bi-link-45deg"></i></a>` : ''}
                    </div>
                    <div><em>Technologies: ${technologies}</em></div>
                    ${projectDescription ? `<div class="mt-1">${projectDescription}</div>` : ''}
                </div>
            `;
        });
        
        // Generate resume HTML based on selected template
        let resumeHtml = `
            <div class="resume-template resume-${selectedTemplate}">
                <div class="resume-header">
                    <h2>${fullName}</h2>
                    <p>${jobTitle}</p>
                    <div class="d-flex flex-wrap justify-content-between">
                        <span><i class="bi bi-envelope"></i> ${email}</span>
                        <span><i class="bi bi-telephone"></i> ${phone}</span>
                        <span><i class="bi bi-geo-alt"></i> ${location}</span>
                        <span><i class="bi bi-link"></i> ${website}</span>
                    </div>
                </div>
                
                <div class="resume-section">
                    <h3 class="resume-section-title">Summary</h3>
                    <p>${summary}</p>
                </div>
                
                <div class="resume-section">
                    <h3 class="resume-section-title">Skills</h3>
                    ${skillsHtml}
                </div>
                
                <div class="resume-section">
                    <h3 class="resume-section-title">Experience</h3>
                    ${experienceHtml || '<p>No experience added yet.</p>'}
                </div>
                
                <div class="resume-section">
                    <h3 class="resume-section-title">Education</h3>
                    ${educationHtml || '<p>No education added yet.</p>'}
                </div>
                
                <div class="resume-section">
                    <h3 class="resume-section-title">Projects</h3>
                    ${projectsHtml || '<p>No projects added yet.</p>'}
                </div>
            </div>
        `;
        
        // Update preview
        resumePreview.innerHTML = resumeHtml;
    }
});
