import json
import openai
import config
from typing import Text
openai.api_key = config.API_KEY

class GPT:

  def __init__(self, question: str) -> Text:
    self.question = question
    return self.gpt()

  def gpt(self):
    prompt = self.question
    response = openai.Completion.create(
      engine="davinci",
      prompt=prompt,
      temperature=0.9,
      max_tokens=100,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stop=["\n"]
    )
    answer = response.choices[0]['text']
    return answer

