import sqlite3
from pathlib import Path

import streamlit as st

from modules.database import init_database, update_hr_review


DB_PATH = Path("storage/database.db")


def _get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path)


def get_completed_sessions(db_path=DB_PATH):
    init_database(db_path=db_path)
    if not Path(db_path).exists():
        return []

    with _get_connection(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                candidate_id,
                selected_role,
                compatibility_score,
                total_questions,
                created_at,
                hr_status,
                hr_reviewed_at
            FROM interview_sessions
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_session_details(session_id, db_path=DB_PATH):
    init_database(db_path=db_path)
    with _get_connection(db_path) as conn:
        conn.row_factory = sqlite3.Row
        session = conn.execute(
            """
            SELECT
                id,
                candidate_id,
                resume_text,
                selected_role,
                compatibility_score,
                total_questions,
                created_at,
                hr_status,
                hr_remarks,
                hr_reviewed_at
            FROM interview_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

        responses = conn.execute(
            """
            SELECT
                question_index,
                question_text,
                transcript_text,
                video_path,
                transcript_path,
                start_time,
                end_time,
                duration_seconds,
                created_at
            FROM interview_responses
            WHERE session_id = ?
            ORDER BY question_index ASC
            """,
            (session_id,),
        ).fetchall()

    session_data = dict(session) if session else None
    response_data = [dict(row) for row in responses]
    return session_data, response_data


def render_hr_dashboard():
    init_database()
    st.title("HRAI - HR Dashboard")
    st.caption("Review completed interview sessions.")

    sessions = get_completed_sessions()
    if not sessions:
        st.info("No completed interviews found yet.")
        return

    session_options = {
        f"Session #{item['id']} | {item['candidate_id']} | {item['selected_role']} | {item['created_at']}": item["id"]
        for item in sessions
    }
    selected_label = st.selectbox("Select completed interview", list(session_options.keys()))
    selected_session_id = session_options[selected_label]

    session, responses = get_session_details(selected_session_id)
    if not session:
        st.error("Selected session not found.")
        return

    st.subheader("Session Summary")
    st.write(f"Candidate ID: {session['candidate_id']}")
    st.write(f"Role: {session['selected_role']}")
    st.write(f"Compatibility Score: {session['compatibility_score']}%")
    st.write(f"Questions Asked: {session['total_questions']}")
    st.write(f"Created At: {session['created_at']}")
    st.write(f"HR Status: {session.get('hr_status', 'Review')}")
    st.write(f"Reviewed At: {session.get('hr_reviewed_at') or '-'}")

    st.subheader("HR Actions")
    status_options = ["Review", "Approve", "Reject"]
    current_status = session.get("hr_status", "Review")
    default_status_index = status_options.index(current_status) if current_status in status_options else 0
    selected_status = st.selectbox("Set status", status_options, index=default_status_index)
    remarks = st.text_area("Remarks", value=session.get("hr_remarks", ""), height=120)
    if st.button("Save HR Decision"):
        update_hr_review(
            session_id=selected_session_id,
            hr_status=selected_status,
            hr_remarks=remarks.strip(),
        )
        st.success("HR decision saved.")
        st.rerun()

    with st.expander("Resume Text", expanded=False):
        st.text(session["resume_text"] or "")

    st.subheader("Interview Transcript")
    if not responses:
        st.warning("No response records found for this session.")
        return

    for item in responses:
        question_number = item["question_index"] + 1
        st.markdown(f"**Q{question_number}. {item['question_text']}**")
        st.write(item["transcript_text"] or "(No transcript)")
        st.caption(
            f"start={item['start_time']}s | end={item['end_time']}s | duration={item['duration_seconds']}s | saved={item['created_at']}"
        )

        video_path = item.get("video_path")
        if video_path and Path(video_path).exists():
            st.video(video_path)

        st.divider()
