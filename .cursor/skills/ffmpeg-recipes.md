---
name: ffmpeg-recipes
description: FFmpeg Recipes Technical Encyclopedia: SVT-AV1, Hardware Acceleration, HDR10/HLG, and Professional Transcoding Standards.
---

# Skill: FFmpeg Recipes (Technical Encyclopedia)

[Back to README](../../README.md)

Comprehensive technical protocols for industrial-grade media processing, transcoding, and stream orchestration using FFmpeg in the 2025 ecosystem. This document defines the standards for high-efficiency codecs (AV1), hardware-accelerated pipelines, and professional color-space management.

---

## 1. High-Efficiency Video Coding (AV1 & SVT-AV1)
The 2025 standard for royalty-free, high-fidelity video distribution.

### 1.1 SVT-AV1 Parameters (Theoretical Maximum)
*   **Target Bitrate:** Mandatory use of CRL (Constant Rate Factor) or 2-pass VBR (Variable Bitrate) for consistent quality.
*   **Key Parameters:**
    *   `-preset`: Range 0-13 (Standard: 6 for archival, 10 for real-time).
    *   `-crf`: Range 0-63 (Standard: 24-30 for 4K, 32-35 for 1080p).
    *   `-tune`: `0` (PQ) or `1` (SSIM).

### 1.2 Transcoding Implementation Protocol
```bash
# 1.2.1 High-Quality 4K SVT-AV1 Archive
ffmpeg -i input.mov \
    -c:v libsvtav1 -preset 6 -crf 24 \
    -svtav1-params "tune=0:enable-overlays=1:film-grain=8" \
    -pix_fmt yuv420p10le \ # 10-bit color mandatory for AV1
    -c:a libopus -b:a 192k \ # Opus is the standard audio pair for AV1
    output.mkv
```

---

## 2. Hardware Acceleration (GPU Offloading)
Optimizing throughput by utilizing specialized CPU/GPU instruction sets.

### 2.1 Cross-Platform Acceleration Protocols
*   **Linux (VAAPI):** `-hwaccel vaapi -hwaccel_device /dev/dri/renderD128`
*   **Windows (D3D11VA):** `-hwaccel d3d11va`
*   **NVIDIA (CUDA/NVENC):** `-hwaccel cuda -c:v h264_nvenc`
*   **macOS (VideoToolbox):** `-c:v h264_videotoolbox`

### 2.2 Low-Latency Stream Transmuxing
Utilizing `-c:v copy` and `-c:a copy` to change containers without re-encoding, preserving 100% quality and using minimal CPU.

---

## 3. Professional Color-Space & HDR Management
Handling HDR10, HLG, and Dolby Vision metadata and tonemapping.

### 3.1 HDR10+ Tonemapping Standard
*   **Protocol:** Utilizing the `zscale` or `tonemap` filters to convert HDR content for SDR displays while preserving dynamic range.
    ```bash
    ffmpeg -i hdr_input.mp4 \
        -vf "zscale=t=linear:npl=100,format=gbrp,tonemap=tonemap=mobius:param=0.01,zscale=p=709:t=709:m=709" \
        -c:v libx264 -crf 18 output_sdr.mp4
    ```

### 3.2 Metadata Verification Checklist
- [ ] `-color_primaries bt2020`
- [ ] `-color_trc smpte2084`
- [ ] `-colorspace bt2020_ncl`

---

## 4. Technical Appendix: Comprehensive CLI Flag Reference
| Flag | Detailed Purpose | Context |
| :--- | :--- | :--- |
| `-movflags +faststart` | Relocates 'moov' atom to the head for web streaming | Web MP4 |
| `-pix_fmt yuv420p` | Maximum compatibility for H.264/H.265 decoders | Global |
| `-g <N>` | Set GOP (Group of Pictures) size for seeking performance | Streaming |
| `-map 0:v:0` | Explicitly selecting the first video stream from the first input | Multi-track |
| `-vf scale=-1:1080` | Aspect-ratio-preserving downscaling to 1080p | Scaling |

---

## 5. Industrial Case Study: Multi-Platform Social Media Export
**Objective:** Simultaneously output 9:16 (TikTok), 1:1 (Instagram), and 16:9 (YouTube) versions from a master 4K file.
1.  **Filter Complex:** Using `[0:v]split=3[v1][v2][v3]` to generate three parallel video paths.
2.  **Cropping:** Applying `crop=1080:1920` for vertical formats and `crop=1080:1080` for square.
3.  **Hardware Encoding:** Utilizing `h264_nvenc` with three parallel output streams to maximize GPU usage.
4.  **Bitrate Targeting:** Applying `-maxrate` and `-bufsize` to ensure compatibility with mobile platforms.

---

## 6. Glossary of FFmpeg & Video Terms
*   **Transcoding:** Decoding a stream and re-encoding it into a different format (lossy process).
*   **Transmuxing:** Changing the container (e.g., MP4 to MKV) without changing the bitstream (lossless process).
*   **CRF (Constant Rate Factor):** A rate-control mode that keeps the quality constant relative to the complexity of the frame.
*   **SVT-AV1:** Scalable Video Technology for AV1, the industrial reference encoder for AV1.
*   **Pixel Format (pix_fmt):** The arrangement of color components in memory (e.g., `yuv422p10le`).

---

## 7. Mathematical Bitrate Calculation
*   **Formula:** $\text{Bitrate} = \text{Width} \cdot \text{Height} \cdot \text{FPS} \cdot \text{Bits Per Pixel (BPP)}$
*   **BPP Guideline:** 
    *   SDR: 0.1 - 0.15
    *   HDR: 0.2 - 0.25
*   **Example:** $3840 \cdot 2160 \cdot 60 \cdot 0.2 = 99,532,800$ bps (~100 Mbps).

---

## 8. Troubleshooting & Performance Verification
*   **Frame Drops:** Checking the `fps=` counter in FFmpeg logs. *Fix: Switch to a faster `-preset` or enable hardware acceleration.*
*   **Sync Issues:** Managing `-itsoffset` to fix audio/video delay.
*   **Container Errors:** Fixing corrupted headers using `-f null -` as an initial health check.

---

## 9. Appendix: Advanced Complex Filters
*   **Overlaying:** Putting a logo over a video using `[0:v][1:v]overlay=W-w-10:H-h-10`.
*   **Concatenation:** Using the `concat` protocol for seamless merging of clips with identical parameters.

---

## 10. Benchmarks & Scaling Laws (2025)
| Codec | Encoder | Preservation | Speed (relative) |
| :--- | :--- | :--- | :--- |
| **H.264** | x264 | 75% | 1.0x |
| **H.265** | x265 | 90% | 0.4x |
| **AV1** | SVT-AV1 | 95% | 0.2x |
| **H.265 (NV)**| NVENC | 85% | 5.0x |

---
[Back to README](../../README.md)
