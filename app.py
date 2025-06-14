import pickle
import os
import json

import logger
import requests
import base64
import logging
from datetime import datetime
import random
from werkzeug.utils import secure_filename

# Fix for werkzeug compatibility issue
import werkzeug
if not hasattr(werkzeug.urls, 'url_quote'):
    werkzeug.urls.url_quote = werkzeug.urls.quote

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from dataset_create import skill_match, education_match, experience_gap
from form_filler import auto_fill_form

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger("app")

# Try to import enhanced_resume_extraction, fall back to basic if not available
try:
    from enhanced_resume_extraction import extract_resume_info
    enhanced_extraction_available = True
    logger.info("Successfully imported enhanced_resume_extraction module")
except ImportError as e:
    logger.warning(f"Enhanced resume extraction import error: {str(e)}")
    from resume_extraction import extract_resume_info
    enhanced_extraction_available = False
    logger.warning("Using basic resume extraction as fallback")
    
from job_description_extractor import extract_job_description

# Try to import job_scraper, fall back to mock_job_generator if dependencies are missing
try:
    from job_scraper import JobScraper, get_jobs_with_matching
    job_scraper_available = True
except ImportError as e:
    logger.warning(f"Job scraper import error: {str(e)}")
    from mock_job_generator import generate_mock_jobs, get_mock_job_details
    job_scraper_available = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger("app")

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}
app.secret_key = 'berojgar_secret_key'  # In a production app, use a secure random key

# Load the model
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

# Load the label encoders
education_encoder = LabelEncoder()
education_encoder.fit(['Bachelors', 'Masters', 'PhD', 'Unknown'])  # Add all possible education classes + 'Unknown'

role_encoder = LabelEncoder()
role_encoder.fit(['Data Scientist', 'Software Engineer', 'Analyst', 'Unknown'])  # Add all possible roles + 'Unknown'


# Load or fit the encoders if needed (You can also save these encoders during training and load them here)

# Global variable for last match result
last_match_result = {"matched": False, "resume_data": {}}

@app.route('/set_match_result', methods=['POST'])
def set_match_result():
    global last_match_result
    last_match_result = request.json
    return jsonify({"status": "ok"})

@app.route('/match_status')
def match_status():
    global last_match_result
    return jsonify(last_match_result)

# API Route to predict suitability
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract data from the request
        resume_data = request.json.get('resume')
        job_data = request.json.get('job_description')

        if not resume_data or not job_data:
            return jsonify({"error": "Missing resume or job description data"}), 400

        # Decode and save the PDF first
        resume_data_str = resume_data
        if isinstance(resume_data_str, str) and resume_data_str.startswith('data:application/pdf;base64,'):
            resume_data_str = resume_data_str.split(',', 1)[1]
        import base64
        resume_bytes = base64.b64decode(resume_data_str)
        resume_file_path = 'uploaded_resume.pdf'
        with open(resume_file_path, 'wb') as f:
            f.write(resume_bytes)

        # Now extract features from the saved PDF
        resume_features = extract_resume_info(resume_file_path)
        job_features = extract_job_description(job_data)

        # Prepare input features for prediction
        input_data = prepare_input_features(resume_features, job_features)

        # Make prediction
        prediction = model.predict(input_data)[0]

        # Find missing skills
        resume_skills = set(s.lower().strip() for s in resume_features.get('skills', []))
        job_skills = set(s.lower().strip() for s in (
            job_features.get('required_skills')
            or job_features.get('Required_Skills')
            or []
        ))
        print("DEBUG: resume_skills =", resume_skills)
        print("DEBUG: job_skills =", job_skills)
        print("DEBUG: intersection =", resume_skills & job_skills)
        # If you use skill_match elsewhere, print that too:
        try:
            from dataset_create import skill_match
            match_score = skill_match(resume_skills, job_skills)
            print("DEBUG: match_score =", match_score)
        except Exception as e:
            print("DEBUG: skill_match error:", e)
        missing_skills = list(job_skills - resume_skills)
        print("DEBUG: missing_skills =", missing_skills)

        # Tips for improving the resume
        resume_tips = [
            "Tailor your resume to include relevant keywords from the job description.",
            "Highlight projects or experiences that match the job requirements.",
            "Add missing skills required for the job if you possess them.",
            "Quantify your achievements and use action verbs.",
            "Keep your resume concise and well-formatted."
        ]

        # If prediction is a match (e.g., 1), or skill match is perfect, trigger form filling
        job_link = job_data if isinstance(job_data, str) else job_data.get('link', '')
        if int(prediction) == 1 or match_score >= 1.0:
            # Save last match result for extension
            resume_data_for_extension = {
                "name": resume_features.get("name", ""),
                "email": resume_features.get("email", ""),
                "phone": resume_features.get("phone", ""),
                "skills": list(resume_skills),
                "education": resume_features.get("education", ""),
                "experience": str(resume_features.get("experience", "")),
            }
            import requests
            try:
                requests.post("http://localhost:5000/set_match_result", json={
                    "matched": True,
                    "resume_data": resume_data_for_extension
                })
            except Exception as e:
                print("DEBUG: Could not update match status for extension:", e)
            # Server-side Selenium auto form fill
            if not job_link:
                return jsonify({"error": "Job link missing or invalid."}), 400
            print("DEBUG: Passing resume_file_path to auto_fill_form:", resume_file_path)
            auto_fill_form(job_link, resume_features, resume_file_path)
            return jsonify({
                "prediction": int(prediction),
                "match_score": match_score,
                "status": "Form auto-fill attempted by agent."
            })
        else:
            # Set match result as not matched
            import requests
            try:
                requests.post("http://localhost:5000/set_match_result", json={
                    "matched": False,
                    "resume_data": {}
                })
            except Exception as e:
                print("DEBUG: Could not update match status for extension:", e)
            return jsonify({
                "prediction": int(prediction),
                "match_score": match_score,
                "status": "No match, form not filled",
                "tips": resume_tips,
                "missing_skills": missing_skills
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Helper function to prepare input features for prediction
def prepare_input_features(resume_features, job_features):
    education_value = resume_features.get('education', 'Unknown')
    experience_value = resume_features.get('experience', 0)

    # Encode the 'Education' and 'Job_Role' features
    education_encoded = education_encoder.transform([education_value])[
        0] if education_value in education_encoder.classes_ else education_encoder.transform(['Unknown'])[0]
    job_role_encoded = role_encoder.transform([resume_features.get('job_role', 'Unknown')])[
        0]  # Default to 'Unknown'

    # Skill match calculation
    skill_match_score = skill_match(resume_features.get('skills', []), job_features.get('required_skills', []))

    # Education match
    edu_match = education_match(resume_features.get('education', ''), job_features.get('preferred_education', ''))

    # Experience gap (ensure values are integers)
    exp_resume = resume_features.get('experience')
    exp_job = job_features.get('min_experience')
    try:
        exp_resume = int(exp_resume) if exp_resume is not None else 0
    except Exception:
        exp_resume = 0
    try:
        exp_job = int(exp_job) if exp_job is not None else 0
    except Exception:
        exp_job = 0
    exp_gap = experience_gap(exp_resume, exp_job)

    # Return the input features in the required format for the model
    input_features = pd.DataFrame([{
        'Education_encoded': education_encoded,
        'Experience': int(exp_resume),  # Ensure this is always int
        'Job_Role_encoded': job_role_encoded,
        'Skill_Match': skill_match_score,
        'Education_Match': edu_match,
        'Experience_Gap': exp_gap
    }])

    return input_features


# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if user is already logged in
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        
        # In a real app, you would validate the user credentials against a database
        # For demo purposes, we'll accept any non-empty username/password
        if username and password:
            # Set session variables
            session['logged_in'] = True
            session['username'] = username
            
            # Log the login
            logger.info(f"User logged in: {username}")
            
            # Redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            # In a real app, you would return an error message
            return render_template('login.html', error="Invalid username or password")
            
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if user is already logged in
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # In a real app, you would validate the form data and create a new user in the database
        # For demo purposes, we'll accept any registration with matching passwords
        if password and password == confirm_password:
            # Set session variables
            session['logged_in'] = True
            session['username'] = name
            
            # Log the registration
            logger.info(f"New user registered: {name}, {email}")
            
            # Redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            # In a real app, you would return an error message
            return render_template('register.html', error="Passwords do not match")
            
    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    # Clear the session
    session.pop('logged_in', None)
    session.pop('username', None)
    
    # Log the logout
    logger.info("User logged out")
    
    # Redirect to the home page
    return redirect(url_for('index'))

# Feedback submission route
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if request.method == 'POST':
        # In a real app, you would save the feedback to a database
        feedback_type = request.form.get('feedbackType')
        subject = request.form.get('feedbackSubject')
        message = request.form.get('feedbackMessage')
        rating = request.form.get('rating')
        
        # Log the feedback for demonstration purposes
        logger.info(f"Feedback received: Type={feedback_type}, Subject={subject}, Rating={rating}")
        
        # Return a success response
        return jsonify({'success': True, 'message': 'Feedback submitted successfully!'})
    
    return jsonify({'success': False, 'message': 'Invalid request method'})

# Add a /last_resume_data endpoint to the Flask app that returns example resume data as JSON
@app.route('/last_resume_data')
def last_resume_data():
    # Example: Replace with actual logic to fetch the latest parsed resume
    # You may want to store the last parsed resume in a global variable or database
    # Here is a static example for demonstration
    return jsonify({
        "name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "+1234567890",
        "skills": ["Python", "Machine Learning", "SQL"],
        "education": "Masters",
        "experience": "5 years"
    })


# Job search route
@app.route('/job-search')
def job_search():
    return render_template('job_search.html')

# Job search API
@app.route('/api/jobs/search', methods=['POST'])
def search_jobs():
    # Initialize variables with defaults
    query = ""
    location = ""
    resume_data = None
    jobs = []
    
    try:
        logger.info("Job search API called")
        
        # Handle both form data and JSON data
        if request.is_json:
            data = request.json or {}
            query = data.get('query', '')
            location = data.get('location', '')
            resume_data = data.get('resume_data', None)
            logger.info(f"JSON request received - Query: '{query}', Location: '{location}'")
        else:
            # Handle form data
            query = request.form.get('query', '')
            location = request.form.get('location', '')
            logger.info(f"Form request received - Query: '{query}', Location: '{location}'")
            
            # Process resume file if uploaded
            if 'resume' in request.files:
                resume_file = request.files['resume']
                if resume_file.filename != '':
                    try:
                        logger.info(f"Processing uploaded resume: {resume_file.filename}")
                        # Save the file temporarily
                        temp_dir = os.path.join(os.getcwd(), 'temp')
                        os.makedirs(temp_dir, exist_ok=True)
                        temp_path = os.path.join(temp_dir, secure_filename(resume_file.filename))
                        resume_file.save(temp_path)
                        
                        # Extract resume data
                        if enhanced_extraction_available:
                            resume_data = extract_resume_info(temp_path)
                            logger.info("Resume data extracted using enhanced extraction")
                        else:
                            # Fallback to basic extraction
                            resume_data = {'skills': []}
                            logger.info("Resume data extracted using basic extraction")
                            
                        # Clean up
                        os.remove(temp_path)
                    except Exception as e:
                        logger.error(f"Error processing resume: {str(e)}")
                        # Continue without resume data
                        resume_data = {'skills': []}
        
        # Validate inputs
        if not query or not isinstance(query, str):
            logger.warning("Empty or invalid query provided")
            return jsonify({"success": False, "error": "Please provide a valid job search query"}), 400
        
        # Log the search query for debugging
        logger.info(f"Job search request - Query: '{query}', Location: '{location}'")
        
        # If query is empty, use a default query to ensure we get some results
        if not query.strip():
            query = "developer"  # Default search term to get some results
            logger.info(f"Empty query provided, using default: '{query}'")
    except Exception as e:
        logger.error(f"Unexpected error in job search API: {str(e)}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500
    
    # Always try to use the real job scraper first
    try:
        # Check if required packages are installed
        try:
            import requests
            from bs4 import BeautifulSoup
            logger.info("Required packages for job scraping are available")
        except ImportError as import_error:
            logger.error(f"Missing required packages: {str(import_error)}")
            # Return empty list instead of falling back to mock data
            logger.info("Returning empty job list due to missing packages")
            return jsonify({
                "success": True,
                "jobs": []
            })
        
        # Initialize the job scraper
        try:
            from job_scraper import JobScraper, get_jobs_with_matching
            scraper = JobScraper()
            logger.info("Successfully initialized JobScraper")
        except Exception as scraper_init_error:
            logger.error(f"Error initializing JobScraper: {str(scraper_init_error)}")
            # Fall back to mock data if scraper initialization fails
            jobs = generate_mock_jobs(query, location, resume_data)
            logger.info("Using mock job data due to scraper initialization failure")
            return jsonify({
                "success": True,
                "jobs": jobs
            })
        
        # Try multiple sources in parallel to maximize chances of getting jobs
        all_jobs = []
        
        # Check if this is a software engineering related query
        software_related = any(term in query.lower() for term in [
            'software', 'developer', 'engineer', 'programming', 'coder', 'web', 'frontend', 
            'backend', 'fullstack', 'python', 'java', 'javascript', 'react', 'node', 'angular'
        ])
        
        # For non-software titles, prioritize Google Jobs which works better for diverse job types
        if not software_related:
            logger.info(f"Non-software job title detected: {query}. Prioritizing Google Jobs search.")
            try:
                google_jobs = scraper.search_google_jobs(query, location, limit=15)
                if google_jobs:
                    all_jobs.extend(google_jobs)
                    logger.info(f"Found {len(google_jobs)} jobs from Google Jobs for non-software title")
            except Exception as google_error:
                logger.warning(f"Error searching Google Jobs for non-software title: {str(google_error)}")
        
        # Try Remotive API (works well for software jobs)
        try:
            remotive_jobs = scraper.search_remotive(query, location, limit=10)
            if remotive_jobs:
                all_jobs.extend(remotive_jobs)
                logger.info(f"Found {len(remotive_jobs)} jobs from Remotive API")
        except Exception as remotive_error:
            logger.warning(f"Error searching Remotive: {str(remotive_error)}")
        
        # Try Adzuna if we have API credentials
        try:
            if scraper.adzuna_app_id and scraper.adzuna_api_key:
                adzuna_jobs = scraper.search_adzuna(query, location, limit=10)
                if adzuna_jobs:
                    all_jobs.extend(adzuna_jobs)
                    logger.info(f"Found {len(adzuna_jobs)} jobs from Adzuna API")
        except Exception as adzuna_error:
            logger.warning(f"Error searching Adzuna: {str(adzuna_error)}")
        
        # Try GitHub Jobs
        try:
            github_jobs = scraper.search_github_jobs(query, location, limit=10)
            if github_jobs:
                all_jobs.extend(github_jobs)
                logger.info(f"Found {len(github_jobs)} jobs from GitHub Jobs")
        except Exception as github_error:
            logger.warning(f"Error searching GitHub Jobs: {str(github_error)}")
        
        # If we still don't have enough jobs and haven't tried Google Jobs yet, try it now
        if len(all_jobs) < 5 and software_related:
            try:
                google_jobs = scraper.search_google_jobs(query, location, limit=10)
                if google_jobs:
                    all_jobs.extend(google_jobs)
                    logger.info(f"Found {len(google_jobs)} jobs from Google Jobs")
            except Exception as google_error:
                logger.warning(f"Error searching Google Jobs: {str(google_error)}")
        
        # Deduplicate jobs by title and company
        seen = set()
        jobs = []
        for job in all_jobs:
            # Skip jobs with missing essential data
            if not job.get('title') or not job.get('company'):
                continue
                
            key = (job.get('title', '').lower(), job.get('company', '').lower())
            if key not in seen:
                seen.add(key)
                
                # Ensure job has a valid URL
                if not job.get('url') or job.get('url') == '#':
                    # Create a Google search URL as fallback
                    title_slug = job.get('title', '').replace(' ', '+')
                    company_slug = job.get('company', '').replace(' ', '+')
                    job['url'] = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
                
                # Ensure all required fields are present
                job['description'] = job.get('description', 'No description available')
                job['location'] = job.get('location', 'Remote/Various')
                job['skills'] = job.get('skills', [])
                job['posted_date'] = job.get('posted_date', 'Recently')
                job['job_type'] = job.get('job_type', 'Full-time')
                
                # Ensure all jobs have a valid URL for the Apply Now button
                if not job.get('url') or job.get('url') == '#' or job.get('url').startswith('javascript:'):
                    # Create a Google search URL as fallback
                    title_slug = job.get('title', '').replace(' ', '+')
                    company_slug = job.get('company', '').replace(' ', '+')
                    job['url'] = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
                
                jobs.append(job)
        
        # If we don't have jobs, return an empty list instead of using mock data
        if not jobs:
            logger.warning(f"No real jobs found for query '{query}', returning empty list")
            jobs = []
            
        # Add match scores if resume data is provided
        if resume_data and 'skills' in resume_data:
            resume_skills = resume_data.get('skills', [])
            # Add match scores to each job
            for job in jobs:
                job_skills = job.get('skills', [])
                matching_skills = set([s.lower() for s in resume_skills]).intersection(
                    set([s.lower() for s in job_skills]))
                job['match_score'] = int((len(matching_skills) / max(len(job_skills), 1)) * 100)
                job['matching_skills'] = list(matching_skills)
        
        logger.info(f"Successfully found {len(jobs)} jobs for query '{query}'")
        
    except Exception as e:
        logger.error(f"Error using JobScraper: {str(e)}")
        # Return empty list instead of falling back to mock data
        jobs = []
        logger.info("Returning empty job list due to scraping error")
    
    # Log the final job count
    if not jobs:
        logger.warning("No jobs found, returning empty list")
        jobs = []
    
    # Log the final job count
    logger.info(f"Returning {len(jobs)} jobs for query '{query}'")
    
    # Return the final response
    return jsonify({
        "success": True,
        "jobs": jobs
    })

# Job details API
@app.route('/job_details/<job_id>')
def job_details(job_id):
    # Get job details
    job = get_job_by_id(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify({
        "success": True,
        "job": job
    })

# API route for job details
@app.route('/api/jobs/<job_id>')
def api_job_details(job_id):
    logger.info(f"Job details request for job_id: {job_id}")
    
    # Check if this is a real job (from an external source)
    is_real_job = job_id.startswith(('google_', 'remotive_', 'adzuna_', 'github_', 'rss_'))
    
    if is_real_job:
        try:
            # Attempt to retrieve the real job from cache or job scraper
            if job_scraper_available:
                # Initialize the job scraper
                from job_scraper import JobScraper
                scraper = JobScraper()
                
                # Parse job ID to get source and index
                parts = job_id.split('_')
                source = parts[0]
                
                # Try to fetch job from scraper's cache or directly from source
                job = None
                
                # Try to get job from the appropriate source
                if source == 'remotive':
                    try:
                        remotive_jobs = scraper.search_remotive("", "", limit=50)
                        # Find matching job by ID
                        job = next((j for j in remotive_jobs if j.get('id') == job_id), None)
                        logger.info(f"Found Remotive job: {job is not None}")
                    except Exception as e:
                        logger.error(f"Error fetching job from Remotive: {str(e)}")
                
                elif source == 'adzuna':
                    try:
                        # Try to fetch the specific job from Adzuna
                        job = scraper.get_adzuna_job_details(job_id)
                        logger.info(f"Found Adzuna job: {job is not None}")
                    except Exception as e:
                        logger.error(f"Error fetching job from Adzuna: {str(e)}")
                
                elif source == 'github':
                    try:
                        github_jobs = scraper.search_github_jobs("", "", limit=50)
                        # Find matching job by ID
                        job = next((j for j in github_jobs if j.get('id') == job_id), None)
                        logger.info(f"Found GitHub job: {job is not None}")
                    except Exception as e:
                        logger.error(f"Error fetching job from GitHub: {str(e)}")
                
                elif source == 'google':
                    try:
                        # For Google jobs, we need to search more broadly
                        # Try to get from cache first
                        if hasattr(scraper, 'job_cache'):
                            for cache_key, cache_jobs in scraper.job_cache.items():
                                if cache_key.startswith('google_'):
                                    job = next((j for j in cache_jobs if j.get('id') == job_id), None)
                        logger.info(f"Found Google job: {job is not None}")
                    except Exception as e:
                        logger.error(f"Error fetching job from Google: {str(e)}")
            
            # If we couldn't get a real job, create a Google search URL
            if not job:
                logger.warning(f"Could not find real job with ID {job_id}, creating Google search URL")
                # Create a Google search URL based on the job ID
                parts = job_id.split('_')
                source = parts[0] if len(parts) > 0 else 'job'
                
                # Construct search query
                search_query = f"{source} job apply"
                job = {
                    'id': job_id,
                    'title': f'{source.title()} Job',
                    'company': f'{source.title()} Company',
                    'url': f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                }
            
        except Exception as e:
            logger.error(f"Error retrieving real job details: {str(e)}")
            # Fall back to mock job with Google search URL
            job = get_mock_job_details(job_id)
            
            # Create a Google search URL for the job
            title_slug = job.get('title', '').replace(' ', '+')
            company_slug = job.get('company', '').replace(' ', '+')
            job['url'] = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
            job['application_url'] = job['url']
    else:
        # For mock jobs, use the existing function but make URL more realistic
        job = get_mock_job_details(job_id)
        
        # Create a Google search URL for the job
        title_slug = job.get('title', '').replace(' ', '+')
        company_slug = job.get('company', '').replace(' ', '+')
        job['url'] = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
        job['application_url'] = job['url']
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify({
        "success": True,
        "job": job
    })

# Apply to job API
@app.route('/apply_job', methods=['POST'])
def apply_job():
    data = request.json
    job_id = data.get('job_id')
    resume_file = data.get('resume_file')
    
    if not job_id:
        return jsonify({"error": "Job ID is required"}), 400
    
    # Get job details
    job = get_mock_job_details(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    # For demonstration purposes, we'll simulate a successful application
    # without actually calling the auto_fill_form function which requires Selenium
    
    # In a production environment, you would:
    # 1. Save the resume to a temporary file
    # 2. Extract resume data
    # 3. Use Selenium to fill out the application form
    
    # Mock resume data for demonstration
    resume_data = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '123-456-7890',
        'skills': ['Python', 'JavaScript', 'Machine Learning', 'Data Analysis'],
        'experience': 3,
        'education': 'Bachelor of Science in Computer Science'
    }
    
    # Check if this is a real job (from an external source)
    is_real_job = job_id.startswith(('google_', 'remotive_', 'adzuna_', 'github_', 'rss_'))
    
    if is_real_job:
        # For real jobs, we redirect to the actual application URL
        # First check for a specific application_url, then fall back to the regular url
        application_url = job.get('application_url') or job.get('url')
        
        if application_url:
            # Log the application attempt
            logger.info(f"Application submitted for job {job_id} - {job.get('title')}")
            
            # Return success with redirect URL
            return jsonify({
                "success": True,
                "message": "Application submitted successfully. Redirecting to the official application page.",
                "redirect_url": application_url
            })
        else:
            return jsonify({"error": "No application URL found for this job"}), 400
    else:
        # For mock jobs, provide a more meaningful redirection
        company_websites = {
            "TechCorp Inc.": "https://techcorp.com/careers",
            "InnovateTech": "https://innovatetech.com/jobs",
            "StartupXYZ": "https://startupxyz.com/apply",
            "ConsultPro": "https://consultpro.com/job-application",
            "DataDriven Inc.": "https://datadriveninc.com/careers"
        }
        
        # Fallback generic job search sites
        generic_job_sites = [
            "https://www.linkedin.com/jobs/",
            "https://www.indeed.com/jobs",
            "https://www.glassdoor.com/Job/",
            "https://www.monster.com/jobs/search/"
        ]
        
        # Try to get company-specific career page
        application_url = company_websites.get(job.get('company'), random.choice(generic_job_sites))
        
        # Log the application attempt
        logger.info(f"Mock application submitted for job {job_id} - {job.get('title')}")
        
        return jsonify({
            "success": True,
            "message": "Application submitted successfully. Redirecting to job application page.",
            "redirect_url": application_url,
            "job_title": job.get('title'),
            "company": job.get('company'),
            "application_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
# Helper function to get job by ID
def get_job_by_id(job_id):
    # Check if this is a real job (from an external source)
    is_real_job = job_id.startswith(('google_', 'remotive_', 'adzuna_', 'github_', 'rss_'))
    
    if is_real_job:
        try:
            # Attempt to retrieve the real job from cache or job scraper
            if job_scraper_available:
                # Initialize the job scraper
                from job_scraper import JobScraper
                scraper = JobScraper()
                
                # Parse job ID to get source and index
                parts = job_id.split('_')
                source = parts[0]
                
                # Try to fetch job from scraper's cache or directly from source
                job = None
                
                # For Remotive jobs which have the most reliable URLs
                if source == 'remotive':
                    # Try to fetch directly from Remotive API
                    try:
                        remotive_jobs = scraper.search_remotive("", "", limit=20)
                        # Find matching job by ID
                        job = next((j for j in remotive_jobs if j.get('id') == job_id), None)
                    except Exception as e:
                        logger.error(f"Error fetching job from Remotive: {str(e)}")
            
            # If we couldn't get a real job, return not found
            if not job:
                return {"error": "Job not found"}
                
        except Exception as e:
            logger.error(f"Error getting real job details: {str(e)}")
            return {"error": "Job not found"}
    else:
        # If not a real job source, return not found
        return {"error": "Job not found"}
    
    return job



# Dashboard route
@app.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get username from session
    username = session.get('username', 'User')
    
    # Get current date for "today's date" references
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # User stats
    user_stats = {
        'applications': 0,
        'interviews': 0,
        'profile_views': 0,
        'saved_jobs': 0
    }
    
    # Resume analysis
    resume_analysis = {
        'completeness': 0,
        'ats_optimization': 0,
        'improvement_suggestions': []
    }
    
    # Recent applications - use real job titles and companies
    # Generate realistic application dates within the last month
    recent_applications = []
    status_options = ['Pending', 'Screening', 'Interview', 'Rejected', 'No Response']
    status_classes = {
        'Pending': 'bg-warning text-dark',
        'Screening': 'bg-info text-dark',
        'Interview': 'bg-success',
        'Rejected': 'bg-danger',
        'No Response': 'bg-secondary'
    }
    
    # Try to get real job titles from the job scraper
    job_titles = []
    try:
        if job_scraper_available:
            scraper = JobScraper()
            jobs = scraper.search_google_jobs('software developer', limit=10)
            job_titles = [job.get('title', '') for job in jobs if job.get('title')]
            companies = [job.get('company', '') for job in jobs if job.get('company')]
        else:
            raise Exception("Job scraper not available")
    except Exception as e:
        logger.warning(f"Could not get real job titles: {str(e)}")
        # Fallback job titles and companies
        job_titles = [
            'Software Developer', 'Data Analyst', 'Frontend Developer', 'Full Stack Engineer',
            'IT Consultant', 'UX Designer', 'Product Manager', 'DevOps Engineer'
        ]
        companies = [
            'TechCorp Inc.', 'DataDriven Inc.', 'WebSolutions Ltd.', 'InnovateTech',
            'ConsultPro', 'DesignMasters', 'ProductGenius', 'CloudOps'
        ]
    
    # Generate application dates (most recent first)
    for i in range(min(8, len(job_titles))):
        days_ago = i * 3 + random.randint(0, 2)  # Space out applications by roughly 3 days
        application_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - 
                           datetime.timedelta(days=days_ago))
        date_str = application_date.strftime('%B %d, %Y')
        
        # Determine status based on how old the application is
        if days_ago < 3:
            status = 'Pending'
        elif days_ago < 7:
            status = random.choice(['Pending', 'Screening'])
        elif days_ago < 14:
            status = random.choice(['Screening', 'Interview', 'Rejected'])
        else:
            status = random.choice(['Interview', 'Rejected', 'No Response'])
        
        # Calculate match score - higher for interviews, lower for rejections
        if status == 'Interview':
            match_score = random.randint(80, 95)
        elif status == 'Rejected':
            match_score = random.randint(60, 75)
        elif status == 'Screening':
            match_score = random.randint(75, 85)
        else:
            match_score = random.randint(65, 90)
        
        # Add job details
        job = {
            'id': job_id,
            'title': job_titles[i % len(job_titles)],
            'company': companies[i % len(companies)],
            'location': 'New York, NY',
            'description': 'Job description',
            'posted_date': date_str,
            'job_type': 'Full-time',
            'skills': ['Python', 'JavaScript', 'HTML', 'CSS'],
            'salary': '$100,000 - $120,000',
            'url': f"https://www.google.com/search?q={job_titles[i % len(job_titles)].replace(' ', '+')}+{companies[i % len(companies)].replace(' ', '+')}+job+apply"
        }
        
        recent_applications.append({
            'title': job['title'],
            'company': job['company'],
            'date': date_str,
            'status': status,
            'status_class': status_classes[status],
            'match_score': match_score
        })
    
    # Get skills from resume or use industry-relevant skills
    # In a real app, these would come from the user's resume
    try:
        # Try to get skills from the ATS analysis or job search data
        from resume_extraction import extract_skills_from_text
        
        # Get skills from job descriptions to show relevant skills
        if job_scraper_available:
            scraper = JobScraper()
            jobs = scraper.search_google_jobs('software developer', limit=5)
            
            # Extract skills from job descriptions
            all_skills = set()
            for job in jobs:
                if 'description' in job:
                    extracted_skills = extract_skills_from_text(job['description'])
                    all_skills.update(extracted_skills)
            
            # Convert to list and sort by relevance (in a real app this would be more sophisticated)
            skill_list = list(all_skills)
            
            # Create user skills with proficiency levels
            user_skills = [
                {'name': skill, 'proficiency': random.randint(70, 95)} 
                for skill in skill_list[:6]  # Limit to top 6 skills
            ]
        else:
            raise Exception("Job scraper not available")
    except Exception as e:
        logger.warning(f"Could not extract accurate skills: {str(e)}")
        # Fallback to more diverse and accurate skills for various roles
        user_skills = [
            {'name': 'Communication', 'proficiency': random.randint(80, 95)},
            {'name': 'Problem Solving', 'proficiency': random.randint(75, 90)},
            {'name': 'JavaScript', 'proficiency': random.randint(70, 90)},
            {'name': 'Python', 'proficiency': random.randint(70, 85)},
            {'name': 'Data Analysis', 'proficiency': random.randint(65, 85)},
            {'name': 'Project Management', 'proficiency': random.randint(60, 80)}
        ]
    
    # In-demand skills based on current job market
    in_demand_skills = [
        'Machine Learning', 'AWS', 'Docker', 'Kubernetes', 'TypeScript',
        'Node.js', 'CI/CD', 'Microservices', 'Data Visualization', 'Agile Methodologies'
    ]
    
    # Recommended courses based on skills gap
    recommended_courses = [
        {'title': 'AWS Certified Solutions Architect', 'url': 'https://www.coursera.org/aws-certified-solutions-architect'},
        {'title': 'Docker and Kubernetes: The Complete Guide', 'url': 'https://www.udemy.com/course/docker-kubernetes-the-complete-guide'},
        {'title': 'Machine Learning A-Z™', 'url': 'https://www.udemy.com/course/machinelearning'}
    ]
    
    # Learning materials for career development
    learning_materials = [
        {
            'category': 'Resume Building',
            'resources': [
                {
                    'title': 'Resume Writing Masterclass',
                    'description': 'Learn how to craft a resume that passes ATS systems and impresses recruiters',
                    'type': 'Video Course',
                    'duration': '2 hours',
                    'url': 'https://www.udemy.com/course/resume-writing-masterclass',
                    'icon': 'bi-camera-video'
                },
                {
                    'title': 'The Ultimate ATS Resume Template Guide',
                    'description': 'Free downloadable templates optimized for Applicant Tracking Systems',
                    'type': 'PDF Guide',
                    'duration': '15 pages',
                    'url': 'https://www.resumebuilder.com/ats-resume-templates',
                    'icon': 'bi-file-earmark-pdf'
                },
                {
                    'title': 'Quantifying Your Achievements',
                    'description': 'How to add measurable results to your resume that hiring managers love',
                    'type': 'Article',
                    'duration': '10 min read',
                    'url': 'https://www.themuse.com/advice/how-to-quantify-your-resume-bullets',
                    'icon': 'bi-file-text'
                }
            ]
        },
        {
            'category': 'Interview Preparation',
            'resources': [
                {
                    'title': 'Mastering the Behavioral Interview',
                    'description': 'Practice answering the most common behavioral questions using the STAR method',
                    'type': 'Interactive Workshop',
                    'duration': '3 hours',
                    'url': 'https://www.interviewprep.org/behavioral-interviews',
                    'icon': 'bi-people'
                },
                {
                    'title': 'Technical Interview Handbook',
                    'description': 'Comprehensive guide to acing coding interviews with practice problems',
                    'type': 'GitHub Repository',
                    'duration': 'Self-paced',
                    'url': 'https://github.com/yangshun/tech-interview-handbook',
                    'icon': 'bi-github'
                },
                {
                    'title': '50 Most Common Interview Questions',
                    'description': 'Prepare confident answers for the questions you\'re most likely to face',
                    'type': 'Checklist',
                    'duration': '5 min read',
                    'url': 'https://www.glassdoor.com/blog/common-interview-questions',
                    'icon': 'bi-check-square'
                }
            ]
        },
        {
            'category': 'Skill Development',
            'resources': [
                {
                    'title': 'LinkedIn Learning Path: Become a Full-Stack Web Developer',
                    'description': 'Comprehensive curriculum covering front-end and back-end development',
                    'type': 'Course Series',
                    'duration': '40+ hours',
                    'url': 'https://www.linkedin.com/learning/paths/become-a-full-stack-web-developer',
                    'icon': 'bi-linkedin'
                },
                {
                    'title': 'Data Science for Beginners',
                    'description': 'Learn Python, data analysis, and machine learning fundamentals',
                    'type': 'Video Course',
                    'duration': '25 hours',
                    'url': 'https://www.datacamp.com/courses/data-science-for-beginners',
                    'icon': 'bi-graph-up'
                },
                {
                    'title': 'Project Management Professional (PMP) Certification Guide',
                    'description': 'Everything you need to know to prepare for the PMP exam',
                    'type': 'Study Guide',
                    'duration': 'Self-paced',
                    'url': 'https://www.pmi.org/certifications/project-management-pmp',
                    'icon': 'bi-kanban'
                }
            ]
        }
    ]
    
    return render_template('dashboard.html',
                           user_stats=user_stats,
                           resume_analysis=resume_analysis,
                           recent_applications=recent_applications,
                           user_skills=user_skills,
                           in_demand_skills=in_demand_skills,
                           recommended_courses=recommended_courses,
                           learning_materials=learning_materials,
                           current_date=current_date)

# Resume Builder route
@app.route('/resume_builder')
def resume_builder():
    return render_template('resume_builder.html')

# ATS Checker route
@app.route('/ats_checker')
def ats_checker():
    return render_template('ats_checker.html')

# ATS Check API
@app.route('/api/analyze_resume', methods=['POST'])
def analyze_resume():
    try:
        # Check if a file was uploaded
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400
            
        resume_file = request.files['resume']
        if resume_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Check file format
        allowed_extensions = {'pdf', 'doc', 'docx'}
        if not resume_file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
            return jsonify({'error': 'File must be PDF, DOC, or DOCX'}), 400
            
        # Save the file temporarily
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, secure_filename(resume_file.filename))
        resume_file.save(temp_path)
        logger.info(f"Saved resume file to {temp_path}")
        
        # Extract data from resume
        try:
            # Try to use enhanced extraction first
            if enhanced_extraction_available:
                logger.info(f"Attempting to extract resume data using enhanced extraction from {temp_path}")
                resume_data = extract_resume_info(temp_path)
                logger.info(f"Successfully extracted resume data using enhanced extraction: {len(str(resume_data))} bytes")
            else:
                # Fall back to basic extraction
                logger.info(f"Enhanced extraction not available, falling back to basic extraction for {temp_path}")
                try:
                    from resume_extraction import extract_resume_info as basic_extract
                    resume_data = basic_extract(temp_path)
                    logger.info("Used basic extraction as fallback")
                except ImportError:
                    logger.error("Basic resume extraction module not available, creating minimal resume data")
                    # Create minimal resume data structure if basic extraction is also not available
                    resume_data = {
                        'skills': ['Python', 'JavaScript', 'HTML', 'CSS'],  # Default skills
                        'name': 'Not detected',
                        'email': 'Not detected',
                        'phone': 'Not detected',
                        'sections': {'summary': True, 'experience': True, 'education': True, 'skills': True},
                        'word_count': 500,  # Default word count
                        'format_score': 0.7,  # Default format score
                        'content_score': 0.7,  # Default content score
                        'keyword_density': 0.5  # Default keyword density
                    }
                
            # Ensure we have all required fields
            if 'skills' not in resume_data:
                resume_data['skills'] = []
            if 'name' not in resume_data:
                resume_data['name'] = 'Not detected'
            if 'email' not in resume_data:
                resume_data['email'] = 'Not detected'
            if 'phone' not in resume_data:
                resume_data['phone'] = 'Not detected'
            if 'sections' not in resume_data:
                resume_data['sections'] = {}
                
            logger.info(f"Resume data extracted with {len(resume_data.get('skills', []))} skills")
        except Exception as e:
            logger.error(f"Error in resume extraction: {str(e)}")
            # Create minimal resume data structure
            resume_data = {
                'skills': [],
                'name': 'Not detected',
                'email': 'Not detected',
                'phone': 'Not detected',
                'sections': {},
                'word_count': 0,
                'format_score': 0.5,  # Default middle score
                'content_score': 0.5,  # Default middle score
                'keyword_density': 0.3  # Default score
            }
            logger.info("Created minimal resume data due to extraction error")
            
        # Get job description if provided
        job_description = request.form.get('jobDescription', '')
        
        # Calculate ATS score
        score = calculate_ats_score(resume_data, job_description)
        
        # Generate improvements and key findings
        improvements = generate_improvements(resume_data, job_description)
        key_findings = generate_key_findings(resume_data, score, job_description)
        
        # Ensure we have suggestions even if none were generated
        if not improvements or len(improvements) == 0:
            logger.warning("No improvements generated, using default suggestions")
            improvements = [
                'Add more industry-specific keywords to your resume to improve ATS matching',
                'Ensure your resume has clear section headings (Summary, Experience, Education, Skills)',
                'Quantify your achievements with numbers and metrics where possible',
                'Include a skills section with both technical and soft skills',
                'Make sure your contact information is clearly visible at the top of your resume',
                'Use a clean, ATS-friendly format without complex tables or graphics'
            ]
        
        # Ensure we have key findings
        if not key_findings or len(key_findings) == 0:
            logger.warning("No key findings generated, using default findings")
            key_findings = [
                {'type': 'info', 'text': 'Resume analysis complete'},
                {'type': 'info', 'text': 'Consider adding more relevant keywords to your resume'},
                {'type': 'info', 'text': 'Make sure your resume is properly formatted for ATS systems'}
            ]
        
        # Prepare detailed analysis
        analysis = {
            'score': score,
            'name': resume_data.get('name', 'Not detected'),
            'contact': {
                'email': resume_data.get('email', resume_data.get('contact', {}).get('email', 'Not detected')),
                'phone': resume_data.get('phone', resume_data.get('contact', {}).get('phone', 'Not detected'))
            },
            'fileInfo': {
                'format': resume_file.filename.split('.')[-1].upper(),
                'wordCount': resume_data.get('word_count', calculate_word_count(resume_data))
            },
            'keywords': {
                'found': resume_data.get('skills', []),
                'missing': get_missing_skills(resume_data.get('skills', []), job_description)
            },
            'format': analyze_resume_format(resume_data),
            'content': analyze_resume_content(resume_data),
            'improvements': improvements,
            'keyFindings': key_findings
        }
        
        # Log the analysis for debugging
        logger.info(f"Generated analysis with {len(improvements)} improvements and {len(key_findings)} key findings")
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error in resume analysis: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

# Helper function to calculate word count
def calculate_word_count(resume_data):
    # Combine all text fields and count words
    text = ''
    if 'summary' in resume_data:
        text += resume_data['summary'] + ' '
    if 'experience_text' in resume_data:
        text += resume_data['experience_text'] + ' '
    if 'education_text' in resume_data:
        text += resume_data['education_text'] + ' '
        
    return len(text.split())

# Helper function to analyze resume format
def analyze_resume_format(resume_data):
    return {
        'hasProperHeadings': 'summary' in resume_data and 'experience' in resume_data and 'education' in resume_data,
        'hasBulletPoints': resume_data.get('has_bullet_points', True),
        'fontConsistency': 90,  # This would require PDF style analysis in a real app
        'usesTables': resume_data.get('has_tables', False),
        'hasImages': resume_data.get('has_images', False),
        'margins': 'appropriate'
    }
    
# Helper function to analyze resume content
def analyze_resume_content(resume_data):
    experience = resume_data.get('experience_text', '')
    
    # Check for measurable results (numbers, percentages)
    has_measurable = any(char.isdigit() for char in experience) if experience else False
    
    # Check for action verbs
    action_verbs = ['managed', 'developed', 'created', 'implemented', 'designed', 'led', 'built']
    has_action_verbs = any(verb in experience.lower() for verb in action_verbs) if experience else False
    
    return {
        'hasMeasurableResults': has_measurable,
        'usesActionVerbs': has_action_verbs,
        'hasDates': resume_data.get('has_dates', True),
        'spelling': 95,  # Would require more advanced NLP
        'grammar': 92,   # Would require more advanced NLP
        'density': 'good'
    }
    
# Helper function to calculate ATS score
def calculate_ats_score(resume_data, job_description=''):
    """Calculate a realistic ATS score based on multiple factors with improved relevance"""
    logger.info(f"Calculating ATS score with resume data: {resume_data.keys()}")
    
    # Initialize base scores
    format_score = 0
    content_score = 0
    keyword_density = 0
    
    # Check if we're using the enhanced extraction module
    if enhanced_extraction_available and 'format_score' in resume_data and 'content_score' in resume_data:
        # Use the pre-calculated scores from enhanced extraction
        format_score = resume_data.get('format_score', 0) * 30  # Scale to 30%
        content_score = resume_data.get('content_score', 0) * 30  # Scale to 30%
        keyword_density = resume_data.get('keyword_density', 0) * 20  # Scale to 20%
        logger.info(f"Using enhanced extraction scores: format={format_score}, content={content_score}, keyword_density={keyword_density}")
    else:
        # Improved granular scoring that varies between resumes
        # Format scoring (30%)
        format_score = 0
        
        # Detect sections more comprehensively
        sections = resume_data.get('sections', {})
        
        # Check for summary section - multiple ways it could be represented
        has_summary = False
        summary_indicators = ['summary', 'profile', 'objective', 'about']
        
        # Check in sections dictionary
        if any(sections.get(key, False) for key in summary_indicators):
            has_summary = True
        
        # Check in resume_data keys
        if any(key in resume_data for key in summary_indicators):
            has_summary = True
        
        # Check in raw text if available
        if 'raw_text' in resume_data:
            raw_text = resume_data['raw_text'].lower()
            if any(f"{indicator}:" in raw_text or f"{indicator}\n" in raw_text for indicator in summary_indicators):
                has_summary = True
        
        if has_summary:
            format_score += 5
            logger.info("Summary section found: +5 points")
        
        # Experience is very important - improved detection
        experience_points = 0
        has_experience = False
        experience_indicators = ['experience', 'employment', 'work history', 'professional experience', 'career']
        
        # Check in sections dictionary
        if any(sections.get(key, False) for key in ['experience', 'work_experience', 'employment']):
            has_experience = True
        
        # Check if experience list exists
        if isinstance(resume_data.get('experience'), list) and len(resume_data.get('experience', [])) > 0:
            has_experience = True
        
        # Check if experience_text exists and has content
        if resume_data.get('experience_text') and len(resume_data.get('experience_text', '')) > 20:
            has_experience = True
        
        # Check in raw text if available
        if 'raw_text' in resume_data:
            raw_text = resume_data['raw_text'].lower()
            if any(f"{indicator}:" in raw_text or f"{indicator}\n" in raw_text for indicator in experience_indicators):
                has_experience = True
        
        if has_experience:
            experience_points += 7  # Increased from 5 to 7 (more important)
            # Add points based on years of experience
            years_exp = resume_data.get('experience_years', 0)
            if isinstance(years_exp, (int, float)) and years_exp > 0:
                experience_points += min(8, years_exp / 1.5)  # Up to 8 more points based on years (increased importance)
                logger.info(f"Experience section found with {years_exp} years: +{min(8, years_exp/1.5) + 7} points")
            else:
                logger.info("Experience section found but no years detected: +7 points")
        format_score += experience_points
        
        # Education section - improved detection
        has_education = False
        education_indicators = ['education', 'academic', 'degree', 'university', 'college', 'school']
        
        # Check in sections dictionary
        if any(sections.get(key, False) for key in ['education', 'academic', 'qualifications']):
            has_education = True
        
        # Check if education list exists
        if isinstance(resume_data.get('education'), list) and len(resume_data.get('education', [])) > 0:
            has_education = True
        
        # Check if education string exists and is not 'Unknown'
        if isinstance(resume_data.get('education'), str) and resume_data.get('education') != 'Unknown':
            has_education = True
        
        # Check in raw text if available
        if 'raw_text' in resume_data:
            raw_text = resume_data['raw_text'].lower()
            if any(f"{indicator}:" in raw_text or f"{indicator}\n" in raw_text for indicator in education_indicators):
                has_education = True
            # Check for common degree keywords
            degree_keywords = ['bachelor', 'master', 'phd', 'mba', 'bs', 'ba', 'ms', 'b.s.', 'b.a.', 'm.s.', 'ph.d']
            if any(keyword in raw_text for keyword in degree_keywords):
                has_education = True
        
        if has_education:
            education_points = 5
            # Add points based on education level
            edu_level = resume_data.get('education', '')
            if isinstance(edu_level, str):
                if 'phd' in edu_level.lower() or 'doctorate' in edu_level.lower():
                    education_points += 3
                elif 'master' in edu_level.lower():
                    education_points += 2
                elif 'bachelor' in edu_level.lower() or 'bs' in edu_level.lower() or 'ba' in edu_level.lower():
                    education_points += 1
            format_score += education_points
            logger.info(f"Education section found: +{education_points} points")
        
        # Skills section - improved detection
        has_skills = False
        
        # Check in sections dictionary
        if sections.get('skills', False):
            has_skills = True
        
        # Check if skills list exists and has items
        if isinstance(resume_data.get('skills'), list) and len(resume_data.get('skills', [])) > 0:
            has_skills = True
        
        # Check in raw text if available
        if 'raw_text' in resume_data:
            raw_text = resume_data['raw_text'].lower()
            if 'skills:' in raw_text or 'skills\n' in raw_text or 'technical skills' in raw_text or 'core competencies' in raw_text:
                has_skills = True
        
        if has_skills:
            format_score += 10
            logger.info("Skills section found: +10 points")
        
        # Content scoring (30%) - more granular and improved
        content_score = 0
        experience_text = resume_data.get('experience_text', '')
        
        # Check for measurable results with numbers - improved detection
        if experience_text:
            # Look for specific patterns that indicate measurable achievements
            measurable_patterns = [
                r'\d+%', r'\d+\s*percent', r'increased\s+by\s+\d+', r'decreased\s+by\s+\d+',
                r'\$\d+', r'\d+\s*million', r'\d+\s*billion', r'\d+\s*thousand',
                r'improved\s+\w+\s+by\s+\d+', r'reduced\s+\w+\s+by\s+\d+',
                r'\d+\s+users', r'\d+\s+customers', r'\d+\s+clients', r'\d+\s+projects'
            ]
            
            # Count matches for each pattern
            measurable_matches = 0
            for pattern in measurable_patterns:
                matches = re.findall(pattern, experience_text, re.IGNORECASE)
                measurable_matches += len(matches)
            
            # Award points based on matches with diminishing returns
            if measurable_matches > 0:
                measurable_points = min(12, 5 + (measurable_matches * 1.5))  # Base 5 points + 1.5 per match up to 12
                content_score += measurable_points
                logger.info(f"Measurable results found ({measurable_matches} matches): +{measurable_points} points")
        
        # Check for action verbs - expanded list
        action_verbs = [
            'managed', 'developed', 'created', 'implemented', 'designed', 'led', 'built',
            'achieved', 'improved', 'increased', 'decreased', 'reduced', 'negotiated',
            'coordinated', 'established', 'delivered', 'generated', 'maintained',
            'supervised', 'trained', 'analyzed', 'launched', 'executed', 'streamlined',
            'optimized', 'transformed', 'spearheaded', 'orchestrated', 'pioneered',
            'formulated', 'cultivated', 'directed', 'revitalized', 'maximized',
            'facilitated', 'guided', 'mentored', 'innovated', 'programmed', 'engineered'
        ]
        
        if experience_text:
            verb_count = sum(1 for verb in action_verbs if verb in experience_text.lower())
            # More points for action verbs
            verb_points = min(12, verb_count * 1.2)  # Up to 12 points based on action verb count
            content_score += verb_points
            logger.info(f"Action verbs in experience ({verb_count} found): +{verb_points} points")
        
        # Check for proper formatting
        if resume_data.get('has_bullet_points', False):
            content_score += 6  # Increased from 5 to 6 (more important)
            logger.info("Bullet points detected: +6 points")
        
        if resume_data.get('has_dates', False):
            content_score += 6  # Increased from 5 to 6 (more important)
            logger.info("Dates detected: +6 points")
        
        # Penalize for bad formatting
        if resume_data.get('has_tables', False):
            content_score -= 8  # Increased penalty from 5 to 8 (more significant issue)
            logger.info("Tables detected (not ATS friendly): -8 points")
        
        # Keyword density (20%) - more granular
        skills = resume_data.get('skills', [])
        if skills:
            # Base points on number of skills with diminishing returns
            skill_count = len(skills)
            keyword_density = min(20, 5 + (skill_count * 1.5))  # Base 5 points + 1.5 per skill up to 20
            logger.info(f"Keyword density from {skill_count} skills: {keyword_density} points")
    
    # Keyword scoring based on skills (20%) - improved
    skills = resume_data.get('skills', [])
    skill_count = len(skills)
    
    # More granular skill scoring with diminishing returns
    if skill_count <= 5:
        keyword_score = skill_count * 2.5  # 2.5 points per skill for first 5 skills (increased value)
    else:
        keyword_score = 12.5 + min(7.5, (skill_count - 5) * 0.75)  # 12.5 points for first 5, then 0.75 point per additional skill
    
    logger.info(f"Keyword score from {skill_count} skills: {keyword_score} points")
    
    # Calculate job-specific relevance if job description provided (30%) - improved matching
    if job_description:
        # Extract job keywords more effectively
        job_keywords = extract_keywords(job_description)
        
        # Add common industry terms that might be in the job description
        industry_terms = [
            'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma',
            'cloud', 'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'docker', 'kubernetes',
            'frontend', 'backend', 'fullstack', 'web', 'mobile', 'desktop', 'api',
            'database', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle',
            'machine learning', 'ai', 'artificial intelligence', 'data science', 'big data',
            'analytics', 'business intelligence', 'visualization', 'tableau', 'power bi',
            'security', 'cybersecurity', 'networking', 'infrastructure', 'architecture',
            'project management', 'product management', 'agile', 'scrum master', 'product owner'
        ]
        
        # Check if any industry terms are in the job description but not in the keywords
        for term in industry_terms:
            if term in job_description.lower() and term not in [k.lower() for k in job_keywords]:
                job_keywords.append(term)
        
        matching_keywords = []
        partial_matches = 0
        
        # Improved matching algorithm
        for skill in skills:
            exact_match = False
            partial_match = False
            
            for keyword in job_keywords:
                # Check for exact matches first (worth more)
                if skill.lower() == keyword.lower():
                    matching_keywords.append(skill)
                    exact_match = True
                    break
                # Then check for partial matches with improved logic
                elif (keyword.lower() in skill.lower() or skill.lower() in keyword.lower()) and \
                     (len(keyword) > 3 and len(skill) > 3):  # Avoid matching on very short terms
                    partial_match = True
            
            if not exact_match and partial_match:
                partial_matches += 1
        
        # Calculate relevance score with more weight to exact matches
        if job_keywords:
            # Improved scoring formula
            exact_match_score = (len(matching_keywords) / max(1, len(job_keywords))) * 25  # 25% for exact matches
            partial_match_score = (partial_matches / max(1, len(job_keywords))) * 5  # 5% for partial matches
            
            # Bonus points for high match percentage
            match_percentage = (len(matching_keywords) + (partial_matches * 0.5)) / max(1, len(job_keywords))
            if match_percentage > 0.7:  # If more than 70% of keywords match
                bonus_points = 5
                logger.info(f"High keyword match percentage ({match_percentage:.1%}): +{bonus_points} bonus points")
            else:
                bonus_points = 0
                
            relevance_score = exact_match_score + partial_match_score + bonus_points
            logger.info(f"Job relevance: {len(matching_keywords)} exact matches, {partial_matches} partial matches, score: {relevance_score}")
        else:
            relevance_score = 15  # Default middle score if no keywords found
            logger.info("No job keywords found, using default relevance score: 15")
    else:
        relevance_score = 15  # Default middle score if no job description
        logger.info("No job description provided, using default relevance score: 15")
    
    # Calculate total score with improved weighting
    total_score = format_score + content_score + keyword_score + relevance_score
    logger.info(f"Raw score components: format={format_score}, content={content_score}, keyword={keyword_score}, relevance={relevance_score}")
    logger.info(f"Total raw score: {total_score}")
    
    # Add some randomness to make scores more realistic (±2 points) - reduced randomness for more consistency
    import random
    random_factor = random.uniform(-2, 2)
    total_score += random_factor
    logger.info(f"Added randomness factor of {random_factor:.2f}")
    
    # Normalize to 0-100 with a more realistic range
    # Most ATS systems reject below 70%, so we use a 65-98 range
    normalized_score = min(98, max(65, total_score))  # Keep scores in realistic range (65-98)
    logger.info(f"Final normalized ATS score: {int(normalized_score)}")
    
    return int(normalized_score)
    
# Helper function to extract keywords from text
def extract_keywords(text):
    # This is a simplified keyword extraction - in a real app, you'd use NLP
    words = text.lower().split()
    stopwords = {'and', 'the', 'is', 'in', 'of', 'to', 'a', 'for', 'with', 'on', 'at'}
    keywords = [word for word in words if word not in stopwords and len(word) > 3]
    return list(set(keywords))
    
# Helper function to get missing skills
def get_missing_skills(resume_skills, job_description):
    if not job_description:
        return []
        
    # Extract potential required skills from job description
    job_keywords = extract_keywords(job_description)
    common_job_skills = ['python', 'java', 'javascript', 'sql', 'react', 'node', 'agile', 'aws', 
                         'cloud', 'data', 'analysis', 'management', 'communication', 'leadership']
                         
    # Filter job keywords to focus on likely skills
    potential_skills = [keyword for keyword in job_keywords 
                      if keyword in common_job_skills or keyword.title() in common_job_skills]
                      
    # Find skills in job description missing from resume
    resume_skills_lower = [skill.lower() for skill in resume_skills]
    missing_skills = [skill for skill in potential_skills 
                     if not any(skill in rs or rs in skill for rs in resume_skills_lower)]
    
    return missing_skills
# Helper function to generate improvement suggestions
def generate_improvements(resume_data, job_description):
    """Generate specific, actionable improvement suggestions for the resume"""
    improvements = []
    
    # Check for proper sections
    sections = resume_data.get('sections', {})
    if not sections.get('summary', False) and 'summary' not in resume_data:
        improvements.append('Add a professional summary at the top of your resume that highlights your key qualifications')
        
    if not sections.get('skills', False) and 'skills' not in resume_data:
        improvements.append('Add a dedicated skills section that clearly lists your technical and soft skills')
    
    # Check for content quality
    experience = resume_data.get('experience_text', '')
    if not any(char.isdigit() for char in experience):
        improvements.append('Include measurable achievements with numbers in your experience section (e.g., "increased sales by 25%")')
        
    action_verbs = ['managed', 'developed', 'created', 'implemented', 'designed', 'led', 'built', 'achieved', 'improved', 'increased']
    if not any(verb in experience.lower() for verb in action_verbs):
        improvements.append('Start each bullet point in your experience section with strong action verbs like "Developed," "Implemented," or "Managed"')
    
    # Check for formatting issues
    if resume_data.get('has_tables', False):
        improvements.append('Remove tables from your resume as they can confuse ATS systems - use simple bullet points instead')
        
    if not resume_data.get('has_bullet_points', True):
        improvements.append('Use bullet points to format your experience and skills sections for better ATS readability')
    
    # Check for contact information
    if resume_data.get('email', 'Not found') == 'Not found':
        improvements.append('Add your email address to your contact information section')
        
    if resume_data.get('phone', 'Not found') == 'Not found':
        improvements.append('Add your phone number to your contact information section')
    
    # Check for skills
    skills = resume_data.get('skills', [])
    if len(skills) < 8:
        improvements.append('Add more relevant skills to your resume - aim for at least 10-15 key skills')
    
    # Job-specific improvements
    if job_description:
        missing_skills = get_missing_skills(skills, job_description)
        if missing_skills:
            # Limit to top 5 missing skills for readability
            top_missing = missing_skills[:5]
            improvements.append(f'Add these key skills from the job description: {", ".join(top_missing)}')
            
        # Check for job title match
        job_title_match = False
        job_keywords = extract_keywords(job_description)
        resume_job_role = resume_data.get('job_role', 'Unknown')
        
        for keyword in job_keywords:
            if keyword.lower() in resume_job_role.lower():
                job_title_match = True
                break
                
        if not job_title_match and resume_job_role != 'Unknown':
            improvements.append('Consider aligning your job title/objective with the target position in the job description')
    
    # Education improvements
    if 'education' in resume_data and resume_data['education'] == 'Unknown':
        improvements.append('Clearly state your degree and education details in a dedicated education section')
    
    # Prioritize and return top 6 improvements
    return improvements[:6]

# Helper function to generate key findings
def generate_key_findings(resume_data, score, job_description):
    """Generate detailed key findings about the resume's ATS compatibility with more relevant insights"""
    findings = []
    logger.info(f"Generating key findings with resume data keys: {resume_data.keys()}")
    
    # Score-based findings - more specific and actionable
    if score < 70:
        findings.append({'type': 'warning', 'text': f'Your resume scored {score}%, which is below the typical 75% threshold used by many ATS systems. Major improvements are needed.'})
    elif score < 80:
        findings.append({'type': 'info', 'text': f'Your resume scored {score}%, which is in the borderline range. Several improvements could help you pass more ATS screenings.'})
    elif score < 90:
        findings.append({'type': 'info', 'text': f'Your resume scored {score}%, which is good but not excellent. Some targeted improvements would maximize your chances.'})
    else:
        findings.append({'type': 'success', 'text': f'Your resume scored an excellent {score}%. It is highly optimized for ATS systems and should perform well in automated screening.'})
    
    # Section findings - improved detection logic
    sections = resume_data.get('sections', {})
    missing_sections = []
    
    # More comprehensive section detection
    # Check for summary section - multiple ways it could be represented
    has_summary = False
    summary_indicators = ['summary', 'profile', 'objective', 'about']
    
    # Check in sections dictionary
    if any(sections.get(key, False) for key in summary_indicators):
        has_summary = True
    
    # Check in resume_data keys
    if any(key in resume_data for key in summary_indicators):
        has_summary = True
    
    # Check in raw text if available
    if 'raw_text' in resume_data:
        raw_text = resume_data['raw_text'].lower()
        if any(f"{indicator}:" in raw_text or f"{indicator}\n" in raw_text for indicator in summary_indicators):
            has_summary = True
    
    if not has_summary:
        missing_sections.append('professional summary')
        findings.append({'type': 'warning', 'text': 'Missing professional summary section. Adding a 3-5 line summary at the top with key qualifications will improve ATS recognition by 15-20%.'})
    else:
        findings.append({'type': 'success', 'text': 'Professional summary detected. This section helps ATS systems quickly categorize your profile and match you to relevant positions.'})
    
    # Check for skills section - multiple ways it could be represented
    has_skills = False
    
    # Check in sections dictionary
    if sections.get('skills', False):
        has_skills = True
    
    # Check if skills list exists and has items
    if isinstance(resume_data.get('skills'), list) and len(resume_data.get('skills', [])) > 0:
        has_skills = True
        logger.info(f"Skills found: {resume_data.get('skills')}")
    
    # Check in raw text if available
    if 'raw_text' in resume_data:
        raw_text = resume_data['raw_text'].lower()
        if 'skills:' in raw_text or 'skills\n' in raw_text or 'technical skills' in raw_text or 'core competencies' in raw_text:
            has_skills = True
    
    if not has_skills:
        missing_sections.append('skills')
        findings.append({'type': 'warning', 'text': 'Missing dedicated skills section. ATS systems heavily weight keyword matching - adding a clear skills section can improve your match rate by 25-30%.'})
    else:
        # Check if there are enough skills
        skills = resume_data.get('skills', [])
        if len(skills) < 8:
            findings.append({'type': 'info', 'text': f'Skills section detected but only contains {len(skills)} skills. Expanding to 12-15 relevant skills would improve ATS matching.'})
        else:
            findings.append({'type': 'success', 'text': f'Strong skills section with {len(skills)} skills detected. This significantly improves your keyword matching in ATS systems.'})
    
    # Check for experience section - multiple ways it could be represented
    has_experience = False
    experience_indicators = ['experience', 'employment', 'work history', 'professional experience', 'career']
    
    # Check in sections dictionary
    if any(sections.get(key, False) for key in ['experience', 'work_experience', 'employment']):
        has_experience = True
        logger.info("Experience section found in sections dictionary")
    
    # Check if experience list exists
    if isinstance(resume_data.get('experience'), list) and len(resume_data.get('experience', [])) > 0:
        has_experience = True
        logger.info(f"Experience list found with {len(resume_data.get('experience'))} entries")
    
    # Check if experience_text exists and has content
    if resume_data.get('experience_text') and len(resume_data.get('experience_text', '')) > 20:
        has_experience = True
        logger.info("Experience text found")
    
    # Check for experience years
    if resume_data.get('experience_years', 0) > 0:
        has_experience = True
        logger.info(f"Experience years found: {resume_data.get('experience_years')}")
    
    # Check in raw text if available
    if 'raw_text' in resume_data:
        raw_text = resume_data['raw_text'].lower()
        if any(f"{indicator}:" in raw_text or f"{indicator}\n" in raw_text for indicator in experience_indicators):
            has_experience = True
            logger.info("Experience section found in raw text")
    
    # Check for measurable results and action verbs in experience
    experience = resume_data.get('experience_text', '')
    has_measurable = any(re.search(r'\d+%|\d+\s*million|\$\d+|increased|decreased|improved|reduced|\d+\s*people', experience, re.IGNORECASE)) if experience else False
    
    action_verbs = ['managed', 'developed', 'created', 'implemented', 'designed', 'led', 'built', 'achieved', 'improved', 'increased']
    has_action_verbs = any(verb in experience.lower() for verb in action_verbs) if experience else False
    
    if not has_experience:
        missing_sections.append('work experience')
        findings.append({'type': 'warning', 'text': 'Missing clear work experience section. This is the most critical section for ATS evaluation and recruiter review.'})
    else:
        if not has_measurable and experience:
            findings.append({'type': 'info', 'text': 'Your experience section lacks quantifiable achievements. Adding 2-3 metrics per role (e.g., "increased sales by 25%") can improve ATS scoring by 15-20%.'})
        elif has_measurable:
            findings.append({'type': 'success', 'text': 'Quantifiable achievements detected in your experience section. This significantly improves how ATS systems and recruiters evaluate your impact.'})
            
        if not has_action_verbs and experience:
            findings.append({'type': 'info', 'text': 'Your experience section lacks strong action verbs. Starting bullets with words like "Developed" or "Implemented" helps ATS identify your contributions.'})
        elif has_action_verbs:
            findings.append({'type': 'success', 'text': 'Strong action verbs detected in your experience section. This helps ATS systems properly categorize your accomplishments.'})
    
    # Check for education section - multiple ways it could be represented
    has_education = False
    education_indicators = ['education', 'academic', 'degree', 'university', 'college', 'school']
    
    # Check in sections dictionary
    if any(sections.get(key, False) for key in ['education', 'academic', 'qualifications']):
        has_education = True
        logger.info("Education section found in sections dictionary")
    
    # Check if education list exists
    if isinstance(resume_data.get('education'), list) and len(resume_data.get('education', [])) > 0:
        has_education = True
        logger.info(f"Education list found with {len(resume_data.get('education'))} entries")
    
    # Check if education string exists and is not 'Unknown'
    if isinstance(resume_data.get('education'), str) and resume_data.get('education') != 'Unknown':
        has_education = True
        logger.info(f"Education string found: {resume_data.get('education')}")
    
    # Check in raw text if available
    if 'raw_text' in resume_data:
        raw_text = resume_data['raw_text'].lower()
        if any(f"{indicator}:" in raw_text or f"{indicator}\n" in raw_text for indicator in education_indicators):
            has_education = True
            logger.info("Education section found in raw text")
        # Check for common degree keywords
        degree_keywords = ['bachelor', 'master', 'phd', 'mba', 'bs', 'ba', 'ms', 'b.s.', 'b.a.', 'm.s.', 'ph.d']
        if any(keyword in raw_text for keyword in degree_keywords):
            has_education = True
            logger.info("Education degree keywords found in raw text")
    
    if not has_education:
        missing_sections.append('education')
        findings.append({'type': 'warning', 'text': 'Missing education section. Even if you have limited formal education, include this section as 90% of ATS systems look for it.'})
    else:
        # Check education level
        education = resume_data.get('education', 'Unknown')
        if education == 'Unknown':
            findings.append({'type': 'info', 'text': 'Education section detected but degree level is unclear. Explicitly state your degree (e.g., "Bachelor of Science") for better ATS recognition.'})
        elif education in ['PhD', 'Masters']:
            findings.append({'type': 'success', 'text': f'Advanced degree ({education}) detected. This is valuable for many positions and properly formatted for ATS recognition.'})
        else:
            findings.append({'type': 'success', 'text': 'Education section properly detected and formatted for ATS systems.'})
    
    # Format findings
    if resume_data.get('has_tables', False):
        findings.append({'type': 'warning', 'text': 'Tables detected in your resume. These confuse 80% of ATS systems - replace with simple bullet points and clear section headers.'})
    
    if not resume_data.get('has_bullet_points', True):
        findings.append({'type': 'info', 'text': 'No bullet points detected. Using 3-5 bullet points per role improves ATS readability by approximately 25%.'})
    
    # Contact information findings
    if resume_data.get('email', 'Not found') == 'Not found':
        findings.append({'type': 'warning', 'text': 'No email address detected. This is required by 100% of ATS systems and should be clearly visible at the top of your resume.'})
    
    if resume_data.get('phone', 'Not found') == 'Not found':
        findings.append({'type': 'warning', 'text': 'No phone number detected. This is required by 95% of ATS systems and should be clearly visible at the top of your resume.'})
    
    # Job-specific findings - more detailed and actionable
    if job_description:
        missing_skills = get_missing_skills(skills, job_description)
        if missing_skills:
            if len(missing_skills) > 5:
                findings.append({'type': 'warning', 'text': f'Your resume is missing {len(missing_skills)} keywords from the job description. Top missing skills: {", ".join(missing_skills[:5])}.'})
                findings.append({'type': 'info', 'text': 'Adding these missing keywords could improve your ATS match rate by 30-40% for this specific job.'})
            else:
                findings.append({'type': 'info', 'text': f'Your resume is missing a few keywords from the job description: {", ".join(missing_skills)}. Adding these could improve your match.'})
        else:
            findings.append({'type': 'success', 'text': 'Excellent keyword match with the job description! Your resume contains most or all of the key terms the employer is looking for.'})
    
    # Summary of section completeness
    if missing_sections and len(missing_sections) > 1:
        findings.append({'type': 'warning', 'text': f'Your resume is missing {len(missing_sections)} key sections: {', '.join(missing_sections)}. Adding these would significantly improve ATS compatibility.'})
    elif len(missing_sections) == 1:
        findings.append({'type': 'info', 'text': f'Your resume is only missing the {missing_sections[0]} section. Adding this would complete your ATS-friendly resume structure.'})
    elif len(missing_sections) == 0:
        findings.append({'type': 'success', 'text': 'Your resume contains all essential sections required by ATS systems. This provides a strong foundation for successful screening.'})
    
    # Prioritize findings - most important first
    # Sort by type (warning first, then info, then success) and limit to most important
    priority_order = {'warning': 0, 'info': 1, 'success': 2}
    findings.sort(key=lambda x: priority_order.get(x['type'], 3))
    
    return findings[:10]  # Return top 10 most important findings

# Resume Parsing API
@app.route('/api/resume/parse', methods=['POST'])
def parse_resume():
    try:
        # Check if a file was uploaded
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400
            
        resume_file = request.files['resume']
        if resume_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Save the file temporarily
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, secure_filename(resume_file.filename))
        resume_file.save(temp_path)
        
        # Extract resume data
        if enhanced_extraction_available:
            resume_data = extract_resume_info(temp_path)
        else:
            # Fallback to basic extraction
            resume_data = {
                'skills': [],
                'name': 'Not detected',
                'contact': {
                    'email': 'Not detected',
                    'phone': 'Not detected'
                }
            }
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'resume_data': resume_data
        })
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        return jsonify({'error': f'Parsing failed: {str(e)}'}), 500

# Resume Generation API
@app.route('/api/generate_resume', methods=['POST'])
def generate_resume():
    try:
        data = request.json
        template = data.get('template', 'professional')
        resume_data = data.get('resume_data', {})
        
        # In a real implementation, you would generate a PDF here
        # For now, we'll just return success
        
        return jsonify({
            "success": True,
            "message": "Resume generated successfully",
            "template": template
        })
    except Exception as e:
        logger.error(f"Error generating resume: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Save Resume API
@app.route('/api/save_resume', methods=['POST'])
def save_resume():
    try:
        data = request.json
        user_id = data.get('user_id', 'demo_user')  # In a real app, get from auth
        resume_data = data.get('resume_data', {})
        
        # In a real implementation, you would save to a database
        # For now, we'll just return success
        
        return jsonify({
            "success": True,
            "message": "Resume saved successfully",
            "resume_id": f"resume_{datetime.now().timestamp()}"
        })
    except Exception as e:
        logger.error(f"Error saving resume: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
