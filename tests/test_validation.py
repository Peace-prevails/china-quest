import copy
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from common import manifest, read, write, ROOT
from validate_story import validate_assets
from story import Story


class ValidationTests(unittest.TestCase):
    def test_reference_cycles_rejected(self):
        data=manifest()
        data['assets'][1]['reference_assets']=['BG03_COUNTER']
        with self.assertRaisesRegex(ValueError,'cycle'):
            validate_assets(data)

    def test_unknown_reference_rejected(self):
        data=manifest();data['assets'][0]['reference_assets']=['MISSING']
        with self.assertRaisesRegex(ValueError,'Unknown reference'):
            validate_assets(data)

    def test_save_resume_and_isolated_replay(self):
        story=Story();story.current='end';story.state.update(item_selected='zhajiang',spicy=False,wants_water=True,inheritance_response='reject',trust_alignment='distrust_both')
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/'save.json';story.save(path)
            loaded=Story();loaded.load(path)
            self.assertEqual(story.state,loaded.state)
            replay=loaded.replay_exploration()
            replay.state['explored_hotspots'].append('door')
            self.assertEqual(loaded.current,'end')
            self.assertEqual(replay.current,'explore')
            self.assertEqual(replay.learning['replay_count'],1)
            self.assertEqual(loaded.state['explored_hotspots'],[])
            self.assertEqual(read(path)['current'],'end')

    def test_bad_save_and_choice_rejected(self):
        story=Story()
        with self.assertRaises(ValueError):story.choose('missing')
        with tempfile.TemporaryDirectory() as temp:
            path=pathlib.Path(temp)/'save.json';story.save(path)
            data=read(path);data['story']['wants_water']='false';write(path,data)
            with self.assertRaises(ValueError):story.load(path)

    def test_help_and_envelope_rewards(self):
        story=Story()
        for text in ['面馆在哪里？','我听不懂','往前走']:
            choice=next(c for c in story.view()['choices'] if c['zh']==text)
            story.choose(choice['id'])
        self.assertTrue(story.state['asked_directions'])
        self.assertTrue(story.state['used_help_location'])
        self.assertEqual(story.learning['hint_usage']['S0'],1)
        story.current='billion'
        self.assertEqual(story.view()['conditional_lines'],[])
        story.state['saw_red_envelope']=True
        self.assertEqual(len(story.view()['conditional_lines']),1)
