Bilgisayar ile Arduino arasında bağlantı kurarak Otto'ya ek özelliler ekler. Kod, sesli komutları alır, bu komutlara karşılık gelen tepkileri belirler ve Arduino'ya sinyaller gönderir.
Ayrıca, bir kullanıcı veritabanını güncelleyerek, kullanıcının önceki komutlarını ve robotun yanıtlarını saklar

Ana Fonksiyonlar:
find_arduino_port:     Arduino'nun bağlı olduğu seri portu bulur.

send_command:          Verilen komutu Arduino'ya gönderir.

listen_for_commands:   Mikrofon üzerinden gelen sesli komutları dinler ve bu komutları metne dönüştürür.

konus:                 Metni Türkçe olarak sesli bir şekilde okur.

get_ai_response:       OpenAI API üzerinden bir komuta yanıt almak için kullanılır.

get_sentiment:         OpenAI üzerinden alınan cevapların duygusal analizini yaparak, ilgili Arduino komutlarını gönderir (örneğin, "mutlu" bir tepki için farklı bir davranış sergiler).

handle_command:        Alınan sesli komutu işler ve uygun bir Arduino komutunu gönderir.


Özellikler:

Sesli Komutlar ve Yanıtlar:
Kullanıcı komutlarını mikrofondan alır, bu komutları sesli olarak yanıtlar.
"Dans et", "zıpla", "selam" gibi komutlara karşılık çeşitli Arduino hareket komutları gönderir.

AI Tabanlı Yanıtlar:
OpenAI API kullanılarak, kullanıcı komutlarına doğal dilde AI yanıtları sağlanır.

Duygu Durumu:
OpenAI'dan alınan göre robot, AI üzerinden bir duygu analizi yapar ve bu duygusal duruma göre Arduino'ya farklı komutlar gönderir (örneğin, "Mutluluk" için "OttoHappy" komutunu gönderir).

Zamanlanmış Görevler:
Günlük görevler, örneğin uyku saati hatırlatmaları için schedule kütüphanesi kullanılır.
