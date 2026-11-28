"""Regression cases: ASR agreement is not human listening; old approvals cannot pass changed exports."""
import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import qa
from common import sha256,FAIL,UNSURE


class FinalReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name).resolve()
        self.video=self.folder/'film.mp4';self.video.write_bytes(b'final export')
        self.caption=self.folder/'film.srt';self.caption.write_text('approved captions')
        self.spec=self.folder/'spec.json';self.spec.write_text(json.dumps({'kind':'narrated','music':False,'lines':[],
             'captions':[{'path':str(self.caption),'lang':'en'}]}))
        self.report={'policy_revision':qa.POLICY_REVISION,'listening_required':True,'video':str(self.video),
            'sha256':sha256(self.video),'audio':None,'audio_sha256':None,'spec':str(self.spec),
            'spec_sha256':sha256(self.spec),'input_sha256':{str(self.caption):sha256(self.caption)},
            'items':[],'incomplete':[],'skipped':[]}
        self.save()

    def tearDown(self):self.temp.cleanup()
    def save(self):(self.folder/'report.json').write_text(json.dumps(self.report))
    def approve(self,approve_unsure=False,accept_asr_only=False):
        args=argparse.Namespace(dir=str(self.folder),reviewer='owner',evidence='Owner approved this exact version.',approve_unsure=approve_unsure,accept_asr_only=accept_asr_only)
        with contextlib.redirect_stdout(io.StringIO()):return qa.cmd_final_review(args)
    def gate(self):qa.require(self.video,out=str(self.folder))

    def test_clean_asr_without_listening_does_not_pass(self):
        with self.assertRaises(SystemExit):self.gate()
        self.assertEqual(self.approve(),0);self.gate()

    def test_changed_export_invalidates_approval(self):
        self.approve();self.video.write_bytes(b'new voice take')
        with self.assertRaises(SystemExit):self.gate()
        with self.assertRaises(SystemExit):self.approve()

    def test_changed_caption_and_spec_require_recheck(self):
        self.approve();self.caption.write_text('new captions')
        with self.assertRaises(SystemExit):self.gate()
        with self.assertRaises(SystemExit):self.approve()
        self.caption.write_text('approved captions');self.spec.write_text('{}')
        with self.assertRaises(SystemExit):self.gate()

    def test_changed_music_stem_or_source_requires_recheck(self):
        for key in ('music_audio', 'music_source'):
            music = self.folder / (key + '.wav')
            music.write_bytes(b'checked music')
            spec = json.loads(self.spec.read_text())
            spec[key] = str(music)
            self.spec.write_text(json.dumps(spec))
            self.report['spec_sha256'] = sha256(self.spec)
            self.report['input_sha256'][str(music)] = sha256(music)
            self.save()
            self.approve()
            self.gate()
            music.write_bytes(b'changed music')
            with self.assertRaises(SystemExit):self.gate()
            music.write_bytes(b'checked music')

    def test_owner_approval_cannot_waive_failures(self):
        self.report['items']=[dict(verdict=FAIL,key='wrong.number',code='narration.number',title='Wrong number',detail='')];self.save()
        self.assertEqual(self.approve(True),2)
        with self.assertRaises(SystemExit):self.gate()

    def test_explicit_whole_version_approval_resolves_unsure(self):
        self.report['items']=[dict(verdict=UNSURE,key='pronunciation',code='narration.line',title='Listen to ending',detail='')];self.save()
        self.assertEqual(self.approve(True),0);self.gate()

    def test_old_policy_report_is_rejected(self):
        self.report.pop('policy_revision');self.save()
        with self.assertRaises(SystemExit):self.gate()

    def test_explicit_human_asr_adjudication_keeps_original_finding(self):
        self.report['items']=[dict(verdict=FAIL,key='asr.words',code='narration.line',title='ASR spelling dispute',detail='',
            problems=[dict(verdict=FAIL,code='narration.text')])];self.save()
        self.assertEqual(self.approve(True),2)
        self.assertEqual(self.approve(True,True),0);self.gate()
        self.assertEqual(json.loads((self.folder/'report.json').read_text())['items'][0]['verdict'],FAIL)

    def test_asr_adjudication_does_not_accept_numbers_or_media_failures(self):
        for code in ['narration.number','narration.negation','picture.freeze','format.audio']:
            self.report['items']=[dict(verdict=FAIL,key=code,code='narration.line',title='Hard failure',detail='',
                problems=[dict(verdict=FAIL,code=code)])];self.save()
            self.assertEqual(self.approve(True,True),2)
            with self.assertRaises(SystemExit):self.gate()

    def test_extra_track_approval_is_not_main_track_approval(self):
        alt=self.folder/'zh.m4a';alt.write_bytes(b'Chinese track')
        self.report.update(audio=str(alt),audio_sha256=sha256(alt));self.save();self.approve()
        qa.require(self.video,out=str(self.folder),audio=alt)
        with self.assertRaises(SystemExit):self.gate()

    def test_mono_requires_explicit_spec_and_preserves_default(self):
        import fmt
        facts={'streams':[{'codec_type':'audio','codec_name':'aac','sample_rate':'48000','channels':1}],
               'format':{'duration':'10'}}
        with patch.object(fmt,'ffprobe',return_value=facts):
            self.assertTrue(fmt.audio_file(Path('zh.m4a'),10)[1])
            self.assertFalse(fmt.audio_file(Path('zh.m4a'),10,channels=1)[1])

    def test_final_review_cli_is_available(self):
        result=subprocess.run([sys.executable,str(Path(qa.__file__)),'final-review','--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('--approve-unsure',result.stdout)


if __name__=='__main__':unittest.main()
