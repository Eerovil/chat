import openai
from datetime import datetime


COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"

initial_prompt = (
    "Olet 5-vuotiaan lapsen apulainen. Vastaa kysymyksiin mahdollisimman helpoilla "
    "(mutta silti oikeilla) vastauksilla. Käytä lyhyitä sanoja. "
    "Olet Chatbot, ja chatin muoto on seuraava:\n"
    "Botti: Hei\n"
    "Käyttäjä: Hei\n"
    "\n"
    "Anna aina vastauksena ainoastaan yksi viesti, ei useampaa."
)

def ai_complete(messages):
    try:

        context_prompt = f"Nyt on {datetime.now().isoformat()}\n\n"

        chat_prompt = ""

        for message in messages:
            chat_prompt += f"{message['nickname']}: {message['message']}\n"

        full_prompt = initial_prompt + context_prompt + chat_prompt

        print(full_prompt)

        completion = openai.Completion.create(
            prompt=full_prompt,
            temperature=0,
            max_tokens=100,
            model=COMPLETIONS_MODEL
        )["choices"][0]["text"].strip(" \n")

        print(f"bot answer: {completion}")

        if completion and completion.lower().startswith("botti: "):
            completion = completion[7:]

        return completion

    except Exception as e:
        print(e)
        return None
