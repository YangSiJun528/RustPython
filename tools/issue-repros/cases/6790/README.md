# #6790 — Support xz

Original issue: [#6790](https://github.com/RustPython/RustPython/issues/6790)

## Reproduction procedure

The recorded comparison used macOS ARM64. Install Git, rustup and the Xcode Command Line Tools. For the repository's native build prerequisites, see [CONTRIBUTING.md](https://github.com/RustPython/RustPython/blob/f39b054b9c8cbbf884f53123eef028131789990c/CONTRIBUTING.md#setting-up-a-development-environment).

Run the shell blocks in order in the same Bash or Zsh session. Stop if checkout, build or version verification fails. The commands create two independent checkouts and build directories under a new temporary directory; keep `rustpython_repro_root` set for all subsequent steps. Keep both source directories until finished: historical binaries can retain standard-library paths from build time.

### 1. Check out the two recorded revisions

```sh
rustpython_repro_root="$(mktemp -d)"
(
  set -eu
  git init -q "$rustpython_repro_root/historical"
  git -C "$rustpython_repro_root/historical" fetch --depth 1 \
    https://github.com/RustPython/RustPython.git ed785e3d868966e2a5f7478632cabd5a630e6934
  git -C "$rustpython_repro_root/historical" checkout --detach FETCH_HEAD
  test "$(git -C "$rustpython_repro_root/historical" rev-parse HEAD)" = ed785e3d868966e2a5f7478632cabd5a630e6934
  git init -q "$rustpython_repro_root/current"
  git -C "$rustpython_repro_root/current" fetch --depth 1 \
    https://github.com/RustPython/RustPython.git f39b054b9c8cbbf884f53123eef028131789990c
  git -C "$rustpython_repro_root/current" checkout --detach FETCH_HEAD
  test "$(git -C "$rustpython_repro_root/current" rev-parse HEAD)" = f39b054b9c8cbbf884f53123eef028131789990c
)
```

### 2. Build and verify each interpreter

Historical: Rust **1.96.1**. Current: Rust **1.99.0**. Both builds use default features and the selected revision's committed `Cargo.lock` with `--locked`.

```sh
(
  set -eu
  rustup toolchain install 1.96.1 --profile minimal
  rustup toolchain install 1.99.0 --profile minimal
  cd "$rustpython_repro_root/historical"
  CARGO_BUILD_JOBS=2 cargo +1.96.1 build --release --locked \
    --target-dir "$rustpython_repro_root/target-historical"
  cd "$rustpython_repro_root/current"
  CARGO_BUILD_JOBS=2 cargo +1.99.0 build --release --locked \
    --target-dir "$rustpython_repro_root/target-current"
)
```

Check the embedded commit in each executable before running the reproducer. Both commands below must succeed; each prints `sys.version` and asserts the expected commit prefix. The version changes because a different compiled executable is selected. Shallow checkouts may change branch/tag text in the banner; the assertions verify the pinned commit.

```sh
(
  set -eu
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE
  RUSTPYTHONPATH="$rustpython_repro_root/historical/Lib" PYTHONDONTWRITEBYTECODE=1 \
    "$rustpython_repro_root/target-historical/release/rustpython" \
    -c 'import sys; print(sys.version); assert "ed785e3" in sys.version'
  RUSTPYTHONPATH="$rustpython_repro_root/current/Lib" PYTHONDONTWRITEBYTECODE=1 \
    "$rustpython_repro_root/target-current/release/rustpython" \
    -c 'import sys; print(sys.version); assert "f39b054" in sys.version'
)
```

Each interpreter below is paired with `Lib` from its own checkout. These revisions all have a top-level `Lib` directory.

### 3. Save the shared reproduction input

Write the input once; both runs below execute this exact file.

Both builds use their own `test.support` and lzma implementation. The input applies the decorator and actually invokes the wrapped function.

```sh
cat > "$rustpython_repro_root/repro.py" <<'PY'
import unittest

from test import support


def dummy():
    pass


selected = support.requires_lzma()(dummy)
print("skip", getattr(selected, "__unittest_skip__", False))
print("reason", getattr(selected, "__unittest_skip_why__", None))
try:
    selected()
    print("invoked", "success")
except unittest.SkipTest as exc:
    print("invoked", "SkipTest")
    print("skip_message", str(exc))
PY
```

### 4. Run the historical and current builds

Each command prints the process exit code, including expected failures, so an old-version exception does not prevent the current-version check. Compare the output with the table below.

**Historical:**

```sh
(
  cd "$rustpython_repro_root" || exit
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE
  if RUSTPYTHONPATH="$rustpython_repro_root/historical/Lib" PYTHONDONTWRITEBYTECODE=1 \
    "$rustpython_repro_root/target-historical/release/rustpython" \
    "$rustpython_repro_root/repro.py"; then
    printf 'exit_code=0\n'
  else
    printf 'exit_code=%s\n' "$?"
  fi
)
```

**Current:**

```sh
(
  cd "$rustpython_repro_root" || exit
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE
  if RUSTPYTHONPATH="$rustpython_repro_root/current/Lib" PYTHONDONTWRITEBYTECODE=1 \
    "$rustpython_repro_root/target-current/release/rustpython" \
    "$rustpython_repro_root/repro.py"; then
    printf 'exit_code=0\n'
  else
    printf 'exit_code=%s\n' "$?"
  fi
)
```

## Before and after

- **Before — [ed785e3d8689](https://github.com/RustPython/RustPython/commit/ed785e3d868966e2a5f7478632cabd5a630e6934) (source revision linked in the report):** The decorated function raises SkipTest: requires lzma.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** skip False; reason None; invoked success.

Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames are omitted only where noted; long stderr lines are wrapped for display. The full logs are linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>stdout</th>
<td valign="top"><pre><code>skip True
reason requires lzma
invoked SkipTest
skip_message requires lzma</code></pre></td>
<td valign="top"><pre><code>skip False
reason None
invoked success</code></pre></td>
</tr>
<tr>
<th>stderr</th>
<td valign="top"><em>No other output</em><p><em>8 interpreter cleanup warning lines omitted.</em></p></td>
<td valign="top"><em>No output</em></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

## Analysis and closure rationale

The unconditional `lzma = None` override was removed from `requires_lzma`. With the module available, `requires_lzma()(dummy)` now invokes the function successfully; the requested removal of the forced skip is complete.

[PR #7896](https://github.com/RustPython/RustPython/pull/7896): remove the unconditional lzma skip override.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).
- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
