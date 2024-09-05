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
    def __init__(self, log_file, csv_writer, on_ready):
        self.log_file = log_file
        self.csv_writer = csv_writer
        self.transport = None
        self.buffer = ''
        self.test_complete = False
        self.on_ready = on_ready

    def connection_made(self, transport):
        self.transport = transport
        print("Serial connection established.")
        # Проверяем состояние on_ready
        if not self.on_ready.done():
            self.on_ready.set_result(True)

    def data_received(self, data):
        self.buffer += data.decode('utf-8')

        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            line = line.strip()
            if line:
                self.log_file.write(line + '\n')
                print(f"Received line: {line}")  # Отладочный вывод

                if line.startswith("timestamp"):
                    parts = line.split(',')
                    timestamp = int(parts[1])
                    speed = int(parts[3])
                    self.csv_writer.writerow([timestamp, speed])

                if "System Ready" in line:
                    if not self.on_ready.done():
                        self.on_ready.set_result(True)

                if "Test complete" in line:
                    self.test_complete = True
                    self.transport.close()

    def connection_lost(self, exc):
        if exc:
            print(f"Serial connection lost: {exc}")
        else:
            print("Serial connection closed.")


async def user_input(transport):
    while True:
        command = input("Enter command (1-9 to set speed, '-' to stop): ")
        if command in {'1', '2', '3', '4', '5', '6', '7', '8', '9', '-'}:
            # Отправляем команду с символом новой строки
            message = command + '\n'
            transport.write(message.encode('utf-8'))
            print(f"Sent command: {message.strip()}")
            await asyncio.sleep(0.1)  # Даем немного времени для передачи
            # transport.flush()  # Если нужно, можно добавить flush, но это не всегда необходимо
            if command == '-':
                break
        else:
            print("Invalid command. Use 1-9 to control speed, '-' to stop.")


async def main():
    with open(log_file_name, 'w') as log_file, open(csv_file_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Speed'])

        loop = asyncio.get_running_loop()

        on_ready = loop.create_future()

        reader = SerialReader(log_file, csv_writer, on_ready)
        transport, protocol = await serial_asyncio.create_serial_connection(loop, lambda: reader, serial_port, baud_rate)

        # Ждем, пока Arduino не сообщит о готовности
        await on_ready

        # Теперь можем начать ввод команд
        await user_input(transport)

        while not reader.test_complete:
            await asyncio.sleep(1)

    print("Log collection complete.")
    print("Plotting graph...")
    plot_graph()


def plot_graph():
    timestamps = []
    speeds = []

    with open(csv_file_name, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
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
    plt.savefig(png_file_name)
    plt.close()

    print(f"Graph saved as {png_file_name}")


if __name__ == "__main__":
    asyncio.run(main())