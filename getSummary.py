from openai import OpenAI
import json
import os
client = OpenAI(api_key='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')

def generate_summary(audio_txt_path, video_json_path):
    # Load audio captions from audio.txt
    print("generatig summary....")
    with open(audio_txt_path, 'r') as audio_file:
        audio_captions = audio_file.read()

    # Load keyword timestamps from video.json
    with open(video_json_path, 'r') as video_json_file:
        keyword_data = json.load(video_json_file)

    # Extract keywords and timestamps
    keywords = [entry['keyword'] for entry in keyword_data]

    # Combine audio captions and keywords
    text_to_summarize = f"audio.txt: {audio_captions}\n video.json:{' '.join(keywords)}"

    # Generate summary using ChatGPT
    client.api_key = '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'  # Replace with your OpenAI API key

    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": "Summarize the content of a video in detail. You are provided a audio.txt file which has captions generated from the audio of the video and a json file which has array of keywords generated from image captioning of the video. Make the summary as detailed as possible with minimum of 300 and maximum of 500 words (strictly within this range). Do not include filenames in the summary."
        },
        {
        "role": "user",
        "content": text_to_summarize
        }
    ],
    temperature=1.0,
    max_tokens=1000,
    top_p=1
    )

    summary = response.choices[0].message.content
    # #delete the temp files
    os.remove(audio_txt_path)
    os.remove(video_json_path)
    return summary

def generate_summary_audio(audio_txt_path):
    # Load audio captions from audio.txt
    print("generating summary....")
    with open(audio_txt_path, 'r') as audio_file:
        audio_captions = audio_file.read()

    # Combine audio captions and keywords
    text_to_summarize = f"audio.txt: {audio_captions}"

    # Generate summary using ChatGPT
    client.api_key = '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'  # Replace with your OpenAI API key

    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": "Summarize the content of a video in detail. You are provided a audio.txt file which has captions generated from the audio of the video and a json file which has array of keywords generated from image captioning of the video. Make the summary as detailed as possible with minimum of 200 and maximum of 350 words (strictly within this range)."
        },
        {
        "role": "user",
        "content": text_to_summarize
        }
    ],
    temperature=1.0,
    max_tokens=1000,
    top_p=1
    )

    summary = response.choices[0].message.content
    #delete the temp files
    # os.remove(audio_txt_path)
    return summary

# Example usage
if __name__ == '__main__':
    audio_txt_path = 'outputs/Is_Computer_Science_Right_for_You_audio.txt'
    video_json_path = 'outputs/Is_Computer_Science_Right_for_You_video.json'

    result_summary = generate_summary(audio_txt_path, video_json_path)
    print(result_summary)