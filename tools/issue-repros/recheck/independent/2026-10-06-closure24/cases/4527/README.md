**#4527 — 전역 객체의 정상 종료 시 finalization**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/4527)은 2026-10-05T16:08:44.730465+00:00 UTC 조회에서 **open**였다. 본문과 댓글 0개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문은 __del__에서 deleted!를 출력하는 X와 최상위 x=X()만 둔 스크립트이다. CPython은 종료 때 출력하지만 당시 RustPython은 출력하지 않았다. 플랫폼·버전·추가 의존성은 없다.

초안 검증 범위: 원래 전역 객체 예제가 정상 종료 과정에서 deleted!를 stdout에 쓰고 exit 0, stderr 없음이라는 주장이다.

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

실행 입력 [4527-original.py](../../agent-a/inputs/4527-original.py.txt), SHA-256 `9855fcf04216ce2fe520ca86d42e7e64bea2071ed4465bc787be88695e90aaac`:

```python
class X:
    def __del__(self):
        print("deleted!")


x = X()
```

실행 입력 [4527-explicit.py](../../agent-a/inputs/4527-explicit.py.txt), SHA-256 `f0accd250aaf65ec0f7b45886ebc09ea0fd401653f0e705960e2df0600ddb134`:

```python
class X:
    def __del__(self):
        print("deleted!")


x = X()
del x
print("after explicit del")
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 4527-original-rp
"$RP" -B "$A/inputs/4527-original.py"
# 4527-original-cp
"$CP" -B "$A/inputs/4527-original.py"
# 4527-explicit-rp
"$RP" -B "$A/inputs/4527-explicit.py"
# 4527-explicit-cp
"$CP" -B "$A/inputs/4527-explicit.py"
```

관찰과 판정 근거: 원래 수명 패턴을 그대로 실행했고 두 프로세스 모두 정상 종료에서 stdout `deleted!\n`, stderr 0바이트, exit 0, timeout 없음이었다. os._exit, 강제 del, gc 호출을 원문에 넣지 않았다. 별도 explicit-del control도 deleted! 다음 after explicit del을 출력했다.

대표 원시 출력 `4527-original-rp` (stdout/stderr 구분은 record 참조):

```text
deleted!
```

원문·본문·실행 입력 대조: 기존 recorded input은 원문 그대로다. 초안의 따옴표·빈 줄 차이는 객체 수명이나 종료 경로를 바꾸지 않는다. explicit-del control을 원문 종료 검증과 구분했다.

과거 e5735cde67b86699bd68c8959167ecf2649a6f2d에서는 같은 전역 객체 스크립트가 exit 0이었지만 stdout이 비어 deleted!가 없었다. 이 사례에서는 exit 0만으로 성공을 판단할 수 없다.

과거 증거는 `e5735cde67b86699bd68c8959167ecf2649a6f2d`의 기록을 읽어 대조했다. 기록된 exit는 `0`이다. 저장된 historical stdout/stderr의 export hash가 metadata와 일치함을 [별도 audit](../../agent-a/old-history-audit.json)에서 확인했다. 이 과거 바이너리는 이번에 재실행하지 않았다. 경로를 치환한 옛 로그의 hash 일치는 로그 보존 확인이며 과거 빌드의 모든 입력을 새로 인증하는 것은 아니다.

관련 변경: 3814348943491629c37d916af69a5f6ce24b4167 (#6934)는 atexit 뒤, stream flush 앞에 vm.finalize_modules()를 연결하고 모듈 참조 정리를 추가한다. 현재 interpreter 종료 경로도 이 호출을 유지한다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: 프로세스 abort, 참조 순환, 임의의 모듈 정리 순서와 모든 destructor 부작용은 미검증이다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 원래 전역 객체 예제는 일반적인 인터프리터 종료에서 __del__을 호출하고 deleted!를 출력한다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
