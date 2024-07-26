from pathlib import Path
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel
from pydantic.types import Enum
from xtts_api_server.tts_funcs import TTSWrapper, supported_languages

# Define the SynthesisRequest model
class SynthesisRequest(BaseModel):
    input: str
    voice: str
    language: Optional[str] = None  # Optional field, default value is None


# Define the SynthesisFileRequest model
class SynthesisFileRequest(BaseModel):
    input: str
    voice: str
    language: Optional[str] = None
    file_name_or_path: str


# Define the ModelNameRequest model
class ModelNameRequest(BaseModel):
    model_name: str


# Define the TTSSettingsRequest model
class TTSSettingsRequest(BaseModel):
    speed: float
    pitch: float
    emotion: str
    emotion_strength: float
    volume: float
    enable_emoji: bool
    voice_3d: str


# Define the OutputFolderRequest model
class OutputFolderRequest(BaseModel):
    output_folder: str


# Define the SpeakerFolderRequest model
class SpeakerFolderRequest(BaseModel):
    speaker_folder: str

# Define the AudioFormatEnum for the tts_file_request
class AudioFormatEnum(str, Enum):
    WAV = "wav"
    MP3 = "mp3"

# Define the AudioQualityEnum for the tts_file_request
class AudioQualityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Define the tts_file_request model
class tts_file_request(BaseModel):
    input: str
    voice: str
    language: Optional[str] = None
    file_name_or_path: str
    format: Optional[AudioFormatEnum] = AudioFormatEnum.WAV
    quality: Optional[AudioQualityEnum] = AudioQualityEnum.HIGH

# Define the ModelVersionRequest model
class ModelVersionRequest(BaseModel):
    model_version: str

# Define the TextToAudioRequest model
class TextToAudioRequest(BaseModel):
    text: str
    speaker_wav: str
    language: str

# Define the StreamingOptionsRequest model
class StreamingOptionsRequest(BaseModel):
    minimum_sentence_length: int
    minimum_first_fragment_length: int
    tokenizer: str
    language: str
    context_size: int

# Define the PlayModeRequest model
class PlayModeRequest(BaseModel):
    play_mode: bool

# Define the StreamModeRequest model
class StreamModeRequest(BaseModel):
    stream_mode: bool

# Define the UseCacheRequest model
class UseCacheRequest(BaseModel):
    use_cache: bool

# Define the ModelSourceRequest model
class ModelSourceRequest(BaseModel):
    model_source: str

# Define the ModelVersionRequest model
class ModelVersionRequest(BaseModel):
    model_version: str

# Define the DeviceRequest model
class DeviceRequest(BaseModel):
    device: str

# Define the LowVRAMModeRequest model
class LowVRAMModeRequest(BaseModel):
    low_vram_mode: bool

# Define the DeepSpeedRequest model
class DeepSpeedRequest(BaseModel):
    deepspeed: bool

# Define the BaseURLRequest model
class BaseURLRequest(BaseModel):
    base_url: str

# Define the OutputFolderRequest model
class OutputFolderRequest(BaseModel):
    output_folder: str

# Define the SpeakerFolderRequest model
class SpeakerFolderRequest(BaseModel):
    speaker_folder: str

# Define the ModelFolderRequest model
class ModelFolderRequest(BaseModel):
    model_folder: str

# Define the LANGRequest model
class LANGRequest(BaseModel):
    lang: str

# Define the StreamModeRequest model
class StreamModeRequest(BaseModel):
    stream_mode: bool

# Define the StreamModeImproveRequest model
class StreamModeImproveRequest(BaseModel):
    stream_mode_improve: bool

# Define the StreamPlaySyncRequest model
class StreamPlaySyncRequest(BaseModel):
    stream_play_sync: bool

# Define the InstallDeepspeedBasedOnPythonVersionRequest model
class InstallDeepspeedBasedOnPythonVersionRequest(BaseModel):
    install_deepspeed_based_on_python_version: bool

# Define the CheckStream2sentenceVersionRequest model
class CheckStream2sentenceVersionRequest(BaseModel):
    check_stream2sentence_version: bool

# Define the CoquiEngineRequest model
class CoquiEngineRequest(BaseModel):
    specific_model: str
    use_deepspeed: bool
    local_models_path: str

# Define the TextToAudioStreamRequest model
class TextToAudioStreamRequest(BaseModel):
    engine: CoquiEngineRequest
    specific_model: str
    use_deepspeed: bool
    local_models_path: str

# Define the OutputFolderRequest model
class OutputFolderRequest(BaseModel):
    output_folder: str

@app.post("/v1/audio/speech")
async def tts_to_audio(request: SynthesisRequest, background_tasks: BackgroundTasks):
    if STREAM_MODE or STREAM_MODE_IMPROVE:
        try:
            global stream
            # Validate language code against supported languages.
            #if request.language.lower() not in supported_languages:
            #    raise HTTPException(status_code=400,
            #                        detail="Language code sent is either unsupported or misspelled.")

            speaker_wav = XTTS.get_speaker_wav(request.voice)
            language = LANG[0:2]

            if stream.is_playing() and not STREAM_PLAY_SYNC:
                stream.stop()
                stream = TextToAudioStream(engine)

            engine.set_voice(speaker_wav)
            engine.language = LANG

            # Start streaming, works only on your local computer.
            stream.feed(request.input)
            play_stream(stream, language)

            # It's a hack, just send 1 second of silence so that there is no sillyTavern error.
            this_dir = Path(__file__).parent.resolve()
            output = this_dir / "RealtimeTTS" / "silence.wav"


            return FileResponse(
                path=output,
                media_type='audio/wav',
                filename="silence.wav",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    else:
        try:
            if XTTS.model_source == "local":
                logger.info(f"Processing TTS to audio with request: {request}")

            # Validate language code against supported languages.
            #if request.language.lower() not in supported_languages:
            #    raise HTTPException(status_code=400,
            #                        detail="Language code sent is either unsupported or misspelled.")

            # Generate an audio file using process_tts_to_file.
            output_file_path = XTTS.process_tts_to_file(
                text=request.input,
                speaker_name_or_path=request.voice,
                language=LANG,
                file_name_or_path=f'{str(uuid4())}.wav'
            )

            if not XTTS.enable_cache_results:
                background_tasks.add_task(os.unlink, output_file_path)


            # Return the file in the response
            return FileResponse(
                path=output_file_path,
                media_type='audio/wav',
                filename="output.wav",
            )

        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/tts_to_file")
async def tts_to_file(request: SynthesisFileRequest):

    try:
        if XTTS.model_source == "local":
            logger.info(f"Processing TTS to file with request: {request}")

        # Validate language code against supported languages.
        #if request.language.lower() not in supported_languages:
        #    raise HTTPException(status_code=400,
        #                        detail="Language code sent is either unsupported or misspelled.")

        # Now use process_tts_to_file for saving the file.
        output_file = XTTS.process_tts_to_file(
            text=request.input,
            speaker_name_or_path=request.voice,
            language=LANG.lower(),
            file_name_or_path=request.file_name_or_path  # The user-provided path to save the file is used here.
        )

        return {"message": "The audio was successfully made and stored.", "output_path": output_file}

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)