# #2527 — expressions in blocks don't print their value in the REPL

Original issue: [#2527](https://github.com/RustPython/RustPython/issues/2527)

## Reproduction procedure

The recorded comparison used Linux ARM64 in Docker. Install Git and Docker with Linux ARM64 support; the commands pin the two recorded Rust images by digest.

Run the shell blocks in order in the same Bash or Zsh session. Stop if checkout, build or version verification fails. The commands create two independent checkouts and build directories under a new temporary directory; keep `rustpython_repro_root` set for all subsequent steps. Keep both source directories until finished: historical binaries can retain standard-library paths from build time.

### 1. Check out the two recorded revisions

```sh
rustpython_repro_root="$(mktemp -d)"
(
  set -eu
  git init -q "$rustpython_repro_root/historical"
  git -C "$rustpython_repro_root/historical" fetch --depth 1 \
    https://github.com/RustPython/RustPython.git 163cd1953377f4049e06fdae55c715889857a301
  git -C "$rustpython_repro_root/historical" checkout --detach FETCH_HEAD
  test "$(git -C "$rustpython_repro_root/historical" rev-parse HEAD)" = 163cd1953377f4049e06fdae55c715889857a301
  git init -q "$rustpython_repro_root/current"
  git -C "$rustpython_repro_root/current" fetch --depth 1 \
    https://github.com/RustPython/RustPython.git f39b054b9c8cbbf884f53123eef028131789990c
  git -C "$rustpython_repro_root/current" checkout --detach FETCH_HEAD
  test "$(git -C "$rustpython_repro_root/current" rev-parse HEAD)" = f39b054b9c8cbbf884f53123eef028131789990c
)
```

### 2. Build and verify each interpreter

Historical: Rust **1.47.0**. Current: Rust **1.99.0**. Both builds use default features and the selected revision's committed `Cargo.lock` with `--locked`.

```sh
rustpython_repro_historical_image="rust@sha256:48f4b36c3f3492b82a5e14b2fc991d3163c1d2ce18ac1f0561e9657103192713"
rustpython_repro_current_image="rust@sha256:cb1b90b0ce00f9eb950c4de62cc1bb89c7bf8a3577de6600d10e31fb15f876de"
(
  set -eu
  mkdir -p "$rustpython_repro_root/target-historical"
  docker run --rm --platform linux/arm64 --cpus 2 --memory 4g \
    --mount "type=bind,source=$rustpython_repro_root/historical,target=/repo,readonly" \
    --mount "type=bind,source=$rustpython_repro_root/target-historical,target=/target" \
    --env CARGO_BUILD_JOBS=2 --env RUSTUP_TOOLCHAIN=1.47.0 \
    --workdir /repo "$rustpython_repro_historical_image" \
    sh -c 'git config --global --add safe.directory /repo && cargo build --release --locked --target-dir /target'
  mkdir -p "$rustpython_repro_root/target-current"
  docker run --rm --platform linux/arm64 --cpus 2 --memory 4g \
    --mount "type=bind,source=$rustpython_repro_root/current,target=/repo,readonly" \
    --mount "type=bind,source=$rustpython_repro_root/target-current,target=/target" \
    --env CARGO_BUILD_JOBS=2 --env RUSTUP_TOOLCHAIN=1.99.0 \
    --workdir /repo "$rustpython_repro_current_image" \
    sh -c 'git config --global --add safe.directory /repo && cargo build --release --locked --target-dir /target'
)
```

Check the embedded commit in each executable before running the reproducer. Both commands below must succeed; each prints `sys.version` and asserts the expected commit prefix. The version changes because a different compiled executable is selected. Shallow checkouts may change branch/tag text in the banner; the assertions verify the pinned commit.

```sh
(
  set -eu
  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE
  docker run --rm --platform linux/arm64 --network none \
    --mount "type=bind,source=$rustpython_repro_root/historical,target=/repo,readonly" \
    --mount "type=bind,source=$rustpython_repro_root/target-historical,target=/target,readonly" \
    --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \
    --workdir /repo "$rustpython_repro_historical_image" \
    /target/release/rustpython -c 'import sys; print(sys.version); assert "163cd19" in sys.version'
  docker run --rm --platform linux/arm64 --network none \
    --mount "type=bind,source=$rustpython_repro_root/current,target=/repo,readonly" \
    --mount "type=bind,source=$rustpython_repro_root/target-current,target=/target,readonly" \
    --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \
    --workdir /repo "$rustpython_repro_current_image" \
    /target/release/rustpython -c 'import sys; print(sys.version); assert "f39b054" in sys.version'
)
```

Each interpreter below is paired with `Lib` from its own checkout. These revisions all have a top-level `Lib` directory.

### 3. Run the historical interpreter interactively

Run this in a terminal with a TTY. The container uses its matching checkout and executable and writes REPL history/output only in its scratch directory.

```sh
mkdir -p "$rustpython_repro_root/scratch-historical/config/rustpython"
docker run --rm -it --platform linux/arm64 --network none \
  --mount "type=bind,source=$rustpython_repro_root/historical,target=/repo,readonly" \
  --mount "type=bind,source=$rustpython_repro_root/target-historical,target=/target,readonly" \
  --mount "type=bind,source=$rustpython_repro_root/scratch-historical,target=/scratch" \
  --env TERM=xterm --env XDG_CONFIG_HOME=/scratch/config \
  --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \
  --workdir /scratch "$rustpython_repro_historical_image" \
  /target/release/rustpython
```

Enter these lines at the Python prompts. Press Enter on an empty line after each indented block, wait for the primary prompt, then enter the next block. Use these same inputs for both versions:

```python
for i in range(10):
    i

with open("repl-output.txt", "w") as f:
    f.write("hello")
```

Neither block should display expression values on this historical build. After both blocks return to the primary prompt, enter `exit()` to return to the shell before continuing.

### 4. Run the current interpreter interactively

Run this in a terminal with a TTY. The container uses its matching checkout and executable and writes REPL history/output only in its scratch directory.

```sh
mkdir -p "$rustpython_repro_root/scratch-current/config/rustpython"
docker run --rm -it --platform linux/arm64 --network none \
  --mount "type=bind,source=$rustpython_repro_root/current,target=/repo,readonly" \
  --mount "type=bind,source=$rustpython_repro_root/target-current,target=/target,readonly" \
  --mount "type=bind,source=$rustpython_repro_root/scratch-current,target=/scratch" \
  --env TERM=xterm --env XDG_CONFIG_HOME=/scratch/config \
  --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \
  --workdir /scratch "$rustpython_repro_current_image" \
  /target/release/rustpython
```

Enter these lines at the Python prompts. Press Enter on an empty line after each indented block, wait for the primary prompt, then enter the next block. Use these same inputs for both versions:

```python
for i in range(10):
    i

with open("repl-output.txt", "w") as f:
    f.write("hello")
```

The loop should display 0 through 9, and the `with` block should display 5. After both blocks return to the primary prompt, enter `exit()` to return to the shell before continuing.

## Before and after

- **Before — [163cd1953377](https://github.com/RustPython/RustPython/commit/163cd1953377f4049e06fdae55c715889857a301) (nearest pre-issue main revision; approximate baseline):** Neither block displayed its expression values.
- **After — [f39b054b9c8c](https://github.com/RustPython/RustPython/commit/f39b054b9c8cbbf884f53123eef028131789990c):** The loop displays 0 through 9; the with block displays 5.

The table extracts the expression values from the recorded terminal session, in execution order. Startup text, prompts, echoed input and terminal control sequences are omitted. The PTY recording combines stdout and stderr; the full transcript is linked below.

<table>
<thead><tr><th>Output</th><th>Historical</th><th>Current</th></tr></thead>
<tbody>
<tr>
<th>REPL expression output</th>
<td valign="top"><em>No output</em></td>
<td valign="top"><pre><code>0
1
2
3
4
5
6
7
8
9
5</code></pre></td>
</tr>
<tr>
<th>Exit code</th>
<td valign="top"><code>0</code></td>
<td valign="top"><code>0</code></td>
</tr>
</tbody>
</table>

## Analysis and closure rationale

Interactive compilation now emits expression output inside module-level blocks. The original loop displays 0–9 and the `with` block displays 5, resolving both missing-output examples on Linux with `TERM=xterm`.

[PR #7067](https://github.com/RustPython/RustPython/pull/7067): interactive expression handling in nested blocks.

These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.

## Recorded evidence

- [Execution metadata, toolchain and log hashes](evidence/metadata.json).
- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).

AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.
