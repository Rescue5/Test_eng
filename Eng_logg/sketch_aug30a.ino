#include <Servo.h>
#include <avr/sleep.h>

Servo esc;

int escPin = A2;
int minThrottle = 1000;
int maxThrottle = 2000;
int currentSpeed = 0;
int destThrottle; // Переменная для хранения значения 25% мощности

bool testComplete = false; // Флаг завершения теста

// Определяем структуру для хранения данных лога
struct LogData {
  unsigned long timestamp;  // Время логгирования
  int speed;                // Текущая скорость
};

LogData logData;

void setup() {
  Serial.begin(9600);
  esc.attach(escPin);

  // Калибровка ESC
  Serial.println("Starting ESC Calibration...");
  esc.writeMicroseconds(maxThrottle);  // Устанавливаем максимальное значение
  Serial.println("Max throttle set. Wait for ESC to recognize max throttle.");
  delay(3000);  // Ожидание для ESC

  esc.writeMicroseconds(minThrottle);  // Устанавливаем минимальное значение
  Serial.println("Min throttle set. Calibration complete.");
  delay(3000);  // Ожидание для завершения калибровки

  // Расчет значения для 25% мощности
  destThrottle = minThrottle + (maxThrottle - minThrottle) / 4;
  
  Serial.println("Enter START to begin the test.");
}

void loop() {
  if (!testComplete) {
    if (Serial.available()) {
      String command = Serial.readStringUntil('\n');
      command.trim();

      Serial.print("Received command: ");
      Serial.println(command);  // Для отладки

      if (command == "START") {
        delay(1500);
        runMotorTest();
      } else {
        Serial.println("Unknown command.");
      }
    }
  } else {
    // Выводим сообщение о завершении теста
    Serial.println("Test complete.");
    Serial.println("Entering sleep mode...");
    Serial.flush();  // Дожидаемся завершения передачи данных по последовательному порту
    
    // Переход в режим сна
    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    sleep_enable();
    sleep_mode();
    
  }
}

void runMotorTest() {
  // Плавное увеличение скорости до 25%
  for (int speed = minThrottle; speed <= destThrottle; speed += 10) {
    setSpeed(speed);
    delay(100);
  }

  // Держим скорость на 25% в течение 3-х секунд
  delay(3000);

  // Плавное уменьшение скорости до 0
  for (int speed = destThrottle; speed >= minThrottle; speed -= 10) {
    setSpeed(speed);
    delay(100);
  }

  Serial.println("Test complete");
  testComplete = true;
}

void setSpeed(int speed) {
  esc.writeMicroseconds(speed);
  currentSpeed = speed;
  logData.speed = currentSpeed;
  logData.timestamp = millis();  // Получаем время в миллисекундах с момента старта
  logDataToSerial(logData);  // Логгируем данные на компьютер
}

void logDataToSerial(const LogData& data) {
  Serial.print("timestamp,");
  Serial.print(data.timestamp);
  Serial.print(",speed,");
  Serial.println(data.speed);
}