import os
from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment
import streamlit as st

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
st.title("Audio Transcription with Whisper")
whisper_prompt = st.text_area("Set Whisper Prompt", "")
uploaded_files = st.file_uploader("Upload MP3 Files", type="mp3", accept_multiple_files=True)

if st.button("Process Files"):
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

            # Construct the full path for the output text file
            output_file_path = f"/tmp/{Path(uploaded_file.name).stem}.txt"

            # Write the transcription to the text file
            with open(output_file_path, "w") as text_file:
                text_file.write(combined_transcription)

            st.write(f"Processed {uploaded_file.name}")

            # Provide download link for the text file
            with open(output_file_path, "r") as file:
                st.download_button(
                    label="Download Transcription",
                    data=file,
                    file_name=f"{Path(uploaded_file.name).stem}.txt",
                    mime="text/plain"
                )

        st.success("All files have been processed!")
    else:
        st.error("Please upload at least one MP3 file.")
