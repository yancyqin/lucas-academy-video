"""Actual ducking, whole-film coverage and music-evidence regression cases."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[2]))
import mix
import music_ducking


class MusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temp.name)
        cls.sr = 16000
        cls.t = np.arange(16 * cls.sr) / cls.sr
        cls.source = (.05 * np.sin(2 * np.pi * 220 * cls.t)).astype(np.float32)
        cls.voice = np.zeros_like(cls.source)
        cls.cues = [{'speech': {'start': a, 'end': b}} for a, b in [(2, 4), (6, 8), (10, 12)]]
        for c in cls.cues:
            a, b = c['speech'].values()
            on = (cls.t >= a) & (cls.t < b)
            cls.voice[on] = .1 * np.sin(2 * np.pi * 900 * cls.t[on])
        envpath = cls.folder / 'env.wav'
        music_ducking.envelope(cls.cues, 16, -26, envpath)
        envelope, rate = sf.read(envpath)
        cls.gain = np.interp(cls.t * rate, np.arange(len(envelope)), envelope)
        for n in ['voice', 'music', 'source']:
            (cls.folder / n).touch()
        cls.spec = {'music': True, 'format': {'audio_channels': 1}, 'lines': [{'start': 2, 'end': 12}],
                    'voice_audio': str(cls.folder / 'voice'), 'music_audio': str(cls.folder / 'music'),
                    'music_source': str(cls.folder / 'source')}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def check(self, music=None, source=None, played=None, channels=None, **changes):
        source = self.source if source is None else source
        music = source * self.gain if music is None else music
        arrays = {'voice': self.voice, 'music': music, 'source': source}
        with patch('common.decode_audio', side_effect=lambda p: arrays[Path(p).name]), \
             patch('common.ffprobe', side_effect=lambda p: {'streams': [{'codec_type': 'audio',
                   'channels': (channels or {}).get(Path(p).name, 1)}]}):
            return mix.ducking(self.voice + music if played is None else played, self.spec | changes)

    def codes(self, **kwargs):
        return {f['code'] for f in self.check(**kwargs)[1]}

    def test_correct_smooth_ducking_and_full_coverage(self):
        info, findings = self.check()
        self.assertEqual(findings, [])
        self.assertEqual(info['gaps'], 2)
        self.assertTrue(all(row['rise_db'] >= 6 for row in info['rows']))

    def test_flat_quiet_bed_still_fails_ducking(self):
        self.assertIn('mix.ducking_gap', self.codes(music=self.source * .12))

    def test_mono_voice_in_stereo_mix_uses_correct_analysis_route(self):
        music = self.source * self.gain
        info, found = self.check(music=music, played=self.voice * np.sqrt(2) + music,
                                 format={'audio_channels': 2}, channels={'music': 2})
        self.assertNotIn('mix.music_reconstruction', {f['code'] for f in found})
        self.assertAlmostEqual(info['voice_analysis_route_gain'], np.sqrt(2))

    def test_mono_music_in_stereo_mix_uses_correct_analysis_route(self):
        music = self.source * self.gain
        info, found = self.check(music=music, played=(self.voice + music) * np.sqrt(2),
                                 format={'audio_channels': 2})
        self.assertNotIn('mix.music_reconstruction', {f['code'] for f in found})
        self.assertAlmostEqual(info['music_analysis_route_gain'], np.sqrt(2))

    def test_inverted_ducking_fails(self):
        inverted = self.source * (.7 - self.gain)
        self.assertIn('mix.ducking_gap', self.codes(music=inverted))

    def test_unauthorized_music_hole_fails(self):
        music = self.source * self.gain
        music[(self.t > 4.2) & (self.t < 5.7)] = 0
        self.assertIn('mix.music_coverage', self.codes(music=music))

    def test_source_natural_rest_is_not_a_missing_bed(self):
        source = self.source.copy()
        source[(self.t > 4.2) & (self.t < 5.7)] = 0
        self.assertNotIn('mix.music_coverage', self.codes(source=source))

    def test_claimed_stem_not_in_final_mix_fails(self):
        self.assertIn('mix.music_reconstruction', self.codes(played=self.voice))

    def test_missing_stems_cannot_pass_with_caption_heuristic(self):
        self.assertIn('mix.music_evidence', self.codes(music_audio=None))

    def test_exception_needs_owner_evidence(self):
        self.assertIn('mix.music_exception', self.codes(music_exceptions=[{'start': 4, 'end': 6, 'reason': 'test'}]))

    def test_authorized_exception_is_limited_to_declared_span(self):
        music = self.source * self.gain
        music[(self.t > 4.2) & (self.t < 5.7)] = 0
        info, found = self.check(music=music, music_exceptions=[
            {'start': 4.2, 'end': 5.7, 'reason': 'Owner requested silence', 'owner_evidence': 'Owner: silence here.'}])
        self.assertNotIn('mix.music_coverage', {f['code'] for f in found})
        self.assertEqual(len(info['authorized_exceptions']), 1)
        music[(self.t > 8.2) & (self.t < 9.7)] = 0
        self.assertIn('mix.music_coverage', self.codes(music=music, music_exceptions=info['authorized_exceptions']))

    def test_composition_dynamics_do_not_hide_or_invent_ducking(self):
        source = self.source * np.where((self.t > 4) & (self.t < 6), .15, 1)
        self.assertNotIn('mix.ducking_gap', self.codes(source=source))
        self.assertIn('mix.ducking_gap', self.codes(source=source, music=source * .12))

    def test_paragraph_internal_pauses_use_actual_voice(self):
        cues = music_ducking.speech_cues(self.voice, self.sr)
        self.assertEqual(len(cues), 3)
        self.assertAlmostEqual(cues[1]['speech']['start'], 6, places=2)

    def test_quiet_speech_limiter_never_changes_voice_or_raises_music(self):
        voice = self.voice.copy()
        original = voice.copy()
        music = np.repeat(self.source[:, None], 2, axis=1)
        limited = music_ducking.limit_under_voice(music, voice, self.sr)
        np.testing.assert_array_equal(voice, original)
        self.assertTrue(np.all(np.abs(limited) <= np.abs(music) + 1e-8))
        core = (self.t > 2.5) & (self.t < 3.5)
        self.assertLess(np.sqrt(np.mean(limited[core] ** 2)), np.sqrt(np.mean(voice[core] ** 2)) * .11)


if __name__ == '__main__':
    unittest.main()
