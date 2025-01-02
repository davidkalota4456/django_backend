import os
import json
import numpy as np
from django.http import JsonResponse
from tensorflow.keras.models import load_model
import nltk
import pickle
import random
from nltk.stem.lancaster import LancasterStemmer
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Download necessary NLTK data
nltk.download('punkt')

# Initialize the stemmer
stemmer = LancasterStemmer()

# Ensure correct paths to the model and data
model_path = os.path.join(settings.BASE_DIR, 'chatbot_model.h5')
data_path = os.path.join(settings.BASE_DIR, 'data.pickle')
intents_path = os.path.join(settings.BASE_DIR, 'bot_data.json')

# Load the trained model
model = load_model(model_path)

# Load words, labels, training, and output from the pickle file
with open(data_path, 'rb') as f:
    words, labels, training, output = pickle.load(f)

# Load intents data from JSON
with open(intents_path) as file:
    chatbot_data = json.load(file)

# Function to create Bag of Words vector
def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]
    
    # Tokenize and stem the input string
    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(w.lower()) for w in s_words]

    # Create the Bag of Words vector
    for sent in s_words:
        for idx, word in enumerate(words):
            if word == sent:
                bag[idx] = 1

    return np.array(bag)

@csrf_exempt
def bot_communication(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            print(user_message)

            if user_message.lower() == "q":
                return JsonResponse({"response": "Goodbye!"})

            # Make prediction with the model
            bow = bag_of_words(user_message, words)
            results = model.predict(np.array([bow]))  # Wrap input for model
            predicted_index = np.argmax(results)
            predicted_label = labels[predicted_index]

            # Find response based on predicted label
            responses = None
            for tg in chatbot_data['intents']:
                if tg['tag'] == predicted_label:
                    responses = tg['responses']
                    break

            if responses:
                choise = random.choice(responses)
                print(choise)
                return JsonResponse({"response": random.choice(responses)})
            else:
                return JsonResponse({"response": "I'm not sure how to respond to that."})

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
