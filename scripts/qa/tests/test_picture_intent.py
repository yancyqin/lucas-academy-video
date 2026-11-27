"""Intent can qualify camera estimates, but cannot hide black frames or frozen footage."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import picture


class PictureIntentTests(unittest.TestCase):
    def stats(self):
        n = 120
        shift = np.zeros((n, 2))
        shift[45, 0] = 12
        shift[46, 0] = -12
        return dict(fps=30, px1920=2, size=[960, 540], regions=[], luma=np.full(n, 120.),
                    lstd=np.full(n, 20.), mad=np.zeros((n, 4)), shift=shift, conf=np.ones(n), fine=np.ones(n))

    def findings(self, camera=True, stats=None):
        spec = dict(shots=[dict(id='foreground', start=0, end=4, kind='footage', camera_motion=camera)])
        with patch.object(picture, 'measure', return_value=stats or self.stats()):
            return picture.check(Path('film.mp4'), spec)[1]

    def test_default_camera_jump_stays_failure(self):
        self.assertTrue(any(f['code'] == 'picture.jump' and f['verdict'] == 'fail' for f in self.findings()))

    def test_declared_foreground_estimate_requires_review(self):
        self.assertTrue(any(f['code'] == 'picture.jump' and f['verdict'] == 'unsure'
                            for f in self.findings('review')))

    def test_intent_does_not_hide_black(self):
        stats = self.stats()
        stats['luma'][:] = 16
        stats['lstd'][:] = 0
        self.assertTrue(any(f['code'] == 'picture.black' and f['verdict'] == 'fail'
                            for f in self.findings(False, stats)))

    def test_intent_does_not_hide_freeze(self):
        stats = self.stats()
        stats['fine'][:] = 0
        self.assertTrue(any(f['code'] == 'picture.freeze' and f['verdict'] == 'fail'
                            for f in self.findings(False, stats)))


if __name__ == '__main__':
    unittest.main()
