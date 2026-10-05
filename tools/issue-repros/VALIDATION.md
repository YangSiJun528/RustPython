# Bundle validation

Validated locally on October 5, 2026 (Asia/Seoul), with RustPython source at
`f39b054b9c8cbbf884f53123eef028131789990c`.

## Version-specific procedure checks

The documentation now provides separate checkout, build, version verification
and execution commands for both revisions in each of the 15 runtime cases.

- All 90 shell blocks passed Bash and Zsh syntax checks. Checkout SHAs, Rust
  toolchains, committed lockfile hashes and standard-library paths were checked
  against the recorded metadata. The 14 shared script inputs retain the same
  Python ASTs as the previous direct commands, including the original source
  string in the compile-only check.
- All 14 current native script commands were extracted from the documents and
  executed with the recorded, hash-verified macOS baseline binary. Expected
  exceptions, warnings and printed exit codes matched the case oracles.
- For #2527, both exact commits were fetched into new independent checkouts and
  built in the pinned Linux ARM64 Docker images, using Rust 1.47.0 and 1.99.0.
  Both embedded-commit assertions passed. The scoped Git `safe.directory` setup
  was also executed successfully in both images.
- Both documented REPL launch commands were run through a real PTY against
  those fresh builds with identical input. Historical: no expression values;
  current: 0–9 followed by 5. Both interpreters exited with code 0.
- Native historical build instructions were matched to their prior successful
  build records and unchanged committed lockfiles; those 14 historical builds
  were not repeated for this documentation revision.
- Reusing a moved historical native binary exposed its original build-time
  standard-library path. The new procedures therefore build each version in
  its own retained checkout; no result from that mismatched-library attempt
  was counted as a historical reproduction.
- A focused review passed. Runtime/oracle functions, the combined submission
  draft, inline output tables and all 84 exported log hashes remain unchanged.

## Earlier reproducer checks

- The revised reports contain direct interpreter commands. All 14 script commands
  were copied from the documents and executed successfully through the shell.
  The documented Linux REPL startup command and both input blocks also passed.
  These checks used the baseline binaries listed below.
- All 14 script checks passed on macOS ARM64 using the recorded baseline binary.
- Both #2527 blocks passed through the new PTY runner on Linux ARM64:
  the loop displayed 0–9 and the `with` block displayed 5.
- The #4784 read-only HTTP check returned the RustPython 0.6.0 API page.
- All 14 archived current script outcomes were accepted by the oracles, and all
  14 archived historical outcomes were rejected. Expected exceptions and warnings
  were checked independently of process exit success.
- Original input bytes and all 84 selected exported log hashes matched their
  recorded metadata, including the staged Git blobs.
- All local document links resolved; the combined issue draft contains 16 issue
  bullets with absolute links to the fork branch.
- Inline output tables in all 15 runtime reports were checked against the
  recorded stdout, stderr and exit codes. HTML escaping preserves diagnostic
  text; displayed excerpts and omissions are labeled. All 84 exported log
  hashes remain unchanged, and local document links resolve.

The initial Linux runner trial timed out because terminal redraw carriage
returns prevented prompt recognition. After correcting prompt detection, the
same two blocks completed successfully. Fresh run output remains local in the
Git-ignored `runs/` directory; the recorded October 4 evidence is unchanged.

## Baseline binaries

- macOS ARM64: `d04249e0bc754f7ccd12f373348e639275f7b1e3a248cb56b17a37faea974dbe`.
- Linux ARM64: `62edeb0a360f473213e907dea3c6706e6ed08034bd80976439310069adf7725c`.

Both version banners identify `f39b054b9`. Each fresh run records its supplied
binary, standard-library directory, input hash, interpreter version and outcome.

## Repository checks

The checks below use Rust 1.99.0, two build jobs, disabled incremental compilation
and debug info disabled for dev/test profiles. The C-API checks run from
`crates/capi` to apply its separate Cargo configuration.

- Passed: `cargo +1.99.0 test --locked --workspace --exclude rustpython_wasm --exclude rustpython-venvlauncher --exclude rustpython-capi`.
- Passed: `cargo +1.99.0 test --locked` (from `crates/capi`).
- Passed: `cargo +1.99.0 clippy --locked --workspace --all-targets --exclude rustpython_wasm --exclude rustpython-venvlauncher --exclude rustpython-capi`.
- Passed: `cargo +1.99.0 clippy --locked --all-targets` (from `crates/capi`).
