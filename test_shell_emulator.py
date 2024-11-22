import unittest
import zipfile
import yaml
import os
from shell_emulator import ShellEmulator


class TestShellEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_fs_zip = 'test_fs.zip'
        cls.config_file = 'test_config.yaml'

        # Создаём zip-файл с тестовой файловой системой
        with zipfile.ZipFile(cls.test_fs_zip, 'w') as zip_ref:
            zip_ref.writestr('file1.txt', 'root file')  # Файл в корне
            zip_ref.writestr('folder/file2.txt', 'folder file')  # Файл в папке
            zip_ref.writestr('folder/subfolder/file3.txt', 'nested file')  # Файл в подкаталоге
            zip_ref.writestr('folder/subfolder/', '')  # Пустая папка

        # Создаём конфигурационный файл
        config_data = {
            'username': 'testuser',
            'fs_path': cls.test_fs_zip
        }
        with open(cls.config_file, 'w') as config_file:
            yaml.dump(config_data, config_file)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.test_fs_zip)
        os.remove(cls.config_file)

    def setUp(self):
        self.shell = ShellEmulator(self.config_file)

    def tearDown(self):
        try:
            self.shell.exit()
        except FileNotFoundError:
            pass

    def test_ls_root(self):
        expected = ['file1.txt', 'folder']
        result = self.shell.ls()
        self.assertEqual(result, expected)

    def test_ls_subdirectory(self):
        self.shell.cd('folder')
        expected = ['file2.txt', 'subfolder']
        result = self.shell.ls()
        self.assertEqual(result, expected)

    def test_cd_to_subfolder(self):
        self.shell.cd('folder/subfolder')
        self.assertEqual(self.shell.current_dir, 'folder/subfolder')

    def test_cd_to_parent(self):
        self.shell.cd('folder/subfolder')
        self.shell.cd('..')
        self.assertEqual(self.shell.current_dir, 'folder')

    def test_cd_root(self):
        self.shell.cd('folder')
        self.shell.cd('/')
        self.assertEqual(self.shell.current_dir, '/')

    def test_echo(self):
        result = self.shell.echo('Hello', 'world!')
        self.assertEqual(result, 'Hello world!')

    def test_uname(self):
        result = self.shell.uname()
        self.assertEqual(result, 'UNIX-Like Emulator')

    def test_chmod(self):
        self.shell.chmod('rwx', 'folder/file2.txt')
        self.assertEqual(self.shell.permissions['folder/file2.txt'], 'rwx')

    def test_chmod_absolute_path(self):
        self.shell.chmod('rw-', '/folder/file2.txt')
        self.assertEqual(self.shell.permissions['folder/file2.txt'], 'rw-')

    def test_ls_nonexistent_directory(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.ls('nonexistent')

    def test_cd_nonexistent_directory(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.cd('nonexistent')

    def test_chmod_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.chmod('rwx', 'nonexistent.txt')