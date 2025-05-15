# Fast Bunny CDN Video Downloader with Quality Selection

A high-performance Python script to download videos from Bunny CDN with DRM support and quality selection options. Features optimized download speeds with progress tracking.

## Features

- Fast video downloads with multi-threading support
- Real-time download progress with speed and ETA
- Quality selection with detailed specifications
- Supports multiple quality options:
  - 2160p (4K UHD) - Resolution: 3840x2160, Bitrate: 35-45 Mbps
  - 1440p (2K QHD) - Resolution: 2560x1440, Bitrate: 16-24 Mbps
  - 1080p (Full HD) - Resolution: 1920x1080, Bitrate: 8-12 Mbps
  - 720p (HD) - Resolution: 1280x720, Bitrate: 5-7.5 Mbps
  - 480p (SD) - Resolution: 854x480, Bitrate: 2.5-4 Mbps
  - 360p (LD) - Resolution: 640x360, Bitrate: 1-1.5 Mbps
  - 240p (Very LD) - Resolution: 426x240, Bitrate: 0.5-0.7 Mbps
- Automatic resume of interrupted downloads
- Cross-platform support (Windows, Linux, macOS)

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/)
2. Clone the repository:
```powershell
git clone https://github.com/01RG0/yt-dlp-downloader.git
cd yt-dlp-downloader
```
3. Install requirements:
```powershell
python -m pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)

1. Install Python and git:
```bash
sudo apt update
sudo apt install python3 python3-pip git
```
2. Clone the repository:
```bash
git clone https://github.com/yourusername/bunny-cdn-video-downloader.git
cd bunny-cdn-video-downloader
```
3. Install requirements:
```bash
python3 -m pip install -r requirements.txt
```

### macOS

1. Install Homebrew if not already installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
2. Install Python:
```bash
brew install python
```
3. Clone the repository:
```bash
git clone https://github.com/yourusername/bunny-cdn-video-downloader.git
cd bunny-cdn-video-downloader
```
4. Install requirements:
```bash
python3 -m pip install -r requirements.txt
```

## Usage

### Windows
```powershell
python b-cdn-drm-vod-dl.py
```

### Linux/macOS
```bash
python3 b-cdn-drm-vod-dl.py
```

The script will prompt for:
1. Embed URL of the video
2. Desired filename (without extension)
3. Download path (optional)
   - Windows default: `~/Videos/Bunny CDN/`
   - Linux/macOS default: `~/Videos/Bunny CDN/`

Then:
1. Available video qualities will be displayed with detailed specifications
2. Select your preferred quality by entering the corresponding number
3. The download will start with a progress bar showing:
   - Download speed
   - Progress percentage
   - ETA (Estimated Time of Arrival)
   - File size

### Tips for Faster Downloads

- The script uses multi-threading for improved download speed
- Downloads are automatically resumed if interrupted
- Temporary files are cleaned up after download completion
- For best performance, ensure a stable internet connection

### Troubleshooting

If you encounter any issues:

1. Check your internet connection
2. Verify the embed URL is correct
3. Ensure you have write permissions in the download directory
4. Try updating the dependencies:
   ```bash
   python -m pip install -r requirements.txt --upgrade
   ```
5. Check if the video is still available on the server

## Notes

- The script will automatically detect available quality options for the video
- Higher quality videos will require more bandwidth and storage space
- The download will be saved with the .mp4 extension
- If no download path is specified, files will be saved to ~/Videos/Bunny CDN/

## Dependencies

- Python 3.7+
- requests
- yt-dlp

## License

MIT License - feel free to use and modify as needed.
