import os
import zipfile
import yaml
import tkinter as tk
from tkinter import scrolledtext


class ShellEmulator:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.current_dir = '/'
        self.fs_zip_path = self.config['fs_path']
        self.username = self.config['username']
        self.permissions = {}

        # Проверяем, что указанный архив существует
        if not os.path.exists(self.fs_zip_path):
            raise FileNotFoundError(f"Filesystem archive not found: {self.fs_zip_path}")

        # Открываем архив zip для работы
        self.zip_file = zipfile.ZipFile(self.fs_zip_path, 'r')
        self.fs_structure = self.zip_file.namelist()

        # Генерируем начальные права доступа
        self._initialize_permissions()

    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def prompt(self):
        return f"{self.username}@emulator:{self.current_dir}$ "

    def _resolve_path(self, path):
        if path == "/":
            return "/"
        elif path == "..":
            return os.path.dirname(self.current_dir.rstrip('/')) or '/'
        elif not path.startswith('/'):
            path = os.path.join(self.current_dir, path)
        return os.path.normpath(path).lstrip('/')

    def _initialize_permissions(self):
        for item in self.fs_structure:
            if not item.endswith('/'):
                self.permissions[item] = "rw-"

    def ls(self, path=None):
        if path is None:
            path = '/' + self.current_dir.lstrip('/')

        resolved_path = self._resolve_path(path)
        if not resolved_path.endswith('/'):
            resolved_path += '/'

        if resolved_path == '/':
            resolved_path = ''  # Путь к корню не должен содержать "/"

        # Проверяем, есть ли в архиве файлы или папки, соответствующие указанному пути
        contents = set()
        for item in self.fs_structure:
            # Сравниваем пути в архиве с текущей директорией
            if item.startswith(resolved_path) and item != resolved_path:
                sub_path = item[len(resolved_path):].split('/')[0]
                if sub_path and sub_path != "__MACOSX":  # Исключаем системные файлы
                    contents.add(sub_path)

        if contents:
            return sorted(contents)
        else:
            raise FileNotFoundError(f"No such directory: {path}")

    def cd(self, path):
        resolved_path = self._resolve_path(path)

        # Переход в корень
        if resolved_path == '/':
            self.current_dir = '/'
            return

        # Переход к родительской директории или другой директории
        if any(item.startswith(resolved_path.rstrip('/') + '/') for item in self.fs_structure):
            self.current_dir = resolved_path
        else:
            raise FileNotFoundError(f"No such directory: {path}")

    def echo(self, *args):
        return ' '.join(args)

    def chmod(self, mode, path):
        resolved_path = self._resolve_path(path)

        # Проверяем, существует ли файл в виртуальной файловой системе
        if resolved_path not in self.permissions:
            raise FileNotFoundError(f"No such file or directory: {path}")

        # Обновляем права доступа
        self.permissions[resolved_path] = mode

    def uname(self):
        return "UNIX-Like Emulator"

    def exit(self):
        self.zip_file.close()
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
        self.output_text.configure(state=tk.DISABLED)

        # Поле для ввода текста
        self.input_text = tk.Entry(root, width=60)
        self.input_text.pack(padx=10, pady=(0, 10))
        self.input_text.bind("<Return>", self.execute_command)

    def execute_command(self, event):
        command = self.input_text.get().strip()
        self.input_text.delete(0, tk.END)

        # Вывод введенной команды в поле вывода
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, command + "\n")

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

        if output:
            self.output_text.insert(tk.END, output + "\n")
        self.output_text.insert(tk.END, self.shell.prompt())
        self.output_text.configure(state=tk.DISABLED)
        self.output_text.see(tk.END)


def main():
    config_path = "config.yaml"
    shell = ShellEmulator(config_path)

    root = tk.Tk()
    app = ShellGUI(root, shell)
    root.mainloop()


if __name__ == "__main__":
    main()