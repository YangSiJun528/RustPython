#!/usr/bin/env python3
"""Run selected RustPython issue reproducers and write local per-issue reports."""

import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import shlex
import signal
import subprocess
import sys
import tempfile
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


def reproduction_steps(item):
    """Commands for readers to reproduce behavior directly in RustPython."""
    number = item["issue"]
    case = BUNDLE / "cases" / str(number)
    if item["kind"] == "documentation":
        return [
            "```sh",
            "curl --fail --location https://docs.rs/rustpython",
            "```",
            "",
            "Follow redirects and inspect the returned API documentation. The recorded response was the RustPython 0.6.0 API page.",
        ]
    if item["kind"] == "repl":
        return [
            "On Linux, start the interactive interpreter in a scratch directory with a writable history directory:",
            "",
            "```sh",
            "(",
            '  rustpython_repro_bin="$PWD/target/release/rustpython"',
            '  rustpython_repro_lib="$PWD/Lib"',
            "  rustpython_repro_tmp=$(mktemp -d)",
            '  mkdir -p "$rustpython_repro_tmp/config/rustpython"',
            '  cd "$rustpython_repro_tmp" || exit',
            '  TERM=xterm XDG_CONFIG_HOME="$rustpython_repro_tmp/config" \\',
            '    RUSTPYTHONPATH="$rustpython_repro_lib" "$rustpython_repro_bin"',
            ")",
            "```",
            "",
            "Enter the two blocks below, pressing Enter on an empty line after each block. Use the REPL: running this as a script does not exercise expression display.",
            "",
            "```python",
            "for i in range(10):",
            "    i",
            "",
            'with open("repl-output.txt", "w") as f:',
            '    f.write("hello")',
            "",
            "```",
            "",
            "The current interpreter should display 0 through 9 after the loop and 5 after the `with` block, returning to the primary prompt after each. Enter `exit()` when finished.",
        ]
    code = (case / item["input"]).read_text().rstrip()
    if number == 4690:
        # The report concerns the raw descriptor, which is the first expression.
        code = code.splitlines()[0]
    if number == 4856:
        source = (case / "original-01.txt").read_text()
        code = (
            'source = """\\\n'
            + source
            + '"""\ncompile(source, "repro.py", "exec")\nprint("compile_success")'
        )
    prefix = 'RUSTPYTHONPATH="$PWD/Lib" ./target/release/rustpython'
    lines = [line for line in code.splitlines() if line]
    if len(lines) <= 2 and not any(line[0].isspace() for line in lines):
        command = [prefix + " -c " + shlex.quote("; ".join(lines))]
    else:
        command = [prefix + " -c " + shlex.quote("\n" + code + "\n")]
    steps = ["```sh", *command, "```"]
    prerequisites = {
        4856: "This compiles the original source without executing it, directly testing the reported compiler panic.",
        5181: "The system must provide `en_US.UTF-8` (`locale -a`). The command selects that locale explicitly.",
        6790: "Use the matching RustPython standard library, including `test.support`, with lzma available. The function is actually invoked after applying the decorator.",
    }
    if number in prerequisites:
        steps.extend(["", prerequisites[number]])
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


def render_recorded(manifest):
    sha = manifest["baseline_sha"]
    current_link = (
        f"[{sha[:12]}](https://github.com/RustPython/RustPython/commit/{sha})"
    )
    setup = [
        "Run from a RustPython checkout of the revision being tested. The recorded current revision is "
        + current_link
        + ". Build its default-feature release interpreter:",
        "",
        "```sh",
        "cargo build --release --locked",
        "```",
        "",
        "The commands below invoke RustPython directly and include the reproduction input. The runtime comparisons were recorded on macOS ARM64, except the REPL comparison on Linux ARM64.",
    ]
    history_help = (
        "To repeat a historical comparison, use the same input with an interpreter built from the listed historical revision and that checkout's standard library. "
        "Replace both `./target/release/rustpython` and `RUSTPYTHONPATH` in the command; older trees may use `pylib/Lib` or `vm/pylib-crate/Lib`. "
        "The linked execution metadata records the historical build toolchain."
    )
    brief_results = {
        2527: "REPL block expressions display their values.",
        3418: "Native OrderedDict import succeeds.",
        3430: "ElementTree parses the reported XML input.",
        4527: "The global object's finalizer runs at shutdown.",
        4690: "The raw class-method descriptor matches CPython.",
        4762: "Negative format widths correctly select left alignment.",
        4784: "The README link serves API documentation.",
        4786: "Surrogate type names raise UnicodeEncodeError.",
        4856: "The decorated-class source compiles without the panic.",
        4908: "The AST parse/unparse round trip succeeds.",
        4937: "The reported email Subject is retrieved without KeyError.",
        5181: "The n format respects en_US.UTF-8 grouping.",
        5656: "The invalid bytes escape emits SyntaxWarning.",
        6429: "Py_GIL_DISABLED returns 1 on the tested POSIX build.",
        6790: "The unconditional lzma test skip is removed.",
        8052: "The Ellipsis type name and repr match CPython.",
    }
    aggregate = [
        "# Review 16 resolved issues for closure",
        "",
        f"The reported behaviors below were verified on {current_link} on October 4, 2026; the documentation link was checked separately. "
        "Could you review the linked reproduction results and close these issues?",
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
        aggregate.append(
            f"- [#{number}]({item['url']}) — {brief_results[number]} "
            f"[Report](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/{number}/README.md)"
        )
        text = [
            f"# {title}",
            "",
            f"Original issue: [#{number}]({item['url']})",
            "",
            "## Reproduction procedure",
            "",
        ]
        if item["kind"] != "documentation":
            text.extend([*setup, ""])
        text.extend(
            [
                *steps,
                "",
                "## Before and after",
                "",
                f"- **Before — {historical}:** {item['historical_summary']}",
                f"- **After — {current_link}:** {item['current_summary']}"
                if item["historical_sha"]
                else f"- **After — documentation checked October 4, 2026:** {item['current_summary']}",
                "",
            ]
        )
        if item["historical_sha"]:
            text.extend([history_help, ""])
        text.extend(
            [
                "## Analysis and closure rationale",
                "",
                item["reason_to_close"],
                "",
                item["references"],
                "",
            ]
        )
        if item["historical_sha"]:
            text.extend(
                [
                    "These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.",
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
        else:
            text.extend(
                [
                    "## Recorded evidence",
                    "",
                    "- [HTTP checks](evidence/http-checks.json).",
                ]
            )
        text.extend(
            [
                "",
                "AI assistance: OpenAI Codex assisted with verification, evidence analysis and drafting.",
                "",
            ]
        )
        (case / "README.md").write_text("\n".join(text))
    aggregate.extend(
        [
            "",
            "AI assistance: verification and drafting with OpenAI Codex.",
            "",
        ]
    )
    (BUNDLE / "report.md").write_text("\n".join(aggregate))
    return "\n".join(index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rustpython", type=Path)
    parser.add_argument("--stdlib", type=Path)
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
