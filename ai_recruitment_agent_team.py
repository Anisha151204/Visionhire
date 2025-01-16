import os
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

import requests
from datetime import datetime, timedelta

# OAuth Access Token (replace with your token)
ZOOM_OAUTH_ACCESS_TOKEN = "your_oauth_access_token"

def generate_zoom_link():
    """Generate Zoom meeting link using OAuth token."""
    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {ZOOM_OAUTH_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Define meeting details (you can customize this as needed)
    data = {
        "topic": "Interview",
        "type": 2,  # Scheduled meeting
        "start_time": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration": 45,
        "timezone": "UTC",
        "agenda": "Interview for the role"
    }
    
    # Send POST request to Zoom API
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:  # Meeting created successfully
        meeting_info = response.json()
        meeting_url = meeting_info.get("join_url")
        return meeting_url
    else:
        # Log the error for debugging
        error_message = response.json().get("message", "Unknown error")
        return f"Error creating Zoom meeting: {error_message}"

# Test the function
zoom_link = generate_zoom_link()
if "Error" in zoom_link:
    print(zoom_link)
else:
    print(f"Zoom meeting link: {zoom_link}")

# Helper Functions
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

def schedule_interview(is_selected: bool) -> str:
    """Schedule interview if the candidate is selected."""
    if is_selected:
        interview_date = datetime.now() + timedelta(days=3)
        return f"Scheduled interview for {interview_date.strftime('%Y-%m-%d %H:%M:%S')}"
    return "Interview not scheduled. The resume does not meet the requirements."

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
            return "Email sent successfully!"
    except Exception as e:
        # Log the error for debugging
        return f"Failed to send email: {str(e)}"




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
        st.session_state["sidebar_zoom_client_id"] = ""
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


def download_button_with_icon(pdf_file):
    """Display a download button for the resume with an icon."""
    pdf_bytes = pdf_file.read()
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

def initialize_metrics():
    if 'metrics' not in st.session_state:
        st.session_state.metrics = {
            'total_resumes_uploaded': 0,
            'selected_candidates': 0,
            'interviews_scheduled': 0,
            'applications_by_role': {role: 0 for role in ROLE_REQUIREMENTS}
        }

def update_metrics(role, is_selected):
    st.session_state.metrics['total_resumes_uploaded'] += 1
    st.session_state.metrics['applications_by_role'][role] += 1
    if is_selected:
        st.session_state.metrics['selected_candidates'] += 1
        st.session_state.metrics['interviews_scheduled'] += 1

def show_analytics():
    st.header("Recruitment Analytics Dashboard")
    metrics = st.session_state.metrics
    st.metric(label="Total Resumes Uploaded", value=metrics['total_resumes_uploaded'])
    st.metric(label="Total Selected Candidates", value=metrics['selected_candidates'])
    st.metric(label="Total Interviews Scheduled", value=metrics['interviews_scheduled'])
    role_counts = pd.DataFrame({
        'Role': list(metrics['applications_by_role'].keys()),
        'Applications': list(metrics['applications_by_role'].values())
    })
    st.subheader("Applications by Role")
    fig = px.bar(role_counts, x='Role', y='Applications', title='Applications per Role')
    st.plotly_chart(fig)
    if metrics['total_resumes_uploaded'] > 0:
        selection_rate = (metrics['selected_candidates'] / metrics['total_resumes_uploaded']) * 100
        st.metric(label="Selection Rate (%)", value=f"{selection_rate:.2f}%")
def available_timeslots():
    """Return a list of available interview slots."""
    current_time = datetime.now()
    available_slots = [
        current_time + timedelta(days=3, hours=9),  # Slot 1
        current_time + timedelta(days=3, hours=11),  # Slot 2
        current_time + timedelta(days=3, hours=13),  # Slot 3
        current_time + timedelta(days=3, hours=15),  # Slot 4
    ]
    return available_slots

def schedule_interview_with_candidate(selected_time, candidate_email, role, company_name, sender_email, sender_password):
    """Send email to candidate with selected interview time."""
    interview_subject = f"Your Interview Schedule for {role} Role"
    interview_body = f"""
        Dear Candidate,

        Your interview for the {role} role at {company_name} has been scheduled.

        Interview Details:
        - Date: {selected_time.strftime('%Y-%m-%d')}
        - Time: {selected_time.strftime('%H:%M:%S')} (Your Time Zone)
        - Duration: 45 minutes
        - Interview Format: Technical interview followed by Q&A

        Please be prepared to discuss your experience and skills.

        If you have any questions, feel free to reach out to us.

        Best Regards,
        {company_name}
    """
    # Send email notification
    return send_email(sender_email, sender_password, candidate_email, interview_subject, interview_body)


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
    st.title("AI Recruitment System")
    st.markdown("Please configure the following in the sidebar: Email Sender, Email Password, Company Name")
    
    initialize_metrics()
    st.sidebar.button("Show Analytics", on_click=show_analytics)

    # Define selected_tab here
    selected_tab = st.selectbox("Choose Tab", ["Resume Analysis", "Coding Assessment"])

    if st.button("Check Configuration"):
        if all(config.values()):
            st.success("All configurations are set!")
        else:
            st.error("Some configurations are missing! Please complete all fields.")

    # Add New Application button
    if st.button("Add New Application"):
        # Perform both operations (reset resume text and clear)
        st.session_state.resume_text = ""  # Reset resume text
        st.success("Ready for a new application!")
        st.rerun()  # This will rerun the script and clear any UI states

    # Unified Tab Content
    st.header("Resume Analysis and Interview Scheduling")
    
    role = st.selectbox("Enter the role you want to evaluate", 
                        ["Select a role", "ai_ml_engineer", "full_stack_engineer", "frontend_engineer", "backend_engineer"])

    if role != "Select a role":
        # Display Role Requirements
        st.subheader(f"Role Requirements for {role.replace('_', ' ').title()}:")
        st.markdown(ROLE_REQUIREMENTS[role])

        # Collect Competency Ratings
        st.subheader("Please rate the following competencies (1-10 scale):")
        
        # Define competencies based on the selected role
        competencies = {
            "Technical Skills (Python, PyTorch/TensorFlow)": 0,
            "Machine Learning Algorithms": 0,
            "Deep Learning": 0,
            "MLOps": 0,
            "RAG, LLM, Prompt Engineering": 0
        }

        # If the role is not AI/ML Engineer, you can adjust the competencies list.
        if role != "ai_ml_engineer":
            competencies = {
                "Technical Skills (JavaScript, React.js, Node.js)": 0,
                "Database Management (SQL, NoSQL)": 0,
                "REST APIs, GraphQL": 0,
                "Cloud Deployment (AWS, Azure, GCP)": 0,
                "Version Control (Git)": 0
            }

        for competency in competencies.keys():
            competencies[competency] = st.slider(competency, 1, 10, 5)  # Rating scale changed to 1-10
        
        # Calculate Final Score (out of 10)
        final_score = sum(competencies.values()) / len(competencies)
        
        # Display Final Score
        st.subheader(f"Final Score for {role.replace('_', ' ').title()}: {final_score:.2f} / 10")

        # Provide Feedback Based on Score
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
            # Generate a unique coding assessment URL based on the selected role
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
                time.sleep(5)  # Simulating 5 seconds loading
                is_selected, feedback = analyze_resume(resume_text, role)
                st.session_state.is_selected = is_selected  # Save selection state in session state
                st.session_state.feedback = feedback  # Save feedback
                if is_selected:
                    st.success(f"Selected: You are selected", icon="✅")  # Success with green
                else:
                    st.error(f"Selected: Not selected", icon="❌")  # Error with red
                    update_metrics(role, is_selected)

                st.write(f"Feedback: {feedback}")
                if is_selected:
                    st.success("ALL THE BEST! Proceed to interview scheduling.")
                else:
                    st.error("Unfortunately, your skills don't match our requirement. Better luck next time!")

    
    # Interview Scheduling Tab (Only after resume analysis)
    if 'resume_text' in st.session_state and 'is_selected' in st.session_state:
        is_selected = st.session_state.is_selected  # Accessing from session state
        if is_selected:  # Only proceed if the candidate is selected
            st.header("Proceed to Interview Scheduling")
            proceed_selected = st.checkbox("Confirm to Send Email")
            interview_selected = st.checkbox("Schedule Interview 📅")
            send_button_disabled = not (proceed_selected and interview_selected)

            if st.button("Send Email and Schedule Interview", disabled=send_button_disabled):
                if resume_text:
                    email_status = ""
                    selection_subject = "Congratulations! You are Selected for the Next Stage"
                    selection_body = f"""
                            Dear Candidate,

                            Congratulations! You meet the requirements for the {role} role at {config['company_name']}.
                            We are excited to invite you to the next stage of the interview process.

                            Best Regards,
                            {config['company_name']}
                        """
                    email_status += send_email(config["sender_email"], config["email_app_password"], candidate_email, selection_subject, selection_body) + "\n"

                    if is_selected:
                        interview_date = datetime.now() + timedelta(days=3)  # Interview in 3 days
                        meeting_id = "634 285 2168"  # Replace with actual meeting ID
                        password = "abcdefgh"  # Replace with the meeting password if applicable
                        zoom_link = f"https://zoom.us/j/{meeting_id}?pwd={password}"

                        interview_subject = f"Interview Scheduled for {role} Role"
                        interview_body = f"""
                            Dear Candidate,

                            Congratulations! You have been selected for an interview for the {role} role at {config['company_name']}.

                            Interview Details:
                            - Date: {interview_date.strftime('%Y-%m-%d')}
                            - Time: {interview_date.strftime('%H:%M:%S')} (Your Time Zone)
                            - Duration: 45 minutes
                            - Interview Format: Technical interview followed by Q&A

                            Zoom Link:
                            {zoom_link}

                            Preparation Instructions:
                            1. Please ensure you have a stable internet connection.
                            2. Join the interview 5 minutes early.
                            3. Be prepared to discuss your experience, skills, and problem-solving abilities.

                            If you have any questions or need assistance, feel free to reach out to us.

                            We look forward to meeting you soon!

                            Best Regards,
                            {config['company_name']}
                        """
                        email_status += send_email(config["sender_email"], config["email_app_password"], candidate_email, interview_subject, interview_body) + "\n"
                        
                        st.success("Interview scheduling link has been shared with you!")
                        st.markdown(
                            """
                            ### Application Successfully Processed!
                            Please check your email for:
                            1. Selection confirmation
                            2. Interview details with Zoom link

                            Next steps:
                            1. Review the role requirements
                            2. Prepare for your technical interview
                            3. Join the interview 5 minutes early
                            """
                        )

                    # Show Calendly scheduling link here
                    st.markdown(f"[Self-schedule Interview](https://calendly.com/anishapansare1504)")

                    # Confirm interview scheduling in the system
                    st.success("Interview scheduling link has been shared with you!")
                    update_metrics(role, is_selected)

if __name__ == "__main__":
    main() 