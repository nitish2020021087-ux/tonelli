# Modular Square Root Lab — r² ≡ n (mod p)

Streamlit app that finds `r` with **r² ≡ n (mod p)** using

* **Brute force** – tries every r (O(p), exponential in the bit length)
* **Tonelli–Shanks** – polynomial time, works for hundreds of bits
* **Comparison** – both algorithms on identical inputs, graphed together

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit UI (sidebar menu, 3 pages) |
| `algorithms.py` | prime generation, brute force, Tonelli–Shanks, workbench runner |
| `requirements.txt` | dependencies |

## Run in VS Code
```bash
# 1. open the folder in VS Code, then open the integrated terminal
python -m venv venv
venv\Scripts\activate          # Windows      (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```
The app opens at http://localhost:8501

## Using the app
1. Pick a method in the **left sidebar**.
2. Move the **bits slider**, press **Generate p and n**, then **Find r**.
3. Use the **workbench**: pick several bit sizes (or a preset button) → **Run workbench**.
   The table (bits, p, n, r, time) and the graph update automatically.
4. On **Brute force vs Tonelli–Shanks**, run both and compare the graph and speed-up table.

Sidebar settings: prime type (any / p≡1 mod 4 / p≡3 mod 4), guarantee n is a residue,
brute-force time limit, and trials per bit size (times are averaged).

## Host it (free) on Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. Go to https://share.streamlit.io → **New app** → choose the repo, branch and `app.py`.
3. Deploy — Streamlit installs `requirements.txt` automatically.

## Notes
* Brute-force bit sizes are limited to 4–48 and a time limit applies (Python is slow: ~2²⁵ is the practical ceiling in a few seconds).
* Tonelli–Shanks supports up to 1024 bits.
* Choosing **p ≡ 1 (mod 4)** makes Tonelli–Shanks run its full loop, which gives the richest analysis table.
