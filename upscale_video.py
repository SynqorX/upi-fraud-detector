#!/usr/bin/env python3
"""
Video Upscaler Pipeline using waifu2x-ncnn-vulkan + FFmpeg.
Upscales video frames using local Vulkan/GPU acceleration, preserves audio, and muxes high-bitrate output.
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

def upscale_video(input_path: str, output_path: str, scale: int = 2, denoise: int = 1):
    input_file = Path(input_path).resolve()
    output_file = Path(output_path).resolve()
    
    if not input_file.exists():
        print(f"Error: Input video '{input_file}' not found.")
        sys.exit(1)
        
    work_dir = Path("/tmp/video_upscale_work")
    if work_dir.exists():
        shutil.rmtree(work_dir)
        
    frames_in = work_dir / "frames_in"
    frames_out = work_dir / "frames_out"
    frames_in.mkdir(parents=True, exist_ok=True)
    frames_out.mkdir(parents=True, exist_ok=True)
    
    print(f"==> Step 1/4: Extracting audio and framerate from {input_file.name}...")
    # Get framerate
    cmd_fps = [
        "ffprobe", "-v", "0", "-of", "csv=p=0", 
        "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", str(input_file)
    ]
    fps = subprocess.check_output(cmd_fps).decode().strip()
    print(f"    Detected framerate: {fps} fps")
    
    # Extract audio
    audio_file = work_dir / "audio.aac"
    has_audio = False
    cmd_audio = [
        "ffmpeg", "-y", "-i", str(input_file), "-vn", "-c:a", "copy", str(audio_file)
    ]
    res = subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and audio_file.exists() and audio_file.stat().st_size > 0:
        has_audio = True
        print("    Extracted original audio stream.")
    else:
        print("    No audio stream detected (video only).")
        
    print(f"==> Step 2/4: Extracting video frames...")
    cmd_extract = [
        "ffmpeg", "-y", "-i", str(input_file), 
        "-qscale:v", "1", "-qmin", "1", 
        str(frames_in / "frame_%06d.png")
    ]
    subprocess.run(cmd_extract, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    total_frames = len(list(frames_in.glob("*.png")))
    print(f"    Extracted {total_frames} frames.")
    
    print(f"==> Step 3/4: AI Neural Upscaling {scale}x (denoise={denoise}) with waifu2x-ncnn-vulkan...")
    start_time = time.time()
    cmd_upscale = [
        "waifu2x-ncnn-vulkan",
        "-i", str(frames_in),
        "-o", str(frames_out),
        "-s", str(scale),
        "-n", str(denoise),
        "-f", "png",
        "-j", "1:2:2"
    ]
    subprocess.run(cmd_upscale, check=True)
    elapsed = time.time() - start_time
    print(f"    Neural upscaling completed in {elapsed:.1f}s ({elapsed/max(1, total_frames):.2f}s per frame).")
    
    print(f"==> Step 4/4: Reassembling into output video {output_file.name}...")
    cmd_reassemble = [
        "ffmpeg", "-y",
        "-r", fps,
        "-i", str(frames_out / "frame_%06d.png")
    ]
    if has_audio:
        cmd_reassemble.extend(["-i", str(audio_file)])
        
    cmd_reassemble.extend([
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p"
    ])
    
    if has_audio:
        cmd_reassemble.extend(["-c:a", "copy"])
        
    cmd_reassemble.append(str(output_file))
    subprocess.run(cmd_reassemble, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup temp frames
    shutil.rmtree(work_dir)
    print(f"SUCCESS: Upscaled video saved to {output_file}")
    
    # Print info
    cmd_info = ["ffprobe", "-v", "error", "-show_entries", "stream=width,height,bit_rate", "-of", "default=noprint_wrappers=1", str(output_file)]
    info = subprocess.check_output(cmd_info).decode().strip()
    print("Output Video Info:\n" + info)

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "background.mp4"
    dst = sys.argv[2] if len(sys.argv) > 2 else "background_upscaled.mp4"
    upscale_video(src, dst)
