import tkinter as tk
from tkinter import ttk
import webbrowser
import keyboard
import threading
import win32api
import win32con
import time
import ctypes

class AutoClicker:
    def __init__(self):
        self.clicking = False
        self.click_thread = None
        self.delay = 0.1  # Стартовая задержка (10 CPS)
        
        self.root = tk.Tk()
        self.root.title("")  # Пустой заголовок окна
        self.root.resizable(False, False)
        self.root.attributes('-topmost', False)
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Внутренний крупный заголовок
        self.header_label = ttk.Label(main_frame, text="Супер Быстрый Автокликер", font=('Arial', 16, 'bold'))
        self.header_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.N)
        
        # Инструкция
        self.instruction_label = ttk.Label(main_frame, text="Старт и стоп — F6", font=('Arial', 10))
        self.instruction_label.grid(row=1, column=0, pady=(0, 10), sticky=tk.W)
        
        # Чекбокс поверх всех окон
        self.topmost_var = tk.BooleanVar(value=False)
        topmost_check = ttk.Checkbutton(main_frame, text="Поверх всех окон", variable=self.topmost_var, command=self.toggle_topmost)
        topmost_check.grid(row=2, column=0, sticky=tk.E)
        
        # Статус
        self.status_label = ttk.Label(main_frame, text="Статус: Остановлен", font=('Arial', 10, 'bold'))
        self.status_label.grid(row=3, column=0, pady=5, sticky=tk.W)
        
        self.cps_label = ttk.Label(main_frame, text="Клики: 0", font=('Arial', 10))
        self.cps_label.grid(row=4, column=0, pady=5, sticky=tk.W)
        
        # Фрейм для пресетов
        preset_frame = ttk.LabelFrame(main_frame, text="Пресеты скорости", padding="5")
        preset_frame.grid(row=5, column=0, pady=10, sticky=(tk.W, tk.E))
        
        presets = [
            ("Медленно (1 CPS)", 1.0),
            ("Средне (10 CPS)", 0.1),
            ("Быстро (50 CPS)", 0.02),
            ("Очень быстро (100 CPS)", 0.01),
            ("Ультра (500 CPS)", 0.002),
            ("Максимум", 0)
        ]
        
        for i, (text, delay) in enumerate(presets):
            btn = ttk.Button(preset_frame, text=text, command=lambda d=delay: self.set_delay(d))
            btn.grid(row=i, column=0, pady=2, padx=5, sticky=(tk.W, tk.E))
            
        # Фрейм для ручной настройки
        manual_frame = ttk.LabelFrame(main_frame, text="Ручная настройка", padding="5")
        manual_frame.grid(row=6, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(manual_frame, text="Клики в секунду:").grid(row=0, column=0, pady=5, sticky=tk.W)
        
        self.cps_var = tk.StringVar(value="10")
        cps_entry = ttk.Entry(manual_frame, textvariable=self.cps_var, width=10)
        cps_entry.grid(row=1, column=0, pady=5, sticky=tk.W)
        
        apply_btn = ttk.Button(manual_frame, text="Применить", command=self.apply_manual_cps)
        apply_btn.grid(row=1, column=1, pady=5, padx=5)
        
        # Кнопка старт/стоп (название не меняется)
        self.start_button = ttk.Button(main_frame, text="Старт/Стоп (F6)", command=self.toggle_clicking)
        self.start_button.grid(row=7, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Текущая скорость
        self.speed_label = ttk.Label(main_frame, text="Текущая скорость: 10 CPS", font=('Arial', 9))
        self.speed_label.grid(row=8, column=0, pady=5, sticky=tk.W)
        
        # Нижний блок с подписью и ссылкой
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=9, column=0, pady=(20, 0), sticky=(tk.W, tk.E))
        
        author_label = ttk.Label(bottom_frame, text="by Desper_i9", font=('Arial', 10, 'normal'))
        author_label.pack(side=tk.LEFT, padx=(0, 10))
        
        link = ttk.Label(bottom_frame, text="gl-hf.ru", foreground="blue", cursor="hand2", font=('Arial', 9, 'underline'))
        link.pack(side=tk.LEFT)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://gl-hf.ru"))
        
        # Горячие клавиши
        keyboard.on_press_key("F6", lambda _: self.toggle_clicking())
        keyboard.on_press_key("F7", lambda _: self.stop_clicking())
        
        self.click_count = 0
        self.last_update = time.time()
        
        # Настройка размеров колонок и строк
        main_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(0, weight=1)
        manual_frame.columnconfigure(1, weight=1)
        
        # Центрируем окно
        self.root.update()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")
    
    def toggle_topmost(self):
        self.root.attributes('-topmost', self.topmost_var.get())
        
    def set_delay(self, delay):
        self.delay = delay
        cps = "∞" if delay == 0 else str(int(1 / delay))
        self.speed_label.config(text=f"Текущая скорость: {cps} CPS")
        
    def apply_manual_cps(self):
        try:
            cps = float(self.cps_var.get())
            if cps <= 0:
                return
            self.delay = 1 / cps
            self.speed_label.config(text=f"Текущая скорость: {int(cps)} CPS")
        except ValueError:
            pass
            
    def update_cps(self):
        if self.clicking:
            current_time = time.time()
            elapsed = current_time - self.last_update
            if elapsed >= 1:
                cps = int(self.click_count / elapsed)
                self.cps_label.config(text=f"Клики: {cps}")
                self.click_count = 0
                self.last_update = current_time
            self.root.after(100, self.update_cps)
        
    def click_loop(self):
        click_time = 0
        while self.clicking:
            try:
                current_time = time.time()
                if current_time - click_time >= self.delay:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                    self.click_count += 1
                    click_time = current_time
                else:
                    time.sleep(0.001)  # Минимальная задержка для снижения нагрузки
            except:
                continue
            
    def toggle_clicking(self):
        if not self.clicking:
            self.clicking = True
            self.status_label.config(text="Статус: Запущен")
            # Кнопка не меняет текст
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            self.update_cps()
        else:
            self.stop_clicking()
            
    def stop_clicking(self):
        self.clicking = False
        self.status_label.config(text="Статус: Остановлен")
        # Кнопка не меняет текст
        if self.click_thread:
            self.click_thread.join(timeout=1)
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    clicker = AutoClicker()
    clicker.run() 