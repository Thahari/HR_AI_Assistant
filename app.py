import json
import random
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components
from aiortc.contrib.media import MediaRecorder
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from modules.compatibility import calculate_compatibility
from modules.database import save_interview_session
from modules.question_generator import generate_questions
from modules.resume_analyzer import extract_skills_from_resume
from modules.resume_parser import extract_text_from_pdf
from modules.role_engine import get_role_skills
from modules.speech_to_text import transcribe_media
from modules.hr_dashboard import render_hr_dashboard


VIDEO_DIR = Path("storage/video")
TRANSCRIPT_DIR = Path("storage/transcripts")
WHISPER_MODEL_SIZE = "small"


def ensure_storage_dirs():
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)


def get_video_path(candidate_id, question_index):
    return VIDEO_DIR / f"{candidate_id}_q{question_index + 1}.webm"


def build_transcript_record(question, transcript_data, video_path):
    return {
        "question": question,
        "transcript": transcript_data.get("transcript", ""),
        "start_time": transcript_data.get("start_time"),
        "end_time": transcript_data.get("end_time"),
        "duration_seconds": transcript_data.get("duration_seconds", 0.0),
        "video_path": str(video_path),
        "segments": transcript_data.get("segments", []),
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def save_transcript_json(candidate_id, question_index, transcript_record):
    output_path = TRANSCRIPT_DIR / f"{candidate_id}_q{question_index + 1}.json"
    output_path.write_text(json.dumps(transcript_record, indent=2), encoding="utf-8")
    return output_path


def get_question_time_limit_seconds(question):
    q = question.lower()
    limit = 45
    if any(k in q for k in ["describe", "walk me through", "challenging", "project", "contribution", "example"]):
        limit += 20
    if any(k in q for k in ["stakeholder", "prioritize", "tradeoff", "plan"]):
        limit += 10
    if len(question.split()) > 14:
        limit += 10
    return min(max(limit, 30), 90)


def render_question_timer(seconds, timer_key):
    components.html(
        f"""
        <div id="hrai_timer_{timer_key}" style="font-family: Arial, sans-serif; font-size: 15px; font-weight: 600;">
            Time remaining: {seconds}s
        </div>
        <script>
            (function() {{
                const storageKey = "hrai_timer_start_{timer_key}";
                const duration = {seconds};
                let startedAt = localStorage.getItem(storageKey);
                if (!startedAt) {{
                    startedAt = Date.now().toString();
                    localStorage.setItem(storageKey, startedAt);
                }}
                const el = document.getElementById("hrai_timer_{timer_key}");
                function tick() {{
                    const elapsed = Math.floor((Date.now() - Number(startedAt)) / 1000);
                    const remaining = Math.max(duration - elapsed, 0);
                    if (remaining > 0) {{
                        el.textContent = "Time remaining: " + remaining + "s";
                        el.style.color = remaining <= 10 ? "#b91c1c" : "#0f172a";
                    }} else {{
                        el.textContent = "Time is up. Please stop recording and submit.";
                        el.style.color = "#b91c1c";
                    }}
                }}
                tick();
                setInterval(tick, 1000);
            }})();
        </script>
        """,
        height=55,
    )


st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="💼",
    layout="centered",
)

ensure_storage_dirs()

app_mode = st.sidebar.radio("Mode", ["Candidate Interview", "HR Dashboard"])
if app_mode == "HR Dashboard":
    render_hr_dashboard()
    st.stop()

st.title("HRAI - AI Interview Assistant")
st.write("Upload your resume, select the role, and start your interview.")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

st.subheader("Select Job Role")
role = st.selectbox(
    "Choose the role you are applying for:",
    [
        "Data Analyst",
        "Data Scientist",
        "Machine Learning Engineer",
        "Business Analyst",
        "Software Developer",
    ],
)

st.subheader("Start")
if st.button("Start Interview"):
    if uploaded_file is None:
        st.error("Please upload your resume before starting the interview.")
    else:
        resume_text = extract_text_from_pdf(uploaded_file)
        role_skills = get_role_skills(role)
        found_skills = extract_skills_from_resume(resume_text, role_skills)
        compatibility_score = calculate_compatibility(found_skills, role_skills)

        questions = generate_questions(
            resume_text=resume_text,
            role=role,
            found_skills=found_skills,
            role_skills=role_skills,
            total_questions=50,
        )
        random_question_count = random.randint(1, 20)
        questions_to_ask = questions[:random_question_count]
        candidate_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "_" + uuid4().hex[:8]

        st.session_state["resume_text"] = resume_text
        st.session_state["selected_role"] = role
        st.session_state["candidate_id"] = candidate_id
        st.session_state["questions"] = questions_to_ask
        st.session_state["question_count"] = random_question_count
        st.session_state["current_question"] = 0
        st.session_state["answers"] = []
        st.session_state["transcripts"] = []
        st.session_state["found_skills"] = found_skills
        st.session_state["compatibility_score"] = compatibility_score
        st.session_state["interview_saved"] = False
        st.session_state["saved_session_id"] = None

        st.success("Interview Started.")

if "questions" in st.session_state:
    current_index = st.session_state["current_question"]
    questions = st.session_state["questions"]
    candidate_id = st.session_state["candidate_id"]

    if current_index < len(questions):
        current_question = questions[current_index]
        st.subheader(f"Question {current_index + 1}")
        st.write(current_question)
        time_limit_seconds = get_question_time_limit_seconds(current_question)
        st.caption(
            f"Record with webcam + microphone. Keep this response within {time_limit_seconds} seconds for faster transcription."
        )
        render_question_timer(time_limit_seconds, f"{candidate_id}_{current_index}")

        video_path = get_video_path(candidate_id, current_index)

        def recorder_factory():
            return MediaRecorder(str(video_path))

        webrtc_ctx = webrtc_streamer(
            key=f"qa_{candidate_id}_{current_index}",
            mode=WebRtcMode.SENDONLY,
            media_stream_constraints={"video": True, "audio": True},
            in_recorder_factory=recorder_factory,
            async_processing=True,
        )

        if st.button("Transcribe & Submit", key=f"submit_{current_index}"):
            if webrtc_ctx and webrtc_ctx.state.playing:
                st.warning("Stop recording first, then click Transcribe & Submit.")
            elif not video_path.exists() or video_path.stat().st_size == 0:
                st.error("No recorded video found for this answer. Please record before submitting.")
            else:
                with st.spinner("Transcribing response..."):
                    transcript_data = transcribe_media(video_path, model_size=WHISPER_MODEL_SIZE)

                transcript_text = transcript_data.get("transcript", "").strip()
                if not transcript_text:
                    st.error("Transcription was empty. Please record again with clearer audio.")
                else:
                    transcript_record = build_transcript_record(
                        question=current_question,
                        transcript_data=transcript_data,
                        video_path=video_path,
                    )
                    transcript_json_path = save_transcript_json(
                        candidate_id=candidate_id,
                        question_index=current_index,
                        transcript_record=transcript_record,
                    )

                    transcript_record["transcript_path"] = str(transcript_json_path)
                    st.session_state["answers"].append(transcript_text)
                    st.session_state["transcripts"].append(transcript_record)
                    st.session_state["current_question"] += 1
                    st.rerun()
    else:
        if not st.session_state.get("interview_saved", False):
            try:
                saved_session_id = save_interview_session(
                    candidate_id=st.session_state.get("candidate_id"),
                    resume_text=st.session_state.get("resume_text", ""),
                    selected_role=st.session_state.get("selected_role", ""),
                    compatibility_score=st.session_state.get("compatibility_score", 0.0),
                    questions=st.session_state.get("questions", []),
                    transcripts=st.session_state.get("transcripts", []),
                )
                st.session_state["interview_saved"] = True
                st.session_state["saved_session_id"] = saved_session_id
                st.success("Interview completed and session saved.")
            except Exception as exc:
                st.error(f"Interview completed, but saving failed: {exc}")
        else:
            st.success("Interview completed and session saved.")

        st.write("Thank you for completing the interview.")