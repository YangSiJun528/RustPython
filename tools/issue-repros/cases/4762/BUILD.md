# Build the two revisions for #4762

[Case report and reproduction input](README.md)

The recorded comparison used macOS ARM64. Install Git, rustup and the Xcode Command Line Tools. For the repository's native build prerequisites, see [CONTRIBUTING.md](https://github.com/RustPython/RustPython/blob/f39b054b9c8cbbf884f53123eef028131789990c/CONTRIBUTING.md#setting-up-a-development-environment).

Run the shell blocks in order in the same Bash or Zsh session. Stop if checkout, build or version verification fails. The commands create two independent checkouts and build directories under a new temporary directory; keep `rustpython_repro_root` set for all subsequent steps. Keep both source directories until finished: historical binaries can retain standard-library paths from build time.

## 1. Check out the two recorded revisions

```sh
rustpython_repro_root="$(mktemp -d)"
(
  set -eu
  git init -q "$rustpython_repro_root/historical"
  git -C "$rustpython_repro_root/historical" fetch --depth 1 \
    https://github.com/RustPython/RustPython.git c36e3612e7dd1c7abd9fc7b76b912372bd26afbf
  git -C "$rustpython_repro_root/historical" checkout --detach FETCH_HEAD
  test "$(git -C "$rustpython_repro_root/historical" rev-parse HEAD)" = c36e3612e7dd1c7abd9fc7b76b912372bd26afbf
  git init -q "$rustpython_repro_root/current"
  git -C "$rustpython_repro_root/current" fetch --depth 1 \
    https://github.com/RustPython/RustPython.git f39b054b9c8cbbf884f53123eef028131789990c
  git -C "$rustpython_repro_root/current" checkout --detach FETCH_HEAD
  test "$(git -C "$rustpython_repro_root/current" rev-parse HEAD)" = f39b054b9c8cbbf884f53123eef028131789990c
)
```

## 2. Build and verify each interpreter

Historical: Rust **1.67.1**. Current: Rust **1.99.0**. Both builds use default features and the selected revision's committed `Cargo.lock` with `--locked`.

```sh
(
  set -eu
  rustup toolchain install 1.67.1 --profile minimal
  rustup toolchain install 1.99.0 --profile minimal
  cd "$rustpython_repro_root/historical"
  CARGO_BUILD_JOBS=2 cargo +1.67.1 build --release --locked \
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
    -c 'import sys; print(sys.version); assert "c36e361" in sys.version'
  RUSTPYTHONPATH="$rustpython_repro_root/current/Lib" PYTHONDONTWRITEBYTECODE=1 \
    "$rustpython_repro_root/target-current/release/rustpython" \
    -c 'import sys; print(sys.version); assert "f39b054" in sys.version'
)
```

Each interpreter below is paired with `Lib` from its own checkout. These revisions all have a top-level `Lib` directory.

Return to [Run](README.md#run) in the same shell to execute the shared input with both builds.
