#include <Arduino.h>

const int POT_PIN = A0; // Сюда можно подключить потенциометр

void setup() {
  Serial.begin(115200); // Скорость отправки данных
  while (!Serial) { ; } // Ждем готовности порта
}

void loop() {
  int potValue = analogRead(POT_PIN);
  
  // Переводим значение в угол от 0 до 2*PI
  float angle = (potValue / 1023.0) * (2.0 * PI);
  
  // Отправляем в компьютер
  Serial.println(angle);
  
  delay(16); // ~60 кадров в секунду
}
