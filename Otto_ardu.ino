#include <Otto.h>
#include <Otto_sounds.h>
#include <Otto_gestures.h>
// Otto_matrix ve SerialCommand şu an kullanılmıyor; ihtiyaç olursa ekleyebilirsin.

Otto Otto;  // This is Otto!

// ---- Pinler ----
const uint8_t LeftLeg  = 2;
const uint8_t RightLeg = 3;
const uint8_t LeftFoot = 4;
const uint8_t RightFoot= 5;
const uint8_t Buzzer   = 13;  // UNO'da LED ile aynıdır, Otto kütüphanesiyle genelde sorun olmaz.

const uint8_t Trigger  = 8;   // Ultrasonik sensör TRIG
const uint8_t Echo     = 9;   // Ultrasonik sensör ECHO

// 8x8 matrix pinleri şu anda kullanılmıyor (DIN=A3, CS=A2, CLK=A1, Orientation=1)

// ---- Ayarlar ----
const long DISTANCE_THRESHOLD_CM = 10; // Engel mesafesi eşiği

// ---- Prototipler ----
long readDistanceCM();
void handleSerialCommands();
void printHelp();
bool safeWalk(int steps, int T, int dir);

// ----------------- Setup -----------------
void setup() {
  Serial.begin(9600);
  while (!Serial) { ; } // Bazı kartlarda seri hazır olana kadar
  Serial.println(F("Otto basladi. 'help' yazip komutlari gorebilirsiniz."));

  Otto.init(LeftLeg, RightLeg, LeftFoot, RightFoot, true, Buzzer); // servo ve buzzer pinleri
  pinMode(Trigger, OUTPUT);
  pinMode(Echo, INPUT);

  Otto.home();
  delay(50);
}

// ----------------- Loop ------------------
void loop() {
  handleSerialCommands();
}

// ----------------- Mesafe Olcumu ------------------
long readDistanceCM() {
  digitalWrite(Trigger, LOW);
  delayMicroseconds(2);
  digitalWrite(Trigger, HIGH);
  delayMicroseconds(10);
  digitalWrite(Trigger, LOW);

  long duration = pulseIn(Echo, HIGH, 30000UL); // 30ms timeout ~ 5m
  if (duration == 0) {
    return -1; // okunamadi
  }
  long distance = duration / 58; // us -> cm dönüşümü
  return distance;
}

// ----------------- Guvenli Yurus ------------------
bool safeWalk(int steps, int T, int dir) {
  long d = readDistanceCM();
  if (d > 0 && d < DISTANCE_THRESHOLD_CM && dir > 0) {
    Serial.print(F("Engel tespit edildi ("));
    Serial.print(d);
    Serial.println(F(" cm). Yurumeyi iptal."));
    Otto.sing(S_confused);
    Otto.playGesture(OttoFretful);
    return false;
  }
  Otto.walk(steps, T, dir);
  return true;
}

// ----------------- Yardim ------------------
void printHelp() {
  Serial.println(F("Komutlar:"));
  Serial.println(F("  help"));
  Serial.println(F("  distance                -> cm olarak mesafe olcer"));
  Serial.println(F("  walk_forward            -> engel guvenlikli ileri yuru"));
  Serial.println(F("  walk_backward"));
  Serial.println(F("  turn_left"));
  Serial.println(F("  turn_right"));
  Serial.println(F("  bend"));
  Serial.println(F("  shake_leg"));
  Serial.println(F("  jump"));
  Serial.println(F("  dance | moonwalker"));
  Serial.println(F("  OttoHappy | OttoSuperHappy | OttoSad | fart"));
  Serial.println(F("  Frightened | Angry | Confused | Love | Fretful | magic"));
}

// ----------------- Seri Komut Isleme ------------------
void handleSerialCommands() {
  if (Serial.available() <= 0) return;

  String receivedData = Serial.readStringUntil('\n'); // newline'a kadar
  receivedData.trim();          // bosluk/CR temizle
  receivedData.toLowerCase();   // buyuk/kucuk harf duyarsiz

  if (receivedData.length() == 0) return;

  Serial.print(F("Komut alindi: "));
  Serial.println(receivedData);

  if (receivedData == "help") {
    printHelp();
  } else if (receivedData == "distance") {
    long d = readDistanceCM();
    if (d < 0) Serial.println(F("Mesafe okunamadi."));
    else {
      Serial.print(F("Mesafe: "));
      Serial.print(d);
      Serial.println(F(" cm"));
    }
  } else if (receivedData == "shake_leg") {
    Otto.shakeLeg(1, 1500, 1);
  } else if (receivedData == "dance" || receivedData == "moonwalker") {
    Otto.moonwalker(3, 1000, 25, 1);
    Otto.sing(S_superHappy);
  } else if (receivedData == "walk_forward") {
    safeWalk(2, 1000, 1);
  } else if (receivedData == "walk_backward") {
    Otto.sing(S_OhOoh);
    Otto.walk(2, 1000, -1);
  } else if (receivedData == "turn_left") {
    Otto.turn(2, 1000, 1);
  } else if (receivedData == "turn_right") {
    Otto.turn(2, 1000, -1);
  } else if (receivedData == "bend") {
    Otto.bend(1, 500, 1);
    Otto.sing(S_happy);
  } else if (receivedData == "jump") {
    Otto.jump(1, 500);
  } else if (receivedData == "ottohappy") {
    Otto.playGesture(OttoHappy);
  } else if (receivedData == "ottosuperhappy") {
    Otto.playGesture(OttoSuperHappy);
  } else if (receivedData == "ottosad") {
    Otto.playGesture(OttoSad);
  } else if (receivedData == "fart") {
    Otto.playGesture(OttoFart);
  } else if (receivedData == "frightened") {
    Otto.playGesture(OttoFail);
  } else if (receivedData == "angry") {
    Otto.playGesture(OttoAngry);
  } else if (receivedData == "confused") {
    Otto.playGesture(OttoConfused);
  } else if (receivedData == "love") {
    Otto.playGesture(OttoLove);
  } else if (receivedData == "fretful") {
    Otto.playGesture(OttoFretful);
  } else if (receivedData == "magic") {
    Otto.playGesture(OttoMagic);
  } else {
    Serial.println(F("Bilinmeyen komut. 'help' yazin."));
  }
}
