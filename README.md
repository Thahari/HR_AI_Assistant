# HRAI – AI Resume-Aware Interview Assistant

An AI-powered pre-screening interview system that conducts **resume-aware interviews using live video responses and speech-to-text transcription**, helping HR teams review candidate responses efficiently.

The system records candidate answers through webcam video, extracts speech using **local AI models**, and stores structured transcripts and interview data for HR evaluation.

---

# Overview

Hiring teams often spend significant time conducting initial screening interviews.  
HRAI automates the **first round interview process** by allowing candidates to respond to AI-generated questions while the system records responses and generates transcripts.

HR professionals can then review the interview recordings, transcripts, and resume compatibility analysis through a dashboard.

The system is designed as a **human-in-the-loop AI tool**, assisting HR rather than replacing human decision making.

---

# Key Features

## Resume-Aware Interviewing
Candidates upload their resume and select a job role.  
The system analyzes resume content and prepares contextual interview questions.

## Role Compatibility Scoring
The system compares resume skills against predefined skill requirements for each role.

Supported roles:

- Data Analyst
- Data Scientist
- Machine Learning Engineer
- Business Analyst
- Software Developer

Compatibility score is calculated based on matching skills.

---

## Video-Based Interview Responses
Candidates answer questions using **live webcam recording**.

Each response captures:

- Video
- Audio
- Timestamp information

Video files are saved locally for HR review.

---

## Speech-to-Text Transcription
Candidate answers are transcribed using **Faster-Whisper**, a local speech recognition model.

Advantages:

- No API cost
- Fully offline processing
- High accuracy on clear speech

---

## Structured Interview Storage
All interview data is stored in a SQLite database including:

- Resume text
- Selected job role
- Compatibility score
- Interview questions
- Transcripts
- Video file paths

---

## HR Review Dashboard
HR users can review completed interviews through a dashboard.

Features include:

- Candidate resume review
- Compatibility score visualization
- Transcript inspection
- Video playback of responses
- Interview evaluation notes

---

# System Architecture

```
Candidate Interface (Streamlit)
        │
        │ Resume Upload + Role Selection
        ▼
Resume Parser
        │
        ▼
Skill Extraction & Compatibility Engine
        │
        ▼
Interview Controller
        │
        ▼
Video Recording (WebRTC)
        │
        ▼
Speech-to-Text (Faster-Whisper)
        │
        ▼
Structured Transcript Generation
        │
        ▼
SQLite Database
        │
        ▼
HR Dashboard Review
```

---

# Tech Stack

### Frontend
- Streamlit

### AI / Processing
- Faster-Whisper (Speech-to-Text)
- Ollama (for future LLM enhancements)

### Data Processing
- Python
- PDFPlumber

### Media Handling
- streamlit-webrtc
- av

### Database
- SQLite

---

# Project Structure

```
HRAI/
│
├── app.py
│
├── modules/
│   ├── resume_parser.py
│   ├── resume_analyzer.py
│   ├── role_engine.py
│   ├── compatibility.py
│   ├── question_generator.py
│   ├── speech_to_text.py
│   ├── database.py
│
├── config/
│   └── roles.json
│
├── storage/
│   ├── video/
│   ├── transcripts/
│   └── database.db
│
├── requirements.txt
└── README.md
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/hrai-interview-assistant.git
cd hrai-interview-assistant
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

### Windows
```bash
venv\Scripts\activate
```

### Mac / Linux
```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages include:

- streamlit
- faster-whisper
- streamlit-webrtc
- pdfplumber
- sqlalchemy
- pandas
- av

Ensure **ffmpeg** is installed on your system.

---

# Running the Application

Start the Streamlit app:

```bash
streamlit run app.py
```

The application will open in your browser:

```
http://localhost:8501
```

---

# Interview Flow

1. Candidate uploads resume
2. Candidate selects job role
3. Resume skills are analyzed
4. Compatibility score is calculated
5. AI asks interview questions
6. Candidate records video responses
7. Speech-to-text transcription generates answer transcripts
8. Interview data is stored
9. HR reviews interview in dashboard

---

# Example Metrics

The system currently supports:

- 5 job roles
- 20+ mapped technical skills
- Local speech-to-text inference
- Video-based interview responses
- Structured transcript generation

---

# Future Improvements

Planned enhancements include:

- LLM-based adaptive question generation using Ollama
- Sentiment and confidence analysis
- Automated interview scoring
- Multi-candidate interview sessions
- Cloud deployment support
- Advanced analytics dashboard

---

# Ethical Considerations

This system is designed as a **decision support tool**.

AI assists in:

- Interview structuring
- Transcription
- Resume analysis

Final hiring decisions are **always made by human HR reviewers**.

---
