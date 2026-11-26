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
    def approve(self,approve_unsure=False):
        args=argparse.Namespace(dir=str(self.folder),reviewer='owner',evidence='Owner approved this exact version.',approve_unsure=approve_unsure)
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
