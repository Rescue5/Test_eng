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
speed_png_file_name = 'motor_speed_plot.png'
weight_png_file_name = 'motor_weight_plot.png'


class SerialReader(asyncio.Protocol):
    def __init__(self, log_file, csv_writer):
        self.log_file = log_file
        self.csv_writer = csv_writer
        self.transport = None
        self.buffer = ''
        self.test_complete = False

    def connection_made(self, transport):
        self.transport = transport
        print("Serial connection established.")

    def data_received(self, data):
        self.buffer += data.decode('utf-8')

        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            line = line.strip()
            if line:
                self.log_file.write(line + '\n')
                print(f"Received line: {line}")

                if line.startswith("timestamp"):
                    parts = line.split(',')
                    timestamp = int(parts[1])
                    speed = int(parts[3])
                    weight = int(parts[5])
                    self.csv_writer.writerow([timestamp, speed, weight])

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
            message = command + '\n'
            transport.write(message.encode('utf-8'))
            print(f"Sent command: {message.strip()}")
            await asyncio.sleep(0.1)
            if command == '-':
                break
        else:
            print("Invalid command. Use 1-9 to control speed, '-' to stop.")


async def main():
    with open(log_file_name, 'w') as log_file, open(csv_file_name, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Speed', 'Weight'])

        loop = asyncio.get_running_loop()

        reader = SerialReader(log_file, csv_writer)
        transport, protocol = await serial_asyncio.create_serial_connection(
            loop, lambda: reader, serial_port, baud_rate
        )

        # Запуск задачи для пользовательского ввода
        user_input_task = asyncio.create_task(user_input(transport))

        # Постоянное ожидание завершения теста
        while not reader.test_complete:
            await asyncio.sleep(0.5)

        await user_input_task

    print("Log collection complete.")
    print("Plotting graphs...")
    plot_graphs()


def plot_graphs():
    timestamps = []
    speeds = []
    weights = []

    with open(csv_file_name, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for row in csv_reader:
            timestamps.append(int(row[0]))
            speeds.append(int(row[1]))
            weights.append(int(row[2]))

    plt.figure(figsize=(10, 6))

    # График скорости
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, speeds, label='Speed', color='b', marker='o')
    plt.xlabel('Time (ms)')
    plt.ylabel('Speed (PWM value)')
    plt.title('Motor Speed vs Time')
    plt.legend()
    plt.grid(True)

    # График веса
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, weights, label='Weight', color='r', marker='o')
    plt.xlabel('Time (ms)')
    plt.ylabel('Weight (units)')
    plt.title('Weight vs Time')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(speed_png_file_name)
    plt.savefig(weight_png_file_name)
    plt.close()

    print(f"Graphs saved as {speed_png_file_name} and {weight_png_file_name}")


if __name__ == "__main__":
    asyncio.run(main())