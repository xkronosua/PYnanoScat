bool debugMode=0;

#include <Servo.h>
Servo fWheel;

#define FWHEEL_PIN 5
#define SM_DIR_PIN  4
#define SM_STEP_PIN 11 //7
#define SM_ENABLE_PIN 2
#define HOME_SENSOR_PIN 7  //2

#define LASER_CONTROL_PIN 13
#define LASER_SET_OFF HIGH
#define LASER_SET_ON  LOW
#define LASER_SIM_PIN 9

#define BUTTON_STOP 3
#define BUTTON_CW   6
#define BUTTON_CCW  8


#define FW_CORRECTION 17
byte fWheelAng[6] = {10+FW_CORRECTION, 40+FW_CORRECTION, 70+FW_CORRECTION, 100+FW_CORRECTION, 130+FW_CORRECTION, 160+FW_CORRECTION};
byte activeFilter = 2;

enum COMMANDS {SM_STOP, SM_OFF, SM_ON, SM_HOME_CW, SM_HOME_CCW, SM_ROT_CCW, SM_ROT_CW, SM_ROT_CCWN, SM_ROT_CWN, FWHEEL_ANG, SM_SET_ANGLE};

#define ST_DIR_CCW LOW
#define ST_DIR_CW HIGH



unsigned long curMillis;
unsigned long prevStepMillis = 0;
unsigned long millisBetweenSteps = 1000; // milliseconds
unsigned long mouseReinit = 1800000; // milliseconds
unsigned long mouseReinitTimer = 0; // milliseconds

unsigned long serialPrevStepMillis = 0;
unsigned long serialOutputPeriod = 1000; // milliseconds

unsigned long angle_timer = 0;
unsigned long laser_timer = 0;


String inputString = "";         // a string to hold incoming command
String inputValue = "";         // a string to hold incoming value

boolean stringComplete = false;  // whether the string is complete

long steps = 0;
bool step_state = false;
float angle_step_calibr = 1;

#include <DirectIO.h>
#include "ps2.h"
//PS2 mouse(data, clock);
PS2 mouse(10, 12);

InputPin optEndstop(HOME_SENSOR_PIN);

InputPin stop_button(BUTTON_STOP);
InputPin cw_button(BUTTON_CW);
InputPin ccw_button(BUTTON_CCW);


OutputPin stepperDir(SM_DIR_PIN);
OutputPin stepperStep(SM_STEP_PIN);
OutputPin stepperEnable(SM_ENABLE_PIN);
OutputPin laserControl(LASER_CONTROL_PIN);

OutputPin laserSimulator(LASER_SIM_PIN);

int rotationMode = 0;
int angleCounter = 0;
unsigned long STEP_COUNTER = 0, N_STEPS = 0;
byte homeState = 0;

int stepperSpeed = 512;

int singleStep(int Speed) {
  if (millis() - prevStepMillis >= millisBetweenSteps && rotationMode!=SM_STOP) {
    prevStepMillis = curMillis;
    STEP_COUNTER++;
    tone(SM_STEP_PIN,stepperSpeed,millisBetweenSteps);
    return 1;
  }
  else {
  return 0;  
  }
}

void rotNSteps(int steps, bool dir) {
  stepperDir = dir;
  if (STEP_COUNTER < steps) singleStep(stepperSpeed);
  else {
  }
}


void stepperRotation() {
  // if (stepperEnable == HIGH) stepperEnable = LOW;
  switch (rotationMode) {
    case SM_STOP: stepperEnable = HIGH;noTone(SM_STEP_PIN); break;
    case SM_ROT_CW:  {
        stepperDir = ST_DIR_CW; singleStep(stepperSpeed); break;
      }
    case SM_ROT_CCW: {
        stepperDir = ST_DIR_CCW; singleStep(stepperSpeed); break;
      }
    case SM_ROT_CWN:   rotNSteps(N_STEPS, ST_DIR_CW); break;
    case SM_ROT_CCWN:  rotNSteps(N_STEPS, ST_DIR_CCW); break;
    case SM_HOME_CW: {
        homeState = optEndstop.read();
        stepperDir = ST_DIR_CW;
        if (homeState) {
          rotationMode = SM_STOP;
          angleCounter = 0;
        }
        else {
          singleStep(stepperSpeed);
        }
      }; break;
    case SM_HOME_CCW: {
        homeState = optEndstop.read();
        stepperDir = ST_DIR_CCW;
        if (homeState) {
          rotationMode = SM_STOP;
          angleCounter = 0;
        }
        else {
          singleStep(stepperSpeed);
        }; break;
      }
  }
}

void remoteControl() {
  int st, ang;

  if (inputString == "SM:") {
    if(inputValue == "OFF"){
    rotationMode = SM_OFF;
    stepperEnable = HIGH;
    }
    if(inputValue == "STOP"){   /////////////////////////////////////////////////////////////////___+++__________
    rotationMode = SM_STOP;
    stepperEnable = HIGH;
    }
    if(inputValue == "ON"){
    rotationMode = SM_ON;
    stepperEnable = LOW;
    }
    Serial.println("SM_STOP");
  }
  else if (inputString == "CW" ) {
    stepperEnable = LOW;
    rotationMode = SM_ROT_CW;
    tone(SM_STEP_PIN,stepperSpeed,millisBetweenSteps);
    Serial.println("SM_ROT_CW");
  }
  else if (inputString == "HOME:" ) {
    
    if (inputValue == "CW")  rotationMode = SM_HOME_CW;
    if (inputValue == "CCW") rotationMode = SM_HOME_CCW;
    tone(SM_STEP_PIN,stepperSpeed,millisBetweenSteps);
    stepperEnable = LOW;
    Serial.println("SM_HOME");
  }
  else if (inputString == "SPEED:" ) {
    int val = inputValue.toInt();
    if (val >0 && val < 1023000){
      stepperSpeed = val;
      stepperEnable = HIGH;
      noTone(SM_STEP_PIN);
      tone(SM_STEP_PIN,stepperSpeed,millisBetweenSteps);
      stepperEnable = LOW;
      Serial.print("SM_SPEED:");
      Serial.println(stepperSpeed);
      }
  }
  else if (inputString == "ANGLE:" ) {
    int val = inputValue.toInt();
    angleCounter = val;
    if (debugMode==1) STEP_COUNTER = val;
    Serial.print("ANGLE:");
    Serial.println(angleCounter);
    
  }
  else if (inputString == "CW:") {
    st = inputValue.toInt();
    rotationMode = SM_ROT_CWN;
    stepperEnable = LOW;
    N_STEPS = st;
    STEP_COUNTER = 0;
    stepperEnable = HIGH;
    noTone(SM_STEP_PIN);
    tone(SM_STEP_PIN,stepperSpeed,millisBetweenSteps);
    stepperEnable = LOW;
    Serial.print("SM_ROT_CWN:");
    Serial.println(st);
  }
  else if (inputString == "CCW") {
    stepperEnable = LOW;
    rotationMode = SM_ROT_CCW;
    tone(SM_STEP_PIN,stepperSpeed,millisBetweenSteps);
    Serial.println("SM_ROT_CCW");
  }
  else if (inputString == "CCW:") {
    st = inputValue.toInt();
    rotationMode = SM_ROT_CCWN;
    stepperEnable = LOW;
    N_STEPS = st;
    STEP_COUNTER = 0;
    Serial.print("SM_ROT_CWN:");
    Serial.println(st);
  }
  else if (inputString == "FW:") {
    st = inputValue.toInt();
    setFilter((byte)st);
    activeFilter = (byte)st;
    Serial.print("FW:");
    Serial.println(st);
  }
  else if (inputString == "LASER:") {
    if(inputValue == "OFF") laserControl = LASER_SET_OFF;
    if(inputValue == "ON")  laserControl = LASER_SET_ON;
    
    Serial.print("LASER:");
    Serial.println(inputValue);
  }

}

void setFWheel(int ang) {
  int last_pos = fWheel.read();
  int pos = 0;
  if (last_pos < ang) {
    for (pos = last_pos; pos <= ang; pos += 1) { // goes from 0 degrees to 180 degrees
      // in steps of 1 degree
      fWheel.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
  }
  else {
    for (pos = last_pos; pos >= ang; pos -= 1) { // goes from 180 degrees to 0 degrees
      fWheel.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
  }
}
int setFilter(byte index) {
  if (index < 6) {
    setFWheel(fWheelAng[index]);
  return 1;}
  else {
    return 0;
  }
}



void fWheelTest() {
  int pos = 0;
  for (pos = 0; pos <= 180; pos += 1) // goes from 0 degrees to 180 degrees
  { // in steps of 1 degree
    fWheel.write(pos);              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15ms for the servo to reach the position
  }
  for (pos = 180; pos >= 0; pos -= 1) // goes from 180 degrees to 0 degrees
  {
    fWheel.write(pos);              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15ms for the servo to reach the position
  }
}

void setup() {
  Serial.begin(9600);
  if(debugMode!=1)  {
  Serial.print("INIT:");
  mouse.init();
  Serial.println("DONE");
  }
  Serial.println("READY");
  
  // reserve 5 bytes for the inputString:
  inputString.reserve(20);
  
  stepperEnable = HIGH;
  //###############  uncomment me ###################################
  
  //###############  uncomment me ###################################

  fWheel.attach(FWHEEL_PIN);
  setFilter(activeFilter);

Serial.flush();
}

int r = 0;

void loop() {

  curMillis = millis();
  stepperRotation();
  // print the string when a newline arrives:
  if (millis() - serialPrevStepMillis >= 1500) {
      stepperEnable = HIGH;
      noTone(SM_STEP_PIN);
  }

  if (millis() - serialPrevStepMillis >= serialOutputPeriod || inputString == "STATE?") {
    serialPrevStepMillis = millis();
    Serial.print("^A:");
    Serial.print(angleCounter);
    Serial.print("\tFW:");
    Serial.print(activeFilter);
    Serial.print("\tc:");
    Serial.print(STEP_COUNTER);
    Serial.print("\tZ:");
    Serial.println(optEndstop.read());
    //r = 1;
    Serial.flush();
  }
  if (stringComplete) {
    //Serial.println(inputString);
    // clear the string:
    remoteControl();
    
  //}
  

  
  if((millis()-mouseReinitTimer > mouseReinit) && (rotationMode == SM_STOP || rotationMode == SM_OFF)){
    mouseReinitTimer = millis();
    mouse.init();
    mouse.init();
    Serial.println("Reinit:Done");
    }

    inputString = "";
    inputValue  = "";
    stringComplete = false;
  }
  

  if (curMillis - angle_timer >= 60) {
    angle_timer = curMillis;
    if(debugMode!=1){
      r = mouse.get_y();
      if (r<10){
      angleCounter += r;}
      }
    else {
      angleCounter = STEP_COUNTER;
      }
    //Serial.println(r);
    if (angleCounter>360*2) angleCounter=0;
    else if (angleCounter<0) angleCounter=360*2;
    if(debugMode==1){
    Serial.print(stop_button.read());
    Serial.print("\t");
    Serial.print(cw_button.read());
    Serial.print("\t");
    Serial.println(ccw_button.read());}
    }
  
  //#########################################################
}

/*
  SerialEvent occurs whenever a new data comes in the
  hardware serial RX.  This routine is run between each
  time loop() runs, so using delay inside loop can delay
  response.  Multiple bytes of data may be available.
*/
bool value_aft_command = false;
void serialEvent() {

  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
      value_aft_command = false;
      //wdt_reset();
    }
    else {
      if (value_aft_command) {
        inputValue += inChar;
      } else {
        inputString += inChar;
      }
    }
    if (inChar == ':') {
      value_aft_command = true;
    }
  }
}



