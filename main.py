import http.client
import json
import time
from threading import Thread, Lock
from datetime import datetime

def load_config():
    with open('./config.json') as f:
        return json.load(f)['Config'][0]

def send_message(channel_id, message_data):
    conn = http.client.HTTPSConnection("discord.com", 443)
    try:
        conn.request("POST", f"/api/v10/channels/{channel_id}/messages", message_data, header_data)
        resp = conn.getresponse()
        response_data = resp.read().decode()

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 199 < resp.status < 300:
            print(f"{current_time} - Message sent to channel {channel_id}.")
        elif resp.status == 429:
            # Handle rate limiting
            retry_after = json.loads(response_data)['retry_after']
            print(f"{current_time} - Rate limited. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
        else:
            print(f"{current_time} - HTTP {resp.status}: {resp.reason}")
            print("Response:", response_data)
    except Exception as e:
        print(f"{current_time} - Error: {e}")
    finally:
        conn.close()

def channel_worker(channel_id, message, repeat_interval, delay_before_first_message, lock):
    message_data = {
        "content": message,
        "tts": False
    }

    # Notify that we are waiting before starting
    print(f"Waiting {delay_before_first_message} seconds before sending messages to channel {channel_id}...")
    time.sleep(delay_before_first_message)  # Wait before starting to send messages

    while True:
        with lock:
            send_message(channel_id, json.dumps(message_data))
        time.sleep(repeat_interval)

def main():
    config = load_config()
    token = config['token']
    channels = config['channels']
    
    global header_data
    header_data = {
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot",
        "Authorization": token
    }

    # Create a lock object to synchronize message sending across threads
    lock = Lock()

    # Create a thread for each channel to handle its messaging
    threads = []
    for i, channel in enumerate(channels):
        delay_before_first_message = i * 10  # Increase delay for each subsequent channel
        thread = Thread(target=channel_worker, args=(channel['channelid'], channel['message'], channel['repeat_interval'], delay_before_first_message, lock))
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
