**#2527 — 실제 REPL 블록 안의 표현식 출력**

[원문](https://github.com/RustPython/RustPython/issues/2527)은 2026-10-05T16:08:48.575779+00:00 UTC 조회에서 **open**였다. 본문과 댓글 3개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문 REPL의 for i in range(10): i 블록은 0~9, with open(..., "w"): f.write("hello") 블록은 5를 표시해야 한다. 댓글은 single mode의 PRINT_EXPR/displayhook과 관련 있다고 설명한다. dis(compile(...)) 댓글은 dis 함수를 import했다는 가정이 생략되어 있다.

초안 검증 범위: 실제 terminal/PTY에서 원래 두 블록 값이 표시되고, single mode displayhook·함수 scope 보강 결과도 CPython과 같다는 주장이다.

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

실행 입력 [2527-pty-rp.txt](../../agent-a/inputs/2527-pty-rp.txt), SHA-256 `eb45c102e4ec6710c3d0cd3526ff37628a40a7643f89097ac9735fea1b8d75d3`:

```text
import os, sys
print('ISATTY', sys.stdin.isatty())
for i in range(10):
    i

with open('<closure24-audit>/agent-a/tmp/2527-new-rp.txt', 'w') as f:
    f.write('hello')

sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
```

실행 입력 [2527-displayhook.py](../../agent-a/inputs/2527-displayhook.py.txt), SHA-256 `4f0fbb84c530f982f96b2efbbd21894faded9639bfa3f8f19cc63378b09179f7`:

```python
import sys

seen = []
sys.displayhook = seen.append
exec(compile("for i in range(10):\n    i\n", "for", "single"))
print("for displayhook", seen)
seen.clear()
exec(
    compile(
        "if True:\n    7\n    None\n    for i in range(2):\n        i + 10\n",
        "nested",
        "single",
    )
)
print("nested displayhook", seen)
seen.clear()
exec(compile("def f():\n    9\n", "function", "single"))
print("function definition hook", seen)
f()
print("function execution hook", seen)
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 2527-pty-rp
"$RP" -B -S -q
# 2527-pty-cp
"$CP" -B -S -q
# 2527-displayhook-rp
"$RP" -B "$A/inputs/2527-displayhook.py"
# 2527-displayhook-cp
"$CP" -B "$A/inputs/2527-displayhook.py"
```

관찰과 판정 근거: 두 PTY 모두 sys.stdin.isatty() True이고 첫 prompt와 각 입력 뒤 prompt를 관찰했다. for 뒤 0부터 9까지 각각 한 줄로 출력하고 with 뒤 5를 출력했다. 각 세션은 총 9개의 prompt 관찰 이벤트를 기록했고 생성 파일 내용은 hello이다. 보강 displayhook 출력은 for [0,1,2,3,4,5,6,7,8,9], nested [7,None,10,11], 함수 정의/호출 각각 []로 같았다. 모든 실행 exit 0, timeout 없음이다. PTY stdout/stderr는 동일 transcript에 합쳐졌으므로 stderr가 별도로 비어 있다고 판단하지 않았다.

대표 원시 출력 `2527-pty-rp` (stdout/stderr 구분은 record 참조):

```text
>>> import os, sys
>>> print('ISATTY', sys.stdin.isatty())
ISATTY True
>>> for i in range(10):
...     i
... 
0
1
2
3
4
5
6
7
8
9
>>> with open('<closure24-audit>/agent-a/tmp/2527-new-rp.txt', 'w') as f:
...     f.write('hello')
... 
5
>>> sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
```

원문·본문·실행 입력 대조: 원문 /tmp/file.txt는 새 출력 디렉터리의 고유 파일로 경로만 바꿨고 open 모드 w는 유지했다. 이전 초안은 같은 목적을 위해 x를 썼다. 두 표현식과 block 종료 빈 줄은 그대로이며, 이번 입력·경로를 모두 저장했다. 초안은 Rosetta/xterm, 새 검증은 ARM64/TERM=dumb의 실제 PTY이다.

과거 163cd1953377f4049e06fdae55c715889857a301의 Linux PTY transcript는 for/with 블록을 마친 뒤 primary prompt로 돌아왔으나 0~9 및 5 출력이 없었다. exit 0이더라도 표현식 결과가 빠졌으므로 실패 기록이다.

과거 증거는 `163cd1953377f4049e06fdae55c715889857a301`의 기록을 읽어 대조했다. 기록된 exit는 `0`이다. 저장된 historical stdout/stderr의 export hash가 metadata와 일치함을 [별도 audit](../../agent-a/old-history-audit.json)에서 확인했다. 이 과거 바이너리는 이번에 재실행하지 않았다. 경로를 치환한 옛 로그의 hash 일치는 로그 보존 확인이며 과거 빌드의 모든 입력을 새로 인증하는 것은 아니다.

관련 변경: 46a86ec03663f060d1013dda83ab7964a6615059 (#7067)는 single interactive mode의 module scope 표현식에 Print intrinsic을 추가한다. 함수·클래스 scope는 제외하는 조건을 diff에서 확인했다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: RustPython shell은 환경 RUSTPYTHON_HISTORY를 읽지 않고 실제 사용자 config 경로에 history를 저장한다. 이를 피하려고 결과 확인과 flush 후 os._exit(0)를 썼다. 따라서 REPL 정상 종료·history 저장은 검증하지 않았고 #4527의 정상 종료 판정과 혼합하지 않는다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 실제 macOS ARM64 PTY REPL에서 원래 loop와 file-write 블록의 표현식 값이 표시된다. 결과 관찰 후 os._exit(0)로 즉시 종료해 history 저장을 피했으므로 REPL 종료 수명주기는 검증 범위 밖이다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
