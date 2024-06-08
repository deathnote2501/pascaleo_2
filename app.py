import os
from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment
import streamlit as st
from fpdf import FPDF
from io import BytesIO

from pydub.utils import which
AudioSegment.ffmpeg = which("ffmpeg")

# Set your API key here. It's safer to use an environment variable.
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "API key is not set. Please set the OPENAI_API_KEY environment variable."
    )

# Create an instance of the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Streamlit interface
st.title("Pascaleo")
st.subheader("Retranscription textuelle des entretiens visios")
whisper_prompt = st.text_area("Entrez les termes techniques issus du GPTs #4", "")
uploaded_files = st.file_uploader("Téléversez vos fichiers MP3 pour obtenir une retranscription textuelle au format TXT et PDF", type="mp3", accept_multiple_files=True)

if st.button("Retranscrire les MP3 en TXT et PDF"):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Save uploaded file to a temporary location
            temp_input_path = f"/tmp/{uploaded_file.name}"
            with open(temp_input_path, "wb") as temp_file:
                temp_file.write(uploaded_file.getbuffer())

            # Load the MP3 file
            audio = AudioSegment.from_mp3(temp_input_path)
            duration = len(audio)
            ten_minutes = 10 * 60 * 1000  # 10 minutes in milliseconds

            all_transcriptions = []

            # Split the audio into 10-minute chunks
            for i in range(0, duration, ten_minutes):
                chunk = audio[i : i + ten_minutes]
                chunk_file_path = f"/tmp/{Path(uploaded_file.name).stem}_part_{i//ten_minutes}.mp3"
                chunk.export(chunk_file_path, format="mp3")

                # Open the audio file chunk
                with open(chunk_file_path, "rb") as audio_file:
                    # Call the OpenAI API to transcribe the audio file
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        prompt=whisper_prompt,
                    )

                all_transcriptions.append(transcription.text)

            # Combine all transcriptions
            combined_transcription = "\n".join(all_transcriptions)

            # Write the transcription to a text file in memory
            txt_buffer = BytesIO()
            txt_buffer.write(combined_transcription.encode())
            txt_buffer.seek(0)

            # Create a PDF file in memory
            pdf_buffer = BytesIO()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)

            for line in combined_transcription.split('\n'):
                pdf.multi_cell(0, 10, line)

            pdf.output(pdf_buffer)
            pdf_buffer.seek(0)

            st.write(f"Processed {uploaded_file.name}")

            # Provide download link for the text file
            st.download_button(
                label="Télécharger les retranscriptions (TXT)",
                data=txt_buffer,
                file_name=f"{Path(uploaded_file.name).stem}.txt",
                mime="text/plain"
            )

            # Provide download link for the PDF file
            st.download_button(
                label="Télécharger les retranscriptions (PDF)",
                data=pdf_buffer,
                file_name=f"{Path(uploaded_file.name).stem}.pdf",
                mime="application/pdf"
            )

        st.success("Tous les fichiers ont été traités avec succès")
    else:
        st.error("Veuillez téléverser au moins 1 fichier MP3")
