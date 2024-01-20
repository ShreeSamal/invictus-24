from flask import Flask ,render_template, request
import googleapiclient.discovery
from datetime import datetime, timedelta

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

API_KEY_A = 'AIzaSyAwFJu9A8LOrWgxpCQi-zUTJ3fUYsFEEnY'
youtube_A = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY_A)

local_server = True
app = Flask(__name__)

def get_trending_videos_until_yesterday(max_results=10):
    # Set the publishedAfter and publishedBefore parameters for yesterday
    yesterday = datetime.utcnow() - timedelta(days=1)
    published_after = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    published_before = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Dictionary to store video details
    video_details_dict = {}

    # Get trending videos until yesterday in India
    request = youtube_A.videos().list(
        part='snippet,statistics',
        chart='mostPopular',
        regionCode='US',
        videoCategoryId='0',
        maxResults=max_results
    )
    response = request.execute()

    for item in response['items']:
        video_id = item['id']
        title = item['snippet']['title']
        like_count = item['statistics']['likeCount']
        view_count = item['statistics']['viewCount']
        if 'commentCount' in item['statistics']:
            comments_count = item['statistics']['commentCount']
        else:
            comments_count = 0
        published_at = datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')

        # Filter videos based on publication date
        if published_after <= published_at <= published_before:
            # Store details in the dictionary
            video_details_dict[video_id] = {
                'title': title,
                'video_link': f"https://www.youtube.com/watch?v={video_id}",
                'embed_link': f"https://www.youtube.com/embed/{video_id}",
                'like_count': like_count,
                'view_count': view_count,
                'comments_count': comments_count,
            }

    return video_details_dict

video_details_dict = get_trending_videos_until_yesterday()

def search_videos(query, max_results=6):
    request = youtube_A.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=max_results
    )
    response = request.execute()

    video_details_dict = {}

    for item in response.get('items', []):
        video_id = item['id']['videoId']
        title = item['snippet']['title']

        # Get video statistics using another API call
        stats_request = youtube_A.videos().list(
            part='statistics',
            id=video_id
        )
        stats_response = stats_request.execute()

        if stats_response.get('items'):
            statistics = stats_response['items'][0]['statistics']
            like_count = statistics.get('likeCount', 0)
            view_count = statistics.get('viewCount', 0)
            comments_count = statistics.get('commentCount', 0)
        else:
            like_count = 0
            view_count = 0
            comments_count = 0

        video_details_dict[video_id] = {
            'title': title,
            'video_link': f"https://www.youtube.com/watch?v={video_id}",
            'embed_link': f"https://www.youtube.com/embed/{video_id}",
            'like_count': like_count,
            'view_count': view_count,
            'comments_count': comments_count,
        }

    return video_details_dict

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("index.html", video_details_dict = video_details_dict)

@app.route("/trending/summary/<string:video_id>", methods=['GET', 'POST'])
def trend_summary(video_id):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(video_details_dict[video_id]['title'])
    filtered_text = [word for word in word_tokens if word.lower() not in stop_words]
    
    new_text = []
    
    for i in filtered_text:
        if i.isalnum():
            new_text.append(i.lower())
    
    recommended_video = search_videos(new_text)
    
    del recommended_video[video_id]
    
    return render_template("summary_trend.html", video_details_lst = video_details_dict[video_id], recommended_video = recommended_video)

if __name__ == '__main__':  
   app.run(debug = True)