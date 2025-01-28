import os
import logging
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import PyPDF2
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import base64
import time
import pandas as pd
import plotly.express as px
import pytz  # Add this line
import requests  # Add this line

# Role Requirements
ROLE_REQUIREMENTS = {
    "ai_ml_engineer": """
        Required Skills:
        - Python, PyTorch/TensorFlow
        - Machine Learning algorithms
        - Deep Learning
        - MLOps
        - RAG, LLM, Prompt Engineering
    """,
    "full_stack_engineer": """
        Required Skills:
        - JavaScript, React.js, Node.js
        - HTML/CSS, SASS
        - Database Management (SQL, NoSQL)
        - REST APIs, GraphQL
        - Cloud Deployment (AWS, Azure, GCP)
        - Version Control (Git)
    """,
    "frontend_engineer": """
        Required Skills:
        - JavaScript, React.js
        - HTML/CSS
        - UI/UX Design
        - Responsive Design
        - State Management (e.g., Redux)
    """,
    "backend_engineer": """
        Required Skills:
        - Python, Django/Flask
        - REST APIs
        - Database Management
        - Cloud Services
        - Performance Optimization
    """
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def match_skills_to_role(resume_text, role):
    """Match candidate's skills to role requirements and calculate match score."""
    required_skills = ROLE_REQUIREMENTS[role]["skills"]
    experience_keywords = ROLE_REQUIREMENTS[role]["experience_keywords"]
    
    # Convert resume text to lowercase
    resume_text = resume_text.lower()
    
    # Count skill matches in resume text
    skill_matches = sum(1 for skill in required_skills if skill.lower() in resume_text)
    
    # Count experience-related matches (projects, experience, etc.)
    experience_matches = sum(1 for keyword in experience_keywords if keyword.lower() in resume_text)

    # Calculate match score as a weighted average (skills match + experience match)
    skill_score = skill_matches / len(required_skills)
    experience_score = experience_matches / len(experience_keywords)

    # Total match score (out of 1)
    total_score = (skill_score * 0.7) + (experience_score * 0.3)  # 70% weight on skills, 30% on experience

    return total_score

def analyze_resume(resume_text: str, role: str) -> tuple[bool, str]:
    """Analyze resume and match with role requirements."""
    is_selected = role in resume_text
    if is_selected:
        feedback = f"Your resume matches the requirements for {role}"
    else:
        feedback = """
        The candidate has strong AI/ML skills and project experience, particularly in AI systems and cloud infrastructure.
        However, the candidate lacks direct experience with frontend technologies such as React, Vue.js, or Angular, 
        as well as skills specific to frontend testing, responsive design, and state management. Although JavaScript knowledge 
        is present, related technologies like HTML5, CSS3, and TypeScript, integral to the role, are not highlighted.
        Additionally, the candidate's experience is more aligned with backend and AI-driven applications rather than frontend development.
        """
    return is_selected, feedback

def send_email(sender_email, sender_password, receiver_email, subject, body):
    """Send an email with the given subject and body."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            logger.info(f"Email sent to {receiver_email} with subject: {subject}")
            return "Email sent successfully!"
    except Exception as e:
        logger.error(f"Failed to send email to {receiver_email}: {str(e)}")
        return f"Failed to send email: { str(e)}"

def send_selection_email(candidate_email, role, company_name, sender_email, sender_password):
    """Send selection email to the candidate."""
    subject = "Congratulations! You are Selected for the Next Stage"
    body = f"""
        Dear Candidate,

        Congratulations! You meet the requirements for the {role} role at {company_name}.
        We are excited to invite you to the next stage of the interview process.

        Best Regards,
        {company_name}
    """
    return send_email(sender_email, sender_password, candidate_email, subject, body)

def send_interview_email(candidate_email, role, interview_date, company_name, sender_email, sender_password, meeting_link):
    """Send interview details email to the candidate."""
    subject = f"Interview Scheduled for {role} Role"
    body = f"""
        Dear Candidate,

        Your interview for the {role} role at {company_name} has been scheduled.

        Interview Details:
        - Date: {interview_date.strftime('%Y-%m-%d')}
        - Time: {interview_date.strftime('%H:%M:%S')} (Your Time Zone)
        - Duration: 45 minutes
        - Interview Format: Technical interview followed by Q&A
        - Zoom Meeting Link: {meeting_link}

        Please be prepared to discuss your experience and skills.

        If you have any questions, feel free to reach out to us.

        Best Regards,
        {company_name}
    """
    return send_email(sender_email, sender_password, candidate_email, subject, body)

def send_rejection_email(sender_email, sender_password, receiver_email, role, company) -> None:
    """Send a rejection email to the candidate."""
    
    # Constructing the subject and body of the rejection email
    subject = f"Regarding your application for the {role} role"
    
    body = f"""
    Dear Candidate,
    
    Thank you for your interest in the {role} role at {company}. Unfortunately, we regret to inform you that we will not be proceeding with your application at this time.
    
    While we were impressed with your qualifications, we have decided to move forward with other candidates who more closely match the requirements for this role.
    
    We encourage you to continue preparing and working hard to improve your skills. Please don't be discouraged—your next opportunity may be just around the corner. We welcome you to apply again for future positions with us.

    We wish you all the best in your career journey.
    
    Best regards,
    {company}
    """

    # Creating MIMEText object for email
    msg = MIMEText(body, 'plain', 'utf-8')
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Sending the email through Gmail's SMTP server
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Start TLS encryption
            server.login(sender_email, sender_password)  # Login with the sender's credentials
            server.sendmail(sender_email, receiver_email, msg.as_string())  # Send the email
            logger.info(f"Rejection email sent to {receiver_email} for role: {role}")
    except Exception as e:
        logger.error(f"Failed to send rejection email to {receiver_email}: {str(e)}")

def configure_sidebar():
    """Configure sidebar settings."""
    st.sidebar.header("Configuration")

    # Initialize session state values only if not already initialized
    if "sidebar_openai_api_key" not in st.session_state:
        st.session_state["sidebar_openai_api_key"] = ""
    if "sidebar_zoom_account_id" not in st.session_state:
        st.session_state["sidebar_zoom_account_id"] = ""
    if "sidebar_zoom_client_id" not in st.session_state:
        st.session_state["sidebar_zoom_client_id"] = ""
    if "sidebar_zoom_client_secret" not in st.session_state:
        st.session_state["sidebar_zoom_client_secret"] = ""
    if "sidebar_sender_email" not in st.session_state:
        st.session_state["sidebar_sender_email"] = ""
    if "sidebar_email_app_password" not in st.session_state:
        st.session_state["sidebar_email_app_password"] = ""
    if "sidebar_company_name" not in st.session_state:
        st.session_state["sidebar_company_name"] = ""

    # Flag to reset configuration
    if "reset_config" not in st.session_state:
        st.session_state["reset_config"] = False

    # Reset configuration button
    if st.sidebar.button("Reset Configuration"):
        # Set the flag to trigger reset
        st.session_state["reset_config"] = True
        st.rerun()

    # Set widget values based on reset flag
    if st.session_state["reset_config"]:
        st.session_state["sidebar_openai_api_key"] = ""
        st.session_state["sidebar_zoom_account_id"] = ""
        st.session_state[" sidebar_zoom_client_id"] = ""
        st.session_state["sidebar_zoom_client_secret"] = ""
        st.session_state["sidebar_sender_email"] = ""
        st.session_state["sidebar_email_app_password"] = ""
        st.session_state["sidebar_company_name"] = ""

    # Define the widgets, using session state values as the default value
    openai_api_key = st.sidebar.text_input(
        "OpenAI API Key", 
        type="password", 
        key="sidebar_openai_api_key",
        value=st.session_state["sidebar_openai_api_key"]
    )
    zoom_account_id = st.sidebar.text_input(
        "Zoom Account ID", 
        type="password", 
        key="sidebar_zoom_account_id",
        value=st.session_state["sidebar_zoom_account_id"]
    )
    zoom_client_id = st.sidebar.text_input(
        "Zoom Client ID", 
        type="password", 
        key="sidebar_zoom_client_id",
        value=st.session_state["sidebar_zoom_client_id"]
    )
    zoom_client_secret = st.sidebar.text_input(
        "Zoom Client Secret", 
        type="password", 
        key="sidebar_zoom_client_secret",
        value=st.session_state["sidebar_zoom_client_secret"]
    )
    sender_email = st.sidebar.text_input(
        "Sender Email", 
        key="sidebar_sender_email",
        value=st.session_state["sidebar_sender_email"]
    )
    email_app_password = st.sidebar.text_input(
        "Email App Password", 
        type="password", 
        key="sidebar_email_app_password",
        value=st.session_state["sidebar_email_app_password"]
    )
    company_name = st.sidebar.text_input(
        "Company Name", 
        key="sidebar_company_name",
        value=st.session_state["sidebar_company_name"]
    )

    # Reset the flag after the reset action
    if st.session_state["reset_config"]:
        st.session_state["reset_config"] = False

    return {
        "openai_api_key": openai_api_key,
        "zoom_account_id": zoom_account_id,
        "zoom_client_id": zoom_client_id,
        "zoom_client_secret": zoom_client_secret,
        "sender_email": sender_email,
        "email_app_password": email_app_password,
        "company_name": company_name,
    }

# Call the function
config = configure_sidebar()

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    return "".join([page.extract_text() for page in pdf_reader.pages])

def pdf_to_png(pdf_file):
    """Convert PDF pages to PNG images for display."""
    pdf_file.seek(0)
    pdf_bytes = pdf_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        st.image(img, caption=f"Page {i+1}", use_container_width=True)

def download_button_with_icon(pdf_file):
    """Display a download button for the resume with an icon."""
    # Reset the file pointer to the beginning
    pdf_file.seek(0)
    
    # Read the PDF bytes
    pdf_bytes = pdf_file.read()
    
    # Encode the PDF bytes to Base64
    encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Resume Preview")
        pdf_to_png(pdf_file)

    with col2:
        st.markdown(
            f'<a href="data:application/pdf;base64,{encoded_pdf}" download="resume.pdf">'
            f'<button style="font-size: 16px;">&#8595; Download Resume</button></a>',
            unsafe_allow_html=True
        )
    
    # Instructions for the user
    st.markdown("### Instructions:")
    st.write("After downloading, please open the 'resume.pdf' file to review your resume.")
    
def initialize_metrics():
    """Initialize metrics in session state."""
    if 'metrics' not in st.session_state:
        st.session_state.metrics = {
            'total_resumes_uploaded': 0,
            'selected_candidates': 0,
            'interviews_scheduled': 0,
            'applications_by_role': {role: 0 for role in ROLE_REQUIREMENTS.keys()}
        }
        
        # Initialize selected and interviewed counts for each role
        for role in ROLE_REQUIREMENTS.keys():
            st.session_state.metrics[f"{role}_selected"] = 0
            st.session_state.metrics[f"{role}_interviewed"] = 0

# Initialize a list to store scheduled interviews
scheduled_interviews = []

def schedule_interview(candidate_email, role, selected_slot):
    """Schedule an interview and store the details."""
    scheduled_interviews.append({
        "Email": candidate_email,
        "Role": role,
        "Date": selected_slot.date(),
        "Time": selected_slot.time()
    })

def display_scheduled_interviews():
    """Display the scheduled interviews in a table."""
    if scheduled_interviews:
        st.subheader("Scheduled Interviews")
        st.table(scheduled_interviews)
    else:
        st.write("No interviews scheduled yet.")

def update_metrics(role, is_selected):
    """Update metrics based on the role and selection status."""
    if 'metrics' not in st.session_state:
        logger.error("Metrics not initialized in session state.")
        return

    # Increment total resumes uploaded
    st.session_state.metrics['total_resumes_uploaded'] += 1
    st.session_state.metrics['applications_by_role'][role] += 1

    # Check if the role-specific keys exist, if not initialize them
    if f"{role}_selected" not in st.session_state.metrics:
        st.session_state.metrics[f"{role}_selected"] = 0
    if f"{role}_interviewed" not in st.session_state.metrics:
        st.session_state.metrics[f"{role}_interviewed"] = 0

    if is_selected:
        st.session_state.metrics['selected_candidates'] += 1
        st.session_state.metrics[f"{role}_selected"] += 1  # Increment selected for this role
        st.session_state.metrics['interviews_scheduled'] += 1
        st.session_state.metrics[f"{role}_interviewed"] += 1  # Increment interviewed for this role

def show_analytics():
    st.header("Recruitment Analytics Dashboard")
    
    # Check if metrics exist in session_state
    if "metrics" not in st.session_state or not st.session_state.metrics:
        st.error("Metrics data is not available.")
        return

    # Fetch metrics
    metrics = st.session_state.metrics
    
    # Display key metrics
    st.metric(label="Total Resumes Uploaded", value=metrics['total_resumes_uploaded'])
    
    # Prepare data for role-wise applications
    role_counts = pd.DataFrame({
        'Role': list(metrics['applications_by_role'].keys()),
        'Applications': list(metrics['applications_by_role'].values()),
        'Selected Candidates': [metrics.get(f"{role}_selected", 0) for role in ROLE_REQUIREMENTS],
        'Interviews Scheduled': [metrics.get(f"{role}_interviewed", 0) for role in ROLE_REQUIREMENTS]
    })
    
    st.subheader("Applications by Role")
    st.dataframe(role_counts)  # Display as table

    # Plot graph
    fig = px.bar(
        role_counts, 
        x='Role', 
        y='Applications', 
        title='Applications per Role', 
        color='Role', 
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig)

    # Calculate selection rate
    if metrics['total_resumes_uploaded'] > 0:
        selection_rate = (metrics['selected_candidates'] / metrics['total_resumes_uploaded']) * 100
        st.metric(label="Selection Rate (%)", value=f"{selection_rate:.2f}%")
    else:
        st.warning("No resumes uploaded yet.")

    # Display scheduled interviews
    display_scheduled_interviews()

def available_time_slots(selected_date):
    """Return a list of available interview slots for the selected date."""
    available_slots = []
    for hour in range(9, 17):  # From 9 AM to 5 PM
        available_slots.append(datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=hour))
    return available_slots

def schedule_zoom_meeting(zoom_acc_id, zoom_client_id, zoom_secret, role, interview_date, company_name):
    """Schedule a Zoom meeting and return the meeting link."""
    try:
        # Convert the scheduled datetime to UTC for Zoom API
        local_tz = pytz.timezone("UTC")  # Assuming UTC for simplicity
        local_dt = local_tz.localize(interview_date, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        meeting_time_iso = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format

        # Step 2: Get Zoom OAuth token
        zoom_token_url = "https://zoom.us/oauth/token"
        zoom_payload = {
            'grant_type': 'account_credentials',
            'account_id': zoom_acc_id
        }
        auth = (zoom_client_id, zoom_secret)

        token_response = requests.post(zoom_token_url, data=zoom_payload, auth=auth)
        token_response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
        access_token = token_response.json().get('access_token')
        if not access_token:
            raise ValueError("Failed to fetch Zoom access token.")

        # Step 3: Schedule a Zoom meeting
        zoom_meeting_url = "https://api.zoom.us/v2/users/me/meetings"
        meeting_details = {
            "topic": f"Interview for {role}",
            "type": 2,  # Scheduled meeting
            "start_time": meeting_time_iso,
            "duration": 60,  # Meeting duration in minutes
            "timezone": "UTC",
            "settings": {
                "join_before_host": True,
                "waiting_room": False
            }
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        meeting_response = requests.post(zoom_meeting_url, json=meeting_details, headers=headers)
        meeting_response.raise_for_status()  # This will raise an error for 4xx and 5xx responses
        meeting_data = meeting_response.json()
        meeting_link = meeting_data.get('join_url')

        if not meeting_link:
            raise ValueError("Failed to schedule Zoom meeting.")

        return meeting_link

    except Exception as e:
        logger.error(f"Error scheduling Zoom meeting: {str(e)}")
        return None

def generate_assessment_url(role):
    # Generate a unique assessment URL for each role
    if role == "ai_ml_engineer":
        return "https://docs.google.com/forms/d/e/1FAIpQLScIMEtmyc6HquDLB7ir0VQWEFOhY5qwf9snYiUoBJwG1x7D_w/viewform?usp=dialog"
    elif role == "full_stack_engineer":
        return "https://docs.google.com/forms/d/e/1FAIpQLSdz6e0rqTngQIlUJXDKSeUtwmCj7ifIkdGcEHb7rM5YkReLWg/viewform?usp=dialog"
    elif role == "frontend_engineer":
        return "https://docs.google.com/forms/d/e/1FAIpQLScIMEtmyc6HquDLB7ir0VQWEFOhY5qwf9snYiUoBJwG1x7D_w/viewform?usp=dialog"
    elif role == "backend_engineer":
        return "https://docs.google.com/forms/d/e/1FAIpQLScIMEtmyc6HquDLB7ir0VQWEFOhY5qwf9snYiUoBJwG1x7D_w/viewform?usp=dialog"
    else:
        return "https://coding-assessment-platform.com"

def main():
    st.title("VisionHire Recruitment System")
    st.markdown("Please configure the following in the sidebar: Email Sender, Email Password, Company Name")
    
    initialize_metrics()
    st.sidebar.button("Show Analytics", on_click=show_analytics)

    selected_tab = st.selectbox("Choose Tab", ["Resume Analysis", "Coding Assessment"])

    if st.button("Check Configuration"):
        if all(config.values()):
            st.success("All configurations are set!")
        else:
            st.error("Some configurations are missing! Please complete all fields.")

    if st.button("Add New Application"):
        st.session_state.resume_text = ""
        st.success("Ready for a new application!")
        st.rerun()

    st.header("Resume Analysis and Interview Scheduling")
    
    role = st.selectbox("Enter the role you want to evaluate", 
                        ["Select a role", "ai_ml_engineer", "full_stack_engineer", "frontend_engineer", "backend_engineer"])

    if role != "Select a role":
        st.subheader(f"Role Requirements for {role.replace('_', ' ').title()}:")
        st.markdown(ROLE_REQUIREMENTS[role])

        st.subheader("Please rate the following competencies (1-10 scale):")
        
        competencies = {
            "Technical Skills (Python, PyTorch/TensorFlow)": 0,
            "Machine Learning Algorithms": 0,
            "Deep Learning": 0,
            "MLOps": 0,
            "RAG, LLM, Prompt Engineering": 0
        }

        if role != "ai_ml_engineer":
            competencies = {
                "Technical Skills (JavaScript, React.js, Node.js)": 0,
                "Database Management (SQL, NoSQL)": 0,
                "REST APIs, GraphQL": 0,
                "Cloud Deployment (AWS, Azure, GCP)": 0,
                "Version Control (Git)": 0
            }

        for competency in competencies.keys():
            competencies[competency] = st.slider(competency, 1, 10, 5)
        
        final_score = sum(competencies.values()) / len(competencies)
        
        st.subheader(f"Final Score for {role.replace('_', ' ').title()}: {final_score:.2f} / 10")

        if final_score >= 8.5:
            feedback = "Excellent candidate, highly skilled in all areas."
        elif final_score >= 7:
            feedback = "Good candidate, may require some improvement in certain areas."
        elif final_score >= 5:
            feedback = "Candidate is average, may need significant improvement."
        else:
            feedback = "Candidate may not meet the role requirements."

        st.write(f"Feedback: {feedback}")
        
    if selected_tab == "Coding Assessment":
        role = st.selectbox("Select Role for Assessment", ["ai_ml_engineer", "full_stack_engineer", "frontend_engineer", "backend_engineer"], key="assessment_role_selector")
        if role != "Select a role":
            assessment_url = generate_assessment_url(role)
            st.subheader(f"Coding Assessment for {role.replace('_', ' ').title()}")
            st.markdown(f"[Start Coding Assessment]({assessment_url})")
            st.write("This link will take you to the coding assessment platform with 10 questions based on the selected role.")
    
    resume_file = st.file_uploader("Upload Resume", type=["pdf"])
    if resume_file:
        resume_text = extract_text_from_pdf(resume_file)
        st.session_state.resume_text = resume_text
        download_button_with_icon(resume_file)
        st.success("Resume uploaded successfully!")

        candidate_email = st.text_input("Candidate Email", value="candidate@example.com")

        if st.button("Analyze Resume"):
            with st.spinner("Analyzing resume..."):
                time.sleep(5)
                is_selected, feedback = analyze_resume(resume_text, role)
                st.session_state.is_selected = is_selected
                st.session_state.feedback = feedback
                if is_selected:
                    st.success(f"Selected: You are selected", icon="✅")
                else:
                    st.error(f"Selected: Not selected", icon="❌")
                    update_metrics(role, is_selected)

                st.write(f"Feedback: {feedback}")
                if is_selected:
                    st.success("ALL THE BEST! Proceed to interview scheduling.")
                else:
                    st.error("Unfortunately, your skills don't match our requirement. Better luck next time!")
                    send_rejection_email(config["sender_email"], config["email_app_password"], candidate_email, role, config["company_name"])

    if 'resume_text' in st.session_state and 'is_selected' in st.session_state:
        is_selected = st.session_state.is_selected
        if is_selected:
            st.header("Proceed to Interview Scheduling")
            
            selected_date = st.date_input("Select Interview Date", min_value=datetime.now().date() + timedelta(days=3))
            available_slots = available_time_slots(selected_date)

            selected_slot = st.selectbox("Choose your preferred time slot", available_slots)

            proceed_selected = st.checkbox("Confirm to Send Email")
            send_button_disabled = not proceed_selected

            if st.button("Send Email and Schedule Interview", disabled=send_button_disabled):
                if resume_text:
                    email_status = ""
                    email_status += send_selection_email(candidate_email, role, config["company_name"], config["sender_email"], config["email_app_password"]) + "\n"
                    
                    if is_selected:
                        meeting_link = schedule_zoom_meeting(
                            config["zoom_account_id"],
                            config["zoom_client_id"],
                            config["zoom_client_secret"],
                            role,
                            selected_slot,
                            config["company_name"]
                        )
                        if meeting_link:
                            email_status += send_interview_email(candidate_email, role, selected_slot, config["company_name"], config["sender_email"], config["email_app_password"], meeting_link) + "\n"
                            st.success("Interview scheduling email has been sent to the candidate!")
                            
                            # Schedule the interview
                            schedule_interview(candidate_email, role, selected_slot)
                            
                        else:
                            st.error("Failed to schedule Zoom meeting. Please check your Zoom credentials.")
                            
                    update_metrics(role, is_selected)

if __name__ == "__main__":
    main()