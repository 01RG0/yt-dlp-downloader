import re
import sys
import os
from hashlib import md5
from html import unescape
from random import random
from urllib.parse import urlparse
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

import requests
import yt_dlp

# Video quality specifications
QUALITY_SPECS = {
    "2160p": {"resolution": "3840x2160", "bitrate": "35-45 Mbps", "name": "4K UHD"},
    "1440p": {"resolution": "2560x1440", "bitrate": "16-24 Mbps", "name": "2K QHD"},
    "1080p": {"resolution": "1920x1080", "bitrate": "8-12 Mbps", "name": "Full HD"},
    "720p": {"resolution": "1280x720", "bitrate": "5-7.5 Mbps", "name": "HD"},
    "480p": {"resolution": "854x480", "bitrate": "2.5-4 Mbps", "name": "SD"},
    "360p": {"resolution": "640x360", "bitrate": "1-1.5 Mbps", "name": "LD"},
    "240p": {"resolution": "426x240", "bitrate": "0.5-0.7 Mbps", "name": "Very LD"}
}

class BunnyVideoDRM:
    # user agent and platform related headers
    user_agent = {
        "sec-ch-ua": '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    }
    session = requests.Session()
    session.headers.update(user_agent)

    def __init__(self, referer: str = "https://127.0.0.1/", embed_url: str = "", name: str = "", path: str = "") -> None:
        if not embed_url:
            print("Error: Embed URL is required")
            sys.exit(1)
            
        self.referer: str = referer if referer else "https://127.0.0.1/"
        self.embed_url: str = embed_url
        self.guid: str = urlparse(embed_url).path.split("/")[-1]
        self.headers: Dict[str, Dict[str, str]] = {
            "embed": {
                "authority": "iframe.mediadelivery.net",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "referer": referer,
                "sec-fetch-dest": "iframe",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "cross-site",
                "upgrade-insecure-requests": "1",
            },
            "ping|activate": {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "origin": "https://iframe.mediadelivery.net",
                "pragma": "no-cache",
                "referer": "https://iframe.mediadelivery.net/",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
            },
            "playlist": {
                "authority": "iframe.mediadelivery.net",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "referer": embed_url,
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            },
        }
        
        # Get embed page
        try:
            embed_response = self.session.get(embed_url, headers=self.headers["embed"])
            embed_response.raise_for_status()
            embed_page = embed_response.text
        except requests.RequestException as e:
            print(f"Error fetching video page: {str(e)}")
            sys.exit(1)

        # Extract server ID
        server_match = re.search(r"https://video-(.*?)\.mediadelivery\.net", embed_page)
        if not server_match:
            print("Error: Could not find server ID in the page")
            sys.exit(1)
        self.server_id: str = server_match.group(1)

        # Update headers with server ID
        self.headers["ping|activate"].update(
            {"authority": f"video-{self.server_id}.mediadelivery.net"}
        )

        # Extract context ID and secret
        context_match = re.search(r'contextId=(.*?)&secret=(.*?)"', embed_page)
        if not context_match:
            print("Error: Could not find context ID and secret in the page")
            sys.exit(1)
        self.context_id: str = context_match.group(1)
        self.secret: str = context_match.group(2)

        # Set filename
        if name:
            self.file_name: str = f"{name}.mp4"
        else:
            title_match = re.search(r'og:title" content="(.*?)"', embed_page)
            if not title_match:
                self.file_name = "video.mp4"
            else:
                file_name_unescaped = title_match.group(1)
                file_name_escaped = unescape(file_name_unescaped)
                self.file_name = re.sub(r"\.[^.]*$.*", ".mp4", file_name_escaped)
                if not self.file_name.endswith(".mp4"):
                    self.file_name += ".mp4"

        self.path: str = path if path else "~/Videos/Bunny CDN/"

    def get_available_qualities(self, resolutions: List[str]) -> Dict[int, str]:
        """Returns a dictionary of available quality options."""
        qualities = {}
        for i, res in enumerate(resolutions, 1):
            height = res.split('x')[-1]
            quality_name = f"{height}p"
            if quality_name in QUALITY_SPECS:
                specs = QUALITY_SPECS[quality_name]
                qualities[i] = f"{quality_name} ({specs['name']}) - Resolution: {specs['resolution']}, Bitrate: {specs['bitrate']}"
            else:
                qualities[i] = f"{quality_name} - Resolution: {res}"
        return qualities

    def prepare_dl(self) -> str:
        def ping(time: float, paused: str, res: str) -> None:
            md5_hash = md5(
                f"{self.secret}_{self.context_id}_{time}_{paused}_{res}".encode("utf8")
            ).hexdigest()
            try:
                self.session.get(
                    f"https://video-{self.server_id}.mediadelivery.net/.drm/{self.context_id}/ping",
                    params={
                        "hash": md5_hash,
                        "time": time,
                        "paused": paused,
                        "chosen_res": res,
                    },
                    headers=self.headers["ping|activate"],
                    timeout=10
                ).raise_for_status()
            except requests.RequestException as e:
                print(f"Warning: Ping request failed: {str(e)}")

        def activate() -> None:
            try:
                self.session.get(
                    f"https://video-{self.server_id}.mediadelivery.net/.drm/{self.context_id}/activate",
                    headers=self.headers["ping|activate"],
                    timeout=10
                ).raise_for_status()
            except requests.RequestException as e:
                print(f"Warning: Activation request failed: {str(e)}")

        def main_playlist() -> str:
            try:
                response = self.session.get(
                    f"https://iframe.mediadelivery.net/{self.guid}/playlist.drm",
                    params={"contextId": self.context_id, "secret": self.secret},
                    headers=self.headers["playlist"],
                    timeout=10
                )
                response.raise_for_status()
                resolutions = re.findall(r"\s*(.*?)\s*/video\.drm", response.text)[::-1]
                
                if not resolutions:
                    print("Error: No video qualities found")
                    sys.exit(2)
                
                print("\nAvailable video qualities:")
                qualities = self.get_available_qualities(resolutions)
                for num, quality in qualities.items():
                    print(f"{num}. {quality}")
                
                while True:
                    try:
                        choice = int(input("\nSelect quality number (1 for highest quality): "))
                        if 1 <= choice <= len(resolutions):
                            return resolutions[choice - 1]
                        print("Invalid choice. Please select a number from the list.")
                    except ValueError:
                        print("Please enter a valid number.")
                    
            except requests.RequestException as e:
                print(f"Error fetching playlist: {str(e)}")
                sys.exit(1)

        def video_playlist() -> None:
            params = {"contextId": self.context_id}
            self.session.get(
                f"https://iframe.mediadelivery.net/{self.guid}/{resolution}/video.drm",
                params=params,
                headers=self.headers["playlist"],
            )

        ping(time=0, paused="true", res="0")
        activate()
        resolution = main_playlist()
        video_playlist()
        for i in range(0, 29, 4):  # first 28 seconds, arbitrary (check issue#11)
            ping(
                time=i + round(random(), 6),
                paused="false",
                res=resolution.split("x")[-1],
            )
        self.session.close()
        return resolution

    def download(self) -> None:
        resolution = self.prepare_dl()
        url = [
            f"https://iframe.mediadelivery.net/{self.guid}/{resolution}/video.drm?contextId={self.context_id}"
        ]
        
        class ProgressHook:
            def __init__(self) -> None:
                self.pbar: Optional[tqdm] = None

            def __call__(self, d: Dict[str, Any]) -> None:
                if d['status'] == 'downloading':
                    if self.pbar is None:
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        if total > 0:  # Only show progress bar if we know the size
                            self.pbar = tqdm(
                                total=total,
                                unit='iB',
                                unit_scale=True,
                                desc='Downloading'
                            )
                    if self.pbar is not None:
                        downloaded = d.get('downloaded_bytes', 0)
                        self.pbar.update(downloaded - self.pbar.n)
                elif d['status'] == 'finished' and self.pbar is not None:
                    self.pbar.close()

        ydl_opts = {
            "http_headers": {
                "Referer": self.embed_url,
                "User-Agent": self.user_agent["user-agent"],
            },
            "concurrent_fragment_downloads": 16,  # Increased for faster downloads
            "nocheckcertificate": True,
            "outtmpl": self.file_name,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "nopart": True,
            "paths": {
                "home": os.path.expanduser(self.path),
                "temp": os.path.join(os.path.expanduser(self.path), f".{self.file_name}"),
            },
            "retries": float("inf"),
            "extractor_retries": float("inf"),
            "fragment_retries": float("inf"),
            "skip_unavailable_fragments": False,
            "no_warnings": True,
            "progress_hooks": [ProgressHook()],
            "format": "best",  # Always choose best quality for selected resolution
            "buffersize": 1024 * 1024,  # 1MB buffer size
            "http_chunk_size": 10485760,  # 10MB chunks for faster downloads
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\nDownloading video in {resolution}...")
                ydl.download(url)
                print(f"\nDownload completed! File saved to: {os.path.join(os.path.expanduser(self.path), self.file_name)}")
        except Exception as e:
            print(f"\nError during download: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        print("Bunny CDN Video Downloader")
        print("=========================\n")
        embed_url = input("Enter the embed URL: ")
        name = input("Enter the file name (without extension): ")
        path = input("Enter the download path (leave blank for default): ")

        video = BunnyVideoDRM(
            referer="https://iframe.mediadelivery.net/",
            embed_url=embed_url,
            name=name,
            path=path,
        )
        video.download()
    except KeyboardInterrupt:
        print("\nDownload cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)