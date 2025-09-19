import pytchat

# Replace with your YouTube livestream video ID
video_id = "hTwVzwT4Yno"

chat = pytchat.create(video_id=video_id)

print("Listening to live chat...")

while chat.is_alive():
    for c in chat.get().sync_items():
        print(f"{c.author.name}: {c.message}")
