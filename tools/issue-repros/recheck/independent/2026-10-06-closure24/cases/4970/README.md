**#4970 — LC_ALL 미설정 상태의 locale 숫자 포맷**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/4970)은 2026-10-05T16:08:46.638551+00:00 UTC 조회에서 **open**였다. 본문과 댓글 1개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문은 LC_ALL이 없을 때 test_format.FormatTest.test_locale의 n 포맷에 쉼표가 없어 실패한다는 보고다. 정확한 실행 revision/운영체제는 없다. 댓글 #4613은 locale 기반 n 포맷 문제와 연결한다. C locale이나 skip만으로는 원문 실패 경로를 검증할 수 없다.

초안 검증 범위: LC_ALL은 실제 unset, LANG/LC_NUMERIC=en_US.UTF-8인 상태에서 원래 test_locale 및 int/float locale tests 3개가 skip/xfail 없이 통과한다는 주장이다.

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

실행 입력 [4970-draft.py](../../agent-a/inputs/4970-draft.py.txt), SHA-256 `4a01132eef185a09e4cc187504f735668f5aedaf5a0ab5c126b189aa0103db43`:

```python
import sys
import os
import json
import locale
import unittest

# CPython imports the identical repository test source, while retaining its own stdlib.
test_parent = os.path.join(os.environ["SRC"], "Lib")
import types

test_package = types.ModuleType("test")
test_package.__path__ = [test_parent + "/test"]
test_package.__file__ = test_parent + "/test/__init__.py"
sys.modules["test"] = test_package
from test import test_format, test_types

effective = locale.setlocale(locale.LC_ALL, "")
conv = locale.localeconv()
print(
    json.dumps(
        {
            "LC_ALL_environment": os.environ.get("LC_ALL"),
            "LANG": os.environ.get("LANG"),
            "LC_NUMERIC": os.environ.get("LC_NUMERIC"),
            "effective": effective,
            "conv": {
                k: conv[k] for k in ("decimal_point", "thousands_sep", "grouping")
            },
            "integer": format(123456789, "n"),
            "float": format(1234.5, "n"),
            "test_files": [test_format.__file__, test_types.__file__],
        },
        indent=2,
    ),
    flush=True,
)
assert conv["grouping"], (
    "A grouping locale must be active to reach the original assertion"
)
suite = unittest.TestSuite(
    [
        test_format.FormatTest("test_locale"),
        test_types.TypesTests("test_int__format__locale"),
        test_types.TypesTests("test_float__format__locale"),
    ]
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
assert result.testsRun == 3
assert (
    not result.skipped
    and not result.expectedFailures
    and not result.unexpectedSuccesses
)
assert result.wasSuccessful()
```

실행 입력 [4970-locale-support.py](../../agent-a/inputs/4970-locale-support.py.txt), SHA-256 `3ab48973329a6cf0423713f3833d1062745a9fdcd10635bc2a3b851b0d208c77`:

```python
import locale, os

print("LC_ALL-present", "LC_ALL" in os.environ)
for loc in ["en_US.UTF8", "en_US.UTF-8", ""]:
    try:
        result = locale.setlocale(locale.LC_NUMERIC, loc)
        c = locale.localeconv()
        print(
            repr(loc),
            repr(result),
            repr(c["thousands_sep"]),
            c["grouping"],
            format(123456789, "n"),
            format(1234.5, "n"),
        )
    except locale.Error as e:
        print(repr(loc), "UNAVAILABLE", str(e))
```

다음 locale 설정을 공통 설정 위에 적용한다. LC_ALL은 빈 문자열이 아니라 환경에서 제거한다.

~~~sh
unset LC_ALL
export LANG=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8
~~~

실제 실행 명령:

```sh
# 4970-clean-env-rp
"$RP" -B "$A/inputs/4970-draft.py"
# 4970-clean-env-cp
"$CP" -B "$A/inputs/4970-draft.py"
# 4970-locale-support-rp
"$RP" -B "$A/inputs/4970-locale-support.py"
# 4970-locale-support-cp
"$CP" -B "$A/inputs/4970-locale-support.py"
```

최종 clean-env 명령은 LC_ALL 및 나머지 LC_*를 제거하고 `LANG=en_US.UTF-8 LC_NUMERIC=en_US.UTF-8 SRC="$SRC"`를 지정했다. 이슈 원문에는 실행 전체 test 목록이 없으므로 원래 실패 메서드와 초안의 추가 두 메서드를 각각 포함했다. [locale -a 전체 결과](../../agent-a/logs/identity-locale-list.stdout)도 저장했다.

관찰과 판정 근거: LC_ALL 키가 환경에 없는 것을 확인했다. LC_* 잔여값도 지운 최종 실행의 effective locale은 en_US.UTF-8, thousands_sep=',', grouping=[3,0], decimal_point='.'였다. format(123456789,'n')='123,456,789', format(1234.5,'n')='1,234.5'를 양쪽에서 확인했다. 기존 test_format.test_locale와 test_types의 int/float locale 메서드 3개가 변경 없이 실행되어 모두 통과했고 skip/expectedFailure/unexpectedSuccess는 0이다. macOS에는 en_US.UTF8 별칭이 없어 명시 적용이 실패한다. decorator의 다음 후보 ''는 LANG/LC_NUMERIC으로 지정한 실제 en_US.UTF-8 그룹화 locale에 도달했다. 이 별칭을 지원한다고 판정하지 않으며 C fallback을 통과로 세지 않았다. 첫 실행에는 LC_CTYPE=C.UTF-8이 남아 composite locale이었고, 추가 clean-env 실행으로 전 범주의 locale도 확인했다.

대표 원시 출력 `4970-clean-env-rp` (stdout/stderr 구분은 record 참조):

```text
{
  "LC_ALL_environment": null,
  "LANG": "en_US.UTF-8",
  "LC_NUMERIC": "en_US.UTF-8",
  "effective": "en_US.UTF-8",
  "conv": {
    "decimal_point": ".",
    "thousands_sep": ",",
    "grouping": [
      3,
      0
    ]
  },
  "integer": "123,456,789",
  "float": "1,234.5",
  "test_files": [
    "<workspace>/Lib/test/test_format.py",
    "<workspace>/Lib/test/test_types.py"
  ]
}
```

원문·본문·실행 입력 대조: 초안의 test bootstrap은 동일 저장소 test 소스를 import하고 각 인터프리터의 stdlib 구현을 유지한다. 이전 실행 input의 <slot-b-source>/Lib 대신 SRC/Lib를 사용한 경로 치환 외에 세 테스트의 assertions/data/markers는 변경하지 않았다. 기존 기록은 Rosetta, 새 실행은 native ARM64이다.

과거 7a6000d181b7611c26f2d1353d0462d7bec26da6의 test_locale 실행은 AssertionError: ',' not found in '123456789', Ran 1 test, FAILED (failures=1)을 남겼다. 정확한 보고 revision이 없어 선정한 당시 main 근사 revision의 이전 기록이며 이번 재실행이 아니다.

과거 증거는 [기존 reused-history.json](../../agent-a/old-evidence/tools/issue-repros/recheck/cases/4970/reused-history.json)의 이전 입력·revision·출력 기록이다. 이번 실행과 혼합하지 않았고 과거 바이너리는 재실행하지 않았다. 과거 기록만으로 실제 use-path 성공이나 최초 수정 commit을 판단하지 않는다.

과거 catalog metadata에는 공통 runner가 skip/expectedFailure를 메모리에서 우회할 수 있다는 설명이 있다. 선택된 test_locale의 bypassed_decorators는 []로 기록되지만 과거 runner 자체는 이번에 실행하지 않았다. 새 3개 테스트에서는 decorator/assertion/data를 수정하거나 우회하지 않았다.

관련 변경: 1bd40ffd86c289f6fe4e22770f271d0b65636fca (#7350)는 localeconv의 grouping/thousands_sep/decimal_point를 n 포맷에 전달하며 test_locale의 skip을 제거한다. 관련 diff와 현재 원본 테스트 decorator를 확인했다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: 없는 en_US.UTF8 별칭의 성공을 주장하지 않는다. 모든 locale 및 별도 padding/zero-padding 문제는 이 판정 범위가 아니다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: LC_ALL을 실제 제거하고 en_US.UTF-8의 그룹화를 확인한 macOS ARM64 실행에서 원래 test_locale와 두 관련 locale 테스트가 skip/xfail 없이 통과했다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
