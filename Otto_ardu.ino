#include <Otto.h>
#include <SerialCommand.h>
Otto Otto;  //This is Otto!

#define LeftLeg 2 
#define RightLeg 3
#define LeftFoot 4 
#define RightFoot 5 
#define Buzzer  13 
#define DIN A3 // Data In pin
#define CS A2  // Chip Select pin
#define Trigger 8 // ultrasonic sensor trigger pin
#define Echo 9 // ultrasonic sensor echo pin
#define CLK A1 // Clock pin
#define Orientation 1 // 8x8 LED Matrix orientation  Top  = 1, Bottom = 2, Left = 3, Right = 4 

const long DISTANCE_THRESHOLD = 10; // Distance threshold for obstacle detection (in cm)

long ultrasound() {
   long duration, distance;
   digitalWrite(Trigger,LOW);
   delayMicroseconds(2);
   digitalWrite(Trigger, HIGH);
   delayMicroseconds(10);
   digitalWrite(Trigger, LOW);
   duration = pulseIn(Echo, HIGH);
   distance = duration/58;
   return distance;
}

///////////////////////////////////////////////////////////////////
//-- Setup ------------------------------------------------------//
///////////////////////////////////////////////////////////////////
void setup(){
  Serial.begin(9600);
  Serial.println("başladı");
  Otto.init(LeftLeg, RightLeg, LeftFoot, RightFoot, true, Buzzer); //Set the servo pins and Buzzer pin
  Otto.sing(S_connection); //Otto wake up!
  pinMode(Trigger, OUTPUT); 
  pinMode(Echo, INPUT); 
  Otto.home();
    delay(50);
  Otto.playGesture(OttoHappy);
}

void avoidObstacle() {
  long distance = ultrasound();
  if (distance <= DISTANCE_THRESHOLD && distance > 0) { // Check if there's an obstacle within the threshold
    Otto.sing(S_surprise);
    Otto.playGesture(OttoConfused);
    Otto.walk(2, 1000, -1); // Move backward
    Otto.turn(3, 1000, 1);  // Turn left
    Serial.print("Obstacle detected, distance: ");
    Serial.println(distance);
  }
}

void wander() {
  Otto.walk(5, 1000, 1);  // Walk for distance 5 units, 1000 ms duration, speed 1
  
  // Randomly decide to turn Left or Right
  if (rand() % 2 == 0) {
    Otto.turn(3, 1000, 1);
  } else {
    Otto.turn(3, 1000, -1);
  }
}

void get_back() {
   Otto.sing(S_surprise);
   Otto.walk(2, 1000, -1); // Move backward
   Otto.turn(3, 1000, 1);  // Turn left
}

void handleSerialCommands() {
  if (Serial.available() > 0) {
    String receivedData = Serial.readStringUntil('\n'); // Read till newline
    receivedData.trim(); // Clean up the input

    if (receivedData.length() == 0) return; // Ignore empty strings

    Serial.print("Received command: ");
    Serial.println(receivedData); // Output the command to the serial monitor

    // Handle different commands
    if (receivedData == "shake_leg") {
      Otto.shakeLeg(1, 1500, 1);
      Otto.home();
    } else if (receivedData == "dance") {
      Otto.moonwalker(3, 1000, 25, 1);
      Otto.sing(S_superHappy);
      Otto.home();
    } else if (receivedData == "walk_forward") {
      Otto.walk(2, 1000, 1);
      Otto.home();
    } else if (receivedData == "walk_backward") {
      Otto.sing(S_OhOoh);
      Otto.walk(2, 1000, -1); // Move backward
      Otto.home();
    } else if (receivedData == "turn_left") {
      Otto.turn(2, 1000, 1); // Turn left
      Otto.home();
    } else if (receivedData == "turn_right") {
      Otto.turn(2, 1000, -1); // Turn right
      Otto.home();
    } else if (receivedData == "bend") {
      Otto.bend(1, 500, 1); // Bend gesture
      Otto.sing(S_happy);
      Otto.home();
    } else if (receivedData == "moonwalker") {
      Otto.moonwalker(3, 1000, 25, 1); // Perform moonwalker dance
    } else if (receivedData == "jump") {
      Otto.jump(1, 500); // Perform a jump (simulated)
      Otto.home();
    } else if (receivedData == "OttoHappy") {
      Otto.playGesture(OttoHappy);
      Otto.home();
    } else if (receivedData == "OttoSuperHappy") {
      Otto.playGesture(OttoSuperHappy);
      Otto.home();
    } else if (receivedData == "OttoSad") {
      Otto.playGesture(OttoSad);
      Otto.home();
    } else if (receivedData == "fart") {
      Otto.playGesture(OttoFart);
      Otto.home();
    } else if (receivedData == "Frightened") {
      Otto.playGesture(OttoFail);
      Otto.home();
    } else if (receivedData == "Angry") {
      Otto.playGesture(OttoAngry);
      Otto.home();
    } else if (receivedData == "Confused") {
      Otto.playGesture(OttoConfused);
      Otto.home();
    } else if (receivedData == "Love") {
      Otto.playGesture(OttoLove);
      Otto.home();
    } else if (receivedData == "Fretful") {
      Otto.playGesture(OttoFretful);
      Otto.home();
    } else if (receivedData == "magic") {
      Otto.playGesture(OttoMagic);
      Otto.home();
    } else if (receivedData == "wander"){
      wander();
      Otto.home();
    } else if (receivedData == "get_back"){
      get_back();
      Otto.home();
    }
     else {
      Serial.println("Unknown command: " + receivedData);
    }
  }
}

void loop() {
  avoidObstacle(); // Check for obstacles and react
  handleSerialCommands(); // Check for incoming serial commands
}