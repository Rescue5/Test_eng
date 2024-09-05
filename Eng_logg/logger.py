import asyncio
import serial_asyncio
import csv
import matplotlib.pyplot as plt

# Параметры последовательного порта
serial_port = '/dev/cu.usbserial-A5069RR4'
baud_rate = 9600

# Имена файлов
log_file_name = 'eng.log'
csv_file_name = 'eng.csv'
png_file_name = 'motor_speed_plot.png'


class SerialReader(asyncio.Protocol):
    def __init__(self, log_file, csv_writer):
        """
        Класс описывающий интерфейс для чтения с последовательного порта
        :param log_file: Открытый файл логов
        :param csv_writer: Объект для записи в csv файл
        """
        self.log_file = log_file
        self.csv_writer = csv_writer
        self.transport = None   # Объект представляющий собой серийное соединение
        self.buffer = ''   # Текстовый буффер для временного хранения данных
        self.test_complete = False   # Флаг завеершения теста

    def connection_made(self, transport):
        """
        метод вызывающийся при установлении соединения с последовательным портом
        :param transport: последовательное соединение
        """
        self.transport = transport
        print("Serial connection established.")

    def data_received(self, data):
        # Декодируем данные из последовательного порта в обычный текст и сохраняем в буфер
        self.buffer += data.decode('utf-8')

        # Если в буфере встречается символ переноса строки (считывавем данные построчно)
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            line = line.strip()
            if line:
                self.log_file.write(line + '\n')
                print(line)

                # Записываем данные в CSV, если это строка с данными
                if line.startswith("timestamp"):
                    parts = line.split(',')
                    timestamp = int(parts[1])
                    speed = int(parts[3])
                    self.csv_writer.writerow([timestamp, speed])

                # Закрытие соединения
                if "Test complete" in line:
                    self.test_complete = True
                    self.transport.close()

    # Вызывается, когда соединение закрывается или теряется
    def connection_lost(self, exc):
        if exc:
            print(f"Serial connection lost: {exc}")
        else:
            print("Serial connection closed.")


async def send_start_command():
    """Асинхронная функция для отправки команды START на ардуино"""
    await asyncio.sleep(8)
    print("Sending START command to Arduino...")
    _, writer = await serial_asyncio.open_serial_connection(url=serial_port, baudrate=baud_rate)
    writer.write(b'START\n')   # Отправка команды в байтовой форме
    await writer.drain()   # Ожидание отправки данных
    writer.close()   # Закрытие подключения
    await writer.wait_closed()
    print("START command sent.")


async def main():
    # Открытие файла для записи логов и CSV файла
    with open(log_file_name, 'w') as log_file, open(csv_file_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Запись заголовков таблицы
        csv_writer.writerow(['Timestamp', 'Speed'])

        loop = asyncio.get_running_loop()

        # Запуск асинхронного чтения из последовательного порта
        reader = SerialReader(log_file, csv_writer)
        await serial_asyncio.create_serial_connection(loop, lambda: reader, serial_port, baud_rate)

        # Отправка команды START
        await send_start_command()

        # Ожидание завершения теста
        while not reader.test_complete:
            await asyncio.sleep(1)

    print("Log collection complete.")
    print("Plotting graph...")
    plot_graph()


def plot_graph():
    timestamps = []
    speeds = []

    # Чтение данных из CSV-файла
    with open(csv_file_name, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Пропуск заголовка
        for row in csv_reader:
            timestamps.append(int(row[0]))
            speeds.append(int(row[1]))

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, speeds, label='Speed', color='b', marker='o')
    plt.xlabel('Time (ms)')
    plt.ylabel('Speed (PWM value)')
    plt.title('Motor Speed vs Time')
    plt.legend()
    plt.grid(True)

    # Сохранение графика в файл
    plt.savefig(png_file_name)
    plt.close()

    print(f"Graph saved as {png_file_name}")


if __name__ == "__main__":
    asyncio.run(main())