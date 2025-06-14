import pandas as pd
import random
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle

# Skills, education, and job roles
skill_list = ['Python', 'Java', 'SQL', 'Machine Learning', 'Deep Learning', 'NLP', 'Data Analysis', 'AWS', 'Docker']
education_levels = ['Bachelors', 'Masters', 'PhD']
job_roles = ['Data Scientist', 'ML Engineer', 'Software Developer', 'Data Analyst']

# Generate random resume
def generate_resume():
    return {
        'Candidate_ID': f'C{random.randint(1, 10000)}',  # Increased ID range
        'Skills': random.sample(skill_list, k=random.randint(2, 6)),
        'Experience': random.randint(0, 12),
        'Education': random.choice(education_levels)
    }

# Generate random job
def generate_job():
    return {
        'Job_ID': f'J{random.randint(1, 500)}',  # Increased ID range
        'Required_Skills': random.sample(skill_list, k=random.randint(3, 5)),
        'Min_Experience': random.randint(0, 10),  # Increased experience range
        'Preferred_Education': random.choice(education_levels),
        'Role': random.choice(job_roles)
    }

# Increase dataset complexity with noise
def add_noise_to_dataset():
    global resume_df, job_df
    resume_df['Skills'] = resume_df['Skills'].apply(lambda x: random.sample(skill_list, k=random.randint(2, 6)))
    job_df['Required_Skills'] = job_df['Required_Skills'].apply(lambda x: random.sample(skill_list, k=random.randint(3, 5)))

# Create dataset
resume = [generate_resume() for _ in range(1000)]  # Increased dataset size
job = [generate_job() for _ in range(100)]  # Increased job postings

resume_df = pd.DataFrame(resume)
job_df = pd.DataFrame(job)

# Encode Education and Job Role
education_encoder = LabelEncoder()
resume_df['Education_encoded'] = education_encoder.fit_transform(resume_df['Education'])

role_encoder = LabelEncoder()
job_df['Role_encoded'] = role_encoder.fit_transform(job_df['Role'])

# Skill match
def skill_match(resume_skills, job_skills):
    if not resume_skills or not job_skills:
        return 0
    return len(set(resume_skills).intersection(set(job_skills))) / len(job_skills)

# Education match
def education_match(resume_edu, job_edu):
    levels = {'Bachelors': 1, 'Masters': 2, 'PhD': 3}
    return 1 if levels.get(resume_edu, 0) >= levels.get(job_edu, 0) else 0

# Experience gap
def experience_gap(resume_exp, job_exp):
    return resume_exp - job_exp

# Add noise
add_noise_to_dataset()

# Build dataset for matching
match_data = []

for _, resume in resume_df.iterrows():
    for _, job in job_df.iterrows():
        skill_score = skill_match(resume['Skills'], job['Required_Skills'])
        edu_match = education_match(resume['Education'], job['Preferred_Education'])
        exp_gap = experience_gap(resume['Experience'], job['Min_Experience'])

        suitable = 1 if (skill_score >= 0.6 and edu_match and exp_gap >= 0) else 0

        match_data.append({
            'Candidate_ID': resume['Candidate_ID'],
            'Job_ID': job['Job_ID'],
            'Education_encoded': resume['Education_encoded'],
            'Experience': resume['Experience'],
            'Job_Role_encoded': job['Role_encoded'],
            'Skill_Match': skill_score,
            'Education_Match': edu_match,
            'Experience_Gap': exp_gap,
            'Suitable': suitable
        })

# Save matches to CSV
matches_df = pd.DataFrame(match_data)
matches_df.to_csv('noisy_large_matches.csv', index=False)
print("✅ Large dataset with noise created!")

# Features and Target
X = matches_df[['Education_encoded', 'Experience', 'Job_Role_encoded', 'Skill_Match', 'Education_Match', 'Experience_Gap']]
y = matches_df['Suitable']

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Random Forest model
rf = RandomForestClassifier(random_state=42)
rf.fit(X_train, y_train)

# XGBoost model
xgb = XGBClassifier(eval_metric='logloss', random_state=42)
xgb.fit(X_train, y_train)

# Evaluation function
def evaluate_model(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    print(f"🔹 {name} Evaluation:")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 3))
    print("Precision:", round(precision_score(y_test, y_pred), 3))
    print("Recall:", round(recall_score(y_test, y_pred), 3))
    print("F1 Score:", round(f1_score(y_test, y_pred), 3))
    print("------")

# Evaluate both models
evaluate_model('Random Forest', rf, X_test, y_test)
evaluate_model('XGBoost', xgb, X_test, y_test)

# Choose the best model (Assuming XGBoost is better)
best_model = xgb

# Save the best model
with open('model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

print("✅ Best Model saved successfully!")
