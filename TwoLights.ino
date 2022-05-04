#include "Light.h"
#include <SoftwareSerial.h>

//initializing light values
Light light1(8,2,0,5);
Light light2(9,3,1,6);

//current time
int curTime = millis()/1000;

SoftwareSerial mySerial(10,11);

void setup() {
  
 Serial.begin(115200);
 mySerial.begin(115200);
}
//detects clicks, behaves accordingly to clicks
void clicks(Light &curLight){
  curLight.getMotion();
  //if clicked
  if (curLight.getButtonData()){
    Serial.print("P1 clicks: ");
    delay(200);
    Serial.println(curLight.getClicks());
    //click detected, timeout set before second click
    if (curLight.getClicks() == 0){
      curLight.setTimePress(millis());
      curLight.setTimePressLimit(curLight.getTimePress() + 500);
      curLight.setClicks(1);
      
      //second click detected, change sensing mode
    }else if (curLight.getClicks() == 1 && millis()< curLight.getTimePressLimit()){
      Serial.print("New Sense Value:");
      curLight.setSense(!curLight.getSense());
      Serial.println(curLight.getSense());
      //reset timeout values and clicks
      curLight.setTimePress(0);
      curLight.setTimePressLimit(0);
      curLight.setClicks(0);
    }
  } //only one click detected, change light state
  if (curLight.getClicks()==1 && curLight.getTimePressLimit()!=0 && millis() > curLight.getTimePressLimit()){
  
    if (!curLight.getSense()){
      curLight.flip();
    }
    Serial.print("Sense");
    Serial.println(curLight.getSense());
    Serial.println("SingleClick");
    //reset timeout valeus and clicks
    curLight.setTimePress(0);
    curLight.setTimePressLimit(0);
    curLight.setClicks(0);
  }
}
//function to detect motion
void detectMotion(Light &curLight){
  //if its in sensing mode
  if (curLight.getSense()){
    //Serial.print("Input:");
    //Serial.println(curLight.getPLRData());
    //if motion is detected and light levels are within threshold
    if (curLight.getMotion() && curLight.getPLRData() > curLight.getPLR()){
      //setting up timeout values
      curLight.setCounter(millis()/1000);
      curLight.setTarget(curLight.getCounter() + curLight.getTimeout());
    }
    //Serial.print("Counter:");
    //Serial.println(curLight.getCounter());
    // keep lights on until no motion has been detected for timeout value
    if (curLight.getCounter() < curLight.getTarget()){
      curLight.setCounter(millis()/1000);
      curLight.on();
      //timeout value is over turn off lights
    }else {
      curLight.off();
    }
  }
}
//used to encrypt light states to send to Rpi
void encrypt(Light &curLight){
  int num = curLight.getPLRPin() + 1;
  //if the current light has new data to send
  if (curLight.getDataO() != curLight.getDataN()){
    byte temp = curLight.getDataN();
    // 11 from 6 and 7 is opcode for actively listening
    bitSet(temp,6);
    bitSet(temp,7);
    //grabbing correct light
    if (num == 1){
      bitClear(temp,4);
      bitClear(temp,5);
    }else if (num == 2){
      bitSet(temp,4);
      bitClear(temp,5);
    }else if (num == 3){
      bitSet(temp,4);
      bitClear(temp,5);
    }else {
      bitSet(temp,4);
      bitSet(temp,5);
    }
    //passing in light data from its class to instruction
    curLight.setDataN(temp);
  }
}
//data received, decrypt it
void decrypt(int newData){
  byte binData = (byte) newData;
  //if MSB is 11 then it is actively listening data from Rpi
  if (bitRead(binData, 7) == 1 && bitRead(binData, 6) == 1){
    //updating values
    if (bitRead(binData, 4) == 0 && bitRead(binData, 5) == 0){
      light1.setTarget(0);
      // toggles light state based on bit 2
      if(bitRead(binData,2) == 1){
        light1.on();
        
      }if(bitRead(binData,2) == 0){
        light1.off();
      }
      //set sense value based on bit 1
      light1.setSense(bitRead(binData, 1));
      light1.setTarget(0);
      //same goes for light 2
    }if (bitRead(binData, 4) == 1 && bitRead(binData, 5) == 0){
      light2.setTarget(0);
      if(bitRead(binData,2) == 1){
        light2.on();
      }if(bitRead(binData,2) == 0){
        light2.off();
      }
      light2.setSense(bitRead(binData, 1));
    }
    //if 10 MSB, then we are changing Photoresistor levels
  }if (bitRead(binData, 7) == 1 && bitRead(binData, 6) == 0){
    byte photolevel = binData&15;
    //determining which light to change the PLR value 
    if (bitRead(binData, 4) == 0 && bitRead(binData, 5) == 0){
      light1.setPLR((int) photolevel);
      Serial.print("Light 1 new PLR:");
      Serial.println(light1.getPLR());
    }if (bitRead(binData, 4) == 1 && bitRead(binData, 5) == 0){
      light2.setPLR((int) photolevel);
      Serial.print("Light 2 new PLR:");
      Serial.println(light2.getPLR());
    }
    // if 01 MSB then we are changing trimeout value
  }if (bitRead(binData, 7) == 0 && bitRead(binData, 6) == 1){
    int timeVal = binData&15;
    Serial.println(timeVal);
    //determining which light to change timeout
    if (bitRead(binData, 4) == 0 && bitRead(binData, 5) == 0){
      light1.setTimeoutVal(timeVal);
      Serial.print("Light 1 new Timeout:");
      Serial.println(light1.getTimeout());
      
    }if (bitRead(binData, 4) == 1 && bitRead(binData, 5) == 0){
      light2.setTimeoutVal(timeVal);
      Serial.print("Light 2 new Timeout:");
      Serial.println(light2.getTimeout());
    }
  }
  
}

void loop() {
  //detect clicks, motion, encrypt, send, recieve, decrypt, repeat
  clicks(light1);
  detectMotion(light1);
  encrypt(light1);
  clicks(light2);
  detectMotion(light2);
  encrypt(light2);
  
  if (mySerial.available()){
    //read value from Rpi
    int newVal = mySerial.readString().toInt();
    if (newVal > 15 && newVal < 248){
      Serial.print("Read value ");
      Serial.println(newVal);
      decrypt(newVal);
    }else{
      Serial.println("Error Transmitting, try again!");
    }
  }
  
  if (Serial.available()){
    // for each light pass instruction to Rpi
    if (light1.getDataN() != light1.getDataO() || curTime+5 < (millis()/1000)){
      mySerial.write(light1.getDataN());
      light1.setDataO(light1.getDataN());
      Serial.print("Light 1: ");
      Serial.println(light1.getDataN(), BIN);
      curTime = millis()/1000;
      
    }if (light2.getDataN() != light2.getDataO() || curTime+5 < (millis()/1000)){
      mySerial.write(light2.getDataN());
      light2.setDataO(light2.getDataN());
      Serial.print("Light 2: ");
      Serial.println(light2.getDataN(), BIN);
      curTime = millis()/1000;
    }
  }
}
