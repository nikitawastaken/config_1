import os
import zipfile
import yaml
import shutil
import tempfile
import tkinter as tk
from tkinter import scrolledtext

class ShellEmulator:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.current_dir = '/'
        self.temp_dir = tempfile.mkdtemp()
        self.fs_root = os.path.join(self.temp_dir, "fs")
        self.username = self.config['username']
        
        # Разархивируем виртуальную файловую систему во временную директорию
        with zipfile.ZipFile(self.config['fs_path'], 'r') as zip_ref:
            zip_ref.extractall(self.fs_root)
        
    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
    
    def prompt(self):
        return f"{self.username}@emulator:{self.current_dir}$ "
    
    def ls(self, path=None):
        # Если путь не указан, используем текущую директорию
        if path is None:
            path = self.current_dir

        # Преобразуем относительный путь в абсолютный
        new_path = os.path.normpath(os.path.join(self.current_dir, path))
        full_path = os.path.join(self.fs_root, new_path.lstrip('/'))

        # Проверяем, существует ли указанная директория
        if os.path.isdir(full_path):
            # Получаем содержимое директории, исключая скрытые файлы и папку __MACOSX
            items = os.listdir(full_path)
            return [item for item in items if not item.startswith('.') and item != '__MACOSX']
        else:
            raise FileNotFoundError(f"No such directory: {path}")
    
    def cd(self, path):
        if path == '/':
            self.current_dir = '/'
        else:
            new_path = os.path.normpath(os.path.join(self.current_dir, path))
            full_path = os.path.join(self.fs_root, new_path.lstrip('/'))
            if os.path.isdir(full_path):
                self.current_dir = new_path
            else:
                raise FileNotFoundError(f"No such directory: {path}")
    
    def echo(self, *args):
        return ' '.join(args)
    
    def chmod(self, mode, path):
        if not path.startswith('/'):
            path = os.path.join(self.current_dir, path)
        
        full_path = os.path.join(self.fs_root, path.lstrip('/'))
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"No such file or directory: {path}")
        os.chmod(full_path, int(mode, 8))
    
    def uname(self):
        return "UNIX-Like Emulator"
    
    def exit(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        return "Exiting shell emulator."

class ShellGUI:
    def __init__(self, root, shell):
        self.shell = shell
        self.root = root
        self.root.title("Shell Emulator GUI")
        
        # Поле для вывода текста
        self.output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20, width=60)
        self.output_text.pack(padx=10, pady=10)
        self.output_text.insert(tk.END, self.shell.prompt())
        self.output_text.configure(state=tk.DISABLED)  # Поле вывода только для чтения
        
        # Поле для ввода текста
        self.input_text = tk.Entry(root, width=60)
        self.input_text.pack(padx=10, pady=(0, 10))
        self.input_text.bind("<Return>", self.execute_command)  # Обработка нажатия Enter

    def execute_command(self, event):
        command = self.input_text.get().strip()
        self.input_text.delete(0, tk.END)
        
        # Вывод введенной команды в поле вывода
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, command + "\n")
        
        # Выполнение команды
        parts = command.split()
        if not parts:
            return
        cmd, *args = parts
        try:
            if cmd == "ls":
                try:
                    output = "\n".join(self.shell.ls(args[0] if args else None))
                except FileNotFoundError as e:
                    output = str(e)
            elif cmd == "cd":
                try:
                    self.shell.cd(args[0] if args else "/")
                    output = ""
                except FileNotFoundError as e:
                    output = str(e)
            elif cmd == "echo":
                output = self.shell.echo(*args)
            elif cmd == "chmod":
                if len(args) < 2:
                    output = "chmod: missing operand"
                else:
                    try:
                        self.shell.chmod(args[0], args[1])
                        output = ""
                    except FileNotFoundError as e:
                        output = str(e)
            elif cmd == "uname":
                output = self.shell.uname()
            elif cmd == "exit":
                output = self.shell.exit()
                self.root.quit()
            else:
                output = f"Command not found: {cmd}"
        except Exception as e:
            output = str(e)
        
        # Вывод результата в поле вывода
        if output:
            self.output_text.insert(tk.END, output + "\n")
        self.output_text.insert(tk.END, self.shell.prompt())
        self.output_text.configure(state=tk.DISABLED)
        self.output_text.see(tk.END)  # Прокрутка вниз

def main():
    config_path = "config.yaml"
    shell = ShellEmulator(config_path)
    
    # Создаем главное окно приложения
    root = tk.Tk()
    app = ShellGUI(root, shell)
    root.mainloop()

if __name__ == "__main__":
    main()