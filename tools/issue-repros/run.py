#!/usr/bin/env python3
"""Run selected RustPython issue reproducers and write local per-issue reports."""

import argparse
import datetime
import hashlib
import html
import json
import os
import platform
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def check_result(expected, result):
    if result.get("timeout") or result.get("error"):
        return False
    if result["exit_code"] != expected["exit_code"]:
        return False
    for stream in ("stdout", "stderr"):
        text = result[stream]
        if stream in expected and text != expected[stream]:
            return False
        if stream + "_prefix" in expected and not text.startswith(
            expected[stream + "_prefix"]
        ):
            return False
        if any(value not in text for value in expected.get(stream + "_contains", [])):
            return False
    return True


def run_script(command, env, cwd, timeout):
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    ) as process:
        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    return {
        "exit_code": process.returncode,
        "timeout": timed_out,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
    }


def run_repl(binary, source, env, cwd, timeout):
    import fcntl
    import pty
    import select
    import struct
    import termios

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 120, 0, 0))
    process = subprocess.Popen(
        [str(binary)],
        cwd=cwd,
        env=env,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        start_new_session=True,
    )
    os.close(slave)
    output = bytearray()
    deadline = time.monotonic() + timeout
    sent = []
    prompts = []
    cursor_answers = 0

    def read_chunk():
        nonlocal cursor_answers
        if select.select([master], [], [], 0.05)[0]:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                return
            output.extend(chunk)
            queries = output.count(b"\x1b[6n")
            for _ in range(queries - cursor_answers):
                os.write(master, b"\x1b[1;1R")
            cursor_answers = queries

    def await_prompt(offset):
        while time.monotonic() < deadline:
            read_chunk()
            clean = ANSI.sub(
                "", output[offset:].decode("utf-8", errors="replace")
            ).replace("\r", "")
            match = re.search(r"(?:^|[\r\n])(>{3,5}|\.{3,5}) $", clean)
            if match:
                prompts.append(match[1])
                return match[1]
            if process.poll() is not None:
                raise RuntimeError("REPL exited before returning a prompt")
        raise TimeoutError("REPL did not return a prompt")

    error = None
    timed_out = False
    try:
        await_prompt(0)
        # Keep both original blank block terminators; a script invocation would
        # not exercise interactive expression display.
        for line in source.rstrip().splitlines() + [""]:
            offset = len(output)
            os.write(master, (line + "\n").encode())
            sent.append(line)
            prompt = await_prompt(offset)
            if not line and not prompt.startswith(">"):
                raise RuntimeError(
                    "Compound statement did not return to primary prompt"
                )
        os.write(master, b"exit()\n")
        sent.append("exit()")
        while process.poll() is None and time.monotonic() < deadline:
            read_chunk()
        if process.poll() is None:
            raise TimeoutError("REPL did not exit")
        read_chunk()
    except (RuntimeError, TimeoutError, OSError) as exc:
        error = str(exc)
        timed_out = isinstance(exc, TimeoutError)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        os.close(master)
    text = output.decode("utf-8", errors="replace")
    clean = ANSI.sub("", text).replace("\r", "")
    values = re.findall(r"(?m)^([0-9]+)$", clean)
    return {
        "exit_code": process.returncode,
        "timeout": timed_out,
        "error": error,
        "stdout": text,
        "stderr": "",
        "sent_input": "\n".join(sent) + "\n",
        "prompts": prompts,
        "displayed_values": values,
        "passed": error is None
        and process.returncode == 0
        and values == [str(i) for i in range(10)] + ["5"],
    }


def reproduction_setup(item):
    case = BUNDLE / "cases" / str(item["issue"])
    runs = json.loads((case / "evidence/metadata.json").read_text())["runs"]
    phases = ("historical", "current")
    versions = {
        phase: re.search(r"rustc (\d+\.\d+\.\d+)", runs[phase]["build"]["toolchain"])[1]
        for phase in phases
    }
    is_repl = item["kind"] == "repl"
    environment = (
        "The recorded comparison used Linux ARM64 in Docker. Install Git and Docker with Linux ARM64 support; the commands pin the two recorded Rust images by digest."
        if is_repl
        else "The recorded comparison used macOS ARM64. Install Git, rustup and the Xcode Command Line Tools. For the repository's native build prerequisites, see [CONTRIBUTING.md](https://github.com/RustPython/RustPython/blob/f39b054b9c8cbbf884f53123eef028131789990c/CONTRIBUTING.md#setting-up-a-development-environment)."
    )
    lines = [
        environment,
        "",
        "Run the shell blocks in order in the same Bash or Zsh session. Stop if checkout, build or version verification fails. The commands create two independent checkouts and build directories under a new temporary directory; keep `rustpython_repro_root` set for all subsequent steps. Keep both source directories until finished: historical binaries can retain standard-library paths from build time.",
        "",
        "## 1. Check out the two recorded revisions",
        "",
        "```sh",
        'rustpython_repro_root="$(mktemp -d)"',
        "(",
        "  set -eu",
    ]
    for phase in phases:
        sha = runs[phase]["actual_sha"]
        source = f'"$rustpython_repro_root/{phase}"'
        lines.extend(
            [
                f"  git init -q {source}",
                f"  git -C {source} fetch --depth 1 \\",
                f"    https://github.com/RustPython/RustPython.git {sha}",
                f"  git -C {source} checkout --detach FETCH_HEAD",
                f'  test "$(git -C {source} rev-parse HEAD)" = {sha}',
            ]
        )
    lines.extend(
        [
            ")",
            "```",
            "",
            "## 2. Build and verify each interpreter",
            "",
            f"Historical: Rust **{versions['historical']}**. Current: Rust **{versions['current']}**. Both builds use default features and the selected revision's committed `Cargo.lock` with `--locked`.",
            "",
            "```sh",
        ]
    )
    if is_repl:
        for phase in phases:
            lines.append(
                f'rustpython_repro_{phase}_image="{runs[phase]["build"]["image_digest"]}"'
            )
        lines.extend(["(", "  set -eu"])
        for phase in phases:
            lines.extend(
                [
                    f'  mkdir -p "$rustpython_repro_root/target-{phase}"',
                    "  docker run --rm --platform linux/arm64 --cpus 2 --memory 4g \\",
                    f'    --mount "type=bind,source=$rustpython_repro_root/{phase},target=/repo,readonly" \\',
                    f'    --mount "type=bind,source=$rustpython_repro_root/target-{phase},target=/target" \\',
                    f"    --env CARGO_BUILD_JOBS=2 --env RUSTUP_TOOLCHAIN={versions[phase]} \\",
                    f'    --workdir /repo "$rustpython_repro_{phase}_image" \\',
                    "    sh -c 'git config --global --add safe.directory /repo && cargo build --release --locked --target-dir /target'",
                ]
            )
        lines.append(")")
    else:
        lines.extend(["(", "  set -eu"])
        for version in dict.fromkeys(versions.values()):
            lines.append(f"  rustup toolchain install {version} --profile minimal")
        for phase in phases:
            lines.extend(
                [
                    f'  cd "$rustpython_repro_root/{phase}"',
                    f"  CARGO_BUILD_JOBS=2 cargo +{versions[phase]} build --release --locked \\",
                    f'    --target-dir "$rustpython_repro_root/target-{phase}"',
                ]
            )
        lines.append(")")
    lines.extend(
        [
            "```",
            "",
            "Check the embedded commit in each executable before running the reproducer. Both commands below must succeed; each prints `sys.version` and asserts the expected commit prefix. The version changes because a different compiled executable is selected. Shallow checkouts may change branch/tag text in the banner; the assertions verify the pinned commit.",
            "",
            "```sh",
            "(",
            "  set -eu",
            "  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE",
        ]
    )
    for phase in phases:
        check = shlex.quote(
            f'import sys; print(sys.version); assert "{runs[phase]["actual_sha"][:7]}" in sys.version'
        )
        if is_repl:
            lines.extend(
                [
                    "  docker run --rm --platform linux/arm64 --network none \\",
                    f'    --mount "type=bind,source=$rustpython_repro_root/{phase},target=/repo,readonly" \\',
                    f'    --mount "type=bind,source=$rustpython_repro_root/target-{phase},target=/target,readonly" \\',
                    "    --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \\",
                    f'    --workdir /repo "$rustpython_repro_{phase}_image" \\',
                    f"    /target/release/rustpython -c {check}",
                ]
            )
        else:
            lines.extend(
                [
                    f'  RUSTPYTHONPATH="$rustpython_repro_root/{phase}/Lib" PYTHONDONTWRITEBYTECODE=1 \\',
                    f'    "$rustpython_repro_root/target-{phase}/release/rustpython" \\',
                    f"    -c {check}",
                ]
            )
    lines.extend(
        [
            ")",
            "```",
            "",
            "Each interpreter below is paired with `Lib` from its own checkout. These revisions all have a top-level `Lib` directory.",
            "",
        ]
    )
    return lines


def reproduction_steps(item):
    """Short direct commands; exact checkout/build instructions live in BUILD.md."""
    if item["kind"] == "documentation":
        return [
            "```sh",
            "curl --fail --location https://docs.rs/rustpython",
            "```",
            "",
            "Follow redirects and inspect the API page. An HTTP 200 response alone is insufficient: the old crate landing page also returns 200.",
        ]
    steps = [
        "First complete [BUILD.md](BUILD.md) in the same shell. It creates `rustpython_repro_root`, builds both pinned commits and verifies their versions. Keep both checkouts while running these commands.",
        "",
    ]
    if item["kind"] == "repl":
        steps.extend(
            [
                "Run in a terminal with a TTY. For **each** interpreter, enter the input above, press Enter on an empty line after each indented block, then enter `exit()`. The loop starts historical first, then current. A script or piped stdin does not test interactive display.",
                "",
                "```sh",
                "for phase in historical current; do",
                '  if [ "$phase" = historical ]; then',
                '    rustpython_repro_image="$rustpython_repro_historical_image"',
                "  else",
                '    rustpython_repro_image="$rustpython_repro_current_image"',
                "  fi",
                '  printf "\\n%s REPL\\n" "$phase"',
                '  mkdir -p "$rustpython_repro_root/scratch-$phase/config/rustpython"',
                "  docker run --rm -it --platform linux/arm64 --network none \\",
                '    --mount "type=bind,source=$rustpython_repro_root/$phase,target=/repo,readonly" \\',
                '    --mount "type=bind,source=$rustpython_repro_root/target-$phase,target=/target,readonly" \\',
                '    --mount "type=bind,source=$rustpython_repro_root/scratch-$phase,target=/scratch" \\',
                "    --env TERM=xterm --env XDG_CONFIG_HOME=/scratch/config \\",
                "    --env RUSTPYTHONPATH=/repo/Lib --env PYTHONDONTWRITEBYTECODE=1 \\",
                '    --workdir /scratch "$rustpython_repro_image" /target/release/rustpython',
                "done",
                "```",
                "",
                "For the CPython reference, start `PYTHON_BASIC_REPL=1 python3.14` in a disposable directory and enter the same blocks interactively. Record `python3.14 -VV` first.",
            ]
        )
        return steps
    steps.extend(
        [
            "Save the code above as `$rustpython_repro_root/repro.py` (or copy the linked `repro.py` there). Both versions execute this one file, each with its matching standard library:",
            "",
            "```sh",
            "(",
            '  cd "$rustpython_repro_root" || exit',
            "  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE",
            "  for phase in historical current; do",
            '    printf "\\n%s\\n" "$phase"',
            '    if RUSTPYTHONPATH="$rustpython_repro_root/$phase/Lib" PYTHONDONTWRITEBYTECODE=1 \\',
            '      "$rustpython_repro_root/target-$phase/release/rustpython" \\',
            '      "$rustpython_repro_root/repro.py"; then',
            "      printf 'exit_code=0\\n'",
            "    else",
            "      printf 'exit_code=%s\\n' \"$?\"",
            "    fi",
            "  done",
            ")",
            "```",
        ]
    )
    if item["issue"] != 6790:
        steps.extend(
            [
                "",
                "CPython reference (3.14.6 in the recorded comparison):",
                "",
                "```sh",
                "(",
                '  cd "$rustpython_repro_root" || exit',
                "  unset PYTHONHOME PYTHONPATH PYTHONWARNINGS PYTHONOPTIMIZE RUSTPYTHONPATH",
                "  python3.14 -VV",
                '  if PYTHONDONTWRITEBYTECODE=1 python3.14 "$rustpython_repro_root/repro.py"; then',
                "    printf 'exit_code=0\\n'",
                "  else",
                "    printf 'exit_code=%s\\n' \"$?\"",
                "  fi",
                ")",
                "```",
            ]
        )
    steps.extend(
        [
            "",
            "To run the comparison and capture all outputs together, use the optional [comparison command](../../README.md#compare-both-revisions-at-once). Direct commands above do not require that runner.",
        ]
    )
    return steps


def historical_label(item):
    sha = item["historical_sha"]
    if not sha:
        return "Original documentation-link report"
    if item["issue"] == 4856:
        selection = "reported v0.2.0 release tag"
    elif item["issue"] in (4908, 4937):
        selection = "revision identified in the report"
    elif item["issue"] == 6790:
        selection = "source revision linked in the report"
    else:
        selection = "nearest pre-issue main revision; approximate baseline"
    return f"[{sha[:12]}](https://github.com/RustPython/RustPython/commit/{sha}) ({selection})"


def recorded_output_table(item):
    """Display selected recorded output without changing the evidence files."""
    case = BUNDLE / "cases" / str(item["issue"])
    metadata = json.loads((case / "evidence/metadata.json").read_text())
    reference = case / "evidence/reference.json"
    phases = ["historical", "current"]
    if reference.exists():
        ref = json.loads(reference.read_text())
        phases.insert(0, "cpython")
        if "run" in ref:
            metadata["runs"]["cpython"] = ref["run"]
    is_repl = item["kind"] == "repl"
    rows = []
    for stream in ("stdout",) if is_repl else ("stdout", "stderr"):
        cells = []
        for phase in phases:
            output = (case / "evidence" / f"{phase}.{stream}.txt").read_text()
            notes = []
            if is_repl:
                clean = ANSI.sub("", output).replace("\r", "")
                output = "\n".join(re.findall(r"(?m)^([0-9]+)$", clean))
            elif stream == "stderr":
                lines = output.splitlines()
                retained = [
                    line
                    for line in lines
                    if not (
                        re.match(r"\[(?:WARN\s|[^\]]+ WARN\s)", line)
                        and line.endswith("couldn't run __del__ method for object")
                    )
                ]
                omitted = len(lines) - len(retained)
                if omitted:
                    notes.append(
                        f"{omitted} interpreter cleanup warning lines omitted."
                    )
                if retained and retained[0] == "Traceback (most recent call last):":
                    diagnostic = next(
                        (
                            index
                            for index, line in enumerate(retained[1:], 1)
                            if line and not line[0].isspace()
                        ),
                        0,
                    )
                    if diagnostic:
                        notes.append(
                            f"{diagnostic} traceback header/frame lines omitted."
                        )
                        retained = retained[diagnostic:]
                output = "\n".join(
                    "\n".join(
                        textwrap.wrap(
                            line,
                            width=64,
                            break_long_words=False,
                            break_on_hyphens=False,
                        )
                    )
                    for line in retained
                )
            output = output.rstrip("\n")
            if output:
                cell = f"<pre><code>{html.escape(output, quote=False)}</code></pre>"
            else:
                empty = "No other output" if notes else "No output"
                cell = f"<em>{empty}</em>"
            for note in notes:
                cell += f"<p><em>{note}</em></p>"
            cells.append(cell)
        label = "REPL expression output" if is_repl else stream
        rows.append((label, cells))
    rows.append(
        (
            "Exit code",
            [
                f"<code>{metadata['runs'][phase]['exit_code']}</code>"
                for phase in phases
            ],
        )
    )
    if is_repl:
        note = (
            "The table extracts the expression values from the recorded terminal session, in execution order. "
            "Startup text, prompts, echoed input and terminal control sequences are omitted. "
            "The PTY recording combines stdout and stderr; the full transcript is linked below."
        )
    else:
        note = (
            "Recorded output is shown below. Repeated interpreter cleanup warnings and traceback frames "
            "are omitted only where noted; long stderr lines are wrapped for display. "
            "The full logs are linked below."
        )
    lines = [
        note,
        "",
        "<table>",
        "<thead><tr><th>Output</th>"
        + ("<th>CPython 3.14.6</th>" if "cpython" in phases else "")
        + "<th>RustPython before</th><th>RustPython after</th></tr></thead>",
        "<tbody>",
    ]
    for label, cells in rows:
        lines.extend(
            [
                "<tr>",
                f"<th>{label}</th>",
                *(f'<td valign="top">{cell}</td>' for cell in cells),
                "</tr>",
            ]
        )
    lines.extend(["</tbody>", "</table>", ""])
    return lines


def render_recorded(manifest):
    sha = manifest["baseline_sha"]
    current_link = (
        f"[{sha[:12]}](https://github.com/RustPython/RustPython/commit/{sha})"
    )
    submission_results = {
        2527: (
            "REPL expressions inside blocks",
            "The original loop and `with` block previously displayed no expression values. "
            "They now display `0`–`9` and `5`, respectively, in the Linux REPL with `TERM=xterm`.",
        ),
        3418: (
            "Native `OrderedDict` export",
            "`from _collections import OrderedDict` previously raised `ImportError`. "
            "The native implementation is now exported and the import succeeds.",
        ),
        3430: (
            "ElementTree parsing valid XML",
            '`etree.XML("<root></root>")` previously raised a `TypeError` for a `None` encoding. '
            "It now returns an empty `root` element; the parser accepts that encoding argument.",
        ),
        4527: (
            "Finalization of a global object",
            "The original object's `__del__` previously produced no output at shutdown. "
            "It now prints `deleted!` when the interpreter clears the module globals.",
        ),
        4690: (
            "Native class-method descriptor type",
            '`type(dict.__dict__["fromkeys"]).__name__` now returns '
            "`classmethod_descriptor` instead of `classmethod`, matching CPython. "
            "Native class methods use the dedicated descriptor type.",
        ),
        4762: (
            "Negative dynamic format width",
            "The original `'%*s' % (-5, 'abc') == 'abc  '` assertion now passes. "
            "Negative width selects left alignment, including the required two trailing spaces.",
        ),
        4784: (
            "README API documentation link",
            "The linked docs.rs page previously reported that `rustpython-0.1.2` was not a library. "
            "The README destination now serves the published RustPython 0.6.0 API documentation.",
        ),
        4786: (
            "Surrogate in a type name",
            '`type("A\\udcdcB", (), {})` previously created a class with a replacement character. '
            "It now raises the expected `UnicodeEncodeError`: the literal preserves the surrogate "
            "and type-name validation rejects it.",
        ),
        4856: (
            "Compiler panic with a lambda in a class decorator",
            "Compiling the original decorated-class source now succeeds without the "
            "`table.sub_tables.is_empty()` panic. Decorator scope scanning now matches "
            "code-generation order.",
        ),
        4908: (
            "AST round trip for a starred subscript",
            "Unparsing `A[1:2, *l]` previously produced invalid `A[(1:2, *l)]`. "
            "It now preserves valid subscript syntax and reparses successfully.",
        ),
        4937: (
            "Email Subject with an unknown encoding",
            "Retrieving the original X-encoded Subject now completes without `KeyError: x`. "
            "The email parser handles the unknown encoded-word encoding through its invalid-input recovery.",
        ),
        5181: (
            "Locale-aware `n` formatting",
            "With `en_US.UTF-8` selected, `format(123456789, 'n')` now returns "
            "`'123,456,789'` instead of `'123456789'`, using the locale's grouping and separator.",
        ),
        5656: (
            "Invalid escape warning in a bytes literal",
            "The original bytes assertion still passes, but compilation now emits the previously "
            "missing `SyntaxWarning` for `\\X`. Both the bytes value and the warning were checked.",
        ),
        6429: (
            "`Py_GIL_DISABLED` configuration value",
            "`sysconfig.get_config_var('Py_GIL_DISABLED')` now returns `1` instead of `None` "
            "on the tested POSIX/macOS build. The value is defined in the build-time configuration.",
        ),
        6790: (
            "Forced lzma test skip",
            "The unconditional `lzma = None` override has been removed. With lzma available, "
            "`requires_lzma()(dummy)` now invokes the function instead of raising `SkipTest`, "
            "satisfying the requested removal of the forced skip.",
        ),
        8052: (
            "Ellipsis type name",
            "`type(...).__name__` and the type's repr now give `ellipsis` and "
            "`<class 'ellipsis'>`, matching CPython, in place of the previous `EllipsisType` spelling.",
        ),
    }
    aggregate = [
        "# Review 16 resolved issues for closure",
        "",
        "I rechecked the 16 reports below and found that their reported failures or missing behaviors are resolved. "
        "Could you review these results and close the corresponding issues?",
        "",
        f"Verification used {current_link} on October 4, 2026: macOS ARM64 for the script comparisons, "
        "Linux ARM64 for the interactive REPL, and a separate HTTP check for the documentation link. "
        "Each linked report contains direct reproduction commands, historical/current results and supporting evidence.",
        "",
        "The related PRs contain source changes matching these results; the exact first fixing commit was not established.",
        "",
    ]
    index = []
    for item in manifest["issues"]:
        number = item["issue"]
        case = BUNDLE / "cases" / str(number)
        title = f"#{number} — {item['title']}"
        historical = historical_label(item)
        steps = reproduction_steps(item)
        index.append(f"- [{title}](cases/{number}/README.md)")
        subject, comparison = submission_results[number]
        aggregate.extend(
            [
                f"- **[#{number}]({item['url']}) — {subject}.**",
                f"  {comparison}",
                f"  {item['references']} "
                f"[Reproduction and results](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/{number}/README.md).",
                "",
            ]
        )
        text = [
            f"# {title}",
            "",
            f"Original issue: [#{number}]({item['url']})",
            "",
            f"**Verified closure candidate:** {comparison}",
            "",
        ]
        if item["historical_sha"]:
            text.extend(
                [
                    f"**Tested commits:** before `{item['historical_sha'][:12]}` → after `{sha[:12]}` (October 4, 2026). Historical selection and full build details are below.",
                    "",
                    "## Reproducer",
                    "",
                    f"Canonical input: [{item['input']}]({item['input']}). "
                    + item["derivation"],
                    "",
                ]
            )
            if number == 4856:
                text.extend(
                    [
                        "Compile only: the application names in this source need not exist because the source is never executed.",
                        "",
                    ]
                )
            if number == 5181:
                text.extend(
                    ["Requires the `en_US.UTF-8` system locale (`locale -a`).", ""]
                )
            if number == 2527:
                text.extend(
                    [
                        "Enter the following in a real REPL, with a blank line after each indented block.",
                        "",
                    ]
                )
            text.extend(
                [
                    "```python",
                    (case / item["input"]).read_text().rstrip(),
                    "```",
                    "",
                    "## Expected and observed results",
                    "",
                    f"**Expected:** {item['current_summary']}",
                    "",
                ]
            )
            if number == 6429:
                text.extend(
                    [
                        "CPython's recorded GIL-enabled build reports `0`; the RustPython POSIX build reports `1`. This is a build-configuration check: equality with CPython is not the oracle, and this probe does not establish general free-threading compatibility.",
                        "",
                    ]
                )
            elif number == 6790:
                text.extend(
                    [
                        "This checks RustPython's `test.support.requires_lzma` gate with lzma available. No CPython column is used: the reported defect is RustPython's forced skip. Successful invocation does not establish complete XZ support.",
                        "",
                    ]
                )
            elif number == 2527:
                text.extend(
                    [
                        "The CPython 3.14.6 reference was recorded separately on macOS ARM64 on October 5; both RustPython runs were on Linux ARM64. The same block input was sent through a PTY in all three runs.",
                        "",
                    ]
                )
            text.extend(recorded_output_table(item))
        else:
            text.extend(
                [
                    "## Expected and observed results",
                    "",
                    "**Expected:** the README link opens published RustPython API documentation.",
                    "",
                    f"- **Before (original report):** {item['historical_summary']}",
                    f"- **After (checked October 4, 2026):** {item['current_summary']}",
                    "- The recorded request followed redirects to `https://docs.rs/rustpython/latest/rustpython/` (HTTP 200). The page content was checked separately from the HTTP status.",
                    "- CPython and interpreter build comparisons do not apply to this documentation-link issue.",
                    "",
                ]
            )
        text.extend(
            [
                "## Run",
                "",
                *steps,
                "",
                "## Analysis and closure rationale",
                "",
                item["reason_to_close"],
                "",
                item["references"],
                "",
            ]
        )
        if item["historical_sha"]:
            runs = json.loads((case / "evidence/metadata.json").read_text())["runs"]
            versions = {
                phase: runs[phase]["build"]["toolchain"].splitlines()[0]
                for phase in ("historical", "current")
            }
            text.extend(
                [
                    "These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.",
                    "",
                    "## Versions and environment",
                    "",
                    f"- **Before:** {historical}.",
                    f"- **After:** {current_link}.",
                    "- **Platform:** "
                    + ("Linux ARM64 (Docker)." if number == 2527 else "macOS ARM64."),
                    f"- **Rust toolchains:** before `{versions['historical']}`; after `{versions['current']}`. Default Cargo features, committed lockfiles.",
                ]
            )
            if (case / "evidence/reference.json").exists():
                reference = json.loads((case / "evidence/reference.json").read_text())
                text.append(
                    f"- **CPython:** `{reference['version']}`. [Reference provenance](evidence/reference.json)."
                )
            text.extend(
                [
                    "- **Full reproduction:** [BUILD.md](BUILD.md) contains exact checkout, toolchain, build and executable-version checks. Return to the Run section after setup.",
                    "",
                    "## Recorded evidence",
                    "",
                    "- [Execution metadata, toolchain and log hashes](evidence/metadata.json).",
                    "- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).",
                ]
            )
            if (case / "evidence/historical.stderr.txt").exists():
                text.append(
                    "- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt)."
                )
            if (case / "evidence/reference.json").exists():
                text.append(
                    "- [CPython stdout](evidence/cpython.stdout.txt) / [CPython stderr](evidence/cpython.stderr.txt)."
                )
            stderr_logs = [
                case / "evidence" / f"{phase}.stderr.txt"
                for phase in ("cpython", "historical", "current")
            ]
            if any(log.exists() and log.read_text().strip() for log in stderr_logs):
                text.extend(
                    [
                        "",
                        "<details>",
                        "<summary>Full recorded stderr (including traceback frames)</summary>",
                        "",
                    ]
                )
                for phase in ("cpython", "historical", "current"):
                    log = case / "evidence" / f"{phase}.stderr.txt"
                    if log.exists() and log.read_text().strip():
                        text.extend(
                            [
                                f"**{'CPython' if phase == 'cpython' else phase.capitalize()}:**",
                                "",
                                "```text",
                                log.read_text().rstrip(),
                                "```",
                                "",
                            ]
                        )
                text.extend(["</details>", ""])
            build = [
                f"# Build the two revisions for #{number}",
                "",
                "[Case report and reproduction input](README.md)",
                "",
                *reproduction_setup(item),
                "Return to [Run](README.md#run) in the same shell to execute the shared input with both builds.",
                "",
            ]
            (case / "BUILD.md").write_text("\n".join(build))
        else:
            text.extend(
                [
                    "## Recorded evidence",
                    "",
                    "- [HTTP checks](evidence/http-checks.json).",
                    "",
                ]
            )
        text.extend(
            [
                "AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.",
                "",
            ]
        )
        (case / "README.md").write_text("\n".join(text))
    aggregate.extend(
        [
            "AI assistance: verification and drafting with OpenAI Codex.",
            "",
        ]
    )
    (BUNDLE / "report.md").write_text("\n".join(aggregate))
    return "\n".join(index)


def clean_environment(stdlib=None):
    env = os.environ.copy()
    for key in (
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONWARNINGS",
        "PYTHONOPTIMIZE",
        "PYTHONSTARTUP",
        "PYTHON_BASIC_REPL",
        "RUSTPYTHONPATH",
    ):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if stdlib is not None:
        env["RUSTPYTHONPATH"] = str(stdlib)
    return env


def verify_interpreter(binary, stdlib, expected_sha, cwd, timeout):
    """Reject a mismatched commit, modified Lib, or stale build-time Lib path."""
    binary = binary.resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError(f"Not an executable file: {binary}")
    if stdlib is not None:
        stdlib = stdlib.resolve()
        if not (stdlib / "os.py").is_file():
            raise ValueError(f"Not a RustPython Lib directory: {stdlib}")

        def git(*args):
            return subprocess.check_output(
                ["git", "-C", str(stdlib), *args],
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            ).strip()

        root = Path(git("rev-parse", "--show-toplevel")).resolve()
        if stdlib != root / "Lib":
            raise ValueError("Use the retained checkout's top-level Lib directory")
        tree = git("rev-parse", "HEAD:Lib")
        if tree != git("rev-parse", f"{expected_sha}:Lib") or git(
            "status", "--porcelain", "--untracked-files=normal", "--", str(stdlib)
        ):
            raise ValueError(
                "Lib differs from the expected revision or has local changes"
            )
    env = clean_environment(stdlib)
    probe = run_script(
        [
            str(binary),
            "-c",
            "import sys, os, json; print(json.dumps({"
            "'implementation': sys.implementation.name, 'version': sys.version, "
            "'os': os.__file__, 'json': json.__file__}))",
        ],
        env,
        cwd,
        timeout,
    )
    if probe["timeout"] or probe["exit_code"] != 0:
        raise ValueError(f"Interpreter startup failed: {probe}")
    identity = json.loads(probe["stdout"])
    wanted = "rustpython" if stdlib is not None else "cpython"
    if identity["implementation"] != wanted:
        raise ValueError(f"Expected {wanted}, got {identity['implementation']}")
    if stdlib is not None:
        if not re.search(rf"\b{expected_sha[:7]}[0-9a-f]*\b", identity["version"]):
            raise ValueError(f"Executable does not identify commit {expected_sha}")
        for module in ("os", "json"):
            if not Path(identity[module]).resolve().is_relative_to(stdlib):
                raise ValueError(
                    f"{module} loaded from {identity[module]}, outside supplied {stdlib}; "
                    "retain the original checkout or rebuild using BUILD.md"
                )
        identity["stdlib_tree"] = tree
    return {
        **identity,
        "binary": str(binary),
        "binary_sha256": digest(binary),
        "stdlib": str(stdlib) if stdlib is not None else None,
    }, env


def print_comparison(results):
    labels = list(results)
    width = 44
    print("Field".ljust(10) + " | " + " | ".join(x.ljust(width) for x in labels))
    print("-" * (13 + (width + 3) * len(labels)))
    for field in ("stdout", "stderr", "exit_code", "oracle", "error"):
        cells = [
            textwrap.wrap(
                json.dumps(results[label].get(field, ""), ensure_ascii=True), width
            )
            or [""]
            for label in labels
        ]
        for row in range(max(map(len, cells))):
            print(
                (field if row == 0 else "").ljust(10)
                + " | "
                + " | ".join(
                    (cell[row] if row < len(cell) else "").ljust(width)
                    for cell in cells
                )
            )


def compare_interpreters(args, manifest, parser):
    if not args.issue or len(args.issue) != 1:
        parser.error("--compare requires exactly one --issue")
    item = next((i for i in manifest["issues"] if i["issue"] == args.issue[0]), None)
    if item is None or item["kind"] == "documentation":
        parser.error("--compare requires a known runtime issue; #4784 uses check.sh")
    if item["kind"] == "repl" and sys.platform != "linux":
        parser.error(
            "The RustPython REPL comparison requires Linux; see cases/2527/BUILD.md"
        )
    if not all((args.before, args.before_stdlib, args.after, args.after_stdlib)):
        parser.error(
            "--compare requires --before, --before-stdlib, --after and --after-stdlib"
        )
    if args.rustpython or args.stdlib:
        parser.error("Do not combine --compare with single-interpreter options")
    if args.reference and item["issue"] == 6790:
        parser.error(
            "#6790 compares RustPython's own test.support gate; omit --reference"
        )
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = (args.output or BUNDLE / "runs" / stamp).resolve()
    output.mkdir(parents=True, exist_ok=False)
    interpreters = []
    if args.reference:
        interpreters.append(("CPython", args.reference, None, None))
    interpreters.extend(
        [
            ("Before", args.before, args.before_stdlib, item["historical_sha"]),
            ("After", args.after, args.after_stdlib, manifest["baseline_sha"]),
        ]
    )
    source = BUNDLE / "cases" / str(item["issue"]) / item["input"]
    results = {}
    for label, binary, stdlib, sha in interpreters:
        result = {"oracle": "ERROR"}
        try:
            with tempfile.TemporaryDirectory(
                prefix=f"compare-{item['issue']}-"
            ) as scratch:
                identity, env = verify_interpreter(
                    binary, stdlib, sha, scratch, args.timeout
                )
                result["identity"] = identity
                result["input_sha256"] = digest(source)
                result["command"] = [str(binary.resolve())]
                if item["kind"] != "repl":
                    result["command"].append(str(source))
                result["cwd"] = scratch
                result["environment"] = {
                    key: env[key]
                    for key in ("RUSTPYTHONPATH", "PYTHONDONTWRITEBYTECODE")
                    if key in env
                }
                if item["kind"] == "repl":
                    config = Path(scratch) / "config"
                    (config / "rustpython").mkdir(parents=True)
                    env.update(TERM="xterm", XDG_CONFIG_HOME=str(config))
                    if label == "CPython":
                        env["PYTHON_BASIC_REPL"] = "1"
                    result["environment"].update(
                        {
                            key: env[key]
                            for key in ("TERM", "XDG_CONFIG_HOME", "PYTHON_BASIC_REPL")
                            if key in env
                        }
                    )
                    result.update(
                        run_repl(
                            binary.resolve(),
                            source.read_text(),
                            env,
                            scratch,
                            args.timeout,
                        )
                    )
                    passed = result["passed"]
                else:
                    result.update(
                        run_script(
                            [str(binary.resolve()), str(source)],
                            env,
                            scratch,
                            args.timeout,
                        )
                    )
                    passed = check_result(item["expected"], result)
                result["oracle"] = "PASS" if passed else "FAIL"
                if result.get("timeout") or result.get("error"):
                    result["oracle"] = "ERROR"
                if (
                    label == "CPython"
                    and item["issue"] == 6429
                    and result["oracle"] != "ERROR"
                ):
                    result["oracle"] = (
                        "CONFIG"
                        if result["exit_code"] == 0
                        and result["stdout"].strip() in ("0", "1")
                        else "FAIL"
                    )
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            result.update(error=str(exc), oracle="ERROR")
        results[label] = result
        for stream in ("stdout", "stderr"):
            (output / f"{label.lower()}.{stream}.txt").write_text(
                result.get(stream, "")
            )
    write_json(
        output / "comparison.json",
        {
            "issue": item["issue"],
            "timestamp_utc": stamp,
            "platform": platform.platform(),
            "input_sha256": digest(source),
            "results": results,
        },
    )
    print_comparison(results)
    print(
        "Oracle = current case expectation. Before FAIL alone does not prove the original symptom; compare the recorded diagnostic."
    )
    if item["issue"] == 6429:
        print("CONFIG = CPython build setting, not equality with RustPython.")
    print("Full outputs and versions:", output)
    return int(
        any(r["oracle"] == "ERROR" for r in results.values())
        or results["After"]["oracle"] != "PASS"
        or results.get("CPython", {}).get("oracle") == "FAIL"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rustpython", type=Path)
    parser.add_argument("--stdlib", type=Path)
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare the two recorded revisions using one input",
    )
    parser.add_argument("--before", type=Path, help="Historical RustPython executable")
    parser.add_argument("--before-stdlib", type=Path)
    parser.add_argument(
        "--after", type=Path, help="Current baseline RustPython executable"
    )
    parser.add_argument("--after-stdlib", type=Path)
    parser.add_argument(
        "--reference", type=Path, help="Optional CPython executable (full path)"
    )
    parser.add_argument(
        "--issue",
        type=int,
        action="append",
        help="Repeat to select multiple issues; default: all",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="New output directory; existing directories are never overwritten",
    )
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument(
        "--render-recorded",
        action="store_true",
        help="Regenerate the committed case docs and bullet issue draft from recorded evidence",
    )
    args = parser.parse_args()
    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    if args.render_recorded:
        print(render_recorded(manifest))
        return 0
    if os.name != "posix":
        parser.error("Execution requires a POSIX host (Linux or macOS)")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.compare:
        return compare_interpreters(args, manifest, parser)
    if any(
        (args.before, args.before_stdlib, args.after, args.after_stdlib, args.reference)
    ):
        parser.error("Comparison interpreter options require --compare")
    if not args.rustpython or not args.stdlib:
        parser.error("--rustpython and --stdlib are required for execution")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    binary, stdlib = args.rustpython.resolve(), args.stdlib.resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        parser.error("--rustpython must be an executable file")
    if not (stdlib / "os.py").is_file():
        parser.error("--stdlib must point to the matching RustPython standard library")
    issues = manifest["issues"]
    if args.issue:
        unknown = set(args.issue) - {i["issue"] for i in issues}
        if unknown:
            parser.error(f"Unknown issue numbers: {sorted(unknown)}")
        issues = [i for i in issues if i["issue"] in args.issue]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = (args.output or BUNDLE / "runs" / stamp).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in [
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONWARNINGS",
        "PYTHONOPTIMIZE",
        "RUSTPYTHONPATH",
    ]:
        env.pop(key, None)
    env.update(RUSTPYTHONPATH=str(stdlib), PYTHONDONTWRITEBYTECODE="1")
    version = run_script(
        [str(binary), "-c", "import sys; print(sys.version)"], env, output, args.timeout
    )
    if version["exit_code"] != 0 or version["timeout"]:
        write_json(output / "version-error.json", version)
        print(
            f"Unable to start interpreter; see {output / 'version-error.json'}",
            file=sys.stderr,
        )
        return 2
    run_metadata = {
        "timestamp_utc": stamp,
        "platform": platform.platform(),
        "binary": str(binary),
        "binary_sha256": digest(binary),
        "stdlib": str(stdlib),
        "version": version["stdout"].strip(),
    }
    results = []
    for item in issues:
        number = item["issue"]
        dest = output / str(number)
        dest.mkdir()
        result = {"issue": number, **run_metadata}
        if item["kind"] == "documentation":
            result.update(
                status="MANUAL",
                reason="Run cases/4784/check.sh for the read-only URL check",
            )
        elif item["kind"] == "repl" and sys.platform != "linux":
            result.update(
                status="SKIP",
                reason="The recorded REPL comparison requires Linux and a PTY",
            )
        else:
            source = BUNDLE / "cases" / str(number) / item["input"]
            result["input_sha256"] = digest(source)
            with tempfile.TemporaryDirectory(prefix=f"rustpython-{number}-") as scratch:
                result["cwd"] = scratch
                result["environment"] = {
                    "RUSTPYTHONPATH": str(stdlib),
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
                try:
                    if item["kind"] == "repl":
                        config = Path(scratch) / "config"
                        (config / "rustpython").mkdir(parents=True)
                        repl_env = dict(env, TERM="xterm", XDG_CONFIG_HOME=str(config))
                        result["environment"].update(
                            TERM="xterm", XDG_CONFIG_HOME=str(config)
                        )
                        result.update(
                            run_repl(
                                binary,
                                source.read_text(),
                                repl_env,
                                scratch,
                                args.timeout,
                            )
                        )
                        result["command"] = [str(binary)]
                    else:
                        command = [str(binary), str(source)]
                        result.update(run_script(command, env, scratch, args.timeout))
                        result["command"] = command
                        result["passed"] = check_result(item["expected"], result)
                    result["status"] = "PASS" if result["passed"] else "FAIL"
                except OSError as exc:
                    result.update(status="ERROR", error=str(exc))
            for stream in ("stdout", "stderr"):
                (dest / (stream + ".txt")).write_text(result.get(stream, ""))
        write_json(dest / "result.json", result)
        report = [
            f"# #{number} — {item['title']}",
            "",
            f"- This run: **{result['status']}**.",
            f"- Interpreter: `{run_metadata['version'].replace(chr(10), ' ')}`.",
            f"- Historical observation: {item['historical_summary']}",
            f"- Expected current behavior: {item['current_summary']}",
            f"- Related change: {item['references']}",
            "",
        ]
        if "command" in result:
            report.extend(
                [
                    "```sh",
                    shlex.join(result["command"]),
                    "```",
                    "",
                    "Run with the `RUSTPYTHONPATH` and scratch-directory setup recorded by this runner.",
                    "",
                ]
            )
        for stream in ("stdout", "stderr"):
            if stream in result:
                report.extend(
                    [
                        f"{stream}:",
                        "",
                        "```text",
                        result[stream].rstrip() or "(empty)",
                        "```",
                        "",
                    ]
                )
        if result.get("reason") or result.get("error"):
            report.append(result.get("reason") or result["error"])
        (dest / "report.md").write_text("\n".join(report) + "\n")
        results.append(
            {
                "issue": number,
                "status": result["status"],
                "report": f"{number}/report.md",
            }
        )
        print(f"#{number}: {result['status']}", flush=True)
    write_json(output / "summary.json", {**run_metadata, "results": results})
    (output / "README.md").write_text(
        "# Local reproduction results\n\n"
        + "\n".join(f"- [#{r['issue']}: {r['status']}]({r['report']})" for r in results)
        + "\n"
    )
    print(f"Reports: {output}")
    return int(any(r["status"] in ("FAIL", "ERROR") for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
