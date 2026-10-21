"""Which of several readings does a take sound like? Score each candidate text by forced decoding.

    ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-03/force.py zh ns00-02 "…念腰腰零…" "…念一一零…"

Whisper's free transcript guesses words from context (it may write 一 for a clear yāo), so it cannot tell
a misread from a mishearing. Here every candidate is teacher-forced through Whisper medium on the same
audio, with no prompt, and the summed log-probabilities are compared. Candidates should differ only in
the word in question; use a common homophone for a rare character (腰 for 幺) so the text prior does not
decide. The best candidate is printed first, with how many nats behind each other one is.
"""
import sys
from pathlib import Path

import torch
import whisper

MEDIA = Path("/Users/yqin/repo/playground/lucas-academy-media")
_model = None


def model():
    global _model
    if _model is None:
        _model = whisper.load_model("medium", device="cpu")
    return _model


def scores(lang: str, wav: Path, candidates: list[str]) -> list[tuple[float, str]]:
    m = model()
    tok = whisper.tokenizer.get_tokenizer(m.is_multilingual, num_languages=m.num_languages, language=lang, task="transcribe")
    mel = whisper.log_mel_spectrogram(whisper.pad_or_trim(whisper.load_audio(str(wav))), n_mels=m.dims.n_mels)
    with torch.no_grad():
        features = m.embed_audio(mel[None])
        start = list(tok.sot_sequence_including_notimestamps)
        out = []
        for text in candidates:
            target = tok.encode((" " if lang == "en" else "") + text) + [tok.eot]
            tokens = torch.tensor([start + target])
            logp = m.logits(tokens[:, :-1], features).log_softmax(-1)[0, len(start) - 1:]
            out.append((logp.gather(-1, torch.tensor(target)[:, None]).sum().item(), text))
    return sorted(out, reverse=True)


def main():
    lang, cid, *candidates = sys.argv[1:]
    wav = Path(cid) if cid.endswith(".wav") else MEDIA / f"outputs/louise/{lang}/fun-informatics-03-v1/{cid}.wav"
    ranked = scores(lang, wav, candidates)
    best = ranked[0][0]
    for lp, text in ranked:
        print(f"{lp - best:8.2f}  {text}")


if __name__ == "__main__":
    main()
