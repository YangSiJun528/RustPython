**#4784 — README의 실제 API 문서 링크**

[원문](https://github.com/RustPython/RustPython/issues/4784)은 2026-10-05T16:08:51.316073+00:00 UTC 조회에서 **open**였다. 본문과 댓글 2개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문은 README의 https://docs.rs/rustpython 링크가 rustpython-0.1.2 is not a library 페이지를 보여 준다는 문제다. 댓글의 cargo doc는 로컬 우회 방법일 뿐 public link 해결 증거가 아니다.

초안 검증 범위: README 목적지가 crate/API 항목을 갖춘 RustPython 0.6.0 문서를 제공한다는 주장이다.

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

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 4784-readme-target
git show f39b054b9c8cbbf884f53123eef028131789990c:README.md
# 4784-http
curl --silent --show-error --location --max-time 30 --output "$A/sources/4784-docs.html" --dump-header "$A/sources/4784-headers.txt" --write-out 'status=%{http_code}
url=%{url_effective}
' https://docs.rs/rustpython
# 4784-api-http
curl --silent --show-error --location --max-time 30 --output "$A/sources/4784-api.html" --dump-header "$A/sources/4784-api-headers.txt" --write-out 'status=%{http_code}
url=%{url_effective}
' https://docs.rs/rustpython/latest/rustpython/struct.InterpreterBuilder.html
```

관찰과 판정 근거: 목표 커밋 README:217의 online documentation 링크는 여전히 https://docs.rs/rustpython 이다. 새 요청은 HTTP 200, 최종 https://docs.rs/rustpython/latest/rustpython/을 반환했다. 실제 body의 title은 rustpython - Rust, heading은 Crate rustpython, 버전은 0.6.0이다. Interpreter, InterpreterBuilder, InterpreterBuilderExt, run 등의 API 목록과 crate 설명이 있다. 별도 InterpreterBuilder API 링크도 HTTP 200이며 실제 struct/impl/new 메서드 문서가 존재한다. status만으로 판정하지 않았다. curl exit 0, timeout 없음이다.

원문·본문·실행 입력 대조: 원문과 목표 README의 링크 목적지는 동일하다. 기존 초안의 live page 검증과 새 요청은 같은 종류의 증거다. 외부 사이트의 latest는 목표 source commit으로 고정된 build가 아니다.

관련 변경: 특정 코드 수정 커밋은 주장하지 않는다. README 링크와 현재 게시된 crate/API 문서의 실제 내용으로 죽은 링크 증상이 사라졌음을 확인했다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: docs.rs 현재 응답은 0.6.0 문서이며 f39b054b9c8c의 cargo doc 산출물을 검증한 것이 아니다. 사이트의 향후 상태도 보장하지 않는다. CPython 비교는 적용되지 않는다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 조회 시점의 README 목적지가 RustPython 0.6.0 crate 문서와 실제 API 페이지를 제공한다. 목표 커밋에서 문서를 새로 빌드했다는 의미는 아니다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
