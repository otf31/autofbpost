import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from textual.app import App
from textual.widgets import Button, Input, Label, Select

from configuration import Configuration
from main import Autofbpost
from history import History
from publish import Publish


class UIFlows(unittest.IsolatedAsyncioTestCase):
    async def test_dashboard_adapts_and_keeps_primary_action_accessible(self):
        with patch.object(Autofbpost, "on_load", lambda self: None):
            for size in [(80, 24), (120, 40)]:
                with self.subTest(size=size):
                    app = Autofbpost()
                    async with app.run_test(size=size) as pilot:
                        await pilot.pause()
                        menu = app.query_one("#buttons")
                        workspace = app.query_one("#workspace")
                        self.assertLessEqual(abs(menu.region.x * 2 + menu.region.width - (workspace.region.x * 2 + workspace.region.width)), 1)
                        self.assertEqual(app.query_one("#home").has_class("compact"), size[0] < 100)

                        for button in menu.query(Button):
                            self.assertLessEqual(button.region.bottom, size[1])
                            self.assertGreaterEqual(button.region.x, workspace.region.x)


    async def test_headers_without_section_bar_and_empty_states(self):
        with tempfile.TemporaryDirectory() as directory:
            config = dict(CHROME_BINARY_PATH=__file__, POSTS_FOLDER_PATH=directory, HEADLESS=False)
            with patch.object(Autofbpost, "on_load", lambda self: None), patch('configuration.load_configuration', return_value=config), patch('history.load_configuration', return_value=config), patch('publish.load_configuration', return_value=config):
                for size in [(80, 24), (120, 40)]:
                    app = Autofbpost()
                    async with app.run_test(size=size) as pilot:
                        app.push_screen(Configuration())
                        await pilot.pause()
                        self.assertFalse(app.screen.query('.workspace-nav'))
                        app.pop_screen()
                        app.push_screen(History())
                        await pilot.pause()
                        self.assertIsInstance(app.screen, History)
                        self.assertTrue(app.screen.query_one('#history-empty').display)
                        self.assertFalse(app.screen.query('.workspace-nav'))
                        app.pop_screen()
                        app.push_screen(Publish())
                        await pilot.pause()
                        self.assertIn('empty', str(app.screen.query_one('#preview-text', Label).render()))
                        self.assertTrue(app.screen.query_one('#start', Button).disabled)
                        app.pop_screen()
                        await pilot.pause()
                        self.assertEqual(len(app.screen_stack), 1)

    async def test_cancel_does_not_save_and_save_validates(self):
        with tempfile.TemporaryDirectory() as directory:
            config = dict(CHROME_BINARY_PATH=__file__, POSTS_FOLDER_PATH=directory, HEADLESS=False)
            with patch('configuration.load_configuration', return_value=config), patch('configuration.write_conf_file') as save:
                app = App(css_path=Path(__file__).resolve().parents[1] / "styles.tcss")
                async with app.run_test() as pilot:
                    app.push_screen(Configuration())
                    await pilot.pause()
                    await pilot.click('#save-button', offset=(1, 0))
                    await pilot.pause()
                    save.assert_called_once_with(config)
                    save.reset_mock()
                    app.push_screen(Configuration())
                    await pilot.pause()
                    app.screen.query_one('#pfp', Input).value = '/missing/posts'
                    await pilot.click('#save-button', offset=(1, 0))
                    await pilot.pause()
                    save.assert_not_called()
                    self.assertIn('existing', str(app.screen.query_one('#posts-error', Label).render()))
                    await pilot.click('.action-bar Button', offset=(1, 0))
                    await pilot.pause()
                    save.assert_not_called()
                    self.assertNotIsInstance(app.screen, Configuration)

    async def test_content_library_validates_while_typing(self):
        with tempfile.TemporaryDirectory() as directory:
            config = dict(CHROME_BINARY_PATH=__file__, POSTS_FOLDER_PATH=directory, HEADLESS=False)
            with patch('configuration.load_configuration', return_value=config), patch('configuration.write_conf_file') as save:
                app = App(css_path=Path(__file__).resolve().parents[1] / "styles.tcss")
                async with app.run_test() as pilot:
                    app.push_screen(Configuration())
                    await pilot.pause()
                    field = app.screen.query_one('#pfp', Input)
                    error = app.screen.query_one('#posts-error', Label)
                    field.focus()
                    await pilot.pause()
                    field.selection = (len(field.value), len(field.value))
                    await pilot.press('x')
                    await pilot.pause()
                    self.assertIn('existing', str(error.render()))
                    self.assertTrue(field.has_class('field-invalid'))
                    self.assertTrue(field.has_focus)
                    await pilot.press('backspace')
                    await pilot.pause()
                    self.assertEqual(str(error.render()), '')
                    self.assertTrue(field.has_class('field-valid'))
                    field.value = ''
                    await pilot.pause()
                    self.assertIn('cannot be empty', str(error.render()))
                    save.assert_not_called()

    async def test_preview_validation_and_recheck(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            post = root / 'Example'
            post.mkdir()
            config = dict(CHROME_BINARY_PATH=__file__, POSTS_FOLDER_PATH=directory, HEADLESS=False)
            with patch('publish.load_configuration', return_value=config), patch.object(Publish, 'start_process') as start:
                app = App(css_path=Path(__file__).resolve().parents[1] / "styles.tcss")
                async with app.run_test(size=(120, 40)) as pilot:
                    screen = Publish()
                    app.push_screen(screen)
                    await pilot.pause()
                    screen.query_one(Select).value = 'Example'
                    await pilot.pause()
                    self.assertEqual(screen.query_one(Select).value, 'Example')
                    self.assertTrue(screen.query_one('#start', Button).disabled)
                    self.assertTrue(screen.validation_errors)
                    (post / 'images').mkdir()
                    (post / 'images' / 'photo.jpg').write_bytes(b'example')
                    (post / 'descriptions').mkdir()
                    for index in range(3):
                        (post / 'descriptions' / f'{index}.txt').write_text(f'Description {index}')
                    (post / 'filters.txt').write_text('test')
                    (root / 'groups.csv').write_text('Name;URL;Filters\nExample group;https://facebook.com/groups/123;test\n')
                    await pilot.click('#recheck', offset=(1, 0))
                    await pilot.pause()
                    self.assertTrue(screen.post_ready)
                    self.assertFalse(screen.query_one('#start', Button).disabled)
                    self.assertIn('Example group', str(screen.query_one('#preview-groups', Label).render()))
                    start.assert_not_called()
                    (post / 'filters.txt').write_text('unmatched')
                    await pilot.click('#recheck', offset=(1, 0))
                    await pilot.pause()
                    self.assertFalse(screen.post_ready)
                    self.assertTrue(screen.query_one('#start', Button).disabled)


if __name__ == '__main__':
    unittest.main()
