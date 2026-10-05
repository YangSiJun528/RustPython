# Bundle validation

Validated locally on October 5, 2026 (Asia/Seoul), with RustPython source at
`f39b054b9c8cbbf884f53123eef028131789990c`.

## Reviewer-facing layout and comparison checks

- All 16 reports now place the original input/expected outcome and observed
  results before environment setup. Fifteen runtime cases have a separate
  `BUILD.md`; their checkout, build and version-check shell blocks are unchanged.
  The combined bullet submission draft and manifest are unchanged.
- All 74 shell blocks passed Bash and Zsh syntax checks. Displayed Python inputs
  match their canonical files by AST. The #4856 source string has readable
  multiline formatting with identical compiled bytes; #4690 now displays both
  queries already present in its executable and recorded evidence.
- The 14 current native commands and 13 CPython commands were extracted from the
  reports and executed successfully, including the expected exception and warning.
  CPython 3.14.6 versions and input AST equivalence for the 13 archived references
  were recovered from the original survey; all 84 existing exported log hashes
  remain unchanged. #2527 adds a separately dated CPython 3.14.6 PTY run on macOS
  ARM64, with values 0–9 then 5; its platform difference is explicit in the report.
- The new #2527 shell loop was exercised for each phase through a real Docker
  PTY using the two retained fresh builds from the earlier procedure validation.
  Historical output: no expression values. Current output: 0–9 then 5.
  Both processes exited with code 0.
- #4762's historical commit was freshly checked out and built with the documented
  Rust 1.67.1 command. The new `--compare` command ran that executable, the
  hash-verified current baseline and CPython 3.14.6 on the same input:
  historical `AssertionError`/exit 1, current and CPython exit 0.
- Comparison checks rejected the wrong executable, wrong `Lib` tree, a local
  untracked `Lib` file and a copied checkout paired with an executable retaining
  the original build-time import path. Startup and execution timeouts were
  classified as `ERROR`, not historical bug reproduction. Other interpreters
  continued after a failed column. Controlled outcome checks covered expected
  `UnicodeEncodeError`/exit 1, missing `SyntaxWarning` and CPython's `CONFIG` value.
- A fresh historical build exposed that old RustPython's frozen `codecs` has no
  `__file__`. The environment probe therefore checks `os` and `json` paths,
  resolving the historical `pylib/Lib` symlink. The subsequent real comparison
  passed. Version checks are pairing checks, not build attestations.
- A focused review passed. Local documentation links resolve. The workspace and
  C-API tests and both Clippy commands listed below were rerun and passed.

Only #4762's historical native build was repeated for this layout revision;
other historical script results remain the preserved October 4 evidence. The
REPL comparison mode's native-Linux interface was not freshly built end to end;
the documented Docker/TTY commands were executed as described above. No new
HTTP check was needed for the unchanged #4784 dated observation.

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
