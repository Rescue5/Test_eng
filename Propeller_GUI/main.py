import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import serial.tools.list_ports
import os


class TestApp(ThemedTk):
    def __init__(self):
        super().__init__(theme='arc')  # Используйте тему 'arc' для современного вида

        self.title("Motor and Propeller Test")
        self.geometry("1000x600")  # Установите размер окна

        # Инициализация файлов
        self.engine_file = 'engines.txt'
        self.propeller_file = 'propellers.txt'

        # Настройка меню
        self.create_menu()

        # Настройка вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        # Вкладка графиков
        self.create_graph_tab()

        # Вкладка добавления двигателей
        self.create_engine_tab()

        # Вкладка добавления пропеллеров
        self.create_propeller_tab()

        # Вкладка информации о тестах
        self.create_test_info_tab()

        # Настройка выбора порта
        self.create_port_selection()

        # Обновляем выпадающие списки
        self.update_dropdowns()

    def create_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.quit)

    def create_graph_tab(self):
        self.graph_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_tab, text="Graphs")

        # Создание рамок для графиков
        self.graph_frame = ttk.Frame(self.graph_tab)
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Создание фигур для графиков
        self.figure = Figure(figsize=(12, 3), dpi=100)  # Установите размеры фигуры
        self.ax1 = self.figure.add_subplot(131, title="RPM")
        self.ax2 = self.figure.add_subplot(132, title="Moment")
        self.ax3 = self.figure.add_subplot(133, title="Thrust")

        # Добавляем стильные рамки и фиксированный размер графиков
        self.create_graph_panel(self.ax1, "RPM")
        self.create_graph_panel(self.ax2, "Moment")
        self.create_graph_panel(self.ax3, "Thrust")

        # Добавление графиков на вкладку
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Окна ввода
        self.engine_label = ttk.Label(self.graph_tab, text="Engine:")
        self.engine_label.pack(pady=5, padx=10, anchor='w')
        self.engine_combobox = ttk.Combobox(self.graph_tab, values=self.load_engine_list())
        self.engine_combobox.pack(pady=5, padx=10, fill='x')

        self.propeller_label = ttk.Label(self.graph_tab, text="Propeller:")
        self.propeller_label.pack(pady=5, padx=10, anchor='w')
        self.propeller_combobox = ttk.Combobox(self.graph_tab, values=self.load_propeller_list())
        self.propeller_combobox.pack(pady=5, padx=10, fill='x')

    def create_graph_panel(self, ax, title):
        """ Создает мини-экранчик для графика с рамкой """
        ax.set_title(title)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_facecolor('#f0f0f0')  # Фон графика

        # Добавляем стильную рамку
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1.5)

        # Устанавливаем фиксированный размер графика
        ax.figure.set_size_inches(4, 2.5, forward=True)

    def create_engine_tab(self):
        self.engine_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.engine_tab, text="Add Engine")

        # Сетка для полей ввода характеристик двигателя
        ttk.Label(self.engine_tab, text="Engine Details").pack(pady=10)

        self.engine_entries = {}
        labels = ["Name", "Brand", "Model", "Power", "Weight", "Other"]
        for label_text in labels:
            frame = ttk.Frame(self.engine_tab)
            frame.pack(pady=5, padx=10, fill='x')

            label = ttk.Label(frame, text=label_text + ":")
            label.pack(side='left', padx=5)

            entry = ttk.Entry(frame, width=30)
            entry.pack(side='right', padx=5, fill='x')

            self.engine_entries[label_text] = entry

        add_button = ttk.Button(self.engine_tab, text="Add Engine", command=self.add_engine)
        add_button.pack(pady=10)

    def create_propeller_tab(self):
        self.propeller_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.propeller_tab, text="Add Propeller")

        # Сетка для полей ввода характеристик пропеллера
        ttk.Label(self.propeller_tab, text="Propeller Details").pack(pady=10)

        self.propeller_entries = {}
        labels = ["Name", "Brand", "Model", "Diameter", "Weight", "Other"]
        for label_text in labels:
            frame = ttk.Frame(self.propeller_tab)
            frame.pack(pady=5, padx=10, fill='x')

            label = ttk.Label(frame, text=label_text + ":")
            label.pack(side='left', padx=5)

            entry = ttk.Entry(frame, width=30)
            entry.pack(side='right', padx=5, fill='x')

            self.propeller_entries[label_text] = entry

        add_button = ttk.Button(self.propeller_tab, text="Add Propeller", command=self.add_propeller)
        add_button.pack(pady=10)

    def create_test_info_tab(self):
        self.test_info_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.test_info_tab, text="Test Info")

        # Добавьте элементы управления для отображения информации о тестах
        self.test_info_label = ttk.Label(self.test_info_tab, text="Previous Test Information:")
        self.test_info_label.pack(pady=10)

        # Здесь можно добавить текстовые виджеты или другие элементы для отображения информации о тестах
        self.test_info_text = tk.Text(self.test_info_tab, height=10, width=80)
        self.test_info_text.pack(pady=10, padx=10)

    def create_port_selection(self):
        self.port_frame = ttk.Frame(self)
        self.port_frame.pack(pady=10, padx=10, fill='x')

        self.port_label = ttk.Label(self.port_frame, text="Select COM Port:")
        self.port_label.pack(side='left', padx=5)

        self.port_combobox = ttk.Combobox(self.port_frame)
        self.port_combobox['values'] = self.get_ports()
        self.port_combobox.pack(side='left', padx=5)

        # Кнопка для проверки порта
        self.check_button = ttk.Button(self.port_frame, text="Check Port", command=self.check_port)
        self.check_button.pack(side='left', padx=5)

        # Кнопка для запуска теста
        self.test_button = ttk.Button(self.port_frame, text="Run Test", command=self.run_test)
        self.test_button.pack(side='left', padx=5)

        # Лейбл для отображения результатов проверки порта
        self.test_result_label = ttk.Label(self.port_frame, text="", foreground="red")
        self.test_result_label.pack(side='left', padx=5)

    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["No Ports Available"]

    def check_port(self):
        selected_port = self.port_combobox.get()
        if selected_port == "No Ports Available":
            self.test_result_label.config(text="No ports available", foreground="red")
            return

        try:
            with serial.Serial(selected_port, 9600, timeout=2) as ser:
                ser.write(b"TEST\n")
                response = ser.readline().decode().strip()
                if response == "OK":
                    self.test_result_label.config(text="Port is working", foreground="green")
                else:
                    self.test_result_label.config(text="Invalid response", foreground="red")
        except Exception as e:
            self.test_result_label.config(text=f"Error: {e}", foreground="red")

    def run_test(self):
        selected_port = self.port_combobox.get()
        if selected_port == "No Ports Available":
            self.test_result_label.config(text="No ports available", foreground="red")
            return

        try:
            with serial.Serial(selected_port, 9600, timeout=2) as ser:
                ser.write(b"START\n")
                response = ser.readline().decode().strip()
                if response == "OK":
                    self.test_result_label.config(text="Test started", foreground="green")
                else:
                    self.test_result_label.config(text="Invalid response", foreground="red")
        except Exception as e:
            self.test_result_label.config(text=f"Error: {e}", foreground="red")

    def add_engine(self):
        engine_data = {label: entry.get() for label, entry in self.engine_entries.items()}
        with open(self.engine_file, 'a') as f:
            f.write(','.join(engine_data.values()) + '\n')
        self.update_dropdowns()

    def add_propeller(self):
        propeller_data = {label: entry.get() for label, entry in self.propeller_entries.items()}
        with open(self.propeller_file, 'a') as f:
            f.write(','.join(propeller_data.values()) + '\n')
        self.update_dropdowns()

    def update_dropdowns(self):
        self.engine_combobox['values'] = self.load_engine_list()
        self.propeller_combobox['values'] = self.load_propeller_list()

    def load_engine_list(self):
        if os.path.exists(self.engine_file):
            with open(self.engine_file, 'r') as f:
                return [line.split(',')[0] for line in f]
        return ["No Engines Available"]

    def load_propeller_list(self):
        if os.path.exists(self.propeller_file):
            with open(self.propeller_file, 'r') as f:
                return [line.split(',')[0] for line in f]
        return ["No Propellers Available"]

    def update_graphs(self, rpm, moment, thrust):
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.create_graph_panel(self.ax1, "RPM")
        self.create_graph_panel(self.ax2, "Moment")
        self.create_graph_panel(self.ax3, "Thrust")
        self.ax1.plot(rpm, label='RPM')
        self.ax2.plot(moment, label='Moment')
        self.ax3.plot(thrust, label='Thrust')
        self.ax1.legend()
        self.ax2.legend()
        self.ax3.legend()
        self.canvas.draw()


if __name__ == "__main__":
    app = TestApp()
    app.mainloop()