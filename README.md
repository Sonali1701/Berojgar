# Berojgar - Smart Job Application Platform

![Berojgar Logo](static/images/logo.png)

## Overview

Berojgar is a comprehensive job application platform designed to help job seekers find relevant positions, optimize their resumes for Applicant Tracking Systems (ATS), and streamline the application process. The name "Berojgar" (meaning "unemployed" in Hindi) transforms into "Be-Employed" through our platform's powerful features.

## Key Features

### 1. Job Search
- Real-time job listings from multiple sources (Google Jobs, Remotive, Adzuna)
- Smart matching algorithm to find jobs that align with your skills
- Direct application links to legitimate job postings
- Support for both technical and non-technical job roles

### 2. ATS Resume Checker
- AI-powered resume analysis with realistic scoring (65-98%)
- Detailed feedback on resume structure, content, and formatting
- Keyword matching against job descriptions
- Actionable improvement suggestions

### 3. Resume Builder
- Professional templates optimized for ATS systems
- Section-by-section guidance for creating impactful content
- Real-time preview and editing
- Export options in multiple formats

### 4. User Dashboard
- Track application status and statistics
- Skill assessment and development recommendations
- Learning resources for career growth
- Personalized job recommendations

## Technology Stack

### Backend
- Python with Flask web framework
- Machine learning for resume analysis and job matching
- Web scraping with Selenium and BeautifulSoup
- Natural Language Processing for text analysis

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5 for responsive design
- Interactive UI components

### APIs & Data Sources
- Google Jobs (via scraping)
- Remotive API
- Adzuna API
- GitHub Jobs API

## Getting Started

### Prerequisites
- Python 3.8+
- pip package manager
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/berojgar.git
   cd berojgar
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     ADZUNA_APP_ID=your_adzuna_app_id
     ADZUNA_API_KEY=your_adzuna_api_key
     ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Project Structure

```
berojgar/
├── app.py                 # Main Flask application
├── job_scraper.py         # Job scraping functionality
├── mock_job_generator.py  # Fallback job data generator
├── resume_extraction.py   # Resume parsing and analysis
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── images/            # Images and icons
├── templates/             # HTML templates
│   ├── index.html         # Homepage
│   ├── job_search.html    # Job search page
│   ├── dashboard.html     # User dashboard
│   ├── resume_builder.html # Resume builder
│   └── ats_checker.html   # ATS checker
└── requirements.txt       # Python dependencies
```

## Features in Detail

### Job Search
The job search functionality combines multiple sources to provide comprehensive results:
- Primary sources include Google Jobs, Remotive, and Adzuna
- Fallback to mock data with real Google search URLs if APIs fail
- Intelligent source selection based on job type (technical vs. non-technical)
- Direct application links to ensure users can apply immediately

### ATS Checker
Our ATS checker provides realistic and actionable feedback:
- Section detection (summary, experience, education, skills)
- Keyword matching against job descriptions
- Analysis of measurable achievements and action verbs
- Formatting assessment for ATS compatibility
- Prioritized findings and improvement suggestions

### Resume Builder
The resume builder helps create professional, ATS-optimized resumes:
- Multiple templates designed for different industries
- Section-by-section guidance
- Real-time preview
- Export options (PDF, DOCX)

### User Dashboard
The dashboard provides a centralized hub for job search activities:
- Application tracking and statistics
- Skill assessment and recommendations
- Learning resources for career development
- Personalized job recommendations

## Contributing

We welcome contributions to improve Berojgar! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Job data provided by Google Jobs, Remotive, and Adzuna
- Resume analysis techniques inspired by industry ATS systems
- Bootstrap for the responsive UI framework
