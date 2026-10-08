"""Verify separate Chinese retake candidates before replacing a production WAV."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import time
from pathlib import Path

import whisper

spec=importlib.util.spec_from_file_location("fi02_check",Path(__file__).with_name("check.py"))
check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--watch",action="store_true");ap.add_argument("--cached",action="store_true");args=ap.parse_args()
    expected=json.loads((check.ROOT / "public/fun-informatics-02/narration/zh.json").read_text())["lines"]
    by_id={line["id"]:line for line in expected}
    script=check.ROOT / "out/fun-informatics-02/research/narration-retakes.json"
    candidates=json.loads(script.read_text())["lines"]
    directory=check.ROOT / "out/fun-informatics-02/retakes"
    cache_path=directory / "candidate-check.json"
    cache=json.loads(cache_path.read_text()) if args.cached else {}
    done={};model=check.JoinedLatinWords(whisper.load_model("medium",device="cpu")) if not args.cached else None
    check.shared.units=check.units
    while True:
        for line in candidates:
            cid=line["id"].rsplit("-r",1)[0]
            path=directory / "candidates" / (line["id"]+".wav")
            if line["id"] in done or not path.exists() or time.time()-path.stat().st_mtime<1: continue
            prompt="以下是普通话科普旁白，术语：冗余、噪声、信息、Claude、克劳德、界、代、上、人、栏杆。"
            if args.cached:
                class CachedWords:
                    def transcribe(self,*a,**k): return {"segments":[{"words":cache[line["id"]]["analysis"]["_cut"]["words"]}]}
                result=check.shared.analyse(check.JoinedLatinWords(CachedWords()),path,by_id[cid]["text"],"zh",prompt)
            else:
                result=check.shared.analyse(model,path,by_id[cid]["text"],"zh",prompt)
            if result["extra"] or result["odd"]:
                trimmed=path.with_name(path.stem+".trimmed.wav")
                if check.shared.cut_edges(path,result,trimmed) or check.trim_unmatched_tail(path,result,trimmed):
                    if model is None: model=check.JoinedLatinWords(whisper.load_model("medium",device="cpu"))
                    shorter=check.shared.analyse(model,trimmed,by_id[cid]["text"],"zh","普通话科普旁白。术语：冗余、噪声、信息、备份。")
                    print(f"{cid} trimmed: {shorter['score']:.3f}, extras={shorter['extra']}, unmatched={shorter['odd']}",flush=True)
                    # Removing an untranscribed tail can slightly change ASR
                    # spelling. Require a complete, clean take rather than a
                    # higher spelling score than the contaminated candidate.
                    if shorter["score"]>=.9 and not shorter["extra"] and not shorter["odd"]:
                        path,result=trimmed,shorter
            report=json.loads(check.OUT.read_text())["cues"]
            original=report[cid]
            previous=original["analyses"].get("medium",original["analyses"].get("small"))
            better=result["score"]>=.9 and not result["extra"] and not result["odd"] and result["score"]>previous["score"]
            already=hashlib.sha256((check.VOICES / (cid+".wav")).read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest()
            done[line["id"]]={"analysis":result,"installed":better or already}
            if better:
                production=check.VOICES / (cid+".wav")
                actual=hashlib.sha256(production.read_bytes()).hexdigest()
                if actual!=original["sha256"]: raise SystemExit(f"{cid}: changed during candidate check")
                backup=directory / (cid+".original-"+actual[:8]+".wav")
                shutil.copy2(production,backup);shutil.copy2(path,production)
                report[cid]={"sha256":hashlib.sha256(production.read_bytes()).hexdigest(),"spoken":by_id[cid]["text"],"analyses":{"medium":result},"repair":{"operation":"verified Chinese retake, approved words unchanged","original":str(backup.relative_to(check.ROOT)),"originalSha256":actual,"candidate":str(path.relative_to(check.ROOT))}}
                check.save(report,expected)
            (directory / "candidate-check.json").write_text(json.dumps(done,ensure_ascii=False,indent=2)+"\n")
            print(f"{line['id']}: {result['score']:.3f}, {'installed' if better else 'already installed' if already else 'kept original'}: {result['heard']}",flush=True)
        if len(done)==len(candidates) or not args.watch: break
        time.sleep(5)


if __name__=="__main__": main()
