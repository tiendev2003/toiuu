# tải video
import requests

def downloadVideo(videoUrl, outputPath):
    try:
        response = requests.get(videoUrl, stream=True)
        response.raise_for_status()  # Raise an error for HTTP errors

        with open(outputPath, 'wb') as videoFile:
            for chunk in response.iter_content(chunk_size=8192):
                videoFile.write(chunk)

        print(f"Video downloaded successfully: {outputPath}")
    except Exception as e:
        print(f"Error downloading video: {e}")

videoUrl = "https://upload.dananggo.com/videos/19_08_2025/68a47064c2afc_1755607140.mp4"  # Replace with the actual video URL
outputPath = "video.mp4"  # Replace with the desired output path

downloadVideo(videoUrl, outputPath)