import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
import nltk
nltk.download('punkt_tab')
import os
import json
import pickle
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()






file_path = "./bot_data.json"

with open(file_path) as file:
    data = json.load(file)

try:
  with open("data.pickle", "rb") as f:
    words, labels, training, output = pickle.load(f)


except:  


    words = []
    labels = []
    docs_x = []
    docs_y = []
    
    for intr in data['intents']:
        for pat in intr['patterns']:
            wrds = nltk.word_tokenize(pat)  # Tokenize the pattern
            
            # Extend words and append docs_x and docs_y
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intr['tag'])
    
        if intr['tag'] not in labels:
            labels.append(intr['tag'])
    
    # Filter out punctuation marks and stem the words
    words = [stemmer.stem(w.lower()) for w in words if w.isalpha()]  # Change this line
    
    # Remove duplicates and sort the words and labels
    words = sorted(list(set(words)))
    labels = sorted(labels)

#_____________________ TODO REMEMBER THIS PART ITS STEP 2 __________________

    training = []
    output = []
    
    # Create an empty output vector for each label
    out_empty = [0 for _ in range(len(labels))]  # Use len(labels) instead of labels directly
    
    # Loop through each document in docs_x
    for x, doc in enumerate(docs_x):
        bag = []  # Initialize the Bag of Words vector
    
        # Stem the words in the current document
        wrds = [stemmer.stem(w) for w in doc]  # Ensure doc is split into words
    
        # Create the Bag of Words vector
        for w in words:
            if w in wrds:
                bag.append(1)  # Append 1 if the word is found
            else:
                bag.append(0)  # Append 0 if the word is not found
    
        # Create the one-hot encoded output vector
        output_row = out_empty[:]  # Create a copy of the empty output row
        output_row[labels.index(docs_y[x])] = 1  # Set the appropriate index to 1
    
        training.append(bag)  # Append the Bag of Words vector
        output.append(output_row)  # Append the one-hot encoded output
    
    # Convert the lists to NumPy arrays
    training = np.array(training)
    output = np.array(output)


    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

print('<<<<<<<<<im writing my important data in a pikle file>>>>>>>>>')



# TODO___________________ THIS IS WHERE YOUR TRAINING YOU MODLE_____________________
model_file_path = "chatbot_model.h5"



try:
    model = load_model(model_file_path)
    print("Model loaded successfully.")
except:    
    
    model = Sequential()
    model.add(Dense(128, input_shape=(len(training[0]),), activation='relu'))
    
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    
    model.add(Dropout(0.5))
    model.add(Dense(len(labels), activation='softmax'))
    
    # Compile the model
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    # Train the model
    
    model.fit(np.array(training), np.array(output), epochs=200, batch_size=8)
    
    # Save the model
    model.save(model_file_path)
    print("Model trained and saved successfully.")
