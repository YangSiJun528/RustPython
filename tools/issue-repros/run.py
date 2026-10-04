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


def render_recorded(manifest):
    sha = manifest["baseline_sha"]
    index = []
    aggregate = [
        "# Review 16 resolved RustPython issues for closure",
        "",
        f"I rechecked the reports below on [{sha[:12]}](https://github.com/RustPython/RustPython/commit/{sha}) on October 4, 2026. "
        "The original failures reproduce on the historical revisions recorded in each case; the current results satisfy the reported behavior. "
        "The documentation link was checked separately through docs.rs.",
        "",
        "Could you review these results and close the corresponding issues? "
        "Each entry links to its executable input, local run command and recorded evidence.",
        "",
    ]
    for item in manifest["issues"]:
        number = item["issue"]
        case = BUNDLE / "cases" / str(number)
        title = f"#{number} — {item['title']}"
        index.append(f"- [{title}](cases/{number}/README.md)")
        aggregate.extend(
            [
                f"- **[{title}]({item['url']})**",
                f"  - Previously: {item['historical_summary']}",
                f"  - Verified result and reason to close: {item['reason_to_close']}",
                f"  - Related change: {item['references']}",
                f"  - [Reproducer, commands and evidence](https://github.com/YangSiJun528/RustPython/blob/resolved-issue-reproducers/tools/issue-repros/cases/{number}/README.md)",
                "",
            ]
        )
        text = [
            f"# {title}",
            "",
            item["reason_to_close"],
            "",
            f"Original issue: [{item['url']}]({item['url']})",
            "",
            "## Reproduce locally",
            "",
        ]
        if item["kind"] == "documentation":
            text.extend(
                [
                    "```sh",
                    "sh tools/issue-repros/cases/4784/check.sh",
                    "```",
                    "",
                    "The response should be the RustPython API documentation after redirects. "
                    "The recorded check served version 0.6.0. This command performs a read-only HTTP request.",
                    "",
                ]
            )
        else:
            text.extend(
                [
                    "Build from the repository root with `cargo build --release --locked`, then run:",
                    "",
                    "```sh",
                    "python3 tools/issue-repros/run.py \\",
                    '  --rustpython "$PWD/target/release/rustpython" \\',
                    '  --stdlib "$PWD/Lib" \\',
                    f"  --issue {number}",
                    "```",
                    "",
                    "The Python 3 host script launches the supplied RustPython executable in a temporary directory. "
                    "It writes a fresh `report.md`, `result.json`, stdout and stderr under the printed local output path.",
                    "",
                ]
            )
            if number == 2527:
                text.extend(
                    [
                        "Use Linux with a working PTY. The runner sets `TERM=xterm` and waits for each prompt. "
                        "To check manually, paste the following blocks into the RustPython REPL, including the blank line after each block:",
                        "",
                    ]
                )
            text.extend(
                [
                    f"Input: [{item['input']}]({item['input']})",
                    "",
                    "```python",
                    (case / item["input"]).read_text().rstrip(),
                    "```",
                    "",
                    item["derivation"],
                    "",
                ]
            )
            if number == 5181:
                text.extend(
                    [
                        "The system must provide the `en_US.UTF-8` locale (`locale -a`). A missing locale is a setup error.",
                        "",
                    ]
                )
            if number == 6790:
                text.extend(
                    [
                        "Use the matching RustPython `Lib` tree, including `test.support`, with lzma available.",
                        "",
                    ]
                )
        text.extend(
            [
                "## Recorded comparison",
                "",
                f"- Historical result: {item['historical_summary']}",
                f"- Current result: {item['current_summary']}",
            ]
        )
        historical = item["historical_sha"]
        if historical:
            text.extend(
                [
                    f"- Historical revision: [{historical}](https://github.com/RustPython/RustPython/commit/{historical}).",
                    f"- Current revision: [{sha}](https://github.com/RustPython/RustPython/commit/{sha}).",
                    "- Environment: "
                    + (
                        "Linux ARM64, TERM=xterm."
                        if number == 2527
                        else "macOS 26.5.2 ARM64; default-feature release builds."
                    ),
                ]
            )
            if number == 4856:
                text.append(
                    "- Baseline selection: the reported RustPython v0.2.0 release tag."
                )
            elif number in (4908, 4937):
                text.append(
                    "- Baseline selection: a revision identified in the original report."
                )
            elif number == 6790:
                text.append(
                    "- Baseline selection: the source revision linked by the original report."
                )
            else:
                text.append(
                    "- Baseline selection: nearest pre-issue main revision; an approximation of the original environment."
                )
            text.extend(
                [
                    "- [Execution metadata and log hashes](evidence/metadata.json).",
                    "- [Historical stdout](evidence/historical.stdout.txt) / [current stdout](evidence/current.stdout.txt).",
                ]
            )
            if (case / "evidence/historical.stderr.txt").exists():
                text.append(
                    "- [Historical stderr](evidence/historical.stderr.txt) / [current stderr](evidence/current.stderr.txt)."
                )
        else:
            text.append("- [Recorded HTTP checks](evidence/http-checks.json).")
        text.extend(["", "## Related change", "", item["references"], ""])
        if historical:
            text.extend(
                [
                    "These source changes match the observed behavior. The exact first-fixing commit was not established by executing each change and its parent.",
                    "",
                ]
            )
        text.extend(
            [
                "AI assistance: OpenAI Codex assisted with verification, evidence selection, executable packaging and drafting.",
                "",
            ]
        )
        (case / "README.md").write_text("\n".join(text))
    aggregate.extend(
        [
            "Runtime checks used macOS ARM64 except the REPL check, which used Linux ARM64. "
            "Related PRs identify matching source changes; exact first-fixing commits were not established by parent/commit execution comparisons.",
            "",
            "AI assistance: OpenAI Codex assisted with verification, evidence analysis, executable packaging and drafting.",
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
