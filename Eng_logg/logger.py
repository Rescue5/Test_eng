import asyncio
import serial_asyncio
import matplotlib.pyplot as plt

# Параметры последовательного порта
serial_port = '/dev/cu.usbserial-A5069RR4'
baud_rate = 9600

# имена файлов
log_file_name = 'eng.log'
output_file_name = 'motor_speed_plot.png'

class SerialReader(asyncio.Protocol):
    def __init__(self, log_file):
        self.log_file = log_file
        self.transport = None
        self.buffer = ''
        self.test_complete = False

    def connection_made(self, transport):
        self.transport = transport
        print("Serial connection established.")

    def data_received(self, data):
        # Буферизуем полученные данные
        self.buffer += data.decode('utf-8')

        # Обрабатываем данные по строкам
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            line = line.strip()
            if line:
                self.log_file.write(line + '\n')
                print(line)
                if "Test complete" in line:
                    self.test_complete = True
                    self.transport.close()

    def connection_lost(self, exc):
        if exc:
            print(f"Serial connection lost: {exc}")
        else:
            print("Serial connection closed.")

async def send_start_command():
    # Ожидание перед отправкой команды
    await asyncio.sleep(2)
    print("Sending START command to Arduino...")
    _, writer = await serial_asyncio.open_serial_connection(url=serial_port, baudrate=baud_rate)
    writer.write(b'START\n')
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("START command sent.")

async def main():
    # Открытие файла для записи логов
    with open(log_file_name, 'w') as log_file:
        loop = asyncio.get_running_loop()

        # Запуск асинхронного чтения из последовательного порта
        reader = SerialReader(log_file)
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

    with open(log_file_name, 'r') as log_file:
        for line in log_file:
            if line.startswith("timestamp"):
                parts = line.split(',')
                timestamp = int(parts[1])
                speed = int(parts[3])
                timestamps.append(timestamp)
                speeds.append(speed)

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, speeds, label='Speed', color='b', marker='o')
    plt.xlabel('Time (ms)')
    plt.ylabel('Speed (PWM value)')
    plt.title('Motor Speed vs Time')
    plt.legend()
    plt.grid(True)

    # Сохранение графика в файл
    plt.savefig(output_file_name)
    plt.close()

    print(f"Graph saved as {output_file_name}")

if __name__ == "__main__":
    asyncio.run(main())