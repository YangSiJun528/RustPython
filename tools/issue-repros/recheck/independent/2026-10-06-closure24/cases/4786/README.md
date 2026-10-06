**#4786 — surrogate를 포함한 type 이름**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/4786)은 2026-10-05T16:08:41.952102+00:00 UTC 조회에서 **open**였다. 본문과 댓글 2개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문 `type("A\udcdcB", (), {})`는 클래스를 만들지 않고 UnicodeEncodeError를 내야 한다. 댓글은 non-UTF-8 문자열 지원과 관련된다고 설명한다. 플랫폼·실행 버전은 명시되지 않았다. REPL 출력 앞의 추가 >>> 표시는 입력으로 실행하지 않았다.

초안 검증 범위: surrogate가 치환되지 않고 보존되며 원래 type 생성이 UnicodeEncodeError로 exit 1을 낸다는 주장이다. 연속 surrogate 오류 범위의 차이는 초안도 별도로 인정한다.

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

실행 입력 [4786-original.py](../../agent-a/inputs/4786-original.py.txt), SHA-256 `f9a07b6de9e517d34dfef0f28920c72d0bcf48298f8cdcdf56568f57c58b29b0`:

```python
type("A\udcdcB", (), {})
```

실행 입력 [4786-details.py](../../agent-a/inputs/4786-details.py.txt), SHA-256 `3e19d30999457f91eecb2a6bcb1314010c3c0410350e4f74ecbf3c407ba4b446`:

```python
for s in ["A\udcdcB", "A\ud800\udfffB", "A\ud800B", "A🚀B"]:
    print("input", ascii(s), [ord(c) for c in s])
    try:
        t = type(s, (), {})
        print("accepted", ascii(t.__name__))
    except UnicodeEncodeError as e:
        print("rejected", e.encoding, ascii(e.object), e.start, e.end, e.reason)
        if s == "A\udcdcB":
            assert (e.encoding, e.object, e.start, e.end, e.reason) == (
                "utf-8",
                s,
                1,
                2,
                "surrogates not allowed",
            )
    else:
        assert not any(0xD800 <= ord(c) <= 0xDFFF for c in s)
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 4786-original-rp
"$RP" -B "$A/inputs/4786-original.py"
# 4786-original-cp
"$CP" -B "$A/inputs/4786-original.py"
# 4786-details-rp
"$RP" -B "$A/inputs/4786-details.py"
# 4786-details-cp
"$CP" -B "$A/inputs/4786-details.py"
```

관찰과 판정 근거: 입력 코드 포인트는 [65, 56540, 66]이다. 두 인터프리터 모두 encoding='utf-8', object='A\udcdcB', start=1, end=2, reason='surrogates not allowed'를 관찰했고 assertion이 통과했다. 원문 uncaught 실행은 양쪽 exit 1이며 stderr도 같았다. 이 비정상 종료 코드는 기대한 거부 결과이다. 보강 입력 A\ud800\udfffB는 양쪽 거부하지만 end가 RustPython 2, CPython 3으로 달랐다.

대표 원시 출력 `4786-original-rp` (stdout/stderr 구분은 record 참조):

```text
Traceback (most recent call last):
  File "<closure24-audit>/agent-a/inputs/4786-original.py", line 1, in <module>
    type("A\udcdcB", (), {})
    ~~~~^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcdc' in position 1: surrogates not allowed
```

원문·본문·실행 입력 대조: 과거 입력의 print(repr(type(...)))는 출력 관찰을 위한 wrapper였다. 새 원문 실행은 wrapper를 제거해 출력 과정이 아니라 type 생성 자체에서 오류가 나는지 확인했다. 초안의 원문 입력은 동등하다.

과거 010640ccc8f74f56075df09a654352ae3d162d25에서는 constructor를 print(repr(...))로 관찰했을 때 <class '__main__.A�B'>를 출력하고 exit 0이었다. 원래 surrogate가 치환된 채 type이 만들어졌다는 과거 증상이다.

과거 증거는 `010640ccc8f74f56075df09a654352ae3d162d25`의 기록을 읽어 대조했다. 기록된 exit는 `0`이다. 저장된 historical stdout/stderr의 export hash가 metadata와 일치함을 [별도 audit](../../agent-a/old-history-audit.json)에서 확인했다. 이 과거 바이너리는 이번에 재실행하지 않았다. 경로를 치환한 옛 로그의 hash 일치는 로그 보존 확인이며 과거 빌드의 모든 입력을 새로 인증하는 것은 아니다.

관련 변경: b6aacbf4016ec614b3508fd2778de4b3a29d4aef (#5629)는 surrogate 보존 문자열 처리를 도입했고, 9b2ad34a084a95d55105e32708e039bff11f7ccc (#6547)는 type 이름의 UTF-8 검증을 추가했다. 현재 crates/vm/src/builtins/type.rs의 생성 경로는 name.try_into_utf8(vm)?를 호출한다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: 원문 단일 surrogate 거부는 해결됐다. 모든 UnicodeEncodeError 범위가 같다는 주장은 연속 surrogate 반례 때문에 성립하지 않는다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 원래 A\udcdcB 입력은 surrogate를 보존한 채 UnicodeEncodeError로 거부된다. 연속 surrogate의 오류 end 필드까지 완전히 호환된다는 의미는 아니다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
