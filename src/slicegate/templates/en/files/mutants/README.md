# Mutant suites

Each `*.toml` file is a suite (declare it in `tests/manifest.tsv`). Template:

```toml
zone = "K"
cmd = "python -m pytest -q tests/test_auth.py"

[[mutant]]
id = "auth-01"
file = "src/auth/login.py"
find = "if not verify(password, user.hash):"   # anchor: exactly once in the file
replace = "if False:"
why = "removes the password check ⇒ anyone can log in"
```

The command runs INSIDE THE COPY: it must import the copy's code — a package installed with `pip -e` points back to the
original checkout and makes every mutant "survive" falsely; for Python add `PYTHONPATH=src` to `cmd`.

Run: `slicegate mutants run` (full) · `slicegate mutants run --changed main` (by diff) · `MUT_ONLY=auth-01 slicegate mutants run`.
Anchor check (cheap, part of pre-push): `slicegate mutants anchors`.
