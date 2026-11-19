"""
Modular Square Root Lab  –  solve  r^2 ≡ n (mod p)
Brute force  vs  Tonelli–Shanks      (run with:  streamlit run app.py)
"""
import altair as alt
import pandas as pd
import streamlit as st

import algorithms as alg

st.set_page_config(page_title="Modular Square Root Lab", page_icon="🧮", layout="wide")

# ----------------------------------------------------------------- constants
BF_OPTIONS = list(range(4, 49))
TS_OPTIONS = [4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024]
CMP_OPTIONS = list(range(4, 49, 2)) + [64, 96, 128, 192, 256]

BF_PRESETS = [("Small (8–20)", [8, 10, 12, 14, 16, 18, 20]),
              ("Medium (8–28)", [8, 12, 16, 20, 24, 28]),
              ("Even 8–32", list(range(8, 33, 2)))]
TS_PRESETS = [("Small", [8, 16, 24, 32, 48, 64]),
              ("Medium", [16, 32, 64, 128, 256]),
              ("Large", [64, 128, 256, 512, 1024])]
CMP_PRESETS = [("Small", [8, 12, 16, 20, 24]),
               ("Medium", [8, 12, 16, 20, 24, 28, 32]),
               ("Show the gap", [16, 20, 24, 28, 32, 48, 64, 128, 256])]

TABLE_COLS = ["Bits", "p", "n", "r", "Time (ms)", "Trials", "Status"]
TIME_FMT = st.column_config.NumberColumn("Time (ms)", format="%.5f")


# ----------------------------------------------------------------- state
def init_state():
    for k in ("bf_pn", "ts_pn", "bf_res", "ts_res"):
        st.session_state.setdefault(k, None)
    for k in ("bf_rows", "ts_rows"):
        st.session_state.setdefault(k, {})


def table_df(key: str) -> pd.DataFrame:
    rows = st.session_state[key]
    if not rows:
        return pd.DataFrame(columns=TABLE_COLS)
    return pd.DataFrame([rows[b] for b in sorted(rows)], columns=TABLE_COLS)


def set_sel(key, values):
    st.session_state[key] = list(values)


# ----------------------------------------------------------------- shared widgets
def sidebar():
    st.sidebar.title("🧮 Modular √ Lab")
    st.sidebar.caption("Find r such that  r² ≡ n (mod p)")
    page = st.sidebar.radio(
        "Choose method",
        ["Brute force", "Tonelli–Shanks algorithm", "Brute force vs Tonelli–Shanks"],
    )
    st.sidebar.divider()
    st.sidebar.subheader("Settings")
    mode = st.sidebar.selectbox("Type of prime p", list(alg.PRIME_MODES.keys()))
    residue_only = st.sidebar.checkbox(
        "Guarantee n is a quadratic residue", value=True,
        help="n = x² mod p, so a root r always exists. Untick to use a random n "
             "(about half of them have no square root).")
    timeout = st.sidebar.number_input("Brute-force time limit (s)", 1.0, 600.0, 5.0, 1.0,
                                      help="Brute force stops (and is marked 'Timeout') after this long.")
    trials = st.sidebar.number_input("Trials per bit size (workbench)", 1, 50, 3, 1,
                                     help="Time is averaged over this many random (p, n) pairs.")
    cfg = {"mod4": alg.PRIME_MODES[mode], "residue_only": residue_only,
           "timeout": float(timeout), "trials": int(trials)}
    return page, cfg


def generate_block(prefix, bits_min, bits_max, bits_default, cfg):
    """Step 1 + 2: slider, 'Generate p and n' button, show p and n."""
    st.markdown("### 1️⃣ Choose bits & generate p and n")
    bits = st.slider("Number of bits of p", bits_min, bits_max, bits_default, key=f"{prefix}_bits")
    if st.button("🎲 Generate p and n", key=f"{prefix}_gen", type="primary"):
        p, n = alg.generate_pn(bits, cfg["mod4"], cfg["residue_only"])
        st.session_state[f"{prefix}_pn"] = {"p": p, "n": n, "bits": bits}
        st.session_state[f"{prefix}_res"] = None
    pn = st.session_state[f"{prefix}_pn"]
    st.markdown("### 2️⃣ Generated values")
    if pn is None:
        st.info("Press **Generate p and n** to create the inputs.")
        return None
    c1, c2 = st.columns(2)
    c1.markdown(f"**p** ({pn['p'].bit_length()} bits)")
    c1.code(str(pn["p"]), language=None)
    c2.markdown("**n**")
    c2.code(str(pn["n"]), language=None)
    st.caption(f"p mod 4 = {pn['p'] % 4}")
    return pn


def execute_workbench(algos, bits, cfg):
    prog = st.progress(0.0, text="Starting…")

    def cb(i, total, b):
        prog.progress(i / total, text=f"Finished {b}-bit  ({i}/{total})")

    out = alg.run_workbench(algos, bits, cfg["trials"], cfg["mod4"],
                            cfg["residue_only"], cfg["timeout"], cb)
    prog.empty()
    for a, rows in out.items():
        key = "bf_rows" if a == "bf" else "ts_rows"
        for r in rows:
            st.session_state[key][r["Bits"]] = r


def bit_selector(prefix, options, presets, default):
    sel_key = f"{prefix}_sel"
    st.session_state.setdefault(sel_key, default)
    cols = st.columns(len(presets) + 1)
    for i, (label, vals) in enumerate(presets):
        cols[i].button(label, key=f"{prefix}_preset{i}", on_click=set_sel,
                       args=(sel_key, vals), use_container_width=True)
    cols[-1].button("Clear", key=f"{prefix}_clear_sel", on_click=set_sel,
                    args=(sel_key, []), use_container_width=True)
    return st.multiselect("Bit sizes of p to test", options, key=sel_key)


def draw_chart(df, title, key, log_default=True):
    d = df.dropna(subset=["Time (ms)"]).copy()
    if d.empty:
        st.info("The graph appears here as soon as the workbench table has data.")
        return
    log_y = st.checkbox("Logarithmic time axis", value=log_default, key=f"{key}_log")
    d["Time (ms)"] = d["Time (ms)"].clip(lower=1e-6)
    chart = (
        alt.Chart(d)
        .mark_line(point=alt.OverlayMarkDef(size=80))
        .encode(
            x=alt.X("Bits:Q", title="Bit length of p"),
            y=alt.Y("Time (ms):Q", title="Time (ms)",
                    scale=alt.Scale(type="log" if log_y else "linear")),
            color=alt.Color("Algorithm:N", title="Algorithm"),
            tooltip=["Algorithm", "Bits", alt.Tooltip("Time (ms):Q", format=".5f"), "Status"],
        )
        .properties(height=380, title=title)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)


def combined_df(which):
    frames = []
    names = {"bf": ("bf_rows", "Brute force"), "ts": ("ts_rows", "Tonelli–Shanks")}
    for a in which:
        key, label = names[a]
        d = table_df(key)
        if not d.empty:
            d["Algorithm"] = label
            frames.append(d)
    if not frames:
        return pd.DataFrame(columns=TABLE_COLS + ["Algorithm"])
    return pd.concat(frames, ignore_index=True)


def workbench_output(algo, label, key):
    """Table + CSV + clear button + auto-updating graph for one algorithm."""
    rows_key = f"{algo}_rows"
    df = table_df(rows_key)
    st.markdown("#### 📋 Workbench table")
    if df.empty:
        st.info("No data yet – select bit sizes and press **Run workbench**.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"Time (ms)": TIME_FMT})
        c1, c2 = st.columns(2)
        c1.download_button("⬇ Download CSV", df.to_csv(index=False), f"{algo}_workbench.csv",
                           "text/csv", key=f"{key}_dl")
        if c2.button("🗑 Clear table", key=f"{key}_clear"):
            st.session_state[rows_key] = {}
            st.rerun()
    st.markdown("#### 📈 Graph (updates with the table)")
    draw_chart(combined_df([algo]), f"{label}: time vs bit length", key)


# ----------------------------------------------------------------- page 1
def page_bruteforce(cfg):
    st.title("🔨 Brute force")
    st.write("Tries r = 0, 1, 2, … until **r² mod p = n**.  Cost ≈ O(p) = O(2^bits) — exponential in the bit length.")
    pn = generate_block("bf", 4, 48, 20, cfg)

    st.markdown("### 3️⃣ Find r by brute force")
    if st.button("▶ Find r", key="bf_solve", disabled=pn is None, type="primary"):
        with st.spinner("Searching…"):
            res = alg.brute_force(pn["n"], pn["p"], cfg["timeout"])
        st.session_state["bf_res"] = {**res, "p": pn["p"], "n": pn["n"]}
    res = st.session_state["bf_res"]
    if res and pn and res["p"] == pn["p"] and res["n"] == pn["n"]:
        if res["status"] == "found":
            r, p, n = res["r"], pn["p"], pn["n"]
            st.success(f"r = {r}   (other root: p − r = {p - r})")
            st.markdown("**Analysis table**")
            st.dataframe(pd.DataFrame([
                ("Bits of p", pn["bits"], "slider value"),
                ("p", p, "prime modulus"),
                ("n", n, "target"),
                ("r", r, "first r found with r² ≡ n"),
                ("p − r", p - r, "second root"),
                ("Iterations", res["iterations"], "values of r tried (= r + 1)"),
                ("Time", alg.fmt_time(res["time"]), "wall-clock time"),
                ("r² mod p", r * r % p, "must equal n"),
                ("Verified", r * r % p == n, ""),
            ], columns=["Parameter", "Value", "Note"]).astype(str),
                use_container_width=True, hide_index=True)
        elif res["status"] == "timeout":
            st.warning(f"Stopped after {alg.fmt_time(res['time'])} and {res['iterations']:,} tries "
                       f"(time limit {cfg['timeout']:g} s). Brute force is too slow for this size.")
        else:
            st.error(f"No square root exists: n is not a quadratic residue mod p "
                     f"(checked all {res['iterations']:,} values, {alg.fmt_time(res['time'])}).")

    st.divider()
    st.markdown("### 4️⃣ Workbench – many bit sizes")
    sel = bit_selector("bfwb", BF_OPTIONS, BF_PRESETS, BF_PRESETS[0][1])
    if st.button("🚀 Run workbench", key="bf_run", disabled=not sel, type="primary"):
        execute_workbench(["bf"], sel, cfg)
    workbench_output("bf", "Brute force", "bfchart")


# ----------------------------------------------------------------- page 2
def page_tonelli(cfg):
    st.title("⚡ Tonelli–Shanks algorithm")
    st.write("Finds r with **r² ≡ n (mod p)** in about O(log² p) steps — fast even for hundreds of bits.")
    with st.expander("How the algorithm works"):
        st.markdown("""
1. **Euler's criterion:** n^((p−1)/2) mod p must be 1, otherwise no root exists.
2. Write p − 1 = **Q · 2^S** with Q odd.
3. If S = 1 (p ≡ 3 mod 4):  r = n^((p+1)/4) mod p  – done.
4. Otherwise find a quadratic non-residue **z** and set  
   M = S, c = z^Q, t = n^Q, R = n^((Q+1)/2) (all mod p).
5. While t ≠ 1: find the least i (0 < i < M) with t^(2^i) = 1, let b = c^(2^(M−i−1)),  
   then M = i, c = b², t = t·b², R = R·b.
6. The answer is **r = R** (the other root is p − r).
""")
    pn = generate_block("ts", 4, 1024, 64, cfg)

    st.markdown("### 3️⃣ Find r with Tonelli–Shanks")
    if st.button("▶ Find r", key="ts_solve", disabled=pn is None, type="primary"):
        timed = alg.tonelli_shanks(pn["n"], pn["p"])           # clean timing
        traced = alg.tonelli_shanks(pn["n"], pn["p"], trace=True)  # variable trace
        traced["time"] = timed["time"]
        st.session_state["ts_res"] = {**traced, "p": pn["p"], "n": pn["n"]}
    res = st.session_state["ts_res"]
    if res and pn and res["p"] == pn["p"] and res["n"] == pn["n"]:
        if res["status"] == "found":
            r, p, n = res["r"], pn["p"], pn["n"]
            st.success(f"r found in {alg.fmt_time(res['time'])}   —   verified: r² mod p = n → {r * r % p == n}")
            st.code(f"r     = {r}\np - r = {p - r}", language=None)
            st.markdown("**Analysis table – variables**")
            st.dataframe(pd.DataFrame(res["vars"]), use_container_width=True, hide_index=True)
            if res["iterations"]:
                st.markdown("**Analysis table – main loop iterations**")
                st.dataframe(pd.DataFrame(res["iterations"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No loop iterations were needed (S = 1 shortcut, or t was already 1).")
        else:
            st.error("No square root exists: Euler's criterion gave p − 1, so n is a non-residue mod p.")
            st.dataframe(pd.DataFrame(res["vars"]), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 4️⃣ Workbench – many bit sizes")
    sel = bit_selector("tswb", TS_OPTIONS, TS_PRESETS, TS_PRESETS[1][1])
    if st.button("🚀 Run workbench", key="ts_run", disabled=not sel, type="primary"):
        execute_workbench(["ts"], sel, cfg)
    workbench_output("ts", "Tonelli–Shanks", "tschart")


# ----------------------------------------------------------------- page 3
def page_compare(cfg):
    st.title("⚔️ Brute force vs Tonelli–Shanks")
    st.write("Both algorithms get **identical (p, n)** inputs. Results are stored in each method's own "
             "workbench table, and the graph below compares everything collected so far.")
    sel = bit_selector("cmpwb", CMP_OPTIONS, CMP_PRESETS, CMP_PRESETS[1][1])
    st.caption("Brute force is skipped for larger sizes once it hits the time limit; Tonelli–Shanks keeps going.")
    if st.button("🚀 Run both algorithms", key="cmp_run", disabled=not sel, type="primary"):
        execute_workbench(["bf", "ts"], sel, cfg)

    df = combined_df(["bf", "ts"])
    st.markdown("#### 📈 Comparison graph")
    draw_chart(df, "Time vs bit length – brute force vs Tonelli–Shanks", "cmpchart")

    bf, ts = table_df("bf_rows"), table_df("ts_rows")
    if not bf.empty and not ts.empty:
        m = bf.merge(ts, on="Bits", suffixes=(" (BF)", " (TS)"))
        m = m.dropna(subset=["Time (ms) (BF)", "Time (ms) (TS)"])
        if not m.empty:
            st.markdown("#### 🏁 Head-to-head")
            out = pd.DataFrame({
                "Bits": m["Bits"],
                "Brute force (ms)": m["Time (ms) (BF)"],
                "Tonelli–Shanks (ms)": m["Time (ms) (TS)"],
                "Speed-up (BF / TS)": m["Time (ms) (BF)"] / m["Time (ms) (TS)"],
            })
            st.dataframe(out, use_container_width=True, hide_index=True, column_config={
                "Brute force (ms)": st.column_config.NumberColumn(format="%.5f"),
                "Tonelli–Shanks (ms)": st.column_config.NumberColumn(format="%.5f"),
                "Speed-up (BF / TS)": st.column_config.NumberColumn(format="%.1f ×"),
            })
    if not df.empty:
        st.markdown("#### 📋 Combined data")
        st.dataframe(df[["Algorithm"] + TABLE_COLS], use_container_width=True, hide_index=True,
                     column_config={"Time (ms)": TIME_FMT})
        st.download_button("⬇ Download CSV", df.to_csv(index=False), "comparison.csv", "text/csv")
    st.info("**Why the gap?** Brute force needs ≈ p/2 = 2^(bits−1) tries, so every extra bit doubles the time. "
            "Tonelli–Shanks needs only a handful of modular exponentiations, growing polynomially in the bit length.")


# ----------------------------------------------------------------- main
init_state()
page, cfg = sidebar()
if page == "Brute force":
    page_bruteforce(cfg)
elif page == "Tonelli–Shanks algorithm":
    page_tonelli(cfg)
else:
    page_compare(cfg)
