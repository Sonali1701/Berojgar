"""
Job Scraper Module for Berojgar

This module fetches job listings using Selenium WebDriver for dynamic web scraping
and connects to various job APIs to provide real job listings.
"""

import json
import os
import re
import logging
import random
import time
import requests
from urllib.parse import quote_plus, urlencode
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Selenium and WebDriver dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("job_scraper.log"), logging.StreamHandler()]
)
logger = logging.getLogger("job_scraper")

class JobScraper:
    """Main class for scraping jobs using Selenium WebDriver and API connections"""
    
    def __init__(self, browser='edge'):
        """
        Initialize the job scraper with a specific browser
        
        Args:
            browser (str): Browser to use for scraping. Options: 'edge', 'chrome'
        """
        self.browser = browser.lower()
        self.driver = None  # Initialize driver only when needed
        
        # Cache for job results to avoid repeated API calls
        self.job_cache = {}
        self.cache_expiry = {}  # Store timestamps for cache expiration
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        
        # API keys and endpoints
        self.remotive_api_url = "https://remotive.com/api/remote-jobs"
        self.adzuna_api_url = "https://api.adzuna.com/v1/api/jobs"
        self.adzuna_app_id = os.environ.get('ADZUNA_APP_ID', '')
        self.adzuna_api_key = os.environ.get('ADZUNA_API_KEY', '')
        
        # Create a session for requests to reuse connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _setup_webdriver(self):
        """
        Set up the appropriate WebDriver based on browser selection
        
        Returns:
            WebDriver: Configured WebDriver instance
        """
        try:
            if self.browser == 'edge':
                from selenium.webdriver.edge.service import Service
                from selenium.webdriver.edge.options import Options
                edge_options = Options()
                edge_options.use_chromium = True
                edge_options.add_argument('--headless')  # Run in background
                edge_options.add_argument('--disable-gpu')
                edge_options.add_argument('--no-sandbox')
                edge_options.add_argument('--disable-dev-shm-usage')
                edge_service = Service('msedgedriver.exe')  # Ensure this is in PATH
                return webdriver.Edge(service=edge_service, options=edge_options)
            
            elif self.browser == 'chrome':
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options
                chrome_options = Options()
                chrome_options.add_argument('--headless')  # Run in background
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_service = Service('chromedriver.exe')  # Ensure this is in PATH
                return webdriver.Chrome(service=chrome_service, options=chrome_options)
            
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")
        
        except Exception as e:
            logger.error(f"WebDriver setup error: {e}")
            raise
    
    def search_google_jobs(self, query, location="", limit=20):
        """
        Search for jobs on Google Jobs using Selenium
        
        Args:
            query (str): Job search query (e.g., "python developer")
            location (str): Location for job search (e.g., "New York")
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of job dictionaries
        """
        try:
            # Initialize the driver if not already done
            if not self.driver:
                self.driver = self._setup_webdriver()
                
            # Construct Google Jobs search URL - make sure to include "jobs" in the query
            search_query = f"{quote_plus(query)} jobs"
            if location:
                search_query += f" in {quote_plus(location)}"
            
            google_jobs_url = f"https://www.google.com/search?q={search_query}"
            logger.info(f"Searching Google Jobs with URL: {google_jobs_url}")
            
            # Navigate to Google Jobs
            self.driver.get(google_jobs_url)
            
            # Wait for page to load - try multiple selectors since Google's UI can vary
            selectors_to_try = [
                "div.job_seen_beacon",
                "div.jobsearch-JobCard",
                "div.BjJfJf",
                "div[data-ved]",  # More generic selector that might catch job cards
                "div.g"  # Generic Google search result
            ]
            
            # Try each selector until one works
            job_cards = []
            for selector in selectors_to_try:
                try:
                    # Wait up to 3 seconds for this selector
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_cards:
                        logger.info(f"Found job cards using selector: {selector}")
                        break
                except Exception:
                    continue
            
            # If we still don't have job cards, try taking a screenshot and parsing the page content
            if not job_cards:
                # Take a screenshot for debugging
                screenshot_path = "google_jobs_screenshot.png"
                self.driver.save_screenshot(screenshot_path)
                logger.warning(f"No job cards found with standard selectors. Screenshot saved to {screenshot_path}")
                
                # Try to extract information from the page content
                page_content = self.driver.page_source
                job_listings = self._extract_jobs_from_page_content(page_content, query, limit)
                if job_listings:
                    return job_listings
            
            # Process the job cards we found
            job_listings = []
            for card in job_cards[:limit]:
                try:
                    # Try multiple selectors for job title
                    title = None
                    for title_selector in ["div.BjJfJf", "h3", "a.jobtitle", "a[data-ved] h3", "a[data-ved]"]:
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, title_selector)
                            title = title_elem.text
                            if title:
                                break
                        except NoSuchElementException:
                            continue
                    
                    # If we still don't have a title, try getting it from the card text
                    if not title:
                        card_text = card.text
                        # Use the first line as the title if it's not too long
                        lines = card_text.split('\n')
                        if lines and len(lines[0]) < 100:
                            title = lines[0]
                        else:
                            # Skip this card if we can't find a title
                            continue
                    
                    # Try multiple selectors for company name
                    company = None
                    for company_selector in ["div.nJlQsc", "span.company", "div.company", "div[data-ved] div"]:
                        try:
                            company_elem = card.find_element(By.CSS_SELECTOR, company_selector)
                            company = company_elem.text
                            if company:
                                break
                        except NoSuchElementException:
                            continue
                    
                    # If we still don't have a company name, use a default
                    if not company:
                        company = "Company Not Specified"
                    
                    # Try to get location
                    location_text = location or "Remote/Various"
                    for location_selector in ["div.Qk80Jf", "span.location", "div.location"]:
                        try:
                            location_elem = card.find_element(By.CSS_SELECTOR, location_selector)
                            if location_elem.text:
                                location_text = location_elem.text
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Try to get job description snippet
                    snippet = "No description available"
                    for snippet_selector in ["div.HBvzbc", "span.summary", "div.summary", "div[data-ved] div:nth-child(2)"]:
                        try:
                            snippet_elem = card.find_element(By.CSS_SELECTOR, snippet_selector)
                            if snippet_elem.text and len(snippet_elem.text) > 20:  # Ensure it's a real description
                                snippet = snippet_elem.text
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Try to get the actual job URL
                    job_url = google_jobs_url
                    for url_selector in ["a.pMhGee", "a.jobtitle", "a[data-ved]", "a"]:
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, url_selector)
                            href = link_elem.get_attribute("href")
                            if href and "http" in href:
                                job_url = href
                                break
                        except NoSuchElementException:
                            continue
                    
                    # Extract skills from the description
                    skills = extract_skills_from_text(snippet)
                    
                    job = {
                        'id': f"google_{random.randint(1000, 9999)}",
                        'title': title,
                        'company': company,
                        'location': location_text,
                        'description': snippet,
                        'full_description': snippet,  # Add full description field
                        'source': 'Google Jobs',
                        'url': job_url,
                        'application_url': job_url,  # Add application URL field
                        'skills': skills,
                        'posted_date': 'Recently',
                        'job_type': extract_job_type(snippet)
                    }
                    
                    job_listings.append(job)
                    logger.info(f"Found job: {title} at {company}")
                    
                    if len(job_listings) >= limit:
                        break
                
                except Exception as card_error:
                    logger.warning(f"Error parsing job card: {str(card_error)}")
            
            logger.info(f"Found {len(job_listings)} jobs from Google Jobs for query: {query}")
            return job_listings
        
        except Exception as e:
            logger.error(f"Selenium job search error: {str(e)}")
            return []
        finally:
            # Close the browser if it was initialized
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as quit_error:
                    logger.error(f"Error closing WebDriver: {str(quit_error)}")
                self.driver = None
                
    def _extract_jobs_from_page_content(self, page_content, query, limit=20):
        """
        Fallback method to extract job information from page content when selectors fail
        """
        try:
            # Create a soup object
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Try to find job-like elements
            job_listings = []
            
            # Look for potential job titles (h3 elements or bold text)
            potential_titles = soup.find_all(['h3', 'b', 'strong'])
            
            for i, title_elem in enumerate(potential_titles[:limit]):
                if i >= limit:
                    break
                    
                title = title_elem.get_text().strip()
                
                # Skip if title is too short or doesn't look like a job title
                if len(title) < 5 or len(title) > 100:
                    continue
                
                # Try to find company name (often near the title)
                company = "Company Not Specified"
                parent = title_elem.parent
                if parent:
                    # Look for text that might be a company name
                    for sibling in parent.find_next_siblings():
                        text = sibling.get_text().strip()
                        if text and 5 < len(text) < 50 and text != title:
                            company = text
                            break
                
                # Create a description from nearby text
                description = ""
                container = title_elem.find_parent('div')
                if container:
                    # Get all text in this container
                    all_text = container.get_text().strip()
                    # Remove the title and company from the text
                    description = all_text.replace(title, "").replace(company, "").strip()
                
                if not description:
                    description = f"Job opportunity for {query} at {company}"
                
                # Create a Google search URL for this job
                title_slug = title.replace(' ', '+')
                company_slug = company.replace(' ', '+')
                job_url = f"https://www.google.com/search?q={title_slug}+{company_slug}+job+apply"
                
                # Extract skills
                skills = extract_skills_from_text(description)
                
                job = {
                    'id': f"google_{random.randint(1000, 9999)}",
                    'title': title,
                    'company': company,
                    'location': "Location not specified",
                    'description': description[:500] + '...' if len(description) > 500 else description,
                    'full_description': description,
                    'source': 'Google Jobs',
                    'url': job_url,
                    'application_url': job_url,
                    'skills': skills,
                    'posted_date': 'Recently',
                    'job_type': 'Not specified'
                }
                
                job_listings.append(job)
            
            return job_listings
            
        except Exception as e:
            logger.error(f"Error extracting jobs from page content: {str(e)}")
            return []

    def search_remotive(self, query, location="", limit=20):
        """
        Search for remote jobs on Remotive API
        
        Args:
            query (str): Job search query (e.g., "python developer")
            location (str): Location filter (optional for remote jobs)
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of job dictionaries
        """
        # Check cache first
        cache_key = f"remotive_{query}_{location}_{limit}"
        if cache_key in self.job_cache and time.time() - self.cache_expiry.get(cache_key, 0) < self.cache_duration:
            logger.info(f"Using cached Remotive results for query: {query}")
            return self.job_cache[cache_key][:limit]
            
        try:
            # Prepare API parameters
            params = {}
            if query:
                params['search'] = query
                
            # Make API request
            response = self.session.get(f"{self.remotive_api_url}", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process results
            jobs = []
            for job in data.get('jobs', [])[:limit]:
                # Extract job details
                job_id = f"remotive_{job.get('id', random.randint(1000, 9999))}"
                title = job.get('title', 'No Title')
                company = job.get('company_name', 'Unknown Company')
                job_location = job.get('candidate_required_location', location or 'Remote')
                description = job.get('description', 'No description available')
                job_url = job.get('url', '')
                job_type = job.get('job_type', 'Unknown')
                salary = job.get('salary', 'Not specified')
                
                # Extract skills from description
                skills = extract_skills_from_text(description)
                
                # Create job object
                job_obj = {
                    'id': job_id,
                    'title': title,
                    'company': company,
                    'location': job_location,
                    'description': description[:500] + '...' if len(description) > 500 else description,  # Truncate long descriptions
                    'full_description': description,
                    'source': 'Remotive',
                    'url': job_url,
                    'application_url': job_url,
                    'job_type': job_type,
                    'salary': salary,
                    'posted_date': job.get('publication_date', 'Recently'),
                    'skills': skills
                }
                
                jobs.append(job_obj)
                
                if len(jobs) >= limit:
                    break
                    
            # Update cache
            self.job_cache[cache_key] = jobs
            self.cache_expiry[cache_key] = time.time()
            
            logger.info(f"Found {len(jobs)} Remotive jobs for query: {query}")
            return jobs
            
        except Exception as e:
            logger.error(f"Remotive API error: {e}")
            return []
            
    def search_adzuna(self, query, location="", limit=20):
        """
        Search for jobs on Adzuna API
        
        Args:
            query (str): Job search query
            location (str): Location for job search
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of job dictionaries
        """
        # Check if API credentials are available
        if not self.adzuna_app_id or not self.adzuna_api_key:
            logger.warning("Adzuna API credentials not found. Set ADZUNA_APP_ID and ADZUNA_API_KEY environment variables.")
            return []
            
        # Check cache first
        cache_key = f"adzuna_{query}_{location}_{limit}"
        if cache_key in self.job_cache and time.time() - self.cache_expiry.get(cache_key, 0) < self.cache_duration:
            logger.info(f"Using cached Adzuna results for query: {query}")
            return self.job_cache[cache_key][:limit]
            
        try:
            # Prepare API parameters
            country = "gb"  # Default to UK
            if location and any(loc in location.lower() for loc in ["us", "united states", "america"]):
                country = "us"
                
            # Construct API URL
            api_url = f"{self.adzuna_api_url}/{country}/search/1"
            
            params = {
                "app_id": self.adzuna_app_id,
                "app_key": self.adzuna_api_key,
                "results_per_page": min(limit, 50),  # API limit
                "what": query,
                "content-type": "application/json"
            }
            
            if location and country == "us":
                # Extract state or city
                location_parts = location.split(",")
                if len(location_parts) > 1:
                    params["where"] = location_parts[0].strip()
                else:
                    params["where"] = location
                    
            # Make API request
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process results
            jobs = []
            for job in data.get('results', [])[:limit]:
                # Extract job details
                job_id = f"adzuna_{job.get('id', random.randint(1000, 9999))}"
                title = job.get('title', 'No Title')
                company = job.get('company', {}).get('display_name', 'Unknown Company')
                job_location = job.get('location', {}).get('display_name', location or 'Unknown')
                description = job.get('description', 'No description available')
                job_url = job.get('redirect_url', '')
                salary = job.get('salary_is_predicted', 'Not specified')
                if isinstance(salary, bool) and job.get('salary_min') and job.get('salary_max'):
                    currency = job.get('salary_currency', '$')
                    salary = f"{currency}{int(job.get('salary_min', 0)):,} - {currency}{int(job.get('salary_max', 0)):,}"
                
                # Format posted date
                posted_date = 'Recently'
                if 'created' in job:
                    try:
                        date_obj = datetime.strptime(job['created'], "%Y-%m-%dT%H:%M:%SZ")
                        days_ago = (datetime.now() - date_obj).days
                        posted_date = f"{days_ago} days ago" if days_ago > 0 else "Today"
                    except Exception:
                        pass
                
                # Extract skills from description
                skills = extract_skills_from_text(description)
                
                # Create job object
                job_obj = {
                    'id': job_id,
                    'title': title,
                    'company': company,
                    'location': job_location,
                    'description': description[:500] + '...' if len(description) > 500 else description,  # Truncate long descriptions
                    'full_description': description,
                    'source': 'Adzuna',
                    'url': job_url,
                    'application_url': job_url,
                    'job_type': job.get('contract_type', 'Unknown'),
                    'salary': salary,
                    'posted_date': posted_date,
                    'skills': skills
                }
                
                jobs.append(job_obj)
                
                if len(jobs) >= limit:
                    break
                    
            # Update cache
            self.job_cache[cache_key] = jobs
            self.cache_expiry[cache_key] = time.time()
            
            logger.info(f"Found {len(jobs)} Adzuna jobs for query: {query}")
            return jobs
            
        except Exception as e:
            logger.error(f"Adzuna API error: {e}")
            return []
            
    def search_github_jobs(self, query, location="", limit=20):
        """
        Search for jobs on GitHub Jobs
        
        Args:
            query (str): Job search query
            location (str): Location for job search
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of job dictionaries
        """
        # Check cache first
        cache_key = f"github_{query}_{location}_{limit}"
        if cache_key in self.job_cache and time.time() - self.cache_expiry.get(cache_key, 0) < self.cache_duration:
            logger.info(f"Using cached GitHub Jobs results for query: {query}")
            return self.job_cache[cache_key][:limit]
            
        try:
            # GitHub Jobs API is deprecated, but we can scrape the GitHub Jobs page
            # Initialize the driver if not already done
            if not self.driver:
                self.driver = self._setup_webdriver()
                
            # Construct GitHub Jobs search URL
            base_url = "https://jobs.github.com/positions"
            params = {}
            if query:
                params['description'] = query
            if location:
                params['location'] = location
                
            url = f"{base_url}?{urlencode(params)}"
            
            # Navigate to GitHub Jobs
            self.driver.get(url)
            
            # Wait for job results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job"))
            )
            
            # Find job listings
            job_listings = []
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job")
            
            for job_elem in job_elements[:limit]:
                try:
                    # Extract job details
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, ".title h4 a")
                    title = title_elem.text
                    job_url = title_elem.get_attribute("href")
                    
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".company")
                    company = company_elem.text
                    
                    location_elem = job_elem.find_element(By.CSS_SELECTOR, ".location")
                    job_location = location_elem.text
                    
                    # Get job description by visiting the job URL
                    self.driver.get(job_url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".job-description"))
                    )
                    
                    description_elem = self.driver.find_element(By.CSS_SELECTOR, ".job-description")
                    description = description_elem.text
                    
                    # Extract skills from description
                    skills = extract_skills_from_text(description)
                    
                    # Create job object
                    job_obj = {
                        'id': f"github_{random.randint(1000, 9999)}",
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'description': description[:500] + '...' if len(description) > 500 else description,  # Truncate long descriptions
                        'full_description': description,
                        'source': 'GitHub Jobs',
                        'url': job_url,
                        'application_url': job_url,
                        'job_type': extract_job_type(description),
                        'salary': 'Not specified',
                        'posted_date': 'Recently',
                        'skills': skills
                    }
                    
                    job_listings.append(job_obj)
                    
                    # Go back to search results
                    self.driver.back()
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".job"))
                    )
                    
                    if len(job_listings) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error parsing GitHub job: {e}")
                    continue
                    
            # Update cache
            self.job_cache[cache_key] = job_listings
            self.cache_expiry[cache_key] = time.time()
            
            logger.info(f"Found {len(job_listings)} GitHub jobs for query: {query}")
            return job_listings
            
        except Exception as e:
            logger.error(f"GitHub Jobs search error: {e}")
            return []
        finally:
            # Close the browser if it was initialized
            if self.driver:
                self.driver.quit()
                self.driver = None
                
    def search_jobs(self, query, location="", sources=None, limit=20):
        """
        Search for jobs across multiple sources
        
        Args:
            query (str): Job search query
            location (str): Location for job search
            sources (list): List of sources to search ("remotive", "adzuna", "github", "google")
            limit (int): Maximum number of jobs to return
            
        Returns:
            list: List of job dictionaries
        """
        if not sources:
            sources = ["remotive", "adzuna", "github", "google"]
            
        # Calculate jobs per source
        jobs_per_source = max(5, limit // len(sources))
        
        all_jobs = []
        
        # Search each source
        for source in sources:
            try:
                if source == "remotive":
                    jobs = self.search_remotive(query, location, jobs_per_source)
                elif source == "adzuna":
                    jobs = self.search_adzuna(query, location, jobs_per_source)
                elif source == "github":
                    jobs = self.search_github_jobs(query, location, jobs_per_source)
                elif source == "google":
                    jobs = self.search_google_jobs(query, location, jobs_per_source)
                else:
                    continue
                    
                all_jobs.extend(jobs)
                
            except Exception as e:
                logger.error(f"Error searching {source}: {e}")
                continue
                
        # Deduplicate jobs by title and company
        unique_jobs = []
        seen = set()
        
        for job in all_jobs:
            key = f"{job['title']}_{job['company']}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
                
        # Sort by relevance (presence of query terms in title)
        query_terms = query.lower().split()
        
        def relevance_score(job):
            title = job['title'].lower()
            score = sum(term in title for term in query_terms) * 10
            
            # Boost score for jobs with more details
            if job.get('skills') and len(job.get('skills', [])) > 0:
                score += 5
            if job.get('salary') and job['salary'] != 'Not specified':
                score += 3
            if job.get('full_description') and len(job.get('full_description', '')) > 100:
                score += 2
                
            return score
            
        unique_jobs.sort(key=relevance_score, reverse=True)
        
        return unique_jobs[:limit]

# Helper functions for job parsing
def extract_skills_from_text(text):
    """
    Extract potential skills from job description text
    
    Args:
        text (str): Job description text
        
    Returns:
        list: List of potential skills
    """
    # Common tech skills to look for
    common_skills = [
        # Programming languages
        "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Go",
        "TypeScript", "Rust", "Scala", "Perl", "R", "MATLAB", "Objective-C", "Dart", "Groovy",
        
        # Web technologies
        "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
        "Spring", "ASP.NET", "Laravel", "Ruby on Rails", "jQuery", "Bootstrap", "Tailwind",
        
        # Data science & ML
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras", "scikit-learn",
        "Data Science", "Data Analysis", "NLP", "Computer Vision", "AI", "Artificial Intelligence",
        "Statistics", "Big Data", "Data Mining", "Data Visualization", "Tableau", "Power BI",
        
        # Databases
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "Oracle", "SQLite", "NoSQL", "Redis",
        "Elasticsearch", "Cassandra", "DynamoDB", "Firebase", "GraphQL",
        
        # DevOps & Cloud
        "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "CI/CD",
        "Git", "GitHub", "GitLab", "Terraform", "Ansible", "Puppet", "Chef", "Prometheus",
        "Grafana", "ELK Stack", "Serverless", "Microservices",
        
        # Mobile
        "Android", "iOS", "React Native", "Flutter", "Xamarin", "Cordova", "Ionic",
        
        # Other technical skills
        "Agile", "Scrum", "Jira", "REST API", "GraphQL", "WebSockets", "Testing", "QA",
        "Selenium", "JUnit", "TestNG", "Cypress", "Jest", "Mocha", "Chai", "Security",
        "Blockchain", "Cryptography", "UI/UX", "Design Patterns", "OOP", "Functional Programming",
        
        # Soft skills
        "Communication", "Teamwork", "Problem Solving", "Leadership", "Time Management",
        "Critical Thinking", "Creativity", "Adaptability", "Project Management"
    ]
    
    # Find skills in text
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        if skill.lower() in text_lower:
            found_skills.append(skill)
            
    # Limit to top 15 skills
    return found_skills[:15]

def extract_job_type(text):
    """
    Extract job type from description
    
    Args:
        text (str): Job description text
        
    Returns:
        str: Job type
    """
    text_lower = text.lower()
    
    if "full-time" in text_lower or "full time" in text_lower:
        return "Full-time"
    elif "part-time" in text_lower or "part time" in text_lower:
        return "Part-time"
    elif "contract" in text_lower:
        return "Contract"
    elif "freelance" in text_lower:
        return "Freelance"
    elif "internship" in text_lower or "intern" in text_lower:
        return "Internship"
    elif "temporary" in text_lower or "temp" in text_lower:
        return "Temporary"
    else:
        return "Full-time"  # Default

def get_jobs_with_matching(query, location="", resume_skills=None, limit=20):
    """
    Get jobs with resume matching scores
    
    Args:
        query (str): Job search query
        location (str): Location for job search
        resume_skills (list): List of skills from the resume
        limit (int): Maximum number of jobs to return
        
    Returns:
        list: List of job dictionaries with match scores
    """
    scraper = JobScraper()  # Default to Edge
    
    # Try to get jobs from multiple sources
    jobs = scraper.search_jobs(query, location, sources=["remotive", "adzuna", "github", "google"], limit=limit)
    
    # If no jobs found, fall back to Google Jobs
    if not jobs:
        jobs = scraper.search_google_jobs(query, location, limit)
    
    # If resume skills are provided, calculate match score
    if resume_skills:
        for job in jobs:
            # Get job skills from the job object or extract from description
            job_skills = job.get('skills', [])
            if not job_skills:
                job_skills = extract_skills_from_text(job.get('description', ''))
                job['skills'] = job_skills
            
            # Convert skills to lowercase for comparison
            resume_skills_lower = [skill.lower() for skill in resume_skills]
            job_skills_lower = [skill.lower() for skill in job_skills]
            
            # Find matching skills
            matching_skills = set()
            for r_skill in resume_skills_lower:
                for j_skill in job_skills_lower:
                    if r_skill in j_skill or j_skill in r_skill:
                        matching_skills.add(j_skill)
            
            # Calculate match score
            if job_skills:
                match_score = (len(matching_skills) / len(job_skills)) * 100
            else:
                match_score = 0
                
            job['match_score'] = int(match_score)
            job['matching_skills'] = list(matching_skills)
    
    return jobs

# Example usage
if __name__ == "__main__":
    scraper = JobScraper()
    jobs = scraper.search_jobs("Python Developer", "Remote", limit=5)
    print(f"Found {len(jobs)} jobs")
    for job in jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Source: {job['source']}")
        print(f"Skills: {', '.join(job.get('skills', []))}")
