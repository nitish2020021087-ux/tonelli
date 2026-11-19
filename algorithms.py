"""
Core algorithms for solving   r^2 ≡ n (mod p)   (modular square root).

* generate_prime / generate_pn : random prime p and a number n
* brute_force                  : try r = 0, 1, 2, ... until r^2 mod p == n   -> O(p)
* tonelli_shanks               : Tonelli-Shanks algorithm                    -> O(log^2 p)
* run_workbench                : run one/both algorithms for many bit sizes
"""
from __future__ import annotations

import random
import time
from typing import Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Prime generation
# --------------------------------------------------------------------------- #
_SMALL_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

# label -> required value of p mod 4 (None = no restriction)
PRIME_MODES = {
    "Any odd prime": None,
    "p ≡ 1 (mod 4)  → full Tonelli–Shanks loop (S ≥ 2)": 1,
    "p ≡ 3 (mod 4)  → Tonelli–Shanks shortcut (S = 1)": 3,
}


def is_prime(n: int) -> bool:
    """Miller–Rabin (deterministic for n < 3.3e24, extremely reliable above)."""
    if n < 2:
        return False
    for q in _SMALL_PRIMES:
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _SMALL_PRIMES:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits: int, mod4: Optional[int] = None, rng: Optional[random.Random] = None) -> int:
    """Random prime with exactly `bits` bits (bits >= 4)."""
    if bits < 4:
        raise ValueError("bits must be >= 4")
    rng = rng or random.SystemRandom()
    while True:
        c = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if mod4 == 1:
            c = (c & ~3) | 1
        elif mod4 == 3:
            c |= 3
        if is_prime(c):
            return c


def generate_pn(bits: int, mod4: Optional[int] = None, residue_only: bool = True,
                rng: Optional[random.Random] = None):
    """Return (p, n). If residue_only, n = x^2 mod p so a root is guaranteed to exist."""
    rng = rng or random.SystemRandom()
    p = generate_prime(bits, mod4, rng)
    if residue_only:
        x = rng.randrange(1, p)
        n = x * x % p
    else:
        n = rng.randrange(1, p)
    return p, n


# --------------------------------------------------------------------------- #
# Brute force
# --------------------------------------------------------------------------- #
def brute_force(n: int, p: int, timeout: Optional[float] = None) -> Dict:
    """Try every r in [0, p) until r*r % p == n.  Gives up after `timeout` seconds."""
    n %= p
    start = time.perf_counter()
    mask = (1 << 16) - 1
    for r in range(p):
        if r * r % p == n:
            return {"status": "found", "r": r, "iterations": r + 1,
                    "time": time.perf_counter() - start}
        if timeout is not None and r and (r & mask) == 0:
            if time.perf_counter() - start > timeout:
                return {"status": "timeout", "r": None, "iterations": r + 1,
                        "time": time.perf_counter() - start}
    return {"status": "no_solution", "r": None, "iterations": p,
            "time": time.perf_counter() - start}


# --------------------------------------------------------------------------- #
# Tonelli–Shanks
# --------------------------------------------------------------------------- #
def tonelli_shanks(n: int, p: int, trace: bool = False) -> Dict:
    """
    Solve r^2 ≡ n (mod p) for an odd prime p.
    With trace=True the result also holds `vars` (variable table) and
    `iterations` (one row per pass of the main loop).
    """
    start = time.perf_counter()
    n %= p
    res: Dict = {"status": "found", "r": None, "vars": [], "iterations": [], "euler": None}

    def V(name, value, meaning):
        if trace:
            res["vars"].append({"Variable": name, "Value": str(value), "Meaning": meaning})

    V("p", p, "odd prime modulus")
    V("n", n, "number whose square root we want")

    if p == 2 or n == 0:
        res["r"] = n
    else:
        euler = pow(n, (p - 1) // 2, p)
        res["euler"] = euler
        V("n^((p−1)/2) mod p", euler, "Euler's criterion: 1 → n is a quadratic residue, p−1 → no root")
        if euler != 1:
            res["status"] = "no_solution"
        else:
            q, s = p - 1, 0
            while q % 2 == 0:
                q //= 2
                s += 1
            V("Q", q, "odd part:  p − 1 = Q · 2^S")
            V("S", s, "power of two:  p − 1 = Q · 2^S")
            if s == 1:  # p ≡ 3 (mod 4) shortcut
                res["r"] = pow(n, (p + 1) // 4, p)
                V("shortcut", "r = n^((p+1)/4) mod p", "S = 1 → no loop needed")
            else:
                z = 2
                while pow(z, (p - 1) // 2, p) != p - 1:
                    z += 1
                m = s
                c = pow(z, q, p)
                t = pow(n, q, p)
                r = pow(n, (q + 1) // 2, p)
                V("z", z, "smallest quadratic non-residue mod p")
                V("M (start)", m, "M = S")
                V("c (start)", c, "c = z^Q mod p")
                V("t (start)", t, "t = n^Q mod p")
                V("R (start)", r, "R = n^((Q+1)/2) mod p")
                k = 0
                while t != 1:
                    k += 1
                    i, tt = 0, t
                    while tt != 1:
                        tt = tt * tt % p
                        i += 1
                    b = pow(c, 1 << (m - i - 1), p)
                    m = i
                    c = b * b % p
                    t = t * c % p
                    r = r * b % p
                    if trace:
                        res["iterations"].append({
                            "Iter": k, "i": i, "b": str(b), "M": m,
                            "c": str(c), "t": str(t), "R": str(r)})
                res["r"] = r
                V("loops", k, "number of passes of the main while-loop")
    res["time"] = time.perf_counter() - start
    if res["r"] is not None:
        V("r (answer)", res["r"], "r^2 ≡ n (mod p)")
        V("p − r (other root)", (p - res["r"]) % p, "the second square root")
    return res


# --------------------------------------------------------------------------- #
# Workbench
# --------------------------------------------------------------------------- #
def fmt_time(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    if seconds < 1e-6:
        return f"{seconds * 1e9:.0f} ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:.2f} µs"
    if seconds < 1:
        return f"{seconds * 1e3:.3f} ms"
    return f"{seconds:.3f} s"


def run_workbench(algos: List[str], bits_list: List[int], trials: int,
                  mod4: Optional[int], residue_only: bool, timeout: float,
                  progress: Optional[Callable[[int, int, int], None]] = None) -> Dict[str, List[Dict]]:
    """
    algos : subset of ["bf", "ts"].
    For every bit size and trial a fresh (p, n) is generated and given to every
    algorithm in `algos` (so comparisons use identical inputs).
    Returns {algo: [row, ...]} where row = Bits, p, n, r, Time (ms), Trials, Status.
    """
    out: Dict[str, List[Dict]] = {a: [] for a in algos}
    bf_dead = False
    bits_sorted = sorted(set(bits_list))
    for idx, bits in enumerate(bits_sorted, start=1):
        acc = {a: {"times": [], "p": None, "n": None, "r": None,
                   "failed": False, "status": "OK", "no_root": 0} for a in algos}
        for _ in range(trials):
            p, n = generate_pn(bits, mod4, residue_only)
            for a in algos:
                d = acc[a]
                d["p"], d["n"] = p, n
                if d["failed"]:
                    continue
                if a == "bf":
                    if bf_dead:
                        d["failed"], d["status"] = True, "Skipped (earlier timeout)"
                        continue
                    res = brute_force(n, p, timeout)
                    if res["status"] == "timeout":
                        bf_dead = True
                        d["failed"], d["status"] = True, f"Timeout (> {timeout:g} s)"
                        continue
                else:
                    res = tonelli_shanks(n, p)
                d["times"].append(res["time"])
                d["r"] = res["r"]
                if res["status"] != "found":
                    d["no_root"] += 1
        for a in algos:
            d = acc[a]
            status = d["status"]
            if not d["failed"] and d["no_root"]:
                status = f"No root in {d['no_root']}/{trials} trials"
            avg = sum(d["times"]) / len(d["times"]) if d["times"] else None
            out[a].append({
                "Bits": bits,
                "p": str(d["p"]),
                "n": str(d["n"]),
                "r": "—" if d["r"] is None else str(d["r"]),
                "Time (ms)": None if avg is None else avg * 1000.0,
                "Trials": len(d["times"]),
                "Status": status,
            })
        if progress:
            progress(idx, len(bits_sorted), bits)
    return out
