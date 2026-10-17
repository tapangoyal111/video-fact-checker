"""
Video Transcriber Module using FastWhisper

This module provides functionality to download a video from a public URL,
extract its audio, transcribe the audio to text with timestamps using faster-whisper,
and collect relevant metadata.

Dependencies:
- yt-dlp: For downloading video and extracting metadata.
- faster-whisper: A reimplementation of Whisper for faster inference (requires torch or tensorflow).
- ffmpeg: Must be installed and available in PATH for audio extraction.

Usage:
    from video_transcriber_fast import transcribe_video, VideoTranscriptResult

    result = transcribe_video("https://www.youtube.com/watch?v=example")
    print(result.transcript)  # Transcript in detected language
    print(result.metadata)

    Command-line usage:
        python -m src.video_transcriber_fast <VIDEO_URL> [--model MODEL] [--keep-audio] [--audio-quality QUALITY]
        [--save-transcript FILE] [--device DEVICE] [--compute-type COMPUTE_TYPE] [--language LANGUAGE]

    Example:
        python -m src.video_transcriber_fast "https://www.youtube.com/watch?v=example" --model base --audio-quality 128
        --save-transcript transcript.txt --device cpu --compute-type int8 --language hi
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import yt-dlp and faster-whisper; provide helpful error messages if missing.
try:
    import yt_dlp
except ImportError:  # pragma: no cover
    yt_dlp = None  # type: ignore

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover
    WhisperModel = None  # type: ignore


# Project root: two levels up from this file (assuming this file is in <project>/src/video_transcriber_fast.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Temporary files directory: <project>/resources/tmp
TMP_DIR = PROJECT_ROOT / "resources" / "tmp"
# Output transcripts directory: <project>/resources/transcript
OUTPUT_DIR_BASE = PROJECT_ROOT / "resources" / "transcript"

# Ensure directories exist
TMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR_BASE.mkdir(parents=True, exist_ok=True)


@dataclasses.dataclass
class VideoTranscriptResult:
    """Container for the transcription result and associated metadata."""

    video_url: str
    title: str
    description: Optional[str] = None
    upload_date: Optional[str] = None  # ISO 8601 string if available
    channel: Optional[str] = None
    duration: Optional[float] = None  # in seconds
    language: Optional[str] = None  # Detected language code (e.g., 'en', 'es', 'fr')
    transcript: str = ""
    segments: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    # Optional: path to the downloaded audio file (if kept)
    audio_filepath: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary (for JSON serialization)."""
        return dataclasses.asdict(self)

    def save_transcript(self, filepath: Optional[str] = None, format: str = "txt") -> str:
        """
        Save the transcript to a file.

        Args:
            filepath: Path to the output file. If None, a default name is generated in the
                      <project>/resources/transcript directory.
            format: Output format - 'txt', 'json', or 'srt'.

        Returns:
            The actual filepath used.
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = {"txt": "txt", "json": "json", "srt": "srt"}.get(format, "txt")
            filepath = OUTPUT_DIR_BASE / f"transcript_{timestamp}.{ext}"
        else:
            filepath = Path(filepath)

        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "txt":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.transcript)
        elif format == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        elif format == "srt":
            # Simple SRT generation from segments
            with open(filepath, "w", encoding="utf-8") as f:
                for i, seg in enumerate(self.segments, start=1):
                    start = self._format_srt_timestamp(seg.get("start", 0.0))
                    end = self._format_srt_timestamp(seg.get("end", 0.0))
                    text = seg.get("text", "").strip()
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(filepath.resolve())

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
        assert seconds >= 0
        milliseconds = round(seconds * 1000)
        hours = milliseconds // (3600 * 1000)
        milliseconds %= 3600 * 1000
        minutes = milliseconds // (60 * 1000)
        milliseconds %= 60 * 1000
        secs = milliseconds // 1000
        milliseconds %= 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def _check_dependencies() -> None:
    """Check that required external tools and Python packages are available."""
    missing = []

    if yt_dlp is None:
        missing.append("yt-dlp (pip install yt-dlp)")

    if WhisperModel is None:
        missing.append("faster-whisper (pip install faster-whisper)")

    # Check for ffmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("ffmpeg (install from https://ffmpeg.org/download.html)")

    if missing:
        raise RuntimeError(
            "Missing dependencies: " + ", ".join(missing) + "\n"
            "Please install them before using this module."
        )


def transcribe_video(
    url: str,
    output_dir: Optional[str] = None,  # Kept for compatibility; defaults to TMP_DIR
    model_size: str = "base",
    keep_audio: bool = False,
    audio_quality: str = "128",
    device: str = "auto",
    compute_type: str = "default",
    language: Optional[str] = None,
) -> VideoTranscriptResult:
    """
    Download a video from a public URL, extract audio, transcribe it using faster-whisper,
    and collect metadata.

    Args:
        url: Public video URL (YouTube, Instagram, etc.).
        output_dir: Directory to store temporary files (audio, etc.). If None, uses
                    <project>/resources/tmp.
        model_size: Whisper model size (tiny, base, small, medium, large, large-v2, large-v3).
        keep_audio: If True, keep the downloaded audio file; otherwise delete after transcription.
        audio_quality: Audio bitrate in kbps for the extracted audio (e.g., "64", "128", "192").
                      Lower values reduce file size but may affect transcription accuracy.
        device: Device to run the model on (auto, cpu, cuda). Default: auto.
        compute_type: Type of computation (default, int8, int8_float16, int16, float16, float32).
                     Default: default.
        language: Language code for transcription (e.g., "en" for English, "hi" for Hindi).
                  If None, language is auto-detected.

    Returns:
        VideoTranscriptResult object containing the transcript (in specified or detected language) and metadata.

    Raises:
        RuntimeError: If dependencies are missing or an unrecoverable error occurs.
        ValueError: If the URL is invalid or the video cannot be accessed.
    """
    _check_dependencies()

    # Determine temporary directory
    if output_dir is None:
        tmp_dir = TMP_DIR
    else:
        tmp_dir = Path(output_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract video info and download audio using yt-dlp
    ydl_opts: Dict[str, Any] = {
        "format": "bestaudio/best",  # Select best audio quality
        "outtmpl": str(tmp_dir / "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": audio_quality,
            }
        ],
        "quiet": True,
        "no_warnings": True,
        # Extract metadata without downloading if possible, but we need audio.
    }

    info: Dict[str, Any] = {}
    audio_filepath: Optional[str] = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # After download, find the audio file
            video_id = info.get("id")
            ext = info.get("ext", "webm")
            # The postprocessor should have changed extension to wav
            expected_audio = tmp_dir / f"{video_id}.wav"
            if expected_audio.exists():
                audio_filepath = str(expected_audio)
            else:
                # Fallback: look for any wav file in tmp_dir with the video id
                for f in tmp_dir.iterdir():
                    if f.name.startswith(video_id) and f.suffix == ".wav":
                        audio_filepath = str(f)
                        break
                if audio_filepath is None:
                    raise FileNotFoundError("Audio file not found after extraction.")
    except Exception as e:  # pragma: no cover - depends on network/video availability
        raise RuntimeError(f"Failed to download/extract video: {e}") from e

    # Step 2: Load faster-whisper model and transcribe
    try:
        # Initialize the WhisperModel
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(PROJECT_ROOT / "models")  # Optional: specify download directory
        )

        # Transcribe the audio
        segments, info_obj = model.transcribe(
            audio_filepath,
            beam_size=5,
            word_timestamps=True,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        # Convert segments to list of dictionaries
        segment_list = []
        transcript_parts = []

        for segment in segments:
            segment_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "words": [
                    {
                        "start": word.start,
                        "end": word.end,
                        "word": word.word,
                        "probability": word.probability
                    } for word in segment.words
                ] if hasattr(segment, 'words') and segment.words else []
            }
            segment_list.append(segment_dict)
            transcript_parts.append(segment.text)

        transcript_text = "".join(transcript_parts).strip()
        # Use specified language if provided, otherwise use detected language
        language = language if language is not None else info_obj.language

    except ModuleNotFoundError as e:
        # Handle the specific case of missing 'cgi' module (Python 3.12+ issue)
        if "cgi" in str(e).lower():
            raise RuntimeError(
                "Failed to load the transcription model due to a missing 'cgi' module. "
                "This is required by some versions of the Hugging Face Hub library used by faster_whisper. "
                "Please install it by running: pip install cgi\n"
                "After installing, try running the command again."
            ) from e
        else:
            raise RuntimeError(f"Transcription failed due to missing module: {e}") from e
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Transcription failed: {e}") from e
    finally:
        # Clean up audio file if not keeping it
        if not keep_audio and audio_filepath and os.path.exists(audio_filepath):
            try:
                os.remove(audio_filepath)
            except OSError:
                pass  # Best effort

    # Step 3: Build metadata from info dict
    title = info.get("title", "")
    description = info.get("description")
    # Upload date may be in ISO format or as string; try to normalize
    upload_date_raw = info.get("upload_date")  # YYYYMMDD string
    upload_date: Optional[str] = None
    if upload_date_raw and len(upload_date_raw) == 8 and upload_date_raw.isdigit():
        upload_date = f"{upload_date_raw[0:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:8]}"
    channel = info.get("uploader") or info.get("channel")
    duration = info.get("duration")  # in seconds

    # Create result object
    result_obj = VideoTranscriptResult(
        video_url=url,
        title=title,
        description=description,
        upload_date=upload_date,
        channel=channel,
        duration=duration,
        language=language,
        transcript=transcript_text,
        segments=segment_list,
        audio_filepath=audio_filepath if keep_audio else None,
    )

    return result_obj


# Example usage (can be removed or kept as a simple CLI test)
if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Transcribe a public video URL using faster-whisper.")
    parser.add_argument("url", help="Public video URL (YouTube, Instagram, etc.)")
    parser.add_argument(
        "--model",
        default="base",
        help="Whisper model size (tiny, base, small, medium, large, large-v2, large-v3)",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep the downloaded audio file after transcription",
    )
    parser.add_argument(
        "--audio-quality",
        default="128",
        help="Audio bitrate in kbps for extracted audio (e.g., 64, 128, 192). Lower = smaller file.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device to run the model on (auto, cpu, cuda). Default: auto.",
    )
    parser.add_argument(
        "--compute-type",
        default="default",
        choices=["default", "int8", "int8_float16", "int16", "float16", "float32"],
        help="Type of computation (default, int8, int8_float16, int16, float16, float32). Default: default.",
    )
    parser.add_argument(
        "--language",
        choices=["en", "hi"],
        help="Language for transcription (en: English, hi: Hindi). If not specified, language is auto-detected.",
    )
    parser.add_argument(
        "--save-transcript",
        metavar="FILE",
        help="Save transcript to FILE (format inferred from extension: .txt, .json, .srt). "
             "If not provided, saves to <project>/resources/transcript/transcript_<timestamp>.<ext>",
    )
    args = parser.parse_args()

    try:
        res = transcribe_video(
            url=args.url,
            output_dir=None,  # Use default TMP_DIR
            model_size=args.model,
            keep_audio=args.keep_audio,
            audio_quality=args.audio_quality,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
        )
        print("=== Metadata ===")
        print(f"Title: {res.title}")
        print(f"Channel: {res.channel}")
        print(f"Upload Date: {res.upload_date}")
        print(f"Duration: {res.duration} seconds")
        print(f"Language: {res.language}")  # Detected language
        print("\n=== Transcript (first 500 chars) ===")
        print(res.transcript[:500] + ("..." if len(res.transcript) > 500 else ""))
        print(f"\nFull transcript length: {len(res.transcript)} characters")

        if args.save_transcript:
            ext = os.path.splitext(args.save_transcript)[1].lower()
            if ext == ".json":
                fmt = "json"
            elif ext == ".srt":
                fmt = "srt"
            else:
                fmt = "txt"
            saved_path = res.save_transcript(args.save_transcript, format=fmt)
            print(f"Transcript saved to {saved_path} as {fmt}")
        else:
            # If no --save-transcript provided, still save a default transcript
            saved_path = res.save_transcript()  # uses default naming in OUTPUT_DIR_BASE
            print(f"No output file specified; transcript saved to default: {saved_path}")

    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)