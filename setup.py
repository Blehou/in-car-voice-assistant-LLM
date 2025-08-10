import os 

file_paths = ["intent_classifier/Dataset/", "intent_classifier/Models/", "intent_classifier/Visualisation/", "prompts/", "user/audio/", "user/logs/"]

for file_path in file_paths:
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        print(f"Directory {file_path} created.")
    else:
        print(f"Directory {file_path} already exists.")