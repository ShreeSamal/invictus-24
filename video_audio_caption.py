import io
import os
import json
from PIL import Image
from model import get_caption_model, generate_caption
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import cv2
import assemblyai as aai
from pytube import YouTube
import re


aai.settings.api_key = "73e882792b414fa8b6d83f703694b232"
transcriber = aai.Transcriber()
# Download the stopwords data if not already downloaded

import nltk
nltk.download('stopwords')
nltk.download('punkt')

def get_model():
    return get_caption_model()

caption_model = get_model()

def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [word for word in word_tokens if word.lower() not in stop_words]
    return ' '.join(filtered_text)

def predict(img_path, frame_count, interval_seconds, json_data):
    print(f"Predicting caption for {img_path}...")
    captions = []

    img = Image.open(img_path).convert('RGB')
    img.save('tmp.jpg')

    pred_caption = generate_caption('tmp.jpg', caption_model)
    captions.append(remove_stopwords(pred_caption))

    for _ in range(2):
        pred_caption = generate_caption('tmp.jpg', caption_model, add_noise=True)
        if pred_caption not in captions:
            captions.append(remove_stopwords(pred_caption))

    # Save words and frame count to JSON
    for caption in captions:
        words = caption.split()
        for word in words:
            if word not in json_data:
                json_data[word] = (frame_count // interval_seconds) * interval_seconds
    os.remove(img_path)
    os.remove('tmp.jpg')

def convert_video_to_images(video_path, output_folder, interval_seconds=5):
    # Open the video file
    print(f"Converting video {video_path} to images...")
    cap = cv2.VideoCapture(f'inputs/{video_path}')
    
    # Get the frames per second (fps) of the video
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Calculate the frame interval based on the specified time interval
    frame_interval = int(fps * interval_seconds)

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Start reading frames from the video
    frame_count = 0
    json_data = {}  # Dictionary to store words and frame count

    while True:
        ret, frame = cap.read()

        # Break the loop if we reach the end of the video
        if not ret:
            break

        # Save frames at the specified interval
        if frame_count % frame_interval == 0:
            image_filename = os.path.join(output_folder, f"{video_path}_{(frame_count // frame_interval) * interval_seconds}.png")
            cv2.imwrite(image_filename, frame)

            # Apply the logic to predict captions for each saved image
            predict(image_filename, frame_count, interval_seconds, json_data)

        frame_count += 1

    # Save the JSON file
    json_filename = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(video_path))[0]}_video.json")
    formatted_data = [{"keyword": key, "timestamp": json_data[key]} for key in json_data]
    with open(json_filename, 'w') as json_file:
        json.dump(formatted_data, json_file, indent=2)

    # Release the video capture object
    cap.release()

    print(f"Conversion completed. {frame_count+1 // frame_interval} frames saved to {output_folder}")
    print(f"JSON file saved as {json_filename}")

    print("Transcribing audio...")
    transcript = transcriber.transcribe(f"inputs/temp.mp4")
    # transcript = remove_stopwords(transcript.text)
    # transcript = transcript.lower()
    # transcript = transcript.replace("\n", " ")
    # transcript = transcript.replace("?", " ")
    # transcript = transcript.replace(".", " ")
    # transcript = transcript.replace(",", " ")
    # transcript = transcript.replace("!", " ")
    # transcript = transcript.replace(":", " ")
    # transcript = transcript.replace(";", " ")
    # transcript = transcript.replace("'", " ")
    # transcript = transcript.split()
    # transcript_file_name = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.json")
    # with open(transcript_file_name, 'w') as json_file:
    #     json.dump([transcript], json_file, indent=2)
    #save the transcript as a txt
    transcript_file_name = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.txt")
    with open(transcript_file_name, 'w') as txt_file:
        txt_file.write(transcript.text)
    print(f"subtitle file saved as {transcript_file_name}")




# Example usage
def create_captions(url): 
    print("Creating captions...")
    #url = "https://youtube.com/shorts/h9fGBZkPrjk?feature=shared"
    youtube = YouTube(url)
    video_stream = youtube.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
    if video_stream:
        print(f"Downloading: {youtube.title}")
        filename = "temp.mp4"
        video_stream.download(output_path="inputs", filename=filename)
        output_folder = 'outputs'
        convert_video_to_images(filename, output_folder, interval_seconds=1000)
        os.remove(f"inputs/{filename}")
    else:
        print("No video stream found")

def create_captions_audio(url): 
    print("Creating captions or audio only...")
    #url = "https://youtube.com/shorts/h9fGBZkPrjk?feature=shared"
    youtube = YouTube(url)
    video_stream = youtube.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
    if video_stream:
        print(f"Downloading: {youtube.title}")
        filename = "temp.mp4"
        video_stream.download(output_path="inputs", filename=filename)
        output_folder = 'outputs'
        print("Transcribing audio...")
        transcript = transcriber.transcribe(f"inputs/temp.mp4")
        transcript_file_name = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(filename))[0]}_audio.txt")
        with open(transcript_file_name, 'w') as txt_file:
            txt_file.write(transcript.text)
        print(f"subtitle file saved as {transcript_file_name}")
        os.remove(f"inputs/{filename}")
    else:
        print("No video stream found")

