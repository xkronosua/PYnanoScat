#include <Servo.h>
Servo fWheel;

#define FWHEEL_PIN 4//A2
#define STEPPER_DIR_PIN  6
#define STEPPER_STEP_PIN 10  //7
#define STEPPER_ENABLE_PIN 8
#define HOME_SENSOR_PIN 7  //2

#define LASER_CONTROL_PIN 13
#define LASER_SET_OFF HIGH
#define LASER_SET_ON  LOW
#define LASER_SIM_PIN 5

#define FW_CORRECTION 17
byte fWheelAng[6] = {10+FW_CORRECTION, 40+FW_CORRECTION, 70+FW_CORRECTION, 100+FW_CORRECTION, 130+FW_CORRECTION, 160+FW_CORRECTION};
byte activeFilter = 2;

enum COMMANDS {STEPPER_STOP, STEPPER_OFF, STEPPER_ON, STEPPER_HOME_CW, STEPPER_HOME_CCW, STEPPER_ROT_CCW, STEPPER_ROT_CW, STEPPER_ROT_CCWN, STEPPER_ROT_CWN, FWHEEL_ANG};

#define ST_DIR_CCW HIGH
#define ST_DIR_CW LOW



unsigned long curMillis;
unsigned long prevStepMillis = 0;
unsigned long millisBetweenSteps = 15; // milliseconds

unsigned long serialPrevStepMillis = 0;
unsigned long serialOutputPeriod = 100; // milliseconds

unsigned long angle_timer = 0;
unsigned long laser_timer = 0;


String inputString = "";         // a string to hold incoming command
String inputValue = "";         // a string to hold incoming value

boolean stringComplete = false;  // whether the string is complete

long steps = 0;
bool step_state = false;

#include "ps2.h"
#include <DirectIO.h>
PS2 mouse(11, 12);

InputPin optEndstop(HOME_SENSOR_PIN);
OutputPin stepperDir(STEPPER_DIR_PIN);
OutputPin stepperStep(STEPPER_STEP_PIN);
OutputPin stepperEnable(STEPPER_ENABLE_PIN);
OutputPin laserControl(LASER_CONTROL_PIN);

OutputPin laserSimulator(LASER_SIM_PIN);



int rotationMode = 0;

int angleCounter = 0;
int STEP_COUNTER = 0, N_STEPS = 0;
byte homeState = 0;

int singleStep() {
  if (curMillis - prevStepMillis >= millisBetweenSteps) {
    prevStepMillis = curMillis;
    //stepperStep = (step_state > 0);
    for (int i=0;i<10;i++){
    stepperStep = HIGH;
    delayMicroseconds(50);
    stepperStep = LOW;
    STEP_COUNTER++;
    delayMicroseconds(60);
    }
      return 1;
    
  }
  else return 0;
}

void rotNSteps(int steps, bool dir) {
  stepperDir = dir;
  if (STEP_COUNTER < steps) singleStep();
  else {
    //step_counter = 0;
  }
}

void setPwmFrequency(int pin, int divisor) {
  byte mode;
  if(pin == 5 || pin == 6 || pin == 9 || pin == 10) {
    switch(divisor) {
      case 1: mode = 0x01; break;
      case 8: mode = 0x02; break;
      case 64: mode = 0x03; break;
      case 256: mode = 0x04; break;
      case 1024: mode = 0x05; break;
      default: return;
    }
    if(pin == 5 || pin == 6) {
      TCCR0B = TCCR0B & 0b11111000 | mode;
    } else {
      TCCR1B = TCCR1B & 0b11111000 | mode;
    }
  } else if(pin == 3 || pin == 11) {
    switch(divisor) {
      case 1: mode = 0x01; break;
      case 8: mode = 0x02; break;
      case 32: mode = 0x03; break;
      case 64: mode = 0x04; break;
      case 128: mode = 0x05; break;
      case 256: mode = 0x06; break;
      case 1024: mode = 0x07; break;
      default: return;
    }
    TCCR2B = TCCR2B & 0b11111000 | mode;
  }
}

void stepperRotation() {
  // if (stepperEnable == HIGH) stepperEnable = LOW;
  switch (rotationMode) {
    case STEPPER_STOP: stepperEnable = HIGH; break;
    case STEPPER_ROT_CW:  {
        stepperDir = ST_DIR_CW; singleStep(); break;
      }
    case STEPPER_ROT_CCW: {
        stepperDir = ST_DIR_CCW; singleStep(); break;
      }
    case STEPPER_ROT_CWN:   rotNSteps(N_STEPS, ST_DIR_CW); break;
    case STEPPER_ROT_CCWN:  rotNSteps(N_STEPS, ST_DIR_CCW); break;
    case STEPPER_HOME_CW: {
        homeState = optEndstop.read();
        stepperDir = ST_DIR_CW;
        if (homeState) {
          rotationMode = STEPPER_STOP;
          angleCounter = 0;
        }
        else {
          singleStep();
        }
      }; break;
    case STEPPER_HOME_CCW: {
        homeState = optEndstop.read();
        stepperDir = ST_DIR_CCW;
        if (homeState) {
          rotationMode = STEPPER_STOP;
          angleCounter = 0;
        }
        else {
          singleStep();
        }; break;
      }
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


void remoteControl() {
  int st, ang;

  if (inputString == "STEPPER:") {
    if(inputValue == "OFF"){
    rotationMode = STEPPER_OFF;
    stepperEnable = HIGH;
    }
    if(inputValue == "STOP"){   /////////////////////////////////////////////////////////////////___+++__________
    rotationMode = STEPPER_STOP;
    stepperEnable = HIGH;
    }
    if(inputValue == "ON"){
    rotationMode = STEPPER_ON;
    stepperEnable = LOW;
    }
    Serial.println("STEPPER_STOP");
  }
  else if (inputString == "CW" ) {
    stepperEnable = LOW;
    rotationMode = STEPPER_ROT_CW;
    Serial.println("STEPPER_ROT_CW");
  }
  else if (inputString == "HOME:" ) {
    stepperEnable = LOW;
    if (inputValue == "CW")  rotationMode = STEPPER_HOME_CW;
    if (inputValue == "CCW") rotationMode = STEPPER_HOME_CCW;
    Serial.println("STEPPER_HOME");
  }
  else if (inputString == "CW:") {
    st = inputValue.toInt();
    rotationMode = STEPPER_ROT_CWN;
    stepperEnable = LOW;
    N_STEPS = st;
    STEP_COUNTER = 0;
    Serial.print("STEPPER_ROT_CWN:");
    Serial.println(st);
  }
  else if (inputString == "CCW") {
    stepperEnable = LOW;
    rotationMode = STEPPER_ROT_CCW;
    Serial.println("STEPPER_ROT_CCW");
  }
  else if (inputString == "CCW:") {
    st = inputValue.toInt();
    rotationMode = STEPPER_ROT_CCWN;
    stepperEnable = LOW;
    N_STEPS = st;
    STEP_COUNTER = 0;
    Serial.print("STEPPER_ROT_CWN:");
    Serial.println(st);
  }
  else if (inputString == "FW:") {
    st = inputValue.toInt();
    //rotationMode = FWHEEL_ANG;
    //stepperEnable = LOW;
    //N_STEPS = st;
    //STEP_COUNTER = 0;
    //setFWheel(st);
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

void mouse_init()
{ /*
    mouse.write(0xff);  // reset
    mouse.read();  // ack byte
    mouse.write(0xf0);  // remote mode
    mouse.read();  // ack
    delayMicroseconds(100);
    mouse.write(0xf3);  // Set Sample Rate
    mouse.read();  // ack
    mouse.write(0xc8);  // 200 sampl/s
    mouse.read();  // ack
    mouse.write(0xe8);  // Set Resolution
    mouse.read();  // ack
    mouse.write(0x03);  //  8 counts/mm
    mouse.read();  // ack*/
  mouse.write(0xff);  // reset
  mouse.read();  // ack byte
  mouse.read();  // blank */
  mouse.read();  // blank */
  mouse.write(0xf0);  // remote mode
  mouse.read();  // ack
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

  Serial.begin(19200);
  Serial.println("AAA");
  // reserve 200 bytes for the inputString:
  inputString.reserve(5);


  stepperEnable = HIGH;
  //###############  uncomment me ###################################
  mouse_init();
  //###############  uncomment me ###################################
  // initialize serial:
  fWheel.attach(FWHEEL_PIN);
  setFilter(activeFilter);
  //fWheel.writeMicroseconds(1450);
  //setPwmFrequency(STEPPER_STEP_PIN, 1);
  //fWheelTest();

}

int r = 0;

void loop() {

  curMillis = millis();
  stepperRotation();
  // print the string when a newline arrives:
  if (stringComplete) {
    //Serial.println(inputString);
    // clear the string:
    remoteControl();
    
  //}

  if (inputString == "STATE?"){
  //if (curMillis - serialPrevStepMillis >= serialOutputPeriod) {
    //serialPrevStepMillis = curMillis;
    Serial.print("A:");
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

    inputString = "";
    inputValue  = "";
    stringComplete = false;
  }
  

  //############################   laserStrobSimmulator  ###############################################
  //if (curMillis - laser_timer >= 10) {
  //  laser_timer = curMillis;
  //  laserSimulator = !laserSimulator.read();
  //}
  //#########################################################
  
  if (curMillis - angle_timer >= 60) {
    angle_timer = curMillis;
    r = mouse.get_y(); /////###############  uncomment me ###################################
    angleCounter += r;
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
    // add it to the inputString:



    if (inChar == '\n') {
      //Serial.print(inputString);
      //Serial.print(inputValue);
      //Serial.println("+++++++++++");
      stringComplete = true;
      value_aft_command = false;
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



