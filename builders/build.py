#!/usr/bin/env python3
"""Builds the puzzle box.

Each compartment's markup and logic is encrypted with a key derived from the
PREVIOUS compartment's answer (PBKDF2-HMAC-SHA256, 200k iterations, AES-256-GCM).
Nothing beyond the compartment you are standing in exists in readable form in
the output file. A wrong answer fails GCM authentication — there is no
comparison to patch out.
"""
import base64
import json
import os
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from levels import LEVELS, FLAG, CLOSING  # noqa: E402
from part2 import build_chain, PART2_FLAG  # noqa: E402

ITER = 200_000
SEED = "himitsu"          # opens compartment one; deliberately public
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "puzzle-box.html")


def derive(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER)
    return kdf.derive(passphrase.encode())


def seal(passphrase: str, obj) -> str:
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(derive(passphrase, salt)).encrypt(iv, json.dumps(obj).encode(), None)
    return base64.b64encode(salt + iv + ct).decode()


def build() -> str:
    boxes = []
    for i, lv in enumerate(LEVELS):
        key = SEED if i == 0 else LEVELS[i - 1]["answer"]
        boxes.append(seal(key, {
            "n": lv["n"], "t": lv["title"], "e": lv["engraved"],
            "h": lv["html"], "j": lv["js"],
        }))
    # part two: notes and hints are each sealed under their own line's code,
    # and the whole paper is sealed under the part-one answer.
    codes, notes, hints = build_chain()
    paper = seal(LEVELS[-1]["answer"], {
        "intro": INTRO,
        "c1": codes[0],
        "layers": [seal(codes[i], {"note": notes[i], "hint": hints[i]})
                   for i in range(len(notes))],
        "vault": seal(codes[-1], {"flag": PART2_FLAG}),
    })
    vault = seal(LEVELS[-1]["answer"], {"flag": FLAG, "close": CLOSING})
    return TEMPLATE.replace("__BOXES__", json.dumps(boxes)) \
                   .replace("__VAULT__", json.dumps(vault)) \
                   .replace("__PAPER__", json.dumps(paper)) \
                   .replace("__ITER__", str(ITER)) \
                   .replace("__SEED__", json.dumps(SEED))


INTRO = (
    "Folded into eight and wedged flat under the base plate — the works record "
    "for this unit, still in the transcriber's hand.\n\n"
    "It is one message written down ten times. Line one is how it came off the "
    "roll. Every line below it is the plaintext of the line above, and the last "
    "line is what the whole thing was hiding.\n\n"
    "Nine steps, nine ways the works got it wrong. Each one is described in "
    "full — the scheme is not the secret. The mistake in it is.\n\n"
    "Every record carries the tag NF~ at the front. That tag is how you know a "
    "decode landed, and once it will be the entire break."
)

CSS = r"""
:root{
  --void:#08080a; --panel:#111114; --raise:#17171c; --slot:#0c0c0f;
  --edge:#26262e; --line:#33333d;
  --text:#e9e9ee; --dim:#7e7e8c; --faint:#4a4a56;
  --violet:#7d6cff; --cyan:#3fe0d0; --coral:#ff5f6d; --lime:#b6ff2e;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{
  -webkit-tap-highlight-color:transparent;
  background:
    radial-gradient(90% 70% at 50% -20%, #1a1a22 0%, var(--void) 62%, #050506 100%);
  color:var(--text);
  font:16px/1.6 "Helvetica Neue",Inter,system-ui,-apple-system,sans-serif;
  display:flex; align-items:center; justify-content:center; padding:28px 16px;
  -webkit-font-smoothing:antialiased;
}
.box{width:100%;max-width:660px}

/* ---- wordmark ------------------------------------------------------ */
.brand{text-align:center;margin:0 0 22px}
.wordmark{margin:0;color:var(--lime);
  font:800 clamp(38px,13vw,72px)/.9 "Helvetica Neue",Inter,sans-serif;
  letter-spacing:-.055em;text-shadow:0 0 46px #b6ff2e38}
.wordmark i{font-style:normal;color:#5c7f19}
.tag{margin:10px 0 0;color:var(--dim);font-size:13px;letter-spacing:.16em;
  text-transform:lowercase}

/* ---- tumbler rail -------------------------------------------------- */
.rail{display:flex;gap:5px;justify-content:center;margin-bottom:20px}
.tumbler{width:100%;max-width:34px;height:3px;border-radius:99px;background:var(--edge)}
.tumbler.set{background:var(--violet);box-shadow:0 0 12px #7d6cff70}

/* ---- carcase ------------------------------------------------------- */
.carcase{
  position:relative;background:var(--panel);
  background-image:repeating-linear-gradient(90deg,
    #ffffff05 0 1px, transparent 1px 3px);
  border:1px solid var(--edge);border-radius:10px;
  box-shadow:0 30px 70px -30px #000, inset 0 1px 0 #ffffff0a;
  padding:32px 32px 0;
}
.carcase::after{content:"";position:absolute;inset:0;border-radius:10px;
  pointer-events:none;box-shadow:inset 0 0 90px #00000060}

.compartment{font:500 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;
  letter-spacing:.18em;color:var(--violet);margin-bottom:8px}
#title{font:600 29px/1.15 "Helvetica Neue",Inter,sans-serif;margin:0 0 12px;
  letter-spacing:-.02em}
.engraved{color:var(--dim);margin:0 0 26px;max-width:54ch;font-size:15px}

.stage{min-height:220px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:16px;padding:8px 0 30px;text-align:center}
.stage-hint{color:var(--dim);font-size:14px;margin:6px 0 0;max-width:46ch}

/* ---- keyway -------------------------------------------------------- */
.keyway{display:flex;margin:0 -32px;border-top:1px solid var(--edge);
  background:#00000045;border-radius:0 0 10px 10px;overflow:hidden}
.keyway input{
  flex:1;background:transparent;border:0;outline:0;color:var(--text);
  font:400 16px/1 ui-monospace,Menlo,monospace;letter-spacing:.12em;padding:19px 22px}
.keyway input:focus-visible{box-shadow:inset 2px 0 0 var(--violet)}
.keyway input::placeholder{color:var(--faint);letter-spacing:.04em;
  font-family:"Helvetica Neue",sans-serif}
.keyway button{background:transparent;border:0;border-left:1px solid var(--edge);
  color:var(--violet);font:500 14px "Helvetica Neue",sans-serif;letter-spacing:.04em;
  padding:0 26px;cursor:pointer;transition:background .16s,color .16s}
.keyway button:hover{background:#7d6cff1a;color:#a79bff}
.keyway.wrong{animation:shake .34s}
.verdict{min-height:22px;text-align:center;font-size:14px;color:var(--coral);
  margin:14px 0 0}
.verdict.good{color:var(--cyan)}

/* ---- collected keys ------------------------------------------------ */
.ring{margin:20px 0 0;display:flex;flex-wrap:wrap;gap:6px;justify-content:center}
.ring span{font:400 11px/1 ui-monospace,Menlo,monospace;color:var(--dim);
  border:1px solid var(--edge);border-radius:99px;padding:6px 11px;letter-spacing:.08em}

/* ---- 1 lid --------------------------------------------------------- */
.lid-btn{background:var(--raise);color:var(--text);border:1px solid var(--line);
  border-radius:6px;padding:14px 32px;font:500 15px "Helvetica Neue",sans-serif;
  cursor:pointer;transition:border-color .16s}
.lid-btn:hover{border-color:var(--faint)}
.lid-note{color:var(--dim);font-size:14px;min-height:20px;margin-top:12px}
.rivets{display:flex;gap:56px;margin-top:26px}
.rivet{width:14px;height:14px;border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#4b4b57,#1a1a20);
  box-shadow:inset 0 1px 1px #ffffff1a;position:relative}
.rivet[data-rivet]{cursor:pointer;touch-action:none;-webkit-touch-callout:none;
  user-select:none;-webkit-user-select:none}
.rivet[data-rivet]::before{content:"";position:absolute;inset:-16px}
.rivet.pressing::after{content:"";position:absolute;inset:-6px;border-radius:50%;
  border:1px solid var(--violet);opacity:calc(.2 + var(--fill,0)*.8);
  transform:scale(calc(1 + var(--fill,0)*.3))}
.rivet.sunk{background:var(--violet);box-shadow:0 0 18px #7d6cff90}
.shudder{animation:shake .3s}

/* ---- 2 plate ------------------------------------------------------- */
.stage-plate{position:relative;width:300px;height:130px}
.plate-bed{position:absolute;inset:0;background:var(--slot);border-radius:6px;
  display:flex;align-items:center;padding-left:16px;overflow:hidden;box-shadow:inset 0 0 30px #000}
.plate-word{font:400 clamp(14px,4.6vw,19px) ui-monospace,Menlo,monospace;
  color:var(--cyan);letter-spacing:.1em}
.brass-plate{position:absolute;inset:0;width:58%;-webkit-user-select:none;
  user-select:none;-webkit-touch-callout:none;cursor:grab;touch-action:none;
  background:linear-gradient(150deg,#3a3a44,#1e1e25 55%,#2f2f38);
  border:1px solid var(--line);border-radius:6px;
  box-shadow:0 6px 20px #000a,inset 0 1px 0 #ffffff18;
  display:flex;align-items:center;justify-content:center}
.brass-plate:active{cursor:grabbing}
.keyhole{width:22px;height:38px;background:#08080a;
  clip-path:polygon(50% 0,78% 14%,78% 40%,68% 100%,32% 100%,22% 40%,22% 14%)}
.plate-grip{position:absolute;right:10px;top:50%;transform:translateY(-50%);
  width:2px;height:44px;background:#ffffff14;box-shadow:4px 0 0 #ffffff14,-4px 0 0 #ffffff14}

/* ---- 3 grain ------------------------------------------------------- */
.grain-text{-webkit-user-select:text;user-select:text;max-width:50ch;text-align:left;color:var(--dim);line-height:1.9;font-size:15px}
.ghost{color:transparent}
.ghost::selection{background:#7d6cff4d;color:var(--cyan)}
.ghost.lit{color:var(--cyan);text-shadow:0 0 18px #3fe0d060}

/* ---- 4 pins -------------------------------------------------------- */
.pin-row{display:flex;gap:6px}
.pin{background:none;border:0;cursor:pointer;padding:8px 7px;display:flex;
  flex-direction:column;align-items:center;transition:transform .16s;
  -webkit-tap-highlight-color:transparent}
.pin-head{width:30px;height:30px;border-radius:50%;
  background:radial-gradient(circle at 34% 28%,#4b4b57,#1c1c22);
  box-shadow:inset 0 1px 1px #ffffff1a;display:flex;align-items:center;
  justify-content:center;gap:2px;flex-wrap:wrap;padding:6px}
.pin-head i{width:3px;height:3px;border-radius:50%;background:#b9b9c6;opacity:.75}
.pin-shaft{width:4px;height:44px;background:linear-gradient(#33333d,#15151a)}
.pin.driven{transform:translateY(20px)}
.pin.driven .pin-head{background:var(--violet);box-shadow:0 0 14px #7d6cff70}
.pin.driven .pin-head i{background:#0c0c10;opacity:.9}
.reset{animation:shake .3s}

/* ---- 5 plate ------------------------------------------------------- */
.engraved-plate{background:linear-gradient(150deg,#33333d,#1a1a20 55%,#2a2a33);
  border:1px solid var(--line);color:var(--cyan);
  font:400 20px ui-monospace,Menlo,monospace;letter-spacing:.08em;
  padding:24px 30px;border-radius:6px;cursor:pointer;user-select:all;
  box-shadow:0 6px 24px #000a,inset 0 1px 0 #ffffff18;transition:transform .4s}
.engraved-plate.tilt{transform:rotate3d(1,.4,0,26deg)}

/* ---- 6 soundboard -------------------------------------------------- */
.soundboard{width:230px;height:110px;cursor:pointer;user-select:none;
  -webkit-user-select:none;border:1px solid var(--edge);border-radius:6px;
  background:var(--slot);display:flex;align-items:center;justify-content:center;
  box-shadow:inset 0 0 34px #000}
.wave{width:120px;height:1px;background:var(--violet);opacity:.4}
.struck .wave{animation:ring .6s}
@keyframes ring{0%{transform:scaleY(26);opacity:1}100%{transform:scaleY(1);opacity:.4}}

/* ---- 7 dial -------------------------------------------------------- */
.dial-face{width:150px;height:150px;border-radius:50%;border:1px solid var(--edge);
  background:radial-gradient(circle at 40% 35%,#22222a,#0d0d11);position:relative;
  box-shadow:inset 0 2px 12px #000,0 6px 22px #0008;transition:box-shadow .3s}
.dial-face.open{box-shadow:inset 0 2px 12px #000,0 0 30px #3fe0d055;
  border-color:#3fe0d055}
.dial-needle{position:absolute;left:50%;top:14px;width:2px;height:60px;
  background:var(--violet);transform-origin:50% 61px;margin-left:-1px;border-radius:2px}
.dial-read{position:absolute;inset:auto 0 26px;text-align:center;
  font:400 15px ui-monospace,Menlo,monospace;color:var(--dim)}
.dial-input{width:min(260px,80vw);accent-color:#7d6cff;height:34px}
.nudge{display:flex;gap:10px}
.nudge button{width:52px;height:44px;border-radius:6px;border:1px solid var(--line);
  background:var(--raise);color:var(--text);font:400 19px ui-monospace,Menlo,monospace;
  cursor:pointer}
.nudge button:active{border-color:var(--violet);color:var(--violet)}
.makers-mark{margin-top:16px;font:400 11px ui-monospace,Menlo,monospace;
  color:var(--faint);letter-spacing:.14em}

/* ---- 8 shim -------------------------------------------------------- */
.shim-slot{width:200px;height:8px;background:var(--slot);border-radius:99px;
  box-shadow:inset 0 1px 4px #000;display:flex;align-items:center;padding:0 3px}
.shim{width:44px;height:2px;background:var(--violet);opacity:.6;border-radius:99px;
  touch-action:none;cursor:grab;transform-origin:left center;position:relative}
.shim::before{content:"";position:absolute;inset:-18px -10px}
.shim-etch{min-height:24px;font:400 19px ui-monospace,Menlo,monospace;
  letter-spacing:.16em;color:transparent;transition:color .3s}
.shim-etch.lit{color:var(--cyan)}

/* ---- 9 corner ------------------------------------------------------ */
.joint-face{width:190px;height:130px;border:1px solid var(--edge);border-radius:6px;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,#17171c 49.5%,#33333d 50%,#101014 50.5%)}
.joint-word{font:400 25px ui-monospace,Menlo,monospace;color:var(--cyan);
  transform:scaleX(-1);letter-spacing:.12em;cursor:pointer;transition:transform .5s;
  user-select:none;-webkit-user-select:none}
.joint-word.square{transform:scaleX(1)}

/* ---- 10 vault ------------------------------------------------------ */
.vault-plate{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;width:100%}
.vault-key{border:1px solid var(--edge);border-radius:6px;padding:10px 6px;
  font:400 12px ui-monospace,Menlo,monospace;color:var(--dim);letter-spacing:.04em}
.vault-key b{color:var(--violet);font-weight:600}

/* ---- opened -------------------------------------------------------- */
.flagwrap{text-align:center;padding:58px 20px}
.flagwrap h2{font:600 26px "Helvetica Neue",Inter,sans-serif;margin:0 0 10px;
  letter-spacing:-.02em}
.flagwrap p{color:var(--dim);margin:0 0 30px}
.flag{display:block;max-width:100%;background:#00000060;border:1px solid #3fe0d055;
  border-radius:6px;padding:18px 20px;color:var(--cyan);
  font:400 clamp(12px,3.4vw,16px)/1.5 ui-monospace,Menlo,monospace;user-select:all;
  letter-spacing:.02em;word-break:break-all;box-shadow:0 0 40px #3fe0d022}

/* ---- part two: the paper ------------------------------------------- */
.seam{margin:30px auto 4px;width:74px;height:4px;background:var(--edge);
  border-radius:99px;cursor:pointer;position:relative;
  animation:wiggle 2.6s ease-in-out .15s infinite;transition:background .3s}
.seam::after{content:"";position:absolute;inset:-18px -30px}
.seam:hover,.seam:focus-visible{background:var(--lime);animation:none}
.seam-arrow{margin:0 auto;width:fit-content;display:flex;flex-direction:column;
  align-items:center;gap:4px;color:var(--lime);opacity:0;
  animation:arrow-in .4s ease forwards,arrow-bob 1.1s ease-in-out .4s infinite}
.seam-arrow svg{width:16px;height:16px;transform:rotate(180deg)}
.seam-arrow span{font:500 11px "Helvetica Neue",sans-serif;letter-spacing:.06em;
  color:var(--dim)}
@keyframes arrow-in{to{opacity:1}}
@keyframes arrow-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(5px)}}
@keyframes wiggle{
  0%,26%,100%{transform:translateX(0) scaleX(1);background:var(--edge)}
  4%{transform:translateX(-4px) scaleX(1.1);background:var(--lime)}
  8%{transform:translateX(4px) scaleX(1.1);background:var(--lime)}
  12%{transform:translateX(-3px) scaleX(1.06);background:var(--lime)}
  16%{transform:translateX(2px) scaleX(1.03);background:#4a5d22}
  20%{transform:translateX(0) scaleX(1);background:#4a5d22}}

/* ---- the found note ------------------------------------------------ */
.found{padding:8px 0 34px;text-align:left}
.found-tag{font:500 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.18em;
  color:var(--lime);margin-bottom:10px}
.found h2{margin:0 0 16px;font:600 25px "Helvetica Neue",Inter,sans-serif;
  letter-spacing:-.02em}
.found-note{background:#edece6;color:#22222a;border-radius:4px;padding:20px 22px;
  border-left:3px solid var(--lime);white-space:pre-wrap;
  font:400 14px/1.7 ui-monospace,Menlo,monospace;
  box-shadow:0 20px 50px -24px #000}
.unfold{margin-top:20px;width:100%;min-height:50px;border:0;border-radius:6px;
  background:var(--lime);color:#0d1403;cursor:pointer;
  font:600 15px "Helvetica Neue",Inter,sans-serif;letter-spacing:.01em}
.unfold:hover{background:#c9ff5c}

.pad{background:#edece6;border-radius:4px;padding:0 0 26px;
  box-shadow:0 30px 70px -26px #000,0 0 0 1px #ffffff10;
  color:#16161a;position:relative;overflow:hidden}
.pad-top{height:26px;background:#22222a;display:flex;align-items:center;
  justify-content:center;gap:26px}
.pad-top i{width:11px;height:11px;border-radius:50%;background:#0c0c10;
  box-shadow:inset 0 1px 2px #000}
.pad-head{padding:24px 26px 18px 66px;border-bottom:1px solid #d6d5cd}
.pad-head h2{margin:0 0 6px;font:700 19px "Helvetica Neue",Inter,sans-serif;
  letter-spacing:-.01em;color:#16161a}
.pad-head p{margin:0;font-size:14px;color:#5c5c63;max-width:58ch}

.line{position:relative;padding:16px 26px 18px 66px;border-bottom:1px solid #dcdbd3;
  min-height:56px}
.line::before{content:attr(data-n);position:absolute;left:0;top:0;bottom:0;width:50px;
  border-right:1px solid var(--lime);color:#a8a79d;
  font:400 12px/56px ui-monospace,Menlo,monospace;text-align:right;padding-right:14px}
.line.done{background:#e6e5de}
.line.active{background:#fff}
.code{font:400 12px/1.6 ui-monospace,Menlo,monospace;color:#22222a;
  word-break:break-all;user-select:all;-webkit-user-select:all;margin:0;
  max-height:150px;overflow:auto;-webkit-overflow-scrolling:touch}
.code.blank{color:#b4b3a9;user-select:none}
.line-in{display:flex;gap:8px;align-items:flex-start}
.line-in textarea{flex:1;width:100%;resize:vertical;border:1px solid #c9c8bf;
  border-radius:4px;background:#fff;color:#22222a;padding:12px 13px;min-height:84px;
  font:400 12px/1.6 ui-monospace,Menlo,monospace;outline:0;word-break:break-all}
.line-in textarea:focus{border-color:#8fbe22;box-shadow:0 0 0 2px #b6ff2e40}
.line-in button{border:0;border-radius:3px;background:#22222a;color:#edece6;
  padding:0 16px;min-height:44px;font:500 13px "Helvetica Neue",sans-serif;cursor:pointer}
.line-in button:hover{background:#3a3a44}

.note{margin:16px 0 0;padding:16px 17px;background:#22222a;border-radius:4px;
  color:#c9c8c2;font:400 12px/1.7 ui-monospace,Menlo,monospace;
  white-space:pre-wrap;word-break:break-word;max-height:260px;overflow:auto;
  -webkit-overflow-scrolling:touch}
.note b{color:var(--lime);font-weight:600}
.note-bar{display:flex;align-items:center;gap:12px;margin-top:14px;flex-wrap:wrap}
.hint-btn{background:none;border:1px solid #c1c0b6;border-radius:3px;color:#5c5c63;
  padding:8px 13px;font:500 12px "Helvetica Neue",sans-serif;cursor:pointer;min-height:36px}
.hint-btn:hover{border-color:#8fbe22;color:#3d5a08}
.hint{margin:0;font:400 13px/1.5 "Helvetica Neue",sans-serif;color:#3d5a08;
  font-style:italic;flex:1;min-width:200px}
.mark{font:500 13px "Helvetica Neue",sans-serif}
.mark.no{color:#b4321f}
.mark.yes{color:#3d7a1f}
.pad-flag{margin:22px 26px 0 66px;padding:18px 20px;background:#16161a;
  border-radius:3px;border-left:3px solid var(--lime);color:var(--lime);
  font:400 15px/1.5 ui-monospace,Menlo,monospace;user-select:all;word-break:break-all}
@media (max-width:620px){
  .pad{border-radius:6px}
  .pad-head{padding:20px 18px 16px}
  .pad-head p{font-size:13.5px;line-height:1.6}
  .line{padding:14px 18px 18px}
  .line::before{position:static;display:block;width:auto;border:0;padding:0 0 9px;
    line-height:1;text-align:left;letter-spacing:.16em;color:#8f8e84}
  .line.active{box-shadow:inset 3px 0 0 var(--lime)}
  .line.done{box-shadow:inset 3px 0 0 #d0cfc5}
  .code{font-size:11.5px;max-height:132px}
  .line-in{flex-direction:column;gap:10px}
  .line-in button{width:100%;padding:14px;min-height:50px;font-size:15px}
  .note{font-size:11.5px;padding:14px;max-height:230px}
  .hint-btn{width:100%;min-height:46px;font-size:14px}
  .hint{min-width:0;font-size:13.5px}
  .pad-flag{margin:20px 18px 0;font-size:13px}
  .found-note{padding:17px 16px;font-size:13px;line-height:1.65}
  .found h2{font-size:22px}
}

@keyframes shake{0%,100%{transform:translateX(0)}
  20%{transform:translateX(-7px)}40%{transform:translateX(6px)}
  60%{transform:translateX(-4px)}80%{transform:translateX(3px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media (max-width:560px){
  .carcase{padding:26px 20px 0}.keyway{margin:0 -20px}
  .keyway input{padding:16px}.keyway button{padding:0 18px}
  .stage-plate{width:270px}.vault-plate{grid-template-columns:repeat(2,1fr)}
}
"""

RUNTIME = r"""
const B = __BOXES__, V = __VAULT__, P = __PAPER__, IT = __ITER__, SEED = __SEED__;
const $ = s => document.querySelector(s);
const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

async function unseal(pass, blob) {
  const raw = b64(blob), salt = raw.slice(0, 16), iv = raw.slice(16, 28), ct = raw.slice(28);
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pass),
    'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    {name: 'PBKDF2', salt, iterations: IT, hash: 'SHA-256'},
    base, {name: 'AES-GCM', length: 256}, false, ['decrypt']);
  const pt = await crypto.subtle.decrypt({name: 'AES-GCM', iv}, key, ct);
  return JSON.parse(new TextDecoder().decode(pt));
}

let idx = 0, keys = [], found = null, ac = null;

function paint(lv) {
  found = null;
  if (ac) ac.abort();
  ac = new AbortController();
  delete window.tap;
  $('#compartment').textContent = 'Compartment ' + lv.n + ' of ' + B.length;
  $('#title').textContent = lv.t;
  $('#engraved').textContent = lv.e;
  $('#stage').innerHTML = lv.h;
  $('#verdict').textContent = '';
  $('#verdict').className = 'verdict';
  $('#key').value = '';
  document.querySelectorAll('.tumbler').forEach((t, i) => t.classList.toggle('set', i < idx));
  $('#ring').innerHTML = keys.map(k => '<span>' + k + '</span>').join('');
  const reveal = w => {
    found = w;
    $('#verdict').textContent = 'A word comes loose: ' + w;
    $('#verdict').className = 'verdict good';
  };
  try { new Function('r', 'reveal', 'keys', 'signal', lv.j)($('#stage'), reveal, keys, ac.signal); }
  catch (e) { console.error(e); }
}

function openBox(v, word) {
  document.querySelectorAll('.tumbler').forEach(t => t.classList.add('set'));
  $('#carcase').innerHTML =
    '<div class="flagwrap"><h2>The box is open.</h2>' +
    '<p>' + v.close + '</p>' +
    '<div class="flag">' + v.flag + '</div>' +
    '<div class="seam" id="seam" title="the base sits proud of the chassis"></div>' +
    '</div>';
  const nudge = setTimeout(() => {
    const seam = document.getElementById('seam');
    if (!seam) return;
    seam.insertAdjacentHTML('afterend',
      '<div class="seam-arrow" id="seamArrow">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12l7 7 7-7"/></svg>' +
      '<span>something\'s loose there</span></div>');
  }, 10000);
  $('#seam').addEventListener('click', () => {
    clearTimeout(nudge);
    const arrow = document.getElementById('seamArrow');
    if (arrow) arrow.remove();
    foundNote(word);
  });
}

async function tryKey() {
  const word = $('#key').value.trim().toLowerCase();
  if (!word) return;
  const bar = $('#keyway');
  try {                                   // the last key opens it from anywhere
    const v = await unseal(word, V);
    openBox(v, word);
    return;
  } catch (e) { /* not the last key — carry on down the chain */ }
  try {
    if (idx + 1 < B.length) {
      const next = await unseal(word, B[idx + 1]);
      keys.push(word); idx++;
      paint(next);
    } else {
      openBox(await unseal(word, V), word);
    }
  } catch (e) {
    bar.classList.remove('wrong'); void bar.offsetWidth; bar.classList.add('wrong');
    $('#verdict').className = 'verdict';
    $('#verdict').textContent = found
      ? 'The key does not fit. Cut it exactly as the box gave it.'
      : 'The key does not fit.';
  }
}

// ---- part two: the paper folded into the base ----------------------
let paper = null, ln = 0;

async function foundNote(pass) {
  paper = await unseal(pass, P);
  document.querySelector('.brand .tag').textContent = 'part two — the paper in the base';
  $('#carcase').innerHTML =
    '<div class="found">' +
    '<div class="found-tag">recovered from the base plate</div>' +
    '<h2>You found a note.</h2>' +
    '<div class="found-note">' + esc(paper.intro) + '</div>' +
    '<button class="unfold" id="unfold">Unfold it</button></div>';
  $('#unfold').addEventListener('click', openPaper);
}

async function openPaper() {
  $('#carcase').outerHTML =
    '<section class="pad" id="pad">' +
    '<div class="pad-top"><i></i><i></i><i></i></div>' +
    '<div class="pad-head"><h2>Works record K247</h2>' +
    '<p>Ten lines. Line one came off the roll as printed. Each line is the ' +
    'plaintext of the line above it — decode it and write it on the next line. ' +
    'Every record is tagged NF~ so you know when you have it right. ' +
    'Nine layers, nine mistakes.</p></div>' +
    '<div id="lines"></div></section>';
  document.querySelectorAll('.rail .tumbler').forEach(t => t.classList.remove('set'));
  ln = 0;
  await drawPad(paper.c1, null);
}

async function drawPad(code, mark) {
  const wrap = $('#lines');
  if (!wrap.children.length) addLine(1, code, 'done');
  const meta = await unseal(code, paper.layers[ln]);
  const cur = addLine(ln + 2, null, 'active');
  cur.innerHTML =
    '<div class="line-in">' +
    '<textarea id="ans" spellcheck="false" autocapitalize="off" autocorrect="off" ' +
    'placeholder="the decoded record, tag and all"></textarea>' +
    '<button id="write">Write</button></div>' +
    '<div class="note">' + esc(meta.note) + '</div>' +
    '<div class="note-bar"><button class="hint-btn" id="hint">Show hint</button>' +
    '<p class="hint" id="hinttext"></p><span class="mark" id="mark"></span></div>';
  $('#hint').addEventListener('click', () => {
    $('#hinttext').textContent = meta.hint;
    $('#hint').remove();
  });
  $('#write').addEventListener('click', () => writeLine(meta));
  $('#ans').addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) writeLine(meta);
  });
  $('#ans').focus();
}

function addLine(n, code, cls) {
  const el = document.createElement('div');
  el.className = 'line ' + (cls || '');
  el.dataset.n = String(n).padStart(2, '0');
  if (code !== null) el.innerHTML = '<p class="code">' + esc(code) + '</p>';
  $('#lines').appendChild(el);
  return el;
}

const esc = t => t.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

async function writeLine(meta) {
  const val = $('#ans').value.trim();
  if (!val) return;
  const mark = $('#mark');
  const last = ln === paper.layers.length - 1;
  try {
    if (last) {
      const v = await unseal(val, paper.vault);
      const cur = document.querySelector('.line.active');
      cur.className = 'line done';
      cur.innerHTML = '<p class="code">' + esc(val) + '</p>';
      document.querySelectorAll('.rail .tumbler').forEach(t => t.classList.add('set'));
      $('#pad').insertAdjacentHTML('beforeend',
        '<div class="pad-flag">' + esc(v.flag) + '</div>');
      return;
    }
    await unseal(val, paper.layers[ln + 1]);
    const cur = document.querySelector('.line.active');
    cur.className = 'line done';
    cur.innerHTML = '<p class="code">' + esc(val) + '</p>';
    ln++;
    document.querySelectorAll('.rail .tumbler').forEach((t, i) => t.classList.toggle('set', i < ln));
    await drawPad(val, true);
  } catch (e) {
    mark.textContent = 'no — that is not the record';
    mark.className = 'mark no';
  }
}

$('#turn').addEventListener('click', tryKey);
$('#key').addEventListener('keydown', e => { if (e.key === 'Enter') tryKey(); });
unseal(SEED, B[0]).then(paint);
"""

TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>NINEFOLD</title>
<style>__CSS__</style>
</head><body>
<main class="box">
  <header class="brand">
    <h1 class="wordmark">NINE<i>FOLD</i></h1>
    <p class="tag">nine compartments, one way in</p>
  </header>
  <div class="rail">__RAIL__</div>
  <section class="carcase" id="carcase">
    <div class="compartment" id="compartment">&nbsp;</div>
    <h2 id="title">&nbsp;</h2>
    <p class="engraved" id="engraved">&nbsp;</p>
    <div class="stage" id="stage"></div>
    <div class="keyway" id="keyway">
      <input id="key" autocomplete="off" autocorrect="off" autocapitalize="off"
        spellcheck="false" enterkeyhint="go" placeholder="cut a key to fit">
      <button id="turn">Turn</button>
    </div>
  </section>
  <div class="verdict" id="verdict"></div>
  <div class="ring" id="ring"></div>
</main>
<script>__RUNTIME__</script>
</body></html>
"""

TEMPLATE = (TEMPLATE
            .replace("__CSS__", CSS)
            .replace("__RAIL__", '<i class="tumbler"></i>' * len(LEVELS))
            .replace("__RUNTIME__", RUNTIME))

if __name__ == "__main__":
    html = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html)
    print(f"{OUT}  {len(html):,} bytes")
