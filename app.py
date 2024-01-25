from flask import Flask ,render_template, request, redirect, url_for, flash,jsonify,session
import googleapiclient.discovery
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from getSummary import generate_summary,generate_summary_audio
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from video_audio_caption import create_captions,create_captions_audio
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import OrderedDict
from urllib.parse import urlparse, parse_qs
from flask_bcrypt import Bcrypt
from functools import wraps

sia = SentimentIntensityAnalyzer()

# API_KEY_A = 'AIzaSyBbPQO0_-vLPU8kvgYbPbPlvzxKS0o4sUk'
# API_KEY_A = "AIzaSyB1f-xn81py9UruPLrMnYihldHuhONZU5U"
#API_KEY_A = 'AIzaSyAjKBo9q945sacH_cR7_wxj8G7T8F3B6p0'
# API_KEY_A = 'AIzaSyAhd2CrnNgjDMFwSTa1JFz27btz1rv6M24'
#API_KEY_A = 'AIzaSyA1cg5ojM3qjxNeP2w9TkWqQLWHUI8kzE0'
API_KEY_A = "AIzaSyA6vU5LOTLyl4HZ-8Lf4oZu9FwmdK6u4lk"

youtube_A = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY_A)

local_server = True
app = Flask(__name__)
app.secret_key = "hqvfiuqeogfqlbqljl"
# app.config["MONGO_URI"]="mongodb+srv://cfrost:P2JVTwefRIFHUWQX@invictus24.ilfsi9p.mongodb.net/?retryWrites=true&w=majority"
# db = PyMongo(app).db

uri = "mongodb+srv://cfrost:P2JVTwefRIFHUWQX@invictus24.ilfsi9p.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
bcrypt = Bcrypt(app)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client.test
users = db.users
video_collection = db.videos

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'invic_email' not in session:
            # User is not logged in, redirect to login page
            return redirect(url_for('login_register'))
        return f(*args, **kwargs)
    return decorated_function

def get_trending_videos_until_yesterday(max_results=8):
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



def search_videos_top_10(query, max_results=10):
    request = youtube_A.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=max_results,
        order='viewCount'  # Sort by view count in descending order
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

def get_video_details(video_id):
    # Get video details using API call
    request = youtube_A.videos().list(
        part='snippet,statistics',
        id=video_id
    )
    response = request.execute()

    video_details = {}

    if response.get('items'):
        item = response['items'][0]
        title = item['snippet']['title']
        like_count = item['statistics'].get('likeCount', 0)
        view_count = item['statistics'].get('viewCount', 0)
        comments_count = item['statistics'].get('commentCount', 0)

        video_details = {
            'title': title,
            'video_link': f"https://www.youtube.com/watch?v={video_id}",
            'embed_link': f"https://www.youtube.com/embed/{video_id}",
            'like_count': like_count,
            'view_count': view_count,
            'comments_count': comments_count,
        }

    return video_details

@app.route('/user/login')
def login_register():
    return render_template('login_register.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    login_user = users.find_one({'email' : data['email']})
    if login_user:
        password = bcrypt.check_password_hash(login_user['password'], data['password'])
        if password:
            session['invic_email'] = str(data['email'])
            return jsonify({'message' : 'success'})
        else:
            return jsonify({'message' : 'Invalid Password'})
    return jsonify({'message' : 'Invalid Email'})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed = bcrypt.generate_password_hash(data['password'])
    curr_user = users.find_one({'email' : data['email']})
    if curr_user:
        return jsonify({'message' : 'User already exists'})
    new_user = users.insert_one({'name' : data['name'], 'email' : data['email'], 'password' : hashed,'contact':data['contact']})
    if(new_user):
        return jsonify({'message' : 'success'})
    else: 
        return jsonify({'message' : 'failure'})

@app.route("/", methods=['GET', 'POST'])
def home():
    
    return render_template("index.html", video_details_dict = video_details_dict, status = layout(), current = "home")

@app.route("/trending/summary/<string:video_id>", methods=['GET', 'POST'])
def trend_summary(video_id):
    
    if 'invic_email' in session:
    
        user = users.find_one({'email': session['invic_email']})

        if user:

            # Update the 'visited' field by appending the new 'video_id' to the list
            users.update_one(
                {'email': session['invic_email']},
                {'$push': {'visited': video_id}}
            )
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(video_details_dict[video_id]['title'])
    filtered_text = [word for word in word_tokens if word.lower() not in stop_words]
    
    new_text = []
    
    for i in filtered_text:
        if i.isalnum():
            new_text.append(i.lower())
    
    recommended_video = search_videos(new_text)
    video_detail_lst = video_details_dict[video_id]
    # if (recommended_video[video_id]):
    #     del recommended_video[video_id]
    lst = getChartData(video_id)
    video = video_collection.find_one({'video_id':video_id})
    if video:
        if video["audio_video_summary"] != "":
            return render_template("summary_trend.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary=video['audio_video_summary'],pos=lst[0],neg=lst[1],neu=lst[2], status = layout())
        elif video["audio_summary"] != "":
            return render_template("summary.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary=video['audio_summary'],pos=lst[0],neg=lst[1],neu=lst[2], status = layout())
        else:
            return render_template("summary.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary="",pos=lst[0],neg=lst[1],neu=lst[2], status = layout())
    return render_template("summary.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary="",pos=lst[0],neg=lst[1],neu=lst[2], status = layout())



def get_video_id_from_url(youtube_url):
    # Parse video ID from YouTube URL
    parsed_url = urlparse(youtube_url)
    query_params = parse_qs(parsed_url.query)
    video_id = query_params.get('v', [None])[0]
    if not video_id:
        # Try to extract video ID from the path (for youtu.be links)
        path_segments = parsed_url.path.split('/')
        video_id = path_segments[-1]
    return video_id

def get_video_details_link(video_id):
    # Get video details using API call
    request = youtube_A.videos().list(
        part='snippet,statistics',
        id=video_id
    )
    response = request.execute()

    video_details = {}

    if response.get('items'):
        item = response['items'][0]
        title = item['snippet']['title']
        like_count = item['statistics'].get('likeCount', 0)
        view_count = item['statistics'].get('viewCount', 0)
        comments_count = item['statistics'].get('commentCount', 0)

        video_details = {
            'title': title,
            'video_id': video_id,
            'video_link': f"https://www.youtube.com/watch?v={video_id}",
            'embed_link': f"https://www.youtube.com/embed/{video_id}",
            'like_count': like_count,
            'view_count': view_count,
            'comments_count': comments_count,
        }

    return video_details

def get_video_details_from_url(youtube_url):
    video_id = get_video_id_from_url(youtube_url)

    if video_id:
        return get_video_details_link(video_id)
    else:
        return None



@app.route("/search/results", methods=['GET', 'POST'])
def serach_results():
    keyword = request.form.get("searchKeyword")
    
    if("https://" in keyword):
        video_details_from_url = get_video_details_from_url(keyword)
        
        return redirect("/summary/" + video_details_from_url['video_id'] + "/" + video_details_from_url['title'])
    else:
        search_video_dict = search_videos_top_10(keyword)
        return render_template("search_result.html", search_video_dict = search_video_dict, status = layout())

@app.route("/caption/summary/audio_video/<string:video_id>", methods=['GET', 'POST'])
def caption_summary(video_id):
    print("video_id", video_id)
    video = video_collection.find_one({'video_id':video_id})
    if video:
        if video["audio_video_summary"]!="":
            return video['audio_video_summary']
        else:
            create_captions("https://www.youtube.com/watch?v="+video_id)
            summary = generate_summary("outputs/temp_audio.txt", "outputs/temp_video.json")
            video_collection.insert_one({'video_id':video_id, 'audio_video_summary':summary, 'audio_summary':""})
            return summary
    create_captions("https://www.youtube.com/watch?v="+video_id)
    summary = generate_summary("outputs/temp_audio.txt", "outputs/temp_video.json")
    video_collection.insert_one({'video_id':video_id, 'audio_video_summary':summary, 'audio_summary':""})
    return summary
    
@app.route("/caption/summary/audio/<string:video_id>", methods=['GET', 'POST'])
def caption_summary_audio(video_id):
    print("video_id", video_id)
    video = video_collection.find_one({'video_id':video_id})
    if video:
        if video["audio_summary"]!="":
            return video['audio_summary']
        else:
            create_captions_audio("https://www.youtube.com/watch?v="+video_id)
            summary = generate_summary_audio("outputs/temp_audio.txt")
            video_collection.insert_one({'video_id':video_id, 'audio_summary':summary,'audio_video_summary':""})
            return summary
    create_captions_audio("https://www.youtube.com/watch?v="+video_id)
    summary = generate_summary_audio("outputs/temp_audio.txt")
    video_collection.insert_one({'video_id':video_id, 'audio_summary':summary,'audio_video_summary':""})
    return summary

@app.route("/summary/<string:video_id>/<string:title>", methods=['GET', 'POST'])
def summary(video_id, title):
    
    if 'invic_email' in session:
        
    
        user = users.find_one({'email': session['invic_email']})

        if user:

            # Update the 'visited' field by appending the new 'video_id' to the list
            users.update_one(
                {'email': session['invic_email']},
                {'$push': {'visited': video_id}}
            )
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(title)
    filtered_text = [word for word in word_tokens if word.lower() not in stop_words]
    
    new_text = []
    
    for i in filtered_text:
        if i.isalnum():
            new_text.append(i.lower())
    
    recommended_video = search_videos(new_text)
    video_detail_lst = get_video_details(video_id)
    lst = getChartData(video_id)
    # if (recommended_video[video_id]):
    #     del recommended_video[video_id]
    video = video_collection.find_one({'video_id':video_id})
    if video:
        if video["audio_video_summary"] != "":
            return render_template("summary_trend.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary=video['audio_video_summary'],pos=lst[0],neg=lst[1],neu=lst[2], status = layout())
        elif video["audio_summary"] != "":
            return render_template("summary.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary=video['audio_summary'],pos=lst[0],neg=lst[1],neu=lst[2], status = layout())
        else:
            return render_template("summary.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary="",pos=lst[0],neg=lst[1],neu=lst[2], status = layout())
    return render_template("summary.html", video_details_lst = video_detail_lst, recommended_video = OrderedDict(reversed(list(recommended_video.items()))), video_id = video_id, summary="",pos=lst[0],neg=lst[1],neu=lst[2], status = layout())

def getChartData(video_id):
    request = youtube_A.commentThreads().list(part="snippet",videoId=video_id)

    comments = []
    likes = []
    response = request.execute()

    for item in response['items']:
        com = item['snippet']['topLevelComment']['snippet']
        comments.append(com['textOriginal'])
        likes.append(com['likeCount']+1)

    while (True):
        try:
            nextPageToken = response['nextPageToken']
        except KeyError:
            break
        nextPageToken = response['nextPageToken']
        nextRequest = youtube_A.commentThreads().list(part="snippet", videoId=video_id, pageToken=nextPageToken)
        response = nextRequest.execute()

        for item in response['items']:
            com = item['snippet']['topLevelComment']['snippet']
            comments.append(com['textOriginal'])
            likes.append(com['likeCount']+1)

    pos = 0
    neg = 0
    neu = 0
    total = len(comments)
    for i in comments:
        score = sia.polarity_scores(i)['compound']
        if score > 0 :
            pos += 1
        elif score < 0:
            neg += 1
        else:
            neu += 1
    return [int(100* pos//total), int(100* neg//total), int(100* neu//total)]

@app.route('/history', methods=['GET'])
@login_required 
def history():
    visited_links = {}
    user = users.find_one({'email': session['invic_email']})
    if user:
        user_visited_route = user['visited']
        user_visited_route_set = list(set(user_visited_route))
        
        for item in user_visited_route_set:
            visited_links[item] = get_video_details_link(item)
            
    return render_template('history.html', name=session['invic_email'], search_video_dict = visited_links, status = layout(), current = "history")

@app.route('/about', methods=['GET'])
def aboutUs():
    return render_template('aboutUs.html', status = layout(), current = "about")

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    return redirect("/")

def layout():
    if 'invic_email' in session:
        return "Logout"
    return "Login"

if __name__ == '__main__':  
   app.run(debug = False)