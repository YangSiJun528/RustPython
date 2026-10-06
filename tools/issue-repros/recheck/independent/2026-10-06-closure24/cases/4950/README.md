**#4950 — bool 숫자 format 코드**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/4950)은 2026-10-05T16:08:45.687582+00:00 UTC 조회에서 **open**였다. 본문과 댓글 3개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문 10개 표현식은 False의 f/x/X/e/E/c/g/o/%/o 포맷이다(o가 중복된다). 댓글은 n을 추가하고 d와 비교한다. 원래 환경은 Ubuntu 18.04, RustPython 0.2.0 fa790558211ec690541299258f44d7453501958a, CPython 3.8.0·3.9.0·3.11.3이다. VauleError는 본문 오타다.

초안 검증 범위: False/True에서 원문 코드, n/d, 08x/+08d/.2f/.1%/>5n까지 C locale의 34개 결과가 같다는 주장이다.

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

실행 입력 [4950-original.py](../../agent-a/inputs/4950-original.py.txt), SHA-256 `86f317627af5cbc6e1b3d00655759586c1572cdae9b5a200e3a8588ad496374e`:

```python
"{:f}".format(False)
"{:x}".format(False)
"{:X}".format(False)
"{:e}".format(False)
"{:E}".format(False)
"{:c}".format(False)
"{:g}".format(False)
"{:o}".format(False)
"{:%}".format(False)
"{:o}".format(False)
```

실행 입력 [4950-draft.py](../../agent-a/inputs/4950-draft.py.txt), SHA-256 `6fb4ab15ac9ac9ffe58234bdf0b02d3158de367a1a96052569b215a5c56fa0fd`:

```python
import sys, json


def issue4950():
    import locale

    locale.setlocale(locale.LC_ALL, "C")
    cases = ["f", "x", "X", "e", "E", "c", "g", "o", "%", "o", "n", "d"]
    cases += ["08x", "+08d", ".2f", ".1%", ">5n"]
    results = []
    for value in (False, True):
        for spec in cases:
            actual = ("{:" + spec + "}").format(value)
            assert actual == format(int(value), spec)
            results.append([value, spec, actual])
    print(
        json.dumps(
            {"locale": locale.setlocale(locale.LC_ALL), "results": results},
            sort_keys=True,
        )
    )


globals()["issue" + sys.argv[1]]()
```

실행 입력 [4950-locales.py](../../agent-a/inputs/4950-locales.py.txt), SHA-256 `edd35e3dff95f81b1a735a9871be0517a011101c583916a40667c045e68fc3e5`:

```python
import locale, json

specs = [
    "f",
    "x",
    "X",
    "e",
    "E",
    "c",
    "g",
    "o",
    "%",
    "o",
    "n",
    "d",
    "08x",
    "+08d",
    ".2f",
    ".1%",
    ">5n",
]
for loc in ["C", "en_US.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8"]:
    effective = locale.setlocale(locale.LC_ALL, loc)
    conv = locale.localeconv()
    rows = []
    for value in [False, True]:
        for spec in specs:
            text = ("{:" + spec + "}").format(value)
            assert text == format(int(value), spec)
            rows.append([value, spec, text])
    print(
        json.dumps(
            {
                "requested": loc,
                "effective": effective,
                "grouping": conv["grouping"],
                "separator": conv["thousands_sep"],
                "decimal": conv["decimal_point"],
                "results": rows,
            },
            sort_keys=True,
        )
    )
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 4950-original-rp
"$RP" -B "$A/inputs/4950-original.py"
# 4950-original-cp
"$CP" -B "$A/inputs/4950-original.py"
# 4950-draft-rp
"$RP" -B "$A/inputs/4950-draft.py" 4950
# 4950-draft-cp
"$CP" -B "$A/inputs/4950-draft.py" 4950
# 4950-locales-rp
"$RP" -B "$A/inputs/4950-locales.py"
# 4950-locales-cp
"$CP" -B "$A/inputs/4950-locales.py"
```

관찰과 판정 근거: 원문 표현식 10개는 모두 ValueError 없이 exit 0으로 실행됐다. 초안의 정확한 17개 spec × False/True = 34개 행은 C locale에서 두 인터프리터가 같은 JSON을 냈고 각 결과가 int(bool) format과 같다는 assertion이 통과했다. NUL/제어문자는 JSON \u0000/\u0001로 보존됐다. 실제 제공 locale을 열거한 뒤 C, en_US.UTF-8, de_DE.UTF-8, fr_FR.UTF-8 각각을 setlocale로 적용해 총 136개 결과도 비교했다. 요청 locale과 유효 locale, grouping/소수점/구분자를 로그에 남겼고 stdout은 완전히 같다.

원문·본문·실행 입력 대조: 기존 공유 probes.py 링크에서 issue4950 함수·imports·dispatcher만 표시한 초안이다. 해당 함수의 format 목록과 assertion은 동등하다. 새 실행은 그 선택된 함수만 사용했고 원문 10개 표현식도 별도로 추출·실행했다.

과거 fa790558211ec690541299258f44d7453501958a는 원문에 지정된 revision이다. 9개 고유 format 코드의 기존 실행 stderr에서 각각 ValueError: Invalid format specifier를 확인했다. 원문 o 중복은 별도의 고유 기능이 아니다.

과거 증거는 [기존 reused-history.json](../../agent-a/old-evidence/tools/issue-repros/recheck/cases/4950/reused-history.json)의 이전 입력·revision·출력 기록이다. 이번 실행과 혼합하지 않았고 과거 바이너리는 재실행하지 않았다. 과거 기록만으로 실제 use-path 성공이나 최초 수정 commit을 판단하지 않는다.

관련 변경: 3d2c51962bfdc598310df648dab328bd4550c95b (#5012)는 Parser/format 의존성을 b2f95e2에서 69d27d9로 갱신한다. 새로 읽은 Parser PR #91 patch는 bool을 format_int/format_float로 분기한다. 현재 crates/common/src/format.rs:838의 분기도 확인했다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: 검사하지 않은 locale·폭·정밀도 모든 조합을 보장하지 않는다. 원래 Linux 플랫폼과 이전 CPython 버전은 재실행하지 않았다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: C locale의 명시된 34개 bool format 결과가 CPython과 일치하며, 추가로 적용한 네 locale의 같은 코드 목록에서도 일치한다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
