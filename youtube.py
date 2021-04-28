import os
import re
import time
import requests
import contextlib

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()


DEVELOPER_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
DEFAULT_CHANNEL_ID = "UCRDDHLvQb8HjE2r7_ZuNtWA"  # signal music studios


def get_channel_videos_api(channel_id=DEFAULT_CHANNEL_ID, max_results=5):
    """
    Retrieves last (maxResults) of videos in revers chronological order
    or a specific channel.

    Args:
    channelId (str): id found in URL in homepage of YouTube channel.
    maxResults (int): the amount of results returned desire (max 50)

    Returns:
    list: a list of json (NLJSON) representing [title, description, videoID, publishTime].
    """
    youtube = build(YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    search_response = youtube.search().list(channelId=channel_id,
                                            part='id,snippet',
                                            maxResults=max_results,
                                            order="date").execute()

    # Add each result to the list
    videos = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            video = {"title": search_result['snippet']['title'],
                     "description": search_result['snippet']['description'],
                     "video_id": search_result['id']['videoId'],
                     "publish_time": search_result['snippet']['publishTime']}

        videos.append(video)
    return videos


def get_video_information(video_id):
    """

    """
    pass


def get_channel_video_ids_scrape(channel_id=DEFAULT_CHANNEL_ID):
    """

    """
    rg = re.compile(r'\{"videoId":"([\w&-]+)"')
    channel_url = f'https://www.youtube.com/channel/{channel_id}/videos'
    response = requests.get(channel_url)

    if response.status_code != 200:
        print(f"Non 200 status code in call to channel_url: {channel_url}")
        print(response.content)

    text = str(response.content)
    video_ids = list(set(rg.findall(text)))

    return video_ids


def video_has_transcript(video_id):
    """

    """
    try:
        with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
            for vid in YouTubeTranscriptApi.list_transcripts(video_id):
                if vid.language_code == 'en':
                    return True
    except Exception as e:
        pass
    return False


def get_video_text(video_id):
    """

    """
    if video_has_transcript(video_id):
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = ' '.join([chunk['text'] for chunk in transcript])
        return full_text
    return False


if __name__ == '__main__':
    # See if scrape and api are the same
    videos_from_api = get_channel_videos_api(max_results=30)
    api_ids = sorted([vid['video_id'] for vid in videos_from_api])
    scrape_ids = sorted(get_channel_video_ids_scrape())
    scrape_api_same = scrape_ids == api_ids
    print(f"Scrape and Api Same: {scrape_api_same}")

    # See how many have transcripts
    transcripts = [video_has_transcript(id) for id in api_ids]
    print(f"{sum(transcripts)} / {len(transcripts)} videos have transcripts")

    # test a transcription
    example_id = [id for has_trans, id in zip(transcripts, api_ids) if has_trans][-1]
    transcript = get_video_text(example_id)
    print(f"EXAMPLE TRANS - Total Len: {len(transcript):,} characters")
    print(transcript[:150])

    # stress scrape video id
    print("\nSCRAPE TEST")
    truth = scrape_ids
    start_time = time.time()
    for call_num in range(100):
        print(f"\rCall: {call_num}", end='')
        test_ids = sorted(get_channel_video_ids_scrape())
        if test_ids != truth:
            print("error in video id fetch")
            break
    total_time = time.time() - start_time
    print(f"\nMade {call_num + 1} calls in {total_time:,.0f} seconds")
