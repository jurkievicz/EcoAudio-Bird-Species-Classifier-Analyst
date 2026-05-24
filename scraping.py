import json
import requests
import subprocess
import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm


def convert_to_wav(src_path, dst_path):
    """
    Converts an audio file to a mono 22050 Hz WAV file using ffmpeg.
    """
    try:
        subprocess.run([
            r"C:\Users\kazim\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe",
            "-i", str(src_path),
            "-ac", "1",  # mono
            "-ar", "22050",  # sample rate
            "-loglevel", "error",  # keep terminal output clean
            "-y", str(dst_path)  # overwrite if exists
        ], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nFFMPEG Error on {src_path}: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        print("\nERROR: Python cannot find ffmpeg. Ensure it is installed and your IDE was restarted.")
        return False


def main():
    # 1. Setup directories
    raw_dir = Path("data/raw_mp3")
    wav_dir = Path("data/processed_wav")
    raw_dir.mkdir(parents=True, exist_ok=True)
    wav_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load the JSON data
    try:
        with open('recordings_data.json', 'r', encoding='utf-8') as f:
            recordings = json.load(f)
    except FileNotFoundError:
        print("Could not find recordings_data.json. Please run the scraping script first.")
        return

    metadata_rows = []

    # --- PRE-SCAN FOR CONSOLE STATE ---
    # Count how many wav files already exist to give an accurate starting state
    existing_files = sum(1 for rec in recordings if (wav_dir / f"{rec.get('id')}.wav").exists())
    remaining_files = len(recordings) - existing_files

    print("\n--- Download & Conversion Status ---")
    print(f"Total recordings in JSON: {len(recordings)}")
    print(f"Already downloaded/processed: {existing_files}")
    print(f"Remaining to process: {remaining_files}")
    print("------------------------------------\n")

    # 3. Process each recording with a dynamic progress bar
    with tqdm(total=len(recordings), desc="Overall Progress", unit="file") as pbar:
        for rec in recordings:
            rec_id = rec.get("id")
            file_url = rec.get("file")
            species = rec.get("en", "Unknown")

            if not file_url:
                pbar.update(1)
                continue

            # Update the progress bar text to show what it is currently working on
            pbar.set_postfix_str(f"Current: {species} ({rec_id})")

            # Ensure the URL is absolute
            if file_url.startswith("//"):
                file_url = "https:" + file_url

            mp3_path = raw_dir / f"{rec_id}.mp3"
            wav_path = wav_dir / f"{rec_id}.wav"

            # --- DOWNLOAD STEP ---
            if not mp3_path.exists() and not wav_path.exists():
                # Disguise as a standard web browser
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }

                try:
                    # Stream the download with strict timeouts to prevent hanging
                    response = requests.get(file_url, headers=headers, stream=True, timeout=(10, 30))
                    response.raise_for_status()

                    with open(mp3_path, 'wb') as audio_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                audio_file.write(chunk)

                except requests.exceptions.RequestException as e:
                    # Use tqdm.write instead of print so it doesn't break the progress bar visual
                    tqdm.write(f"\nFailed to download {rec_id} ({species}): {e}")
                    # Clean up corrupted file if download failed halfway
                    if mp3_path.exists():
                        mp3_path.unlink()
                    pbar.update(1)
                    continue

                # Polite rate limiting
                time.sleep(1.5)

            # --- CONVERSION STEP ---
            if not wav_path.exists():
                success = convert_to_wav(mp3_path, wav_path)
                if not success:
                    # If conversion fails, delete the bad mp3 so we can try again next run
                    mp3_path.unlink(missing_ok=True)
                    pbar.update(1)
                    continue

            # --- METADATA STEP ---
            metadata_rows.append({
                "recording_id": rec_id,
                "species": species,
                "scientific_name": rec.get("gen", "") + " " + rec.get("sp", ""),
                "country": rec.get("cnt", ""),
                "location": rec.get("loc", ""),
                "quality": rec.get("q", ""),
                "length_s": rec.get("length", ""),
                "date": rec.get("date", ""),
                "file_path": str(wav_path)
            })

            # Advance the progress bar by 1
            pbar.update(1)

    # 4. Save metadata to CSV
    if metadata_rows:
        df = pd.DataFrame(metadata_rows)
        df.to_csv('metadata.csv', index=False)
        print(f"\n\nSuccess! Processed {len(metadata_rows)} files. Metadata saved to metadata.csv[cite: 36, 67].")
    else:
        print("\n\nNo files were processed successfully.")


if __name__ == "__main__":
    main()