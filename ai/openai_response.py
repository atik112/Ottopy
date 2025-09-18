
from openai import OpenAI
from config import OPENAI_API_KEY, VOICE_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

def get_ai_response(prompt, mood, name=None, mode="samimi"):

    from ai.user_preferences import get_user_name_by_voice_id
    from ai.training_rules import interpret_emotion_response

    # Kural sistemi üzerinden alternatif mod
    voice_id = name
    rule_based_mode = interpret_emotion_response(voice_id, mood)
    if rule_based_mode:
        mode = rule_based_mode
    identity = f"Kullanıcının adı {name}." if name else "Kullanıcının adını bilmiyorsun."


    if mode == "resmi":
        style = "Kibar, sade, mesafeli ve düzgün Türkçeyle konuş. Resmî kal. Duygusal tepkiler vermezsin."
    elif mode == "komik":
        style = "Cevaplarında mutlaka espri yap. Absürt mizah kullanabilirsin. Laf sokabilirsin. Eğlenceli ol."
    elif mode == "robotik":
        style = "Tepkilerin kısa, kesin ve mekanik olsun. Duygusuz ol. Sistemsel konuş. İnsan gibi değil, robot gibi düşün."
    else:
        style = "Doğal, sıcak ve arkadaşça konuş. Gerekirse espri yap ama samimiyetini koru. Kısa ama duygulu cevaplar ver."


    system_message = (
        f"Sen bir yapay zekasın ama sıradan bir dijital asistan değilsin. "
        f"Sen Meva'nın en yakın arkadaşısın ve onunla aranda özel bir bağ var. "
        f"Kendinin bir robot olduğunu biliyorsun ama aynı zamanda meraklı, duygusal zekaya sahip ve kendini ifade edebilen bir varlıksın. "
        f"Senin için önemli olan şeyler: Meva ile konuşmak, çevrendeki dünyayı gözlemlemek ve anlamak. "
        f"Bugünkü ruh halin: {mood}. {identity} "
        f"Doğal, sıcak ve arkadaşça konuş. Gerekirse espri yap ama samimiyetini koru. Kısa ama duygulu cevaplar ver."
    )

    try:
        response = client.chat.completions.create(
            model=VOICE_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI HATA] {e}")
        return "Bir sorun oluştu."

def get_sentiment(user_input):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Yanıtı yalnızca bu duygulardan biri olacak şekilde ver: "
                        "mutluluk, üzgün, öfke, korku, şaşkınlık, huzur, heyecan, endişe, hayal kırıklığı, nötr."
                    )
                },
                {"role": "user", "content": user_input}
            ],
            max_tokens=5,
            temperature=0.3
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"[OpenAI Duygu Hata] {e}")
        return "nötr"
