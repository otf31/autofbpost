import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common_functions import (
    configuration_path,
    get_locales_fb_strings,
    load_configuration,
    write_conf_file,
)
from constants import APP_NAME, CONFIG_FILE_PATH, DEFAULT_CONFIG
from publish import get_descriptions, get_images, read_filters, read_groups
from storage import local_files, matching_files


class StorageTests(unittest.TestCase):
    def test_existing_config_location_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('common_functions.user_config_dir', return_value=directory) as location:
                self.assertEqual(configuration_path(), str(Path(directory) / CONFIG_FILE_PATH))
                location.assert_called_with(APP_NAME, appauthor=None)
                self.assertEqual(load_configuration(), DEFAULT_CONFIG)
                config = dict(DEFAULT_CONFIG, POSTS_FOLDER_PATH='Contenido / Perú')
                write_conf_file(config)
                self.assertEqual(load_configuration(), config)
                for invalid in ['{invalid', '{}', 'null']:
                    Path(configuration_path()).write_text(invalid, encoding='utf-8')
                    self.assertEqual(load_configuration(), DEFAULT_CONFIG)
                self.assertEqual(json.loads(Path(configuration_path()).read_text()), DEFAULT_CONFIG)

    def test_local_content_unicode_patterns_and_natural_sort(self):
        with tempfile.TemporaryDirectory(prefix='contenido ñ ') as directory:
            root = Path(directory)
            for name in ['image10.png', 'image2.jpg', 'image1.jpeg', 'ignore.gif']:
                (root / name).write_bytes(b'image')
            (root / 'folder.png').mkdir()
            images = get_images(directory)
            self.assertEqual([Path(path).name for path in images], ['image1.jpeg', 'image2.jpg', 'image10.png'])
            self.assertTrue(all(Path(path).is_absolute() for path in images))
            (root / 'description.txt').write_text('  ¡Hola, Perú!\n', encoding='utf-8')
            self.assertEqual(get_descriptions(directory), ['¡Hola, Perú!'])
            self.assertEqual(len(matching_files(directory, ['*.png'])), 1)
            filters = root / 'filters.txt'
            filters.write_text(' MÚSICA, tecnología ', encoding='utf-8')
            self.assertEqual(read_filters(str(filters)), ['música', 'tecnología'])
            groups = root / 'groups.csv'
            groups.write_text('Name;URL;Filters\nMúsica;https://example.com/a;música\nOtro;https://example.com/b;otro\n', encoding='utf-8')
            self.assertEqual(read_groups(str(groups), ['música']), [['Música', 'https://example.com/a', 'música']])
            self.assertFalse(local_files.exists(str(root / 'missing')))
            with self.assertRaises(FileNotFoundError):
                matching_files(str(root / 'missing'))

    def test_locales_remain_readable(self):
        self.assertIn('publish', get_locales_fb_strings('es'))
        self.assertIn('publish', get_locales_fb_strings('en'))
