#!/usr/bin/env python3
"""NINEFOLD part two — the paper in the base of the unit.

Nine layers, each a real cryptographic flaw. Built backwards from the final
token: layer n's plaintext IS the code printed on line n+1. Every layer's
challenge note and hint is AES-GCM sealed under that layer's own code, so
nothing below the line you're standing on is readable in the file.

Every code carries the tag NF~ so brute-force attacks have a distinguisher —
that tag is the crib, and in one layer it is the whole break.
"""
import base64
import hashlib
import os
import random
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ALPHA = "".join(chr(c) for c in range(33, 127))   # 94 printable, ! .. ~
N = len(ALPHA)
TAG = "NF~"
FINAL_TOKEN = "NF~P4DD1NG"
PART2_FLAG = "{k3y_r3us3_1s_th3_0ld3st_m1st4k3}"

rnd = random.Random(0xC0FFEE)      # deterministic builds


# ------------------------------------------------------------------ helpers
def shift(s, keystream, sign=1):
    return "".join(ALPHA[(ALPHA.index(ch) + sign * k) % N] for ch, k in zip(s, keystream))


def lcg_stream(seed, count, a=1664525, c=1013904223, m=1 << 32):
    out, st = [], seed
    for _ in range(count):
        st = (a * st + c) % m
        out.append((st >> 16) % N)
    return out


def is_prime(n, rounds=32):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2; r += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def next_prime(n):
    n |= 1
    while not is_prime(n):
        n += 2
    return n


def iroot(x, k):
    """Exact integer k-th root, or the floor of it."""
    if x < 2:
        return x
    lo, hi = 1, 1 << ((x.bit_length() + k - 1) // k + 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** k <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo


def gcm(key, iv, pt):
    return AESGCM(key).encrypt(iv, pt, None)


# --------------------------------------------------------- layer generators
# Each returns (code_for_this_line, note, hint). The code encodes `nxt`.

def layer9(nxt):
    """Textbook RSA, e=3, no padding, m^3 < n. Break: integer cube root."""
    m = int.from_bytes(nxt.encode(), "big")
    bits = (m ** 3).bit_length() + 24
    p = next_prime(rnd.getrandbits(bits // 2) | (1 << (bits // 2 - 1)))
    q = next_prime(rnd.getrandbits(bits // 2) | (1 << (bits // 2 - 1)))
    n = p * q
    assert m ** 3 < n, "cube must not wrap the modulus"
    c = pow(m, 3, n)
    note = ("RSA. No padding, no OAEP, e = 3, and the operator was told the "
            "message was 'far too short to matter'.\n\n"
            f"n = {n}\ne = 3\n\nThe line above is c. Recover m.")
    return f"{TAG}{c}", note, "Nothing wrapped. c is just m cubed, sitting there as an integer."


def layer8(nxt):
    """RSA with primes generated from one seed. Break: Fermat factorisation."""
    need = len(nxt.encode()) * 8 + 24
    half = max(256, (need + 1) // 2 + 8)
    p = next_prime(rnd.getrandbits(half) | (1 << (half - 1)))
    q = next_prime(p + rnd.getrandbits(20))          # p and q are neighbours
    n, e = p * q, 65537
    m = int.from_bytes(nxt.encode(), "big")
    assert m < n
    c = pow(m, e, n)
    note = ("RSA again, this time with padding-free but honest exponentiation. "
            "The keygen script called the generator once and took the next two "
            "primes it found.\n\n"
            f"n = {n}\ne = {e}\n\nThe line above is c.")
    return f"{TAG}{c}", note, "If p and q are neighbours, n is very nearly a perfect square."


def layer7(nxt):
    """AES-GCM, key = SHA-256 of the millisecond clock. Break: search the window."""
    t0 = 1788249600000                                # 2026-05-01T00:00:00Z
    ms = t0 + rnd.randrange(70_000, 176_000)
    key = hashlib.sha256(str(ms).encode()).digest()
    iv = bytes(rnd.getrandbits(8) for _ in range(12))
    ct = gcm(key, iv, nxt.encode())
    note = ("AES-256-GCM. The key is SHA-256 over the Unix millisecond timestamp "
            "at which the record was sealed, taken as an ASCII decimal string.\n\n"
            f"iv  = {iv.hex()}\n"
            "log = sealed 2026-05-01, in the first three minutes after midnight UTC\n\n"
            "The line above is base64(ciphertext||tag).")
    return f"{TAG}{base64.b64encode(ct).decode()}", note, \
        "Three minutes is 180,000 keys. GCM tells you when you have the right one."


def layer6(nxt):
    """AES-GCM under a 4-digit PIN, PBKDF2 with one iteration. Break: 10^4."""
    pin = f"{rnd.randrange(4000, 9800):04d}"
    salt = bytes(rnd.getrandbits(8) for _ in range(16))
    key = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 1, 32)
    iv = bytes(rnd.getrandbits(8) for _ in range(12))
    ct = gcm(key, iv, nxt.encode())
    note = ("AES-256-GCM under a user PIN. Key = PBKDF2-HMAC-SHA256(pin, salt), "
            "32 bytes out.\n\n"
            f"salt       = {salt.hex()}\n"
            f"iv         = {iv.hex()}\n"
            "iterations = 1\n"
            "pin        = four digits, chosen by the operator\n\n"
            "The line above is base64(ciphertext||tag).")
    return f"{TAG}{base64.b64encode(ct).decode()}", note, \
        "A work factor of one is not a work factor. Ten thousand candidates."


def layer5(nxt):
    """Keystream from an LCG with a 16-bit seed. Break: exhaust the seed."""
    seed = rnd.randrange(9000, 64000)
    ks = lcg_stream(seed, len(nxt))
    note = ("Stream cipher over the 94 printable characters ! through ~. "
            "c[i] = A[(A.index(p[i]) + k[i]) mod 94], where k comes from a "
            "linear congruential generator:\n\n"
            "state = (1664525 * state + 1013904223) mod 2^32\n"
            "k[i]  = (state >> 16) mod 94\n\n"
            "The seed is drawn from the operator's 16-bit session counter.")
    return f"{TAG}{shift(nxt, ks, 1)}", note, \
        "65,536 seeds, and you already know the first three characters of the answer."


def layer4(nxt):
    """One keystream, two messages. Break: two-time pad."""
    ks = [rnd.randrange(N) for _ in range(len(nxt) + 64)]
    manifest = ("MANIFEST/K247:DO-NOT-REUSE-THE-COUNTER.DO-NOT-REUSE-THE-COUNTER."
                "ONE-COUNTER-ONE-RECORD.SIGNED-W-CORRIGAN-WORKS-MANAGER-KELLS."
                * 12)
    known = manifest[:len(nxt) + 40]
    d = shift(known, ks, 1)
    note = ("Same stream cipher, same alphabet, same 94-character arithmetic. "
            "A second record was sealed on the same counter value, and its "
            "plaintext survives in the works file.\n\n"
            f"other ciphertext = {d}\n\n"
            f"other plaintext  = {known}")
    return f"{TAG}{shift(nxt, ks, 1)}", note, \
        "Subtract the manifest from its own ciphertext and you are holding the key."


def layer3(nxt):
    """Repeating key, shorter than the crib. Break: read it straight off."""
    key = [ALPHA.index(c) for c in "KRF"]
    ks = [key[i % 3] for i in range(len(nxt))]
    note = ("Same alphabet, same arithmetic, but the key repeats. The operator "
            "chose a short one so it could be remembered without writing it down.\n\n"
            "Every record in this file is tagged. The tag is three characters long.")
    return f"{TAG}{shift(nxt, ks, 1)}", note, \
        "The key is no longer than the thing you already know sits at the front."


def layer2(nxt):
    """Constant shift. Break: 94 candidates."""
    k = rnd.randrange(1, N)
    note = ("Characters are indexed into the 94 printable ASCII values, ! (33) "
            "through ~ (126). Every character of the record was moved along that "
            "alphabet by the same amount.\n\n"
            "c[i] = A[(A.index(p[i]) + k) mod 94]")
    return f"{TAG}{shift(nxt, [k] * len(nxt), 1)}", note, \
        "There are 94 of them. The right one announces itself in the first three characters."


def layer1(nxt):
    """Transcription, not encryption."""
    enc = base64.b32encode(nxt.encode()).decode()
    note = ("Pulled off the roll as-is. The transcriber's terminal could not send "
            "the full byte range, so everything leaving the works was re-cut into "
            "a smaller alphabet first. This is not encryption and was never meant "
            "to be.")
    return f"{TAG}{enc}", note, "Count the distinct characters. There are not 64 of them."


BUILDERS = [layer1, layer2, layer3, layer4, layer5, layer6, layer7, layer8, layer9]


def build_chain():
    """Returns codes[0..9] (line 1..10) and per-layer notes/hints."""
    codes = [FINAL_TOKEN]
    notes, hints = [], []
    for fn in reversed(BUILDERS):
        code, note, hint = fn(codes[0])
        codes.insert(0, code)
        notes.insert(0, note)
        hints.insert(0, hint)
    return codes, notes, hints


if __name__ == "__main__":
    codes, notes, hints = build_chain()
    for i, c in enumerate(codes, 1):
        print(f"line {i:>2}  {len(c):>5} chars  {c[:64]}{'…' if len(c) > 64 else ''}")
