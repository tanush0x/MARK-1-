"""
Gemini Live AI Assistant
Camera + Microphone + Speaker

Install:
pip install google-genai opencv-python pyaudio pillow mss

Set your API key:
Windows PowerShell:
$env:GEMINI_API_KEY="YOUR_API_KEY"

Run:
python main.py

Camera mode:
python main.py --mode camera

Screen mode:
python main.py --mode screen

No camera/screen:
python main.py --mode none

Press Ctrl+C to exit.
"""

import os
import asyncio
import base64
import io
import traceback
import argparse

import cv2
import pyaudio
import PIL.Image

from google import genai
from google.genai import types


# ============================================================
# AUDIO SETTINGS
# ============================================================

FORMAT = pyaudio.paInt16
CHANNELS = 1

# Gemini Live microphone input
SEND_SAMPLE_RATE = 16000

# Gemini Live speaker output
RECEIVE_SAMPLE_RATE = 24000

CHUNK_SIZE = 1024


# ============================================================
# GEMINI
# ============================================================

MODEL = "models/gemini-3.8-live-extended-thinking"

DEFAULT_MODE = "camera"

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set.\n"
        "Set it before running the program."
    )


client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=API_KEY,
)


# ============================================================
# GEMINI LIVE CONFIG
# ============================================================

CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],

    media_resolution="MEDIA_RESOLUTION_MEDIUM",

    thinking_config=types.ThinkingConfig(
        thinking_level="LOW",
    ),

    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Zephyr"
            )
        )
    ),

    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=104857,
        sliding_window=types.SlidingWindow(
            target_tokens=52428
        ),
    ),
)


# ============================================================
# PY AUDIO
# ============================================================

pya = pyaudio.PyAudio()


# ============================================================
# AUDIO LOOP
# ============================================================

class AudioLoop:

    def __init__(self, video_mode=DEFAULT_MODE):

        self.video_mode = video_mode

        self.audio_in_queue = None
        self.out_queue = None

        self.session = None

        self.audio_stream = None
        self.output_stream = None

        self.camera = None


    # ========================================================
    # OPTIONAL TEXT INPUT
    # ========================================================

    async def send_text(self):

        while True:

            try:
                text = await asyncio.to_thread(
                    input,
                    "message > "
                )

                if text.lower().strip() == "q":
                    break

                if text.strip() and self.session is not None:

                    await self.session.send_client_content(
                        turns=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part(
                                        text=text
                                    )
                                ],
                            )
                        ],
                        turn_complete=True,
                    )

            except (EOFError, KeyboardInterrupt):
                break


    # ========================================================
    # CAMERA FRAME
    # ========================================================

    def _get_frame(self, cap):

        ret, frame = cap.read()

        if not ret:
            return None

        # OpenCV BGR -> RGB
        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        img = PIL.Image.fromarray(frame_rgb)

        # Resize large images
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()

        img.save(
            image_io,
            format="jpeg",
            quality=80
        )

        image_io.seek(0)

        image_bytes = image_io.read()

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(
                image_bytes
            ).decode()
        }


    # ========================================================
    # CAMERA LOOP
    # ========================================================

    async def get_frames(self):

        print("📷 Starting camera...")

        cap = await asyncio.to_thread(
            cv2.VideoCapture,
            0
        )

        if not cap.isOpened():

            print("❌ Could not open camera.")

            return

        self.camera = cap

        print("📷 Camera is working.")

        try:

            while True:

                frame = await asyncio.to_thread(
                    self._get_frame,
                    cap
                )

                if frame is None:
                    break

                if self.out_queue is not None:

                    await self.out_queue.put(
                        frame
                    )

                # Send approximately once per second
                await asyncio.sleep(1.0)

        finally:

            cap.release()

            self.camera = None

            print("📷 Camera stopped.")


    # ========================================================
    # SCREEN CAPTURE
    # ========================================================

    def _get_screen(self):

        try:

            import mss

        except ImportError:

            raise ImportError(
                "Please install mss:\n"
                "pip install mss"
            )

        with mss.mss() as sct:

            monitor = sct.monitors[0]

            screenshot = sct.grab(
                monitor
            )

            image_bytes = mss.tools.to_png(
                screenshot.rgb,
                screenshot.size
            )

        img = PIL.Image.open(
            io.BytesIO(image_bytes)
        )

        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()

        img.save(
            image_io,
            format="jpeg",
            quality=80
        )

        image_io.seek(0)

        image_bytes = image_io.read()

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(
                image_bytes
            ).decode()
        }


    # ========================================================
    # SCREEN LOOP
    # ========================================================

    async def get_screen(self):

        print("🖥️ Starting screen sharing...")

        while True:

            frame = await asyncio.to_thread(
                self._get_screen
            )

            if frame is None:
                break

            if self.out_queue is not None:

                await self.out_queue.put(
                    frame
                )

            await asyncio.sleep(1.0)


    # ========================================================
    # SEND CAMERA / SCREEN TO GEMINI
    # ========================================================

    async def send_realtime(self):

        while True:

            msg = await self.out_queue.get()

            if self.session is None:
                continue

            try:

                image_data = base64.b64decode(
                    msg["data"]
                )

                await self.session.send_realtime_input(
                    media=types.Blob(
                        data=image_data,
                        mime_type=msg["mime_type"]
                    )
                )

            except Exception as e:

                print(
                    f"\n⚠️ Video error: {e}"
                )


    # ========================================================
    # MICROPHONE
    # ========================================================

    async def listen_audio(self):

        print("🎤 Finding microphone...")

        mic_info = pya.get_default_input_device_info()

        print(
            f"🎤 Microphone: {mic_info['name']}"
        )

        self.audio_stream = await asyncio.to_thread(
            pya.open,

            format=FORMAT,

            channels=CHANNELS,

            rate=SEND_SAMPLE_RATE,

            input=True,

            input_device_index=mic_info["index"],

            frames_per_buffer=CHUNK_SIZE,
        )

        print("🎤 Microphone is listening.")
        print("🗣️ Speak normally...\n")

        while True:

            try:

                data = await asyncio.to_thread(
                    self.audio_stream.read,
                    CHUNK_SIZE,
                    exception_on_overflow=False
                )

                if self.session is not None:

                    await self.session.send_realtime_input(
                        audio=types.Blob(
                            data=data,
                            mime_type="audio/pcm;rate=16000"
                        )
                    )

            except asyncio.CancelledError:

                break

            except Exception as e:

                print(
                    f"\n⚠️ Microphone error: {e}"
                )

                await asyncio.sleep(0.1)


    # ========================================================
    # RECEIVE GEMINI RESPONSE
    # ========================================================

    async def receive_audio(self):

        print("🤖 Gemini Live connected.")
        print("🎧 Waiting for Gemini...\n")

        while True:

            if self.session is None:
                await asyncio.sleep(0.1)
                continue

            try:

                turn = self.session.receive()

                async for response in turn:

                    # Audio response
                    if response.data:

                        await self.audio_in_queue.put(
                            response.data
                        )

                    # Text response if available
                    if response.text:

                        print(
                            response.text,
                            end="",
                            flush=True
                        )

            except asyncio.CancelledError:

                break

            except Exception as e:

                print(
                    f"\n⚠️ Receive error: {e}"
                )

                await asyncio.sleep(0.5)

            # Clear old audio after turn
            if self.audio_in_queue is not None:

                while not self.audio_in_queue.empty():

                    try:
                        self.audio_in_queue.get_nowait()

                    except asyncio.QueueEmpty:
                        break


    # ========================================================
    # PLAY GEMINI AUDIO
    # ========================================================

    async def play_audio(self):

        self.output_stream = await asyncio.to_thread(
            pya.open,

            format=FORMAT,

            channels=CHANNELS,

            rate=RECEIVE_SAMPLE_RATE,

            output=True,
        )

        print("🔊 Speaker is ready.")

        while True:

            try:

                bytestream = await self.audio_in_queue.get()

                await asyncio.to_thread(
                    self.output_stream.write,
                    bytestream
                )

            except asyncio.CancelledError:

                break

            except Exception as e:

                print(
                    f"\n⚠️ Speaker error: {e}"
                )


    # ========================================================
    # MAIN
    # ========================================================

    async def run(self):

        try:

            print()
            print("=" * 55)
            print("        GEMINI LIVE AI ASSISTANT")
            print("=" * 55)
            print()
            print(f"Model : {MODEL}")
            print(f"Mode  : {self.video_mode}")
            print()
            print("Connecting to Gemini Live...")
            print()

            async with client.aio.live.connect(
                model=MODEL,
                config=CONFIG
            ) as session:

                self.session = session

                self.audio_in_queue = asyncio.Queue()

                self.out_queue = asyncio.Queue(
                    maxsize=5
                )

                async with asyncio.TaskGroup() as tg:

                    # Optional text input
                    # You can still type messages if you want.
                    tg.create_task(
                        self.send_text()
                    )

                    # Camera / screen sender
                    tg.create_task(
                        self.send_realtime()
                    )

                    # Microphone
                    tg.create_task(
                        self.listen_audio()
                    )

                    # Camera
                    if self.video_mode == "camera":

                        tg.create_task(
                            self.get_frames()
                        )

                    # Screen
                    elif self.video_mode == "screen":

                        tg.create_task(
                            self.get_screen()
                        )

                    # Gemini response
                    tg.create_task(
                        self.receive_audio()
                    )

                    # Speaker
                    tg.create_task(
                        self.play_audio()
                    )

                    # Keep program running
                    while True:

                        await asyncio.sleep(1)


        except KeyboardInterrupt:

            print("\n\n🛑 Stopping...")

        except asyncio.CancelledError:

            pass

        except Exception as e:

            print("\n❌ ERROR:")
            traceback.print_exc()

        finally:

            # Close microphone
            if self.audio_stream is not None:

                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()

                except Exception:
                    pass

            # Close speaker
            if self.output_stream is not None:

                try:
                    self.output_stream.stop_stream()
                    self.output_stream.close()

                except Exception:
                    pass

            # Close camera
            if self.camera is not None:

                try:
                    self.camera.release()

                except Exception:
                    pass

            print("\n👋 Gemini Live stopped.")


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        choices=[
            "camera",
            "screen",
            "none"
        ],
        help="camera, screen, or none"
    )

    args = parser.parse_args()

    assistant = AudioLoop(
        video_mode=args.mode
    )

    try:

        asyncio.run(
            assistant.run()
        )

    finally:

        pya.terminate()
