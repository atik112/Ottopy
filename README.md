<b>Robotik Asistan ve Arduino Etkileşimi</b><br>
Bu proje, bir robotik asistanın sesli komutları anlayarak Arduino ile etkileşime girmesini sağlar. Kullanıcı komutları vererek robotu kontrol edebilir ve OpenAI yapay zekasıyla etkileşimde bulunabilir.

<b>Özellikler:</b><br>
Sesli komutla robotu kontrol etme (örneğin: "Dans et", "Zıpla").<br>
Arduino ile etkileşim.<br>
OpenAI yapay zekasından yanıt alma.<br>
Duygu analizi yaparak robotun tepkisini ayarlama.<br>
Türkçe sesli yanıtlar.<br>

<b>Bu projeyi çalıştırmak için aşağıdaki Python kütüphanelerini yükleyin:</b><br>
pip install pygame simpleaudio gtts openai speechrecognition schedule

<b>Kullanım</b><br>
API Anahtarı: OpenAI API anahtarınızı alıp çevresel değişken olarak ayarlayın.<br>
Arduino Bağlantısı: Arduino'nun doğru seri port üzerinden bağlı olduğundan emin olun.<br>
<b>Çalıştırma:</b><br> Python dosyasını çalıştırarak robotu kontrol etmeye başlayın.<br>
python robotik_asistan.py

<b>Desteklenen Komutlar</b><br>
"Dans et": Dans etmeye başlar.<br>
"Zıpla": Robot zıplar.<br>
"Selam": Merhaba yanıtı verir.<br>
"Gez": Robot ileri hareket eder ve döner.<br>
"Dur": Robot durur.<br>
"Kapat": Robot kapanma komutunu bekler.
