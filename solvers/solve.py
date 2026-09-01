#!/usr/bin/env python3
"""Plays part two the way a solver would — only using what each note publishes."""
import base64, hashlib, re, sys, time
sys.path.insert(0, "/home/claude/box")
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from part2 import build_chain, ALPHA, N, TAG, lcg_stream, iroot

codes, notes, hints = build_chain()
body = lambda c: c[len(TAG):]
unshift = lambda s, ks: "".join(ALPHA[(ALPHA.index(c) - k) % N] for c, k in zip(s, ks))
num = lambda note, name: int(re.search(rf"^{name}\s*=\s*(\d+)$", note, re.M).group(1))
hexv = lambda note, name: bytes.fromhex(re.search(rf"{name}\s*=\s*([0-9a-f]+)", note).group(1))


def s1(c, note):
    return base64.b32decode(body(c)).decode()

def s2(c, note):
    for k in range(N):
        p = unshift(body(c), [k] * len(c))
        if p.startswith(TAG):
            return p

def s3(c, note):
    crib = [(ALPHA.index(a) - ALPHA.index(b)) % N for a, b in zip(body(c)[:3], TAG)]
    return unshift(body(c), [crib[i % 3] for i in range(len(c))])

def s4(c, note):
    d = re.search(r"other ciphertext = (\S+)", note).group(1)
    p = re.search(r"other plaintext  = (\S+)", note).group(1)
    ks = [(ALPHA.index(a) - ALPHA.index(b)) % N for a, b in zip(d, p)]
    return unshift(body(c), ks)

def s5(c, note):
    for seed in range(1 << 16):
        p = unshift(body(c)[:3], lcg_stream(seed, 3))
        if p == TAG:
            return unshift(body(c), lcg_stream(seed, len(c)))

def s6(c, note):
    salt, iv, ct = hexv(note, "salt"), hexv(note, "iv"), base64.b64decode(body(c))
    for pin in range(10000):
        key = hashlib.pbkdf2_hmac("sha256", f"{pin:04d}".encode(), salt, 1, 32)
        try:
            return AESGCM(key).decrypt(iv, ct, None).decode()
        except Exception:
            pass

def s7(c, note):
    iv, ct = hexv(note, "iv"), base64.b64decode(body(c))
    t0 = 1788249600000
    for ms in range(t0, t0 + 180_000):
        key = hashlib.sha256(str(ms).encode()).digest()
        try:
            return AESGCM(key).decrypt(iv, ct, None).decode()
        except Exception:
            pass

def s8(c, note):
    n, e, ct = num(note, "n"), num(note, "e"), int(body(c))
    a = iroot(n, 2)
    if a * a < n:
        a += 1
    while True:                                   # Fermat
        b2 = a * a - n
        b = iroot(b2, 2)
        if b * b == b2:
            break
        a += 1
    p, q = a - b, a + b
    d = pow(e, -1, (p - 1) * (q - 1))
    m = pow(ct, d, n)
    return m.to_bytes((m.bit_length() + 7) // 8, "big").decode()

def s9(c, note):
    m = iroot(int(body(c)), 3)
    return m.to_bytes((m.bit_length() + 7) // 8, "big").decode()


SOLVERS = [s1, s2, s3, s4, s5, s6, s7, s8, s9]
ok = True
for i, fn in enumerate(SOLVERS):
    t = time.time()
    got = fn(codes[i], notes[i])
    good = got == codes[i + 1]
    ok &= good
    print(f"  layer {i+1}  {fn.__doc__ or fn.__name__:<4} "
          f"{'solved' if good else 'FAILED'}  {time.time()-t:6.2f}s  -> {codes[i+1][:34]}…")
print("\nPART 2 SOLVABLE" if ok else "\nPART 2 BROKEN")
