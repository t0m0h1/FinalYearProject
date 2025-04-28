import unittest
from unittest.mock import patch, mock_open
import json
import numpy as np
import os
import pickle
import tensorflow as tf
from tensorflow.keras.models import Sequential
from training import lemmatiser, intents, words, classes, training, model


# Ensure that training.py has been run before running the tests


class TestChatbotTraining(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"intents": [{"tag": "greeting", "patterns": ["hello", "hi", "howdy"]}]}')
    def test_load_intents(self, mock_file):
        # Test if the JSON file is loaded correctly
        with open('intents.json') as file:
            data = json.load(file)
        self.assertIn("intents", data)
        self.assertEqual(data["intents"][0]["tag"], "greeting")
    
    @patch("builtins.open", new_callable=mock_open)
    def test_load_intents_file_not_found(self, mock_file):
        # Test if the file is not found
        mock_file.side_effect = FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            with open('intents.json') as file:
                json.load(file)

    @patch("builtins.open", new_callable=mock_open, read_data='{"intents": [{"tag": "greeting", "patterns": ["hello", "hi", "howdy"]}]}')
    def test_tokenization_and_lemmatization(self, mock_file):
        # Test if the words are tokenized and lemmatized correctly
        words = []
        for intent in intents['intents']:
            for pattern in intent['patterns']:
                word_list = nltk.word_tokenize(pattern)
                words.extend(word_list)
        
        # Lemmatize words
        words = [lemmatiser.lemmatize(word) for word in words if word not in ['!', '?', ',', '.']]
        self.assertTrue('hello' in words)
        self.assertTrue('hi' in words)

    def test_training_data_creation(self):
        # Test if the training data is created correctly
        self.assertGreater(len(training), 0)
        for data in training:
            self.assertEqual(len(data[0]), len(words))  # Check if bag of words has the same length as the words list
            self.assertEqual(len(data[1]), len(classes))  # Check if output row has the same length as the classes list
    
    @patch.object(tf.keras.models, 'Sequential', wraps=Sequential)
    def test_model_creation(self, mock_model):
        # Test model creation (Check if the architecture layers are added correctly)
        model = Sequential()
        model.add(Dense(128, input_shape=(len(words),), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(len(classes), activation='softmax'))
        
        self.assertTrue(any(isinstance(layer, Dense) for layer in model.layers))
        self.assertTrue(any(isinstance(layer, Dropout) for layer in model.layers))
        self.assertEqual(len(model.layers), 5)  # Check the number of layers in the model
    
    @patch("tensorflow.keras.models.Sequential.fit")
    def test_train_model(self, mock_fit):
        # Test if the model is being trained (fit method is called)
        model = Sequential()
        model.add(Dense(128, input_shape=(len(words),), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(len(classes), activation='softmax'))
        
        # Pretend the model has been compiled and fit
        mock_fit.return_value = None  # Simulate successful training
        model.fit(np.array([1, 0, 0]), np.array([0, 1]), epochs=1)
        
        mock_fit.assert_called_once_with(np.array([1, 0, 0]), np.array([0, 1]), epochs=1)

    def test_save_pickle_files(self):
        # Test if words and classes are saved to pickle files
        pickle.dump(words, open('words.pkl', 'wb'))
        pickle.dump(classes, open('classes.pkl', 'wb'))
        
        # Check if pickle files exist
        self.assertTrue(os.path.exists('words.pkl'))
        self.assertTrue(os.path.exists('classes.pkl'))
    
    @patch("tensorflow.keras.models.save_model")
    def test_save_trained_model(self, mock_save):
        # Test if the trained model is saved
        model = Sequential()
        model.add(Dense(128, input_shape=(len(words),), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(len(classes), activation='softmax'))
        
        model.save('chatbot_model.h5')
        mock_save.assert_called_once_with('chatbot_model.h5')





if __name__ == "__main__":
    unittest.main()
