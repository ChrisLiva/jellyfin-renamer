import asyncio
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor


async def process_with_ffmpeg_async(input_path, output_path, pbar=None):
    """Process video file with FFmpeg to convert audio to FLAC stereo asynchronously."""
    cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-c:v",
        "copy",
        "-c:s",
        "copy",  # Copy all subtitle streams
        "-af",
        # "loudnorm=I=-14:TP=-1.5:LRA=9",  # Louder normalization for outdoor viewing
        "-ac",
        "2",
        "-c:a",
        "flac",
        "-y",  # Overwrite output file
        output_path,
    ]

    try:
        if pbar:
            pbar.set_description(f"FFmpeg: {os.path.basename(input_path)}")

        # Run FFmpeg in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: subprocess.run(cmd, check=True, capture_output=True, text=True),
            )

        if pbar:
            pbar.update(1)
        return True
    except subprocess.CalledProcessError as e:
        if pbar:
            pbar.write(f"FFmpeg error processing {input_path}: {e}")
            pbar.write(f"FFmpeg stderr: {e.stderr}")
            pbar.update(1)
        return False
