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

# Function to check password
def check_password():
    def password_entered():
        if st.session_state["password"] == "jeromeCPME2024":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        st.error("Mot de passe incorrect")
        return False
    else:
        return True

if check_password():
    # Streamlit interface
    st.title("Pascaleo - Retranscription textuelle des entretiens visios")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Entrez les termes techniques issus du GPTs #4 :")
    whisper_prompt = st.text_area("", "")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Téléversez vos fichiers MP3 :")
    uploaded_files = st.file_uploader("", type="mp3", accept_multiple_files=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    if st.button("Retranscrire les MP3 en texte"):
        if uploaded_files:
            total_files = len(uploaded_files)
            for index, uploaded_file in enumerate(uploaded_files):
                # Save uploaded file to a temporary location
                temp_input_path = f"/tmp/{uploaded_file.name}"
                with open(temp_input_path, "wb") as temp_file:
                    temp_file.write(uploaded_file.getbuffer())

                # Load the MP3 file
                audio = AudioSegment.from_mp3(temp_input_path)
                duration = len(audio)
                ten_minutes = 10 * 60 * 1000  # 10 minutes in milliseconds

                all_transcriptions = []
                num_chunks = (duration // ten_minutes) + 1
                chunk_progress = st.progress(0)

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
                    combined_transcription = "\n".join(all_transcriptions)

                    # Update the progress bar for the chunk
                    chunk_progress.progress((i + ten_minutes) / duration)
                    # Display the transcription in progress
                    st.subheader(f"Transcription partielle pour {uploaded_file.name}")
                    st.text(combined_transcription)

                # Combine all transcriptions
                combined_transcription = "\n".join(all_transcriptions)

                # Construct the full path for the output text file
                output_txt_path = f"/tmp/{Path(uploaded_file.name).stem}.txt"

                # Write the transcription to the text file
                with open(output_txt_path, "w") as text_file:
                    text_file.write(combined_transcription)

                st.write(f"Processed {uploaded_file.name}")

                # Display the final transcription
                st.subheader(f"Transcription finale pour {uploaded_file.name}")
                st.text(combined_transcription)

                # Provide download link for the text file
                with open(output_txt_path, "r") as file:
                    st.download_button(
                        label="Télécharger les retranscriptions (TXT)",
                        data=file,
                        file_name=f"{Path(uploaded_file.name).stem}.txt",
                        mime="text/plain"
                    )

                # Update the overall progress bar
                st.progress((index + 1) / total_files)

            st.success("Tous les fichiers ont été traités avec succès")
        else:
            st.error("Veuillez téléverser au moins 1 fichier MP3")
