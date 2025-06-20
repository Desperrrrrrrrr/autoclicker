import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import keyboard
import threading
import win32api
import win32con
import win32gui
import pyautogui
import time
import ctypes

class AutoClicker:
    def __init__(self):
        self.clicking = False
        self.click_thread = None
        self.delay = 0.1  # Стартовая задержка (10 CPS)
        self.target_hwnd = None
        self.waiting_for_point = False
        self.lock_mouse = False
        
        self.root = tk.Tk()
        self.root.title("")  # Пустой заголовок окна
        self.root.resizable(False, False)
        self.root.attributes('-topmost', False)
        self.root.geometry('350x520')
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Крупный заголовок
        self.header_label = ttk.Label(main_frame, text="Автокликер", font=('Arial', 13, 'bold'))
        self.header_label.grid(row=0, column=0, pady=(0, 5), sticky=tk.N)
        
        # Инструкция и статус на одной строке
        instr_status_frame = ttk.Frame(main_frame)
        instr_status_frame.grid(row=1, column=0, pady=(0, 2), sticky=(tk.W, tk.E))
        self.instruction_label = ttk.Label(instr_status_frame, text="F6 — старт/стоп", font=('Arial', 9))
        self.instruction_label.pack(side=tk.LEFT, padx=(0, 10))
        self.status_label = ttk.Label(instr_status_frame, text="Выключен", font=('Arial', 9, 'bold'), foreground="#1976d2")
        self.status_label.pack(side=tk.LEFT)
        
        # Инструкция по выбору точки (отдельная строка, скрыта по умолчанию)
        self.pick_point_info = ttk.Label(main_frame, text="", font=('Arial', 8), foreground="#1976d2")
        self.pick_point_info.grid(row=2, column=0, sticky=tk.W)
        
        # Чекбокс поверх всех окон
        self.topmost_var = tk.BooleanVar(value=False)
        topmost_check = ttk.Checkbutton(main_frame, text="Поверх окон", variable=self.topmost_var, command=self.toggle_topmost)
        topmost_check.grid(row=3, column=0, sticky=tk.E)
        
        # Чекбокс для режима клика по координатам
        self.coord_mode_var = tk.BooleanVar(value=False)
        coord_mode_check = ttk.Checkbutton(main_frame, text="По координатам (фикс)", variable=self.coord_mode_var)
        coord_mode_check.grid(row=4, column=0, sticky=tk.W)
        
        # Чекбокс и поля для режима клика по окну
        self.window_mode_var = tk.BooleanVar(value=False)
        window_mode_check = ttk.Checkbutton(main_frame, text="В окне", variable=self.window_mode_var)
        window_mode_check.grid(row=5, column=0, sticky=tk.W)
        
        window_frame = ttk.Frame(main_frame)
        window_frame.grid(row=6, column=0, pady=(2, 5), sticky=(tk.W, tk.E))
        
        ttk.Label(window_frame, text="Заголовок:").grid(row=0, column=0, sticky=tk.W)
        self.window_title_var = tk.StringVar()
        ttk.Entry(window_frame, textvariable=self.window_title_var, width=15).grid(row=0, column=1, padx=2)
        
        ttk.Label(window_frame, text="X:").grid(row=0, column=2, sticky=tk.W)
        self.x_var = tk.StringVar(value="100")
        self.x_entry = ttk.Entry(window_frame, textvariable=self.x_var, width=5)
        self.x_entry.grid(row=0, column=3, padx=1)
        
        ttk.Label(window_frame, text="Y:").grid(row=0, column=4, sticky=tk.W)
        self.y_var = tk.StringVar(value="100")
        self.y_entry = ttk.Entry(window_frame, textvariable=self.y_var, width=5)
        self.y_entry.grid(row=0, column=5, padx=1)
        
        self.pick_point_btn = ttk.Button(window_frame, text="Точка", width=7, command=self.pick_point)
        self.pick_point_btn.grid(row=0, column=6, padx=4)
        
        # Статус
        self.cps_label = ttk.Label(main_frame, text="Клики: 0", font=('Arial', 9))
        self.cps_label.grid(row=7, column=0, pady=2, sticky=tk.W)
        
        # Фрейм для пресетов
        preset_frame = ttk.LabelFrame(main_frame, text="Скорость", padding="3")
        preset_frame.grid(row=8, column=0, pady=5, sticky=(tk.W, tk.E))
        
        presets = [
            ("1 CPS", 1.0),
            ("10 CPS", 0.1),
            ("50 CPS", 0.02),
            ("100 CPS", 0.01),
            ("500 CPS", 0.002),
            ("MAX", 0)
        ]
        for i, (text, delay) in enumerate(presets):
            btn = ttk.Button(preset_frame, text=text, width=10, command=lambda d=delay: self.set_delay(d))
            btn.grid(row=i//2, column=i%2, pady=1, padx=2, sticky=(tk.W, tk.E))
        preset_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(1, weight=1)
        
        # Фрейм для ручной настройки
        manual_frame = ttk.LabelFrame(main_frame, text="Своя скорость", padding="3")
        manual_frame.grid(row=9, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(manual_frame, text="CPS:").grid(row=0, column=0, pady=2, sticky=tk.W)
        
        self.cps_var = tk.StringVar(value="10")
        cps_entry = ttk.Entry(manual_frame, textvariable=self.cps_var, width=7)
        cps_entry.grid(row=0, column=1, pady=2, padx=2, sticky=tk.W)
        
        apply_btn = ttk.Button(manual_frame, text="OK", width=5, command=self.apply_manual_cps)
        apply_btn.grid(row=0, column=2, pady=2, padx=2)
        
        # Кнопка старт/стоп
        self.start_button = ttk.Button(main_frame, text="Старт/Стоп (F6)", command=self.toggle_clicking)
        self.start_button.grid(row=10, column=0, pady=4, sticky=(tk.W, tk.E))

        # --- Кнопка мыши ---
        self.button_var = tk.StringVar(value="left")
        button_frame = ttk.LabelFrame(main_frame, text="Кнопка", padding="2")
        button_frame.grid(row=11, column=0, pady=(2, 0), sticky=(tk.W, tk.E))
        ttk.Radiobutton(button_frame, text="Левая", variable=self.button_var, value="left").pack(side=tk.LEFT, padx=1)
        ttk.Radiobutton(button_frame, text="Правая", variable=self.button_var, value="right").pack(side=tk.LEFT, padx=1)
        ttk.Radiobutton(button_frame, text="Обе", variable=self.button_var, value="both").pack(side=tk.LEFT, padx=1)

        # Текущая скорость
        self.speed_label = ttk.Label(main_frame, text="Текущая скорость: 10 CPS", font=('Arial', 8))
        self.speed_label.grid(row=12, column=0, pady=2, sticky=tk.W)

        # Нижний блок с подписью и ссылкой
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=13, column=0, pady=(6, 0), sticky=(tk.W, tk.E))
        author_label = ttk.Label(bottom_frame, text="by Desper_i9", font=('Arial', 8, 'normal'))
        author_label.pack(side=tk.LEFT, padx=(0, 5))
        link = ttk.Label(bottom_frame, text="gl-hf.ru", foreground="blue", cursor="hand2", font=('Arial', 8, 'underline'))
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
        
    def find_window(self, title):
        def enum_handler(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if title.lower() in window_text.lower():
                    result.append(hwnd)
        result = []
        win32gui.EnumWindows(enum_handler, result)
        return result[0] if result else None
    
    def click_mouse(self, x, y):
        btn = self.button_var.get()
        if btn == "left":
            pyautogui.click(x, y, button="left")
        elif btn == "right":
            pyautogui.click(x, y, button="right")
        elif btn == "both":
            pyautogui.click(x, y, button="left")
            pyautogui.click(x, y, button="right")

    def click_in_window(self, hwnd, x, y):
        btn = self.button_var.get()
        lparam = (y << 16) | x
        if btn == "left":
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        elif btn == "right":
            win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
            win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)
        elif btn == "both":
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            win32api.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lparam)
            win32api.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lparam)

    def pick_point(self):
        self.waiting_for_point = True
        self.pick_point_info.config(text="F8 — выбрать точку мыши")
        keyboard.on_press_key("F8", self.save_mouse_position)
    
    def save_mouse_position(self, e=None):
        if not self.waiting_for_point:
            return
        x, y = pyautogui.position()
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        self.pick_point_info.config(text="")
        self.waiting_for_point = False
        keyboard.unhook_key("F8")
    
    def click_loop(self):
        click_time = 0
        if self.coord_mode_var.get():
            # Клик по координатам с "прилипанием" мыши
            try:
                x = int(self.x_var.get())
                y = int(self.y_var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректные координаты X или Y")
                self.stop_clicking()
                return
            self.lock_mouse = True
            def mouse_lock_loop():
                while self.clicking and self.lock_mouse:
                    cur_x, cur_y = pyautogui.position()
                    if (cur_x, cur_y) != (x, y):
                        pyautogui.moveTo(x, y, duration=0)
                    time.sleep(0.001)
            threading.Thread(target=mouse_lock_loop, daemon=True).start()
            while self.clicking:
                current_time = time.time()
                if current_time - click_time >= self.delay:
                    try:
                        self.click_mouse(x, y)
                    except Exception:
                        pass
                    self.click_count += 1
                    click_time = current_time
                else:
                    time.sleep(0.0001)
            self.lock_mouse = False
        elif self.window_mode_var.get():
            # Кликать в выбранном окне
            title = self.window_title_var.get().strip()
            try:
                x = int(self.x_var.get())
                y = int(self.y_var.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректные координаты X или Y")
                self.stop_clicking()
                return
            hwnd = self.find_window(title)
            if not hwnd:
                messagebox.showerror("Ошибка", f"Окно с заголовком '{title}' не найдено")
                self.stop_clicking()
                return
            while self.clicking:
                current_time = time.time()
                if current_time - click_time >= self.delay:
                    try:
                        self.click_in_window(hwnd, x, y)
                    except Exception:
                        pass
                    self.click_count += 1
                    click_time = current_time
                else:
                    time.sleep(0.0001)
        else:
            # Обычный режим
            while self.clicking:
                current_time = time.time()
                if current_time - click_time >= self.delay:
                    try:
                        btn = self.button_var.get()
                        if btn == "left":
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                        elif btn == "right":
                            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
                        elif btn == "both":
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
                    except Exception:
                        pass
                    self.click_count += 1
                    click_time = current_time
                else:
                    time.sleep(0.0001)
        
    def toggle_clicking(self):
        if not self.clicking:
            self.clicking = True
            self.status_label.config(text="Включен", foreground="#00c853")  # Ярко-зеленый
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            self.update_cps()
        else:
            self.stop_clicking()
            
    def stop_clicking(self):
        self.clicking = False
        self.status_label.config(text="Выключен", foreground="#1976d2")  # Ярко-синий
        self.lock_mouse = False
        if self.click_thread and threading.current_thread() != self.click_thread:
            self.click_thread.join(timeout=1)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    clicker = AutoClicker()
    clicker.run() 