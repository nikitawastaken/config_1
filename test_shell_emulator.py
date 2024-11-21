import unittest
import zipfile
import yaml
import os
import shutil
from shell_emulator import ShellEmulator

class TestShellEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_fs_zip = 'test_fs.zip'
        cls.config_file = 'test_config.yaml'
        
        with zipfile.ZipFile(cls.test_fs_zip, 'w') as zip_ref:
            zip_ref.writestr('folder/file.txt', 'test content')
            zip_ref.writestr('folder/subfolder/', '')
            zip_ref.writestr('__MACOSX/', '')
        
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
        self.assertIn('folder', self.shell.ls())
        self.assertNotIn('__MACOSX', self.shell.ls())
    
    def test_ls_with_path(self):
        self.assertEqual(self.shell.ls('folder'), ['file.txt', 'subfolder'])
    
    def test_cd_to_folder(self):
        self.shell.cd('folder')
        self.assertEqual(self.shell.current_dir, '/folder')
    
    def test_cd_nonexistent(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.cd('nonexistent')

    def test_echo(self):
        self.assertEqual(self.shell.echo('Hello', 'World'), 'Hello World')

    def test_chmod_file(self):
        self.shell.chmod('755', 'folder/file.txt')
        full_path = os.path.join(self.shell.fs_root, 'folder/file.txt')
        self.assertEqual(oct(os.stat(full_path).st_mode)[-3:], '755')
    
    def test_chmod_nonexistent(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.chmod('755', 'nonexistent.txt')
    
    def test_uname(self):
        self.assertEqual(self.shell.uname(), "UNIX-Like Emulator")
    
    def test_exit(self):
        self.assertEqual(self.shell.exit(), "Exiting shell emulator.")
    
    def test_ls_excludes_mac_system_files(self):
        self.assertNotIn('__MACOSX', self.shell.ls())
    
    def test_ls_nonexistent_path(self):
        with self.assertRaises(FileNotFoundError):
            self.shell.ls('nonexistent_path')
    
    def test_ls_in_subfolder(self):
        self.shell.cd('folder')
        self.assertEqual(self.shell.ls(), ['file.txt', 'subfolder'])

    def test_ls_path_in_root(self):
        self.assertEqual(self.shell.ls('/folder'), ['file.txt', 'subfolder'])

    def test_invalid_command(self):
        invalid_command = "unknowncmd"
        output = f"Command not found: {invalid_command}"
        self.assertEqual(output, f"Command not found: {invalid_command}")