from google import genai
import keyboard
import pyperclip
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import os
def load_api_key(filepath='apikey.txt'):
    """
    从指定文件中读取 API 密钥。
    1. 使用 with 上下文管理器确保文件自动关闭。  
    2. strip() 去掉首尾空白和换行符。  
    3. 捕获可能的文件不存在或读写错误。
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"API key file not found: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            key = f.read().strip()       # 读取全部内容并去除首尾空白:contentReference[oaicite:0]{index=0}
            if not key:
                raise ValueError("API key file is empty")
            return key
    except OSError as e:
        # 包括 IOError 在内的所有文件读写错误都会被捕获
        raise RuntimeError(f"Error reading API key file: {e}") from e
# —— 1. 初始化 Gemini 客户端 —— 
client = genai.Client(api_key=load_api_key())  # 替换成真实 API Key

# —— 2. 创建并隐藏主窗口 —— 
root = tk.Tk()
root.overrideredirect(True)
root.attributes('-alpha', 0.0)
root.geometry('1x1+0+0')

SENTINEL = "qoiwuenquwien982ueyn9cobq"
is_processing = False

# —— 3. AI 返回对话框 —— 
class ResultDialog(tk.Toplevel):
    def __init__(self, parent, content):
        super().__init__(parent)
        self.title("AI 返回")
        self.resizable(False, False)
        self.grab_set()  # 模态

        text = tk.Text(self, wrap="word", height=10, width=50)
        text.insert("1.0", content)
        text.config(state="disabled")
        text.pack(padx=10, pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(0,10))
        tk.Button(btn_frame, text="复制", width=10,
                  command=lambda: self._copy_and_close(content)
                 ).pack(side="left", padx=(0,5))
        tk.Button(btn_frame, text="确定", width=10,
                  command=self.destroy
                 ).pack(side="left")

        self.bind("<Return>", lambda e: self.destroy())
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) // 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) // 3
        self.geometry(f"+{x}+{y}")
        self.wait_window()

    def _copy_and_close(self, content):
        self.clipboard_clear()
        self.clipboard_append(content)
        self.destroy()


# —— 4. 在主线程中显示输入框 —— 
def show_input_and_start():
    global is_processing
    if is_processing:
        return
    user_input = simpledialog.askstring("补充输入", "请输入附加信息：")
    if user_input is None:
        return
    is_processing = True
    threading.Thread(target=do_ai_task, args=(user_input,), daemon=True).start()


# —— 5. 后台线程：剪贴板抓取 + AI 调用 —— 
def do_ai_task(user_input):
    global is_processing
    try:
        # 1) 获取当前剪贴板内容并模拟 Ctrl+C
        original = pyperclip.paste()
        pyperclip.copy(SENTINEL)
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.1)
        selection = pyperclip.paste()
        pyperclip.copy(original)
        if selection == SENTINEL:
            selection = ""

        # 2) 调用 Gemini 接口
        prompt = f"{selection}\n附加信息：{user_input}\n请基于以上内容，直接给出最终结果。"
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        # 3) 排回主线程弹出结果对话框
        root.after(0, lambda: ResultDialog(root, resp.text))

    except Exception as e:
        # 把异常信息绑定到 lambda 默认参数，避免作用域问题
        root.after(0, lambda err=e: messagebox.showerror("调用出错", str(err)))
    finally:
        is_processing = False


# —— 6. 绑定全局热键 —— 
# 按下 F9 时，不直接调用 simpledialog，而是排到主线程去做
keyboard.on_press_key('f9', lambda e: root.after(0, show_input_and_start))
# 按下 ESC 时退出
#keyboard.on_press_key('esc', lambda e: root.quit())

print("按 F9 → 补充输入 & 调用 AI → 弹出结果；按 ESC → 退出程序。")
root.mainloop()
