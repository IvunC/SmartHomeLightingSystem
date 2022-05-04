//Arduino Light Class


class Light {
  public:
    
    Light(int LEDPin, int motionPin, int plrPin, int button){
      pinMode(LEDPin, OUTPUT);
      pinMode(motionPin, INPUT);
      pinMode(plrPin, INPUT);
      pinMode(button, INPUT);
      _LEDPin = LEDPin;
      _state = false;
      _sense = false;
      _motionPin = motionPin;
      _plrPin = plrPin;
      _button = button;
      _plrLevel = 600;
      _timeout = 15;
      _timePress = 0;
      _timePressLimit = 0;
      _clicks = 0;
      _dataO = 0;
      _dataN = 0;
    }
    void off(){
      digitalWrite(_LEDPin, LOW);
      bitClear(_dataN, 2);
      _state = false;
    }
    void on(){
      digitalWrite(_LEDPin, HIGH);
      bitSet(_dataN,2);
      _state = true;
    }
    void flip(){
      digitalWrite(_LEDPin, !_state);
      if(bitRead(_dataN,2) == 1){
        bitClear(_dataN,2);
      }else{
        bitSet(_dataN,2);
      }
      _state = !_state;
    }
    void setSense(boolean sense){
      if(sense){
        bitSet(_dataN,1);
      }else{
        bitClear(_dataN,1);
      }
    
      _sense = sense;
    }
    
    boolean getSense(){
       return _sense;
    }
    boolean getState(){
      return _state;
    }
    void setPLR(int value){
      _plrLevel = value * 60;
    }
    int getPLRData(){
      return analogRead(_plrPin);
    }
    int getPLR(){
      return _plrLevel;
    }
    int getPLRPin(){
      return _plrPin;
    }
    void setTimeoutVal(int timeoutVal){
      _timeout = 15 * timeoutVal;
    }
    
    int getTimeout(){
      return _timeout;
    }
    boolean getMotion(){
      if (digitalRead(_motionPin)){
        bitSet(_dataN,0);
      }else{
        bitClear(_dataN,0);
      }
      return digitalRead(_motionPin);
    }
    void setCounter(int counter){
      _counter = counter;
    }
    int getCounter(){
      return _counter;
    }
    void setTarget(int target){
      _target = target;
    }
    int getTarget(){
      return _target;
    }
    boolean getButtonData(){
       return digitalRead(_button);
    }
    unsigned long getTimePress(){
      return _timePress;
    }
    void setTimePress(unsigned long timePress){
      _timePress = timePress;
    }
    unsigned long getTimePressLimit(){
      return _timePressLimit;
    }
    void setTimePressLimit(unsigned long timePressLimit){
      _timePressLimit = timePressLimit;
    }
    int getClicks(){
      return _clicks;
    }
    void setClicks(int clicks){
      _clicks = clicks;
    }
    void setDataO(byte dataO){
      _dataO= dataO;
    }byte getDataO(){
      return _dataO;
    }void setDataN(byte dataN){
      _dataN = dataN;
    }byte getDataN(){
      return _dataN;
    }
    
  private:
    boolean _sense;
    boolean _state;
    int _LEDPin;
    int _motionPin;
    int _plrPin;
    int _button;
    int _plrLevel;
    int _timeout;
    int _counter;
    unsigned long _timePress;
    unsigned long _timePressLimit;
    int _clicks; 
    byte _dataO;
    byte _dataN;
    int _target;
};
