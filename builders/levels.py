# Nine compartments + the vault. Answers spell MECHANISM by first letter.
# Each level is decrypted with the previous level's answer, so nothing
# past the current compartment exists in readable form in the output file.

LEVELS = [
    # ---------------------------------------------------------------- 1
    dict(
        n=1,
        answer="mortise",
        title="The lid",
        engraved="A lid that will not lift is not locked. It is waiting.",
        html="""
<div class="stage-lid">
  <button class="lid-btn" data-lid>Lift the lid</button>
  <div class="lid-note" data-note>&nbsp;</div>
  <div class="rivets">
    <span class="rivet"></span><span class="rivet"></span>
    <span class="rivet" data-rivet></span><span class="rivet"></span>
  </div>
</div>
""",
        js="""
const btn = r.querySelector('[data-lid]');
const note = r.querySelector('[data-note]');
const rivet = r.querySelector('[data-rivet]');
const taunts = ['It does not move.', 'Something holds it from beneath.',
                'The lid is not the mechanism.', 'Force is the wrong tool.'];
let i = 0;
btn.addEventListener('click', () => {
  btn.classList.remove('shudder'); void btn.offsetWidth; btn.classList.add('shudder');
  note.textContent = taunts[i++ % taunts.length];
});
let t = null, held = 0, tick = null;
const start = (e) => {
  e.preventDefault();
  if (t) return;
  rivet.classList.add('pressing');
  held = 0;
  tick = setInterval(() => { held += 100; rivet.style.setProperty('--fill', (held/3000)); }, 100);
  t = setTimeout(() => {
    clearInterval(tick); rivet.classList.add('sunk');
    note.textContent = 'The rivet sinks. A mortise opens along the edge.';
    reveal('mortise');
  }, 3000);
};
const stop = () => {
  clearTimeout(t); clearInterval(tick); t = null;
  if (!rivet.classList.contains('sunk')) {
    rivet.classList.remove('pressing'); rivet.style.setProperty('--fill', 0);
  }
};
rivet.addEventListener('pointerdown', start);
addEventListener('pointerup', stop, {signal});
addEventListener('pointercancel', stop, {signal});
""",
    ),
    # ---------------------------------------------------------------- 2
    dict(
        n=2,
        answer="escutcheon",
        title="The plate",
        engraved="The keyhole is a decoy. The plate around it is not.",
        html="""
<div class="stage-plate">
  <div class="plate-bed"><span class="plate-word" data-word>escutcheon</span></div>
  <div class="brass-plate" data-plate>
    <div class="keyhole"></div>
    <div class="plate-grip"></div>
  </div>
  <p class="stage-hint">Take hold of the plate.</p>
</div>
""",
        js="""
const plate = r.querySelector('[data-plate]');
const bed = r.querySelector('.plate-bed');
let travel = 0;
const measure = () => { travel = Math.max(70, bed.clientWidth - plate.offsetWidth - 4); };
measure(); addEventListener('resize', measure, {signal});
let drag = false, x0 = 0, dx = 0, done = false;
plate.addEventListener('pointerdown', e => {
  drag = true; x0 = e.clientX - dx; plate.setPointerCapture(e.pointerId);
});
plate.addEventListener('pointermove', e => {
  if (!drag || done) return;
  dx = Math.max(0, Math.min(travel, e.clientX - x0));
  plate.style.transform = 'translateX(' + dx + 'px)';
  if (dx >= travel - 4) {
    done = true; drag = false;
    plate.style.transform = 'translateX(' + travel + 'px)';
    r.querySelector('.stage-hint').textContent = 'Underneath, the word is stamped into the substrate.';
    reveal('escutcheon');
  }
});
plate.addEventListener('pointerup', () => drag = false);
""",
    ),
    # ---------------------------------------------------------------- 3
    dict(
        n=3,
        answer="cam",
        title="The grain",
        engraved="Some marks are cut so shallow they only show at an angle.",
        html="""
<div class="stage-grain">
  <p class="grain-text">The machinist signed the panel in a hand no one was meant to read. He cut
  the letters along the brush lines, not across them, so the light passes
  straight over them: <span class="ghost">cam</span>. Then he sealed the unit and shipped it
  to a buyer who never opened it.</p>
  <p class="stage-hint">Sweep across the panel. Shallow cuts still catch on something.</p>
</div>
""",
        js="""
const g = r.querySelector('.ghost');
const check = () => {
  const s = document.getSelection();
  if (s && s.toString().toLowerCase().includes('cam')) {
    g.classList.add('lit');
    r.querySelector('.stage-hint').textContent = 'A shallow cut, caught in the light.';
    reveal('cam');
  }
};
document.addEventListener('selectionchange', check, {signal});
document.addEventListener('mouseup', check, {signal});
""",
    ),
    # ---------------------------------------------------------------- 4
    dict(
        n=4,
        answer="hinge",
        title="The pins",
        engraved="Five pins, driven in order. The order is scratched on their heads.",
        html="""
<div class="stage-pins">
  <div class="pin-row" data-pins></div>
  <p class="stage-hint" data-hint>Drive them shallowest first.</p>
</div>
""",
        js="""
const row = r.querySelector('[data-pins]');
const hint = r.querySelector('[data-hint]');
const order = [3, 5, 1, 4, 2];   // notches, left to right
let next = 1;
order.forEach(notches => {
  const p = document.createElement('button');
  p.className = 'pin';
  p.dataset.notches = notches;
  p.innerHTML = '<span class="pin-head">' +
    Array.from({length: notches}, () => '<i></i>').join('') + '</span><span class="pin-shaft"></span>';
  p.addEventListener('click', () => {
    if (p.classList.contains('driven')) return;
    if (notches === next) {
      p.classList.add('driven'); next++;
      if (next > 5) {
        hint.textContent = 'The hinge drops free of the chassis.';
        reveal('hinge');
      }
    } else {
      row.classList.remove('reset'); void row.offsetWidth; row.classList.add('reset');
      row.querySelectorAll('.pin').forEach(x => x.classList.remove('driven'));
      next = 1;
      hint.textContent = 'They spring back. Start again.';
    }
  });
  row.appendChild(p);
});
""",
    ),
    # ---------------------------------------------------------------- 5
    dict(
        n=5,
        answer="aperture",
        title="The etched plate",
        engraved="Sixty-four characters is a small alphabet for a large secret.",
        html="""
<div class="stage-brass">
  <div class="engraved-plate">YXBlcnR1cmU=</div>
  <p class="stage-hint">Etched in an alphabet of sixty-four. Read it back into plain letters.</p>
</div>
""",
        js="""
const plate = r.querySelector('.engraved-plate');
plate.addEventListener('click', () => plate.classList.toggle('tilt'));
""",
    ),
    # ---------------------------------------------------------------- 6
    dict(
        n=6,
        answer="notch",
        title="The sounding board",
        engraved="The box answers when struck. It will not answer here.",
        html="""
<div class="stage-sound">
  <div class="soundboard" data-board><span class="wave"></span></div>
  <p class="stage-hint">Three sharp taps, close together. Strike it, or call to it from somewhere quieter.</p>
</div>
""",
        js="""
const board = r.querySelector('[data-board]');
const strike = () => {
  board.classList.remove('struck'); void board.offsetWidth; board.classList.add('struck');
};
console.log('%c the unit listens ', 'background:#b6ff2e;color:#08080a;padding:2px 6px');
console.log('call tap(n) — n is how many times you strike it');
window.tap = (n) => {
  strike();
  if (n === 3) { reveal('notch'); return 'a notch opens in the resonator'; }
  return 'the board is dull. try again.';
};
let hits = [];
board.addEventListener('click', () => {
  strike();
  const now = Date.now();
  hits = hits.filter(h => now - h < 1400);
  hits.push(now);
  if (hits.length === 3) { hits = []; reveal('notch'); }
}, {signal});
""",
    ),
    # ---------------------------------------------------------------- 7
    dict(
        n=7,
        answer="inlay",
        title="The dial",
        engraved="Every box carries its number. This one wears it in the corner.",
        html="""
<div class="stage-dial">
  <div class="dial-face">
    <div class="dial-needle" data-needle></div>
    <div class="dial-read" data-read>0</div>
  </div>
  <input class="dial-input" type="range" min="0" max="360" value="0" data-range aria-label="dial">
  <div class="nudge">
    <button type="button" data-nudge="-1" aria-label="turn back one">&minus;</button>
    <button type="button" data-nudge="1" aria-label="turn on one">+</button>
  </div>
  <p class="stage-hint" data-hint>Turn the dial to the box's own number.</p>
  <div class="makers-mark">CORRIGAN INSTRUMENTS &nbsp;·&nbsp; No. 247 &nbsp;·&nbsp; KELLS</div>
</div>
""",
        js="""
const range = r.querySelector('[data-range]');
const needle = r.querySelector('[data-needle]');
const read = r.querySelector('[data-read]');
const hint = r.querySelector('[data-hint]');
let open = false;
r.querySelectorAll('[data-nudge]').forEach(b => b.addEventListener('click', () => {
  range.value = Math.max(0, Math.min(360, +range.value + +b.dataset.nudge));
  range.dispatchEvent(new Event('input'));
}));
range.addEventListener('input', () => {
  const v = +range.value;
  needle.style.transform = 'rotate(' + v + 'deg)';
  read.textContent = v;
  if (v === 247 && !open) {
    open = true;
    hint.textContent = 'A tray slides out from the base, lined in inlay.';
    r.querySelector('.dial-face').classList.add('open');
    reveal('inlay');
  }
});
""",
    ),
    # ---------------------------------------------------------------- 8
    dict(
        n=8,
        answer="spline",
        title="The shim",
        engraved="The box keeps a splinter of every hand that opens it.",
        html="""
<div class="stage-shim">
  <div class="shim-slot"><span class="shim" data-shim></span></div>
  <div class="shim-etch" data-etch>&nbsp;</div>
  <p class="stage-hint">Nothing here to work on — unless you can get the shim out.
  The unit has also been keeping notes on everyone who opens it.</p>
</div>
""",
        js="""
try {
  localStorage.setItem('box.carcase.shim', 'enilps');
  localStorage.setItem('box.carcase.note', 'read it as it was cut — from the far end');
} catch (e) {}
const shim = r.querySelector('[data-shim]');
const etch = r.querySelector('[data-etch]');
let drag = false, x0 = 0, dx = 0, out = false;
shim.addEventListener('pointerdown', e => {
  drag = true; x0 = e.clientX - dx; shim.setPointerCapture(e.pointerId);
});
shim.addEventListener('pointermove', e => {
  if (!drag || out) return;
  dx = Math.max(0, Math.min(120, e.clientX - x0));
  shim.style.transform = 'translateX(' + dx + 'px) scaleX(' + (1 + dx / 60) + ')';
  if (dx >= 118) {
    out = true; drag = false;
    etch.textContent = 'enilps';
    etch.classList.add('lit');
  }
});
shim.addEventListener('pointerup', () => drag = false);
""",
    ),
    # ---------------------------------------------------------------- 9
    dict(
        n=9,
        answer="mitre",
        title="The corner",
        engraved="A mitre is two faces meeting. Each one shows the other backwards.",
        html="""
<div class="stage-mitre">
  <div class="joint-face"><span class="joint-word">mitre</span></div>
  <p class="stage-hint">Read the joint as its other face sees it.</p>
</div>
""",
        js="""
const w = r.querySelector('.joint-word');
w.addEventListener('click', () => w.classList.toggle('square'));
""",
    ),
    # ---------------------------------------------------------------- 10
    dict(
        n=10,
        answer="mechanism",
        title="The vault",
        engraved="Nine compartments, cut from one billet. Read their heads in order.",
        html="""
<div class="stage-vault">
  <div class="vault-plate" data-keys></div>
  <p class="stage-hint">Every key was cut from the same stock. Their heads spell what holds them.</p>
</div>
""",
        js="""
const plate = r.querySelector('[data-keys]');
plate.innerHTML = keys.map((k, i) =>
  '<div class="vault-key"><b>' + k[0].toUpperCase() + '</b>' + k.slice(1) + '</div>'
).join('');
""",
    ),
]

FLAG = "{n1n3_c0mp4rtm3nts_0n3_m3ch4n1sm}"

CLOSING = "Nine compartments, one mechanism."
