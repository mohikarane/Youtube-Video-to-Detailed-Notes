import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import textwrap

page_bg_img = """
<style>
    .st-emotion-cache-1yiq2ps {
            # background-image: url("https://plus.unsplash.com/premium_photo-1677187301660-5e557d9c0724?q=80&w=1930&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D.jpg");
            background-image: url("https://images.pexels.com/photos/46274/pexels-photo-46274.jpeg?cs=srgb&dl=pexels-caio-46274.jpg&fm=jpg");
            background-size: cover;
        }
    
</style>
"""


load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API-KEY"))

prompt = """You are Youtube video summarizer. You will be taking the transcript text and summarizing the entire video and 
providing the important summary in points within 250 words. Also provide the detailed notes for user to refer later. Please provide the summary of the text given here. """

#getting transcript data from yt video
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id,  languages=['en-GB', 'en'])

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]    #append all the text and make it in paragraph format

        return transcript

    except Exception as e:
        raise e

#getting summary based on prompt from google api 
def generate_gemini_content(transcript_text , prompt):

    model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")
    response = model.generate_content(prompt+transcript_text)
    return response.text


# Function to generate a PDF
def create_pdf(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    font_size = 11
    line_height = 14
    y = height - 40
    left_margin = 40

    # Nested helper function to wrap and draw lines
    def draw_wrapped_line(line, x, width_limit):
        nonlocal y
        wrapped_lines = textwrap.wrap(line, width=width_limit)
        for wrapped_line in wrapped_lines:
            if y < 40:
                c.showPage()
                y = height - 40
            c.drawString(x, y, wrapped_line)
            y -= line_height

    for line in text.split('\n'):
        stripped = line.strip()

        # Handle bold headings
        if stripped.startswith("**") and stripped.endswith("**"):
            c.setFont("Helvetica-Bold", 13)
            clean_line = stripped.strip("*")
            y -= 10  # Extra spacing for heading
            draw_wrapped_line(clean_line, left_margin, 90)
            c.setFont("Helvetica", font_size)

        # Bullets and indentation
        elif stripped.startswith("* "):
            draw_wrapped_line(f"• {stripped[2:]}", left_margin + 10, 90)
        elif stripped.startswith("*"):
            draw_wrapped_line(f"  ◦ {stripped[1:].strip()}", left_margin + 25, 90)

        # Numbered list
        elif any(stripped.startswith(f"{n}.") for n in range(1, 10)):
            draw_wrapped_line(stripped, left_margin, 90)

        else:
            draw_wrapped_line(stripped, left_margin, 90)

    c.save()
    buffer.seek(0)
    return buffer


#Streamlit app
st.markdown(page_bg_img, unsafe_allow_html=True)
st.title("Youtube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter Youtube video link: ")

if youtube_link:
    video_id = youtube_link.split("=")[1]
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg")# , use_column_width=True  #thumbnail

if st.button("Get Detailed Notes"):
    transcript_text = extract_transcript_details(youtube_link)

    if transcript_text:
        summary = generate_gemini_content(transcript_text, prompt)

        # Store summary in session_state to persist across reruns
        st.session_state["summary"] = summary
        st.session_state["pdf"] = create_pdf(summary)

# Display summary and download if already generated
if "summary" in st.session_state:
    st.markdown("## Detailed Notes")
    st.write(st.session_state["summary"])

    st.download_button(
        label="Download PDF",
        data=st.session_state["pdf"],
        file_name="youtube_summary_notes.pdf",
        mime="application/pdf"
    )


