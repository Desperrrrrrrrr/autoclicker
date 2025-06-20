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
from PIL import Image, ImageDraw, ImageFont, ImageTk

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
        self.root.geometry('350x445')
        try:
            # Устанавливаем эмодзи-иконку (🦅)
            img = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
            font = ImageFont.truetype('seguiemj.ttf', 28)  # стандартный emoji-шрифт Windows
            draw = ImageDraw.Draw(img)
            draw.text((0, 0), '🦅', font=font, fill=(0, 0, 0, 255))
            icon = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, icon)
        except Exception:
            pass
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Крупный заголовок
        self.header_label = ttk.Label(main_frame, text="Автокликер", font=('Arial', 13, 'bold'))
        self.header_label.grid(row=0, column=0, pady=(0, 2), sticky=tk.N)
        
        # Инструкция и статус на одной строке
        instr_status_frame = ttk.Frame(main_frame)
        instr_status_frame.grid(row=1, column=0, pady=(0, 1), sticky=(tk.W, tk.E))
        self.instruction_label = ttk.Label(instr_status_frame, text="F6 — старт/стоп", font=('Arial', 9))
        self.instruction_label.pack(side=tk.LEFT, padx=(0, 10))
        self.status_label = ttk.Label(instr_status_frame, text="Выключен", font=('Arial', 9, 'bold'), foreground="#1976d2")
        self.status_label.pack(side=tk.LEFT)
        
        # Чекбоксы режимов и поверх окон — сразу под статусом
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, pady=(0, 1), sticky=(tk.W, tk.E))
        self.coord_mode_var = tk.BooleanVar(value=False)
        coord_mode_check = ttk.Checkbutton(options_frame, text="По координатам (фикс)", variable=self.coord_mode_var)
        coord_mode_check.pack(side=tk.LEFT, padx=(0, 8))
        self.window_mode_var = tk.BooleanVar(value=False)
        window_mode_check = ttk.Checkbutton(options_frame, text="В окне", variable=self.window_mode_var)
        window_mode_check.pack(side=tk.LEFT, padx=(0, 8))
        self.topmost_var = tk.BooleanVar(value=False)
        topmost_check = ttk.Checkbutton(options_frame, text="Поверх окон", variable=self.topmost_var, command=self.toggle_topmost)
        topmost_check.pack(side=tk.LEFT)
        
        window_frame = ttk.Frame(main_frame)
        window_frame.grid(row=3, column=0, pady=(1, 2), sticky=(tk.W, tk.E))
        
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

        # Перемещаю инструкцию ниже координат
        self.pick_point_info = ttk.Label(main_frame, text="", font=("Arial", 9, "bold"), foreground="#d32f2f")
        self.pick_point_info.grid(row=4, column=0, sticky=tk.W, pady=(0, 1))
        
        # Статус
        self.cps_label = ttk.Label(main_frame, text="Клики: 0", font=('Arial', 9))
        self.cps_label.grid(row=5, column=0, pady=1, sticky=tk.W)
        
        # Фрейм для пресетов
        preset_frame = ttk.LabelFrame(main_frame, text="Скорость", padding="2")
        preset_frame.grid(row=6, column=0, pady=2, sticky=(tk.W, tk.E))
        
        presets = [
            ("1 CPS", 1.0),
            ("10 CPS", 0.1),
            ("50 CPS", 0.02),
            ("100 CPS", 0.01),
            ("500 CPS", 0.002),
            ("MAX", 0)
        ]
        for i, (text, delay) in enumerate(presets):
            btn = ttk.Button(preset_frame, text=text, width=8, command=lambda d=delay: self.set_delay(d))
            btn.grid(row=i//3, column=i%3, pady=1, padx=1, sticky=(tk.W, tk.E))
        for col in range(3):
            preset_frame.columnconfigure(col, weight=1)
        
        # Фрейм для ручной настройки
        manual_frame = ttk.LabelFrame(main_frame, text="Своя скорость", padding="3")
        manual_frame.grid(row=7, column=0, pady=2, sticky=(tk.W, tk.E))
        manual_inner = ttk.Frame(manual_frame)
        manual_inner.pack(anchor=tk.CENTER, pady=2)
        ttk.Label(manual_inner, text="CPS:").pack(side=tk.LEFT, padx=(0, 2))
        self.cps_var = tk.StringVar(value="10")
        cps_entry = ttk.Entry(manual_inner, textvariable=self.cps_var, width=7)
        cps_entry.pack(side=tk.LEFT, padx=(0, 2))
        apply_btn = ttk.Button(manual_inner, text="OK", width=4, command=self.apply_manual_cps)
        apply_btn.pack(side=tk.LEFT)
        
        # Кнопка старт/стоп
        self.start_button = ttk.Button(main_frame, text="Старт/Стоп (F6)", command=self.toggle_clicking)
        self.start_button.grid(row=8, column=0, pady=2, sticky=(tk.W, tk.E))

        # --- Кнопка мыши ---
        self.button_var = tk.StringVar(value="left")
        button_frame = ttk.LabelFrame(main_frame, text="Кнопка", padding="2")
        button_frame.grid(row=9, column=0, pady=(1, 0), sticky=(tk.W, tk.E))
        ttk.Radiobutton(button_frame, text="Левая", variable=self.button_var, value="left").pack(side=tk.LEFT, padx=1)
        ttk.Radiobutton(button_frame, text="Правая", variable=self.button_var, value="right").pack(side=tk.LEFT, padx=1)
        ttk.Radiobutton(button_frame, text="Обе", variable=self.button_var, value="both").pack(side=tk.LEFT, padx=1)

        # Текущая скорость
        self.speed_label = ttk.Label(main_frame, text="Текущая скорость: 10 CPS", font=('Arial', 8))
        self.speed_label.grid(row=10, column=0, pady=1, sticky=tk.W)

        # Ограничители
        limit_frame = ttk.LabelFrame(main_frame, text="Ограничители", padding="3")
        limit_frame.grid(row=11, column=0, pady=(2, 0), sticky=(tk.W, tk.E))
        ttk.Label(limit_frame, text="Секунд:").pack(side=tk.LEFT, padx=2)
        self.timer_var = tk.StringVar(value="")
        ttk.Entry(limit_frame, textvariable=self.timer_var, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(limit_frame, text="Кликов:").pack(side=tk.LEFT, padx=2)
        self.click_limit_var = tk.StringVar(value="")
        ttk.Entry(limit_frame, textvariable=self.click_limit_var, width=7).pack(side=tk.LEFT, padx=2)

        # --- Нижний блок: by Desper ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=12, column=0, pady=(4, 0), sticky=(tk.E, tk.S))
        try:
            font_name = "Google Sans"
            self.desper_label = ttk.Label(bottom_frame, text="by Desper_i9", foreground="#1976d2", font=(font_name, 9))
        except Exception:
            self.desper_label = ttk.Label(bottom_frame, text="by Desper_i9", foreground="#1976d2", font=("Arial", 9))
        self.desper_label.pack(side=tk.LEFT, padx=(0, 5))
        self.site_label = ttk.Label(bottom_frame, text="gl-hf.ru", foreground="#1976d2", cursor="hand2", font=("Arial", 9, "underline"))
        self.site_label.pack(side=tk.LEFT)
        self.site_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://gl-hf.ru"))

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
        self.pick_point_info.config(text="Нажмите F8 для фиксации координат", foreground="#d32f2f", font=("Arial", 9, "bold"))
        keyboard.on_press_key("F8", self.save_mouse_position)
    
    def save_mouse_position(self, e=None):
        if not self.waiting_for_point:
            return
        x, y = pyautogui.position()
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        self.pick_point_info.config(text="", foreground="#1976d2", font=("Arial", 8))
        self.waiting_for_point = False
        keyboard.unhook_key("F8")
    
    def click_loop(self):
        click_time = 0
        start_time = time.time()
        clicks_done = 0
        timer_limit = None
        click_limit = None
        try:
            timer_limit = float(self.timer_var.get()) if self.timer_var.get() else None
        except ValueError:
            timer_limit = None
        try:
            click_limit = int(self.click_limit_var.get()) if self.click_limit_var.get() else None
        except ValueError:
            click_limit = None
        
        def check_limits():
            if timer_limit is not None and (time.time() - start_time) >= timer_limit:
                return True
            if click_limit is not None and clicks_done >= click_limit:
                return True
            return False
        
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
                    clicks_done += 1
                    if check_limits():
                        self.stop_clicking()
                        break
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
                    clicks_done += 1
                    if check_limits():
                        self.stop_clicking()
                        break
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
                    clicks_done += 1
                    if check_limits():
                        self.stop_clicking()
                        break
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