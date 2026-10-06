**#4541 — safe_path 옵션·환경·실제 import 경로**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/4541)은 2026-10-05T16:08:49.489990+00:00 UTC 조회에서 **open**였다. 본문과 댓글 2개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문 checklist는 sys.flags.safe_path, -P, PYTHONSAFEPATH, 실제 unsafe path 삽입 억제다. 제목의 sys.safe_path는 체크리스트상 sys.flags.safe_path를 가리킨다. 댓글은 옵션/env가 연결됐고 실제 구현도 작동하는 듯하다고 쓰므로 플래그만 확인해서는 부족하다.

초안 검증 범위: script/-c/-m/REPL에서 -P와 PYTHONSAFEPATH가 unsafe path를 제거하며 symlink/-E/-I도 CPython과 같다는 주장이다.

모든 새 interpreter 실행의 cwd는 `<workspace>`이고 slot A만 사용했다. OS는 macOS 26.5.2 (25F84), 아키텍처는 ARM64이다. RustPython 실경로는 `<survey>/.build/slot-a/verification/rustpython`, SHA-256은 `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`이다. 배너는 Python 3.14.0.alpha / RustPython 0.6.1 / f39b054b9 / rustc 1.99.0이다. CPython은 `<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14`, 3.14.6 ARM64, SHA-256 `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`이다. RustPython이 실제 읽은 collections/ElementTree/dis/modulefinder/locale/sysconfig 및 test 파일은 `<workspace>/Lib` 아래이며 [실제 경로와 hash](../../agent-a/environment/identity.json)에 기록했다.

현재 HEAD 및 추적 소스는 목표 `f39b054b9c8cbbf884f53123eef028131789990c`이고 tracked diff는 없다. 바이너리 연결은 HEAD만으로 판단하지 않았다. 실행 배너, Cargo build-script 출력, [기존 build-variants-a.json](../../agent-a/environment/build-variants-a.json)의 `optimized_sqlite` actual_sha·동일 바이너리 SHA, 성공한 verification-profile/default+sqlite 빌드 로그가 함께 일치한다. 재빌드하지 않았으므로 과거 모든 build input의 순수성을 독립적으로 재현·증명한 것은 아니다. 동적 링크는 macOS 시스템 라이브러리로 확인했다.

재현용 공통 shell 설정은 다음과 같다. 아래 Python 코드 블록을 표시한 입력 파일명으로 저장한 다음 실행한다.

~~~sh
SRC='<workspace>'
A='<closure24-audit>/agent-a'
RP='<survey>/.build/slot-a/verification/rustpython'
CP='<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14'
export SRC A RP CP
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP PYTHONSAFEPATH RUSTPYTHONPATH
unset LC_COLLATE LC_CTYPE LC_MESSAGES LC_MONETARY LC_NUMERIC LC_TIME
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$A/tmp"
export LANG=C LC_ALL=C NO_COLOR=1 TERM=dumb
cd "$SRC"
~~~

아래 코드는 저장한 실제 새 입력이다. 명령의 `RP`, `CP`, `A`, `SRC`는 각각 위 RustPython 실행 경로, CPython 실행 경로, `<closure24-audit>/agent-a`, `<workspace>`의 약어다. 실행은 `-B`와 PYTHONDONTWRITEBYTECODE=1을 적용했고 TMPDIR은 `$A/tmp`로 격리했다. locale·path 환경 및 제거된 변수의 효과는 각 [실행 기록](../../agent-a/executions.jsonl)의 argv/cwd/relevant_env와 stdout/stderr 파일로 확인할 수 있다. 각 실행은 20~60초 timeout과 process-group cleanup을 두었고 이번 재현에 timeout은 없었다.

실행 입력 [safe_fixture_4541/safe_probe_4541.py](../../agent-a/inputs/safe_fixture_4541/safe_probe_4541.py.txt), SHA-256 `3d10f629d93ce343d83e3089b0462008b2d75018ebaa9de96a5102f55129bc34`:

```python
import sys, os, json, importlib


def can_import(name):
    try:
        return importlib.import_module(name).value
    except ModuleNotFoundError:
        return False


print(
    json.dumps(
        {
            "safe_path": sys.flags.safe_path,
            "isolated": sys.flags.isolated,
            "ignore_environment": sys.flags.ignore_environment,
            "path": sys.path,
            "cwd": os.getcwd(),
            "bare_import": can_import("safe_marker_4541"),
            "cwd_import": can_import(
                "independent-verification.2026-10-06T010610+0900-closure24-f39b054.agent-a.inputs.safe_fixture_4541.safe_marker_4541"
            ),
        },
        sort_keys=True,
    )
)
```

실행 입력 [safe_fixture_4541/safe_marker_4541.py](../../agent-a/inputs/safe_fixture_4541/safe_marker_4541.py.txt), SHA-256 `5cb19c189706019e7bd68ddf291be40047035562bc3b09d6382a0d6c4a1a09d4`:

```python
value = "unique-slot-a-4541"
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 4541-command-default-rp
"$RP" -B -c 'import sys,os,json,importlib
def can_import(name):
 try:return importlib.import_module(name).value
 except ModuleNotFoundError:return False
print(json.dumps({'"'"'safe_path'"'"':sys.flags.safe_path,'"'"'isolated'"'"':sys.flags.isolated,'"'"'ignore_environment'"'"':sys.flags.ignore_environment,'"'"'path'"'"':sys.path,'"'"'cwd'"'"':os.getcwd(),'"'"'bare_import'"'"':can_import('"'"'safe_marker_4541'"'"'),'"'"'cwd_import'"'"':can_import('"'"'independent-verification.2026-10-06T010610+0900-closure24-f39b054.agent-a.inputs.safe_fixture_4541.safe_marker_4541'"'"')},sort_keys=True))
'
# 4541-command-default-cp
"$CP" -B -c 'import sys,os,json,importlib
def can_import(name):
 try:return importlib.import_module(name).value
 except ModuleNotFoundError:return False
print(json.dumps({'"'"'safe_path'"'"':sys.flags.safe_path,'"'"'isolated'"'"':sys.flags.isolated,'"'"'ignore_environment'"'"':sys.flags.ignore_environment,'"'"'path'"'"':sys.path,'"'"'cwd'"'"':os.getcwd(),'"'"'bare_import'"'"':can_import('"'"'safe_marker_4541'"'"'),'"'"'cwd_import'"'"':can_import('"'"'independent-verification.2026-10-06T010610+0900-closure24-f39b054.agent-a.inputs.safe_fixture_4541.safe_marker_4541'"'"')},sort_keys=True))
'
# 4541-command-P-rp
"$RP" -B -P -c 'import sys,os,json,importlib
def can_import(name):
 try:return importlib.import_module(name).value
 except ModuleNotFoundError:return False
print(json.dumps({'"'"'safe_path'"'"':sys.flags.safe_path,'"'"'isolated'"'"':sys.flags.isolated,'"'"'ignore_environment'"'"':sys.flags.ignore_environment,'"'"'path'"'"':sys.path,'"'"'cwd'"'"':os.getcwd(),'"'"'bare_import'"'"':can_import('"'"'safe_marker_4541'"'"'),'"'"'cwd_import'"'"':can_import('"'"'independent-verification.2026-10-06T010610+0900-closure24-f39b054.agent-a.inputs.safe_fixture_4541.safe_marker_4541'"'"')},sort_keys=True))
'
# 4541-command-P-cp
"$CP" -B -P -c 'import sys,os,json,importlib
def can_import(name):
 try:return importlib.import_module(name).value
 except ModuleNotFoundError:return False
print(json.dumps({'"'"'safe_path'"'"':sys.flags.safe_path,'"'"'isolated'"'"':sys.flags.isolated,'"'"'ignore_environment'"'"':sys.flags.ignore_environment,'"'"'path'"'"':sys.path,'"'"'cwd'"'"':os.getcwd(),'"'"'bare_import'"'"':can_import('"'"'safe_marker_4541'"'"'),'"'"'cwd_import'"'"':can_import('"'"'independent-verification.2026-10-06T010610+0900-closure24-f39b054.agent-a.inputs.safe_fixture_4541.safe_marker_4541'"'"')},sort_keys=True))
'
# 4541-module-E-rp
"$RP" -B -E -m safe_probe_4541
# 4541-module-E-cp
"$CP" -B -E -m safe_probe_4541
```

전체 실행은 다음 절차로 재구성할 수 있다. 위 두 Python 코드 블록을 CASE 아래의 표시한 파일명으로 저장한다. CASE의 cwd_import namespace는 SRC 기준의 상대 경로이므로 CASE를 다른 위치로 옮기면 표시된 namespace도 같은 상대 경로로 맞춰야 한다. 실행 cwd는 계속 SRC이고 fixture 디렉터리로 이동하지 않는다.

~~~sh
CASE="$A/inputs/safe_fixture_4541"
LINKDIR="$A/inputs/safe_link_4541"
export CASE LINKDIR
mkdir -p "$CASE" "$LINKDIR"
# 위 safe_probe_4541.py와 safe_marker_4541.py를 CASE에 저장한다.
test -L "$LINKDIR/linked.py" || ln -s "$CASE/safe_probe_4541.py" "$LINKDIR/linked.py"
cd "$SRC"
~~~

아래 Python harness는 56개 비대화형 조합을 정확히 정의한다. RP와 CP는 실행 파일 경로이며 interpreter 비교를 수행하는 외부 harness는 CPython으로 실행한다. 입력 source는 위에 본문으로 제공했으므로 별도 driver 파일을 읽을 필요가 없다.

~~~python
import os
import pathlib
import signal
import subprocess

src = pathlib.Path(os.environ["SRC"])
case = pathlib.Path(os.environ["CASE"])
link = pathlib.Path(os.environ["LINKDIR"]) / "linked.py"
probe = case / "safe_probe_4541.py"
settings = [
    ("default", [], {}),
    ("P", ["-P"], {}),
    ("env1", [], {"PYTHONSAFEPATH": "1"}),
    ("env0", [], {"PYTHONSAFEPATH": "0"}),
    ("envempty", [], {"PYTHONSAFEPATH": ""}),
    ("E", ["-E"], {"PYTHONSAFEPATH": "1"}),
    ("I", ["-I"], {"PYTHONSAFEPATH": "1"}),
]
for implementation in ("RP", "CP"):
    exe = os.environ[implementation]
    for mode in ("script", "command", "module", "symlink"):
        for label, flags, overrides in settings:
            env = dict(os.environ)
            for name in ("PYTHONSAFEPATH", "PYTHONPATH", "RUSTPYTHONPATH"):
                env.pop(name, None)
            env.update(overrides)
            if mode == "module":
                key = "RUSTPYTHONPATH" if implementation == "RP" else "PYTHONPATH"
                env[key] = (
                    str(src / "Lib") + ":" + str(case)
                    if implementation == "RP"
                    else str(case)
                )
            tail = {
                "script": [str(probe)],
                "command": ["-c", probe.read_text()],
                "module": ["-m", "safe_probe_4541"],
                "symlink": [str(link)],
            }[mode]
            command = [exe, "-B", *flags, *tail]
            child = subprocess.Popen(
                command,
                cwd=src,
                env=env,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            timed_out = False
            try:
                stdout, stderr = child.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(child.pid, signal.SIGKILL)
                stdout, stderr = child.communicate()
            finally:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            print(
                implementation,
                mode,
                label,
                "exit",
                child.returncode,
                "timeout",
                timed_out,
            )
            print("stdout:", stdout.decode(errors="replace"))
            print("stderr:", stderr.decode(errors="replace"))
~~~

모든 JSON에서 flags뿐 아니라 path와 실제 import 결과를 확인한다. 기본 script/symlink는 bare_import만 sentinel 값을 반환한다. 기본 command는 cwd_import만 반환한다. 기본 module은 명시 CASE와 자동 cwd가 모두 있어 두 import가 성공한다. safe mode에서는 자동 경로로만 찾던 import가 False이고, 명시 CASE의 bare_import는 module 모드에서 계속 성공한다. -E/-I의 module 실패는 기대한 결과이다.

나머지 14개는 실제 터미널/PTY에서 각각 다음 7개 설정을 RP와 CP에 적용한다. 공통 TERM=dumb을 유지하고 PYTHONPATH와 RUSTPYTHONPATH는 없는 상태로 둔다. 아래 명령은 한 세션을 종료한 뒤 다음 명령을 시작한다.

~~~sh
exe="$RP"  # 첫 7개를 마친 뒤 exe="$CP"로 바꿔 반복한다.
env -u PYTHONSAFEPATH "$exe" -B -S -q
env -u PYTHONSAFEPATH "$exe" -B -S -q -P
env PYTHONSAFEPATH=1 "$exe" -B -S -q
env PYTHONSAFEPATH=0 "$exe" -B -S -q
env PYTHONSAFEPATH= "$exe" -B -S -q
env PYTHONSAFEPATH=1 "$exe" -B -S -q -E
env PYTHONSAFEPATH=1 "$exe" -B -S -q -I
~~~

각 실제 prompt 뒤에 아래를 한 줄씩 입력하고 다음 prompt를 기다린다. 저장된 실행은 open wrapper 대신 동일 probe source text를 exec 문자열에 직접 넣었다. 둘 다 probe 파일의 디렉터리를 sys.path에 삽입하지 않는다.

~~~python
import sys, os, json, importlib

exec(open(os.path.join(os.environ["CASE"], "safe_probe_4541.py")).read())
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
~~~

REPL default/envempty/-E에서는 cwd_import만 sentinel 값을 반환하고 -P/env1/env0/-I에서는 두 import가 모두 False이다. 모든 REPL의 bare_import는 False이다. 이번 자동 PTY 기록은 각 prompt를 기다렸고 세션별 20초 제한을 두었다. stdout/stderr는 하나의 transcript로 기록했다. 저장된 [PTY 입력 및 대기 코드](../../agent-a/pty_runner.py.txt), [전체 JSON 검증 결과](../../agent-a/validation.json), [개별 명령·환경·원시 출력 기록](../../agent-a/executions.jsonl)은 보조 증거다.

관찰과 판정 근거: script/-c/-m/symlink/실제 PTY 각각 default, -P, env="1", env="0", env="", -E+env1, -I+env1을 두 인터프리터에 적용해 70개 프로세스를 실행했다. validation.json은 flags뿐 아니라 전체 path에서 자동 항목의 존재와 실제 sentinel import 값을 assertion으로 검사한다. default/envempty/-E는 safe_path=False, -P/env1/env0/-I는 True이다. -c/REPL의 자동 "" 및 -m의 cwd, script/symlink의 실제 script 디렉터리가 safe mode에서 빠진다. symlink는 링크 디렉터리가 아닌 실제 script 디렉터리를 기본 path로 쓴다. 명시 RUSTPYTHONPATH/PYTHONPATH에 둔 -m 모듈은 -P에서도 import된다. -m -E/-I는 그 환경 경로를 무시하므로 양쪽 각 2개씩 exit 1, No module named safe_probe_4541이 기대 결과다. 나머지 66개는 exit 0, 모든 실행 timeout 없음이다.

원문·본문·실행 입력 대조: 기존 초안은 간소화한 repro_fixture 이름을 쓰고 실제 evidence는 다른 고유 fixture 이름을 쓴다. 새 fixture는 출력 디렉터리 아래에만 만들었고 모든 프로세스 cwd는 슬롯 A 저장소 루트로 고정했다. importlib.import_module의 namespace 경로로 실제 cwd import를 검사했다. 기존 초안 52회와 새 70회는 추가 env0/envempty/-E/-I의 PTY 적용 범위 차이다.

과거 746cb0493f7371304ceafec88c56e5de59155b95에서는 -P가 error: Found argument '-P' which wasn't expected, or isn't valid in this context로 거부됐다. 별도 default probe는 AttributeError: 'flags' object has no attribute 'safe_path'였다. 둘 다 exit 1이며 이 과거 probe만으로 모든 sys.path 동작을 판단하지 않았다.

과거 증거는 [기존 reused-history.json](../../agent-a/old-evidence/tools/issue-repros/recheck/cases/4541/reused-history.json)의 이전 입력·revision·출력 기록이다. 이번 실행과 혼합하지 않았고 과거 바이너리는 재실행하지 않았다. 과거 기록만으로 실제 use-path 성공이나 최초 수정 commit을 판단하지 않는다.

관련 변경: d4be55c2ea02b67d92c04b3e9f682d465acd59b3 (#4611)는 옵션/env/flags를 연결한다. 64c66e00d68c70fed261f8b46720438efda746b5 (#5049)는 safe_path 조건 삽입을 도입한다. 7c6c78f95525c091eb872d96b73090e7454be6d5 (#8605)는 script realpath를 사용한다. 현재 src/settings.rs:250 및 src/lib.rs:203,236,323을 확인했다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: PTY는 flush 뒤 os._exit(0)로 사용자 history 저장을 피했다. PTY transcript는 stderr를 합쳐 기록한다. REPL 정상 종료, Windows의 symlink 규칙, 모든 import hook/사이트 설정은 미검증이다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 검사한 다섯 실행 모드에서 safe_path의 자동 path 삽입 억제와 실제 import 결과가 CPython과 일치했다. -E/-I로 명시 모듈 경로가 무시되어 발생한 -m lookup 실패는 기대한 결과다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
