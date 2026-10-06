**#6429 — Py_GIL_DISABLED 설정 값**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/6429)은 2026-10-05T16:08:47.666839+00:00 UTC 조회에서 **open**였다. 본문과 댓글 2개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문은 sysconfig.get_config_var("Py_GIL_DISABLED")가 None이 아니라 1이어야 한다는 요구다. Windows CI에서는 값이 있었다는 댓글과 POSIX sysconfig 구현 링크가 있다. 인용문만으로는 import가 생략되어 있으므로 import sysconfig를 공급했다.

초안 검증 범위: 검증한 POSIX RustPython 빌드의 값이 정수 1로 정의된다는 주장이다. CPython과 같은 값이나 모든 free-threading/C-extension 호환성을 주장하지 않는다.

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

실행 입력 [6429-config.py](../../agent-a/inputs/6429-config.py.txt), SHA-256 `e558c6d9bf1ca320562058e5c2ba760fad7e2c5966e966387932b47f4b8164e6`:

```python
import sys, sysconfig

value = sysconfig.get_config_var("Py_GIL_DISABLED")
print(value)
print("type", type(value).__name__)
print("implementation", sys.implementation.name)
print("platform", sys.platform)
print("gil_enabled", sys._is_gil_enabled())
if sys.implementation.name == "rustpython":
    assert value == 1 and type(value) is int and sys._is_gil_enabled() is False
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 6429-config-rp
"$RP" -B "$A/inputs/6429-config.py"
# 6429-config-cp
"$CP" -B "$A/inputs/6429-config.py"
```

관찰과 판정 근거: RustPython: `1`, `type int`, `implementation rustpython`, `platform darwin`, `gil_enabled False`. CPython: `0`, `type int`, `implementation cpython`, `platform darwin`, `gil_enabled True`. 두 프로세스 exit 0, stderr 없음, timeout 없음이다. CPython의 0은 실패가 아니라 그 빌드의 GIL 설정을 반영한다.

대표 원시 출력 `6429-config-rp` (stdout/stderr 구분은 record 참조):

```text
1
type int
implementation rustpython
platform darwin
gil_enabled False
```

원문·본문·실행 입력 대조: 과거 입력은 repr 출력 wrapper를 붙여 None을 관찰했다. 초안과 새 probe는 값·타입·implementation·platform·GIL API를 더 출력하며 원래 설정 조회를 유지한다. 기존 Rosetta 결과와 새 native ARM64 결과를 분리한다.

과거 e227956a58f0f072f8be177264e0fdc1b9280e8a에서는 같은 설정 조회 결과가 None이었고 exit 0이었다. 이 값 차이가 원래 증상이다.

과거 증거는 `e227956a58f0f072f8be177264e0fdc1b9280e8a`의 기록을 읽어 대조했다. 기록된 exit는 `0`이다. 저장된 historical stdout/stderr의 export hash가 metadata와 일치함을 [별도 audit](../../agent-a/old-history-audit.json)에서 확인했다. 이 과거 바이너리는 이번에 재실행하지 않았다. 경로를 치환한 옛 로그의 hash 일치는 로그 보존 확인이며 과거 빌드의 모든 입력을 새로 인증하는 것은 아니다.

관련 변경: 3e2ada058651d9a1648bdb1453999758a32c4d13 (#6428) diff는 build_time_vars에 Py_GIL_DISABLED=>1을 넣는다. 현재 crates/vm/src/stdlib/_sysconfigdata.rs:53과 _sysconfig.rs:18은 값 1을 노출하고 sys.rs:769의 _is_gil_enabled는 false를 반환한다. 이는 RustPython의 GIL 부재를 나타내는 고정 구현 설정이며 CPython config 값 복제를 뜻하지 않는다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: Windows/다른 빌드 옵션 재실행, 완전한 free-threading·C-extension ABI 호환성은 미검증이다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 검증한 macOS ARM64 RustPython 빌드의 Py_GIL_DISABLED는 정수 1이다. 이 결과는 CPython 빌드 값과 같아야 한다는 뜻이 아니다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
