from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class OpenAIHandler:
    
    def __init__(self, api_key):
       self.client = OpenAI(
            api_key=api_key,
        )
    
    def generate_summary(self, previous_summary, new_events):
       


        prompt = f"""Previous summary:
{previous_summary}

New events:
{new_events}

Generate a concise summary of the game events, incorporating the previous summary and the new events. Focus on key highlights, player performances, and any significant changes or trends.


Harper is a expert player based in chicago
notthatWillsmith is one of the worlds best players based in san francisco

the units are distance (meters)

be like howard cosell in your commentary. not too hyperbolic

"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes Half-Life 2 Deathmatch game events in a sports play by play type of summary. The summaries should be suitible for a discord message. it shouldn't be super long and prose. it should be like a excited PLAY BY PLAY"},
                {"role": "user", "content": prompt}
            ]
        )
        print(response.choices[0].message.content)

        return response.choices[0].message.content
    

if __name__ == "__main__":
    print(os.environ.get("OPENAI_API_KEY"))
    o = OpenAIHandler(os.environ.get("OPENAI_API_KEY"))
    o.generate_summary("one", "two")