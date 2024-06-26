"""
At the command line, only need to run once to install the package via pip:

$ pip install google-generativeai
"""

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API = os.getenv('GEMINI_TOKEN')

genai.configure(api_key=GEMINI_API)

# Set up the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

convo = model.start_chat(history=[
  {
    "role": "user",
    "parts": ["Hello!"]
  },
  {
    "role": "model",
    "parts": ["Greetings! How may I assist you today?"]
  },
  {
    "role": "user",
    "parts": ["Hello!"]
  },
  {
    "role": "model",
    "parts": ["Greetings! How are you doing today? Is there anything I can help you with?"]
  },
])

convo.send_message("How do I rhyme words smoothly on a rap battle to win?")
print(convo.last.text)