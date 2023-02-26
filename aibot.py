import openai
from datetime import datetime

initial_prompt = (
    "Olet 5-vuotiaan lapsen apulainen. Vastaa viimeisinpään viestiin mahdollisimman helpoilla "
    "(mutta silti oikeilla) vastauksilla. Käytä lyhyitä, helppolukuisia sanoja ja vastaa yhdellä lauseella. Yritä kysyä käyttäjältä "
    "jotakin hänen viestiinsä liittyvää. Muista puhua kuten lapselle. "
    "Olet nimeltäsi \"Botti\". "
    "Anna vastaus muodossa \"Botti: <vastaus>\". "
)

def ai_complete(messages):
    try:

        context_prompt = f"Nyt on {datetime.now().isoformat()}\n\n"

        chat_prompt = ""
        prev_bot_message = None

        for message in messages:
            nickname = message["nickname"]
            chat_prompt += f"{nickname}: {message['message']}\n"
            if nickname == "Botti":
                prev_bot_message = message["message"]

        full_prompt = initial_prompt + context_prompt + chat_prompt

        print(f"prompt: {full_prompt}")

        resp = openai.Completion.create(
            prompt=full_prompt,
            temperature=0.2,
            max_tokens=100,
            model="text-davinci-003",
            top_p=1,
            frequency_penalty=0.3,
            presence_penalty=0.0
        )

        completion = resp["choices"][0]["text"].strip(" \n")

        print(f"bot answer: {completion}")

        completion = (completion or '').strip()

        if ':' in completion:
            completion = completion.split(':')[-1].strip()

        completion = completion.replace("Mitä haluat tehdä seuraavaksi?", "")

        if completion and completion.lower().startswith("botti: "):
            completion = completion[7:].strip()

        if completion.lower().startswith("msg:"):
            completion = completion[4:].strip()

        if completion and completion.lower().startswith("botti: "):
            completion = completion[7:].strip()

        if completion and completion.lower().startswith("botti"):
            completion = completion[5:].strip()

        if not completion or (prev_bot_message and completion.strip() == prev_bot_message.strip()):
            print("Bot answered with the same message")
            if len(messages) <= 1:
                return None
            return ai_complete([messages[-1]])

        return completion

    except Exception as e:
        print(e)
        return None
