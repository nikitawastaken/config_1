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
