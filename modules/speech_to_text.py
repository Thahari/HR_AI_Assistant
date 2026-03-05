from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel


def _resolve_device_and_compute():
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


@lru_cache(maxsize=2)
def get_whisper_model(model_size="small"):
    device, compute_type = _resolve_device_and_compute()
    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe_media(media_path, model_size="small"):
    media_path = Path(media_path)
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found: {media_path}")

    model = get_whisper_model(model_size=model_size)
    segments, info = model.transcribe(
        str(media_path),
        vad_filter=True,
        beam_size=1,
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,
    )

    parsed_segments = []
    transcript_parts = []
    start_time = None
    end_time = None

    for segment in segments:
        segment_text = segment.text.strip()
        if not segment_text:
            continue

        parsed_segments.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment_text,
            }
        )
        transcript_parts.append(segment_text)

        if start_time is None:
            start_time = float(segment.start)
        end_time = float(segment.end)

    return {
        "transcript": " ".join(transcript_parts).strip(),
        "segments": parsed_segments,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": (end_time - start_time) if start_time is not None and end_time is not None else 0.0,
        "language": getattr(info, "language", None),
    }
