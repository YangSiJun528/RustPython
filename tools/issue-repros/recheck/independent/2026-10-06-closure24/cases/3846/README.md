**#3846 — dis 및 modulefinder 실행 경로**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/3846)은 2026-10-05T16:08:50.405629+00:00 UTC 조회에서 **open**였다. 본문과 댓글 9개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문·댓글은 dis.opmap["LOAD_CONST"], EXTENDED_ARG, _unpack_opargs가 필요하고 실제 modulefinder는 bytecode 차이로 추가 작업이 필요할 수 있다고 명시한다. 댓글의 _unpack_opargs(100)는 lazy generator 생성만 관찰한 불완전 예제다. 연결된 PR #3863의 파일·댓글도 확인했다.

초안 검증 범위: 실제 bytecode의 세 API, 5개 local import graph, 17개 원래 ModuleFinderTest가 모두 통과한다는 주장이다.

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

실행 입력 [3846-original.py](../../agent-a/inputs/3846-original.py.txt), SHA-256 `6294f07177acd5a2355a514a1291c9242fa797eb000f0ac77e395b00a9c0ed1f`:

```python
import dis

print("LOAD_CONST", dis.opmap["LOAD_CONST"])
print("EXTENDED_ARG", dis.EXTENDED_ARG)
g = dis._unpack_opargs(100)
print("constructed", type(g).__name__)
try:
    list(g)
except TypeError as e:
    print("invalid integer exhausted", type(e).__name__, str(e))
else:
    raise AssertionError("invalid integer was accepted")
code = compile("import first\nx = 42\n", "<valid-code>", "exec")
ops = list(dis._unpack_opargs(code.co_code))
print("valid exhausted", ops)
assert ops
```

실행 입력 [3846-graph.py](../../agent-a/inputs/3846-graph.py.txt), SHA-256 `284b15f808988f59cbbb783783ceba358e8407407b338388eeca73413b089b16`:

```python
import sys, json


def issue3846():
    import dis, modulefinder, pathlib, tempfile, types

    source = (
        "import first\n"
        "from package import second\n"
        "from package.second import value\n"
        "def nested():\n"
        "    import nested_dependency\n"
    )
    code = compile(source, "<independent-3846>", "exec")
    assert isinstance(dis.opmap["LOAD_CONST"], int)
    assert isinstance(dis.EXTENDED_ARG, int)
    instructions = list(dis._unpack_opargs(code.co_code))
    assert instructions and all(isinstance(x, tuple) for x in instructions)
    print("opmap, EXTENDED_ARG, _unpack_opargs: usable")
    root = pathlib.Path(tempfile.mkdtemp(prefix="modulefinder-"))
    (root / "package").mkdir()
    files = {
        "main.py": source,
        "first.py": "flag=True\n",
        "package/__init__.py": "from . import second\n",
        "package/second.py": "value=42\n",
        "nested_dependency.py": "x=1\n",
    }
    for name, content in files.items():
        with (root / name).open("x") as out:
            out.write(content)
    finder = modulefinder.ModuleFinder(path=[str(root)])
    finder.run_script(str(root / "main.py"))
    expected = ["__main__", "first", "nested_dependency", "package", "package.second"]
    assert sorted(finder.modules) == expected, sorted(finder.modules)
    assert finder.any_missing_maybe() == ([], [])
    print("module graph:", sorted(finder.modules))
    print("missing:", finder.any_missing_maybe())


globals()["issue" + sys.argv[1]]()
```

실행 입력 [3846-suite.py](../../agent-a/inputs/3846-suite.py.txt), SHA-256 `58b6d69daecf63acd06c5dedae15a8eb9942e3cd7c1b14d58f8fe3cc33e0253b`:

```python
import sys, types, os

package = types.ModuleType("test")
package.__path__ = [os.path.join(os.environ["SRC"], "Lib", "test")]
package.__file__ = os.path.join(os.environ["SRC"], "Lib", "test", "__init__.py")
sys.modules["test"] = package
import unittest, json, sys

suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])


def flatten(item):
    if isinstance(item, unittest.TestSuite):
        return [t for child in item for t in flatten(child)]
    return [item]


tests = flatten(suite)
print(
    json.dumps(
        {
            "tests": [
                {
                    "id": t.id(),
                    "skip": bool(
                        getattr(t, "__unittest_skip__", False)
                        or getattr(
                            getattr(t, t._testMethodName), "__unittest_skip__", False
                        )
                    ),
                    "expected_failure": bool(
                        getattr(
                            getattr(t, t._testMethodName),
                            "__unittest_expecting_failure__",
                            False,
                        )
                    ),
                }
                for t in tests
            ]
        },
        sort_keys=True,
    ),
    flush=True,
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(
    json.dumps(
        {
            "run": result.testsRun,
            "skips": [(t.id(), reason) for t, reason in result.skipped],
            "expected_failures": [
                (t.id(), trace) for t, trace in result.expectedFailures
            ],
            "unexpected_successes": [t.id() for t in result.unexpectedSuccesses],
            "success": result.wasSuccessful(),
        },
        sort_keys=True,
    )
)
sys.exit(0 if result.wasSuccessful() else 1)
```

실행 입력 [3846-pr3863-runner.py](../../agent-a/inputs/3846-pr3863-runner.py.txt), SHA-256 `d5c82d2c6e92ebdc850ce2fced5c0efb1bba48ff633dcf4f958ee4bcc856f28a`:

```python
import importlib.util, sys, types, unittest, os, json

package = types.ModuleType("test")
package.__path__ = [os.path.join(os.environ["SRC"], "Lib", "test")]
package.__file__ = os.path.join(os.environ["SRC"], "Lib", "test", "__init__.py")
sys.modules["test"] = package
spec = importlib.util.spec_from_file_location("original3863", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.ModuleFinderTest)
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(
    json.dumps(
        {
            "testsRun": result.testsRun,
            "skips": len(result.skipped),
            "expectedFailures": len(result.expectedFailures),
            "unexpectedSuccesses": len(result.unexpectedSuccesses),
            "success": result.wasSuccessful(),
        }
    )
)
assert (
    result.testsRun == 17
    and not result.skipped
    and not result.expectedFailures
    and not result.unexpectedSuccesses
    and result.wasSuccessful()
)
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 3846-original-rp
"$RP" -B "$A/inputs/3846-original.py"
# 3846-original-cp
"$CP" -B "$A/inputs/3846-original.py"
# 3846-graph-rp
"$RP" -B "$A/inputs/3846-graph.py" 3846
# 3846-graph-cp
"$CP" -B "$A/inputs/3846-graph.py" 3846
# 3846-suite-rp
"$RP" -B "$A/inputs/3846-suite.py" test.test_modulefinder.ModuleFinderTest
# 3846-suite-cp
"$CP" -B "$A/inputs/3846-suite.py" test.test_modulefinder.ModuleFinderTest
# 3846-pr3863-original-suite-rp
"$RP" -B "$A/inputs/3846-pr3863-runner.py" "$A/inputs/3846-pr3863-test_modulefinder.py"
# 3846-pr3863-original-suite-cp
"$CP" -B "$A/inputs/3846-pr3863-runner.py" "$A/inputs/3846-pr3863-test_modulefinder.py"
```

원래 PR #3863의 수정 없는 [437줄 test 입력](../../agent-a/inputs/3846-pr3863-test_modulefinder.py.txt)과 그 [API 파일 응답](../../agent-a/sources/3863-files.stdout)을 함께 보존했다. 마지막 두 명령은 이 파일을 인자로 실제 실행했다. target suite 입력은 기존 `Lib/test/test_modulefinder.py`이며 hash가 실행 기록에 있다.

관찰과 판정 근거: LOAD_CONST=82, EXTENDED_ARG=69를 관찰했다(역사적 CPython 100/144와 숫자가 같을 필요는 없다). _unpack_opargs(100)는 양쪽 generator를 만들지만 끝까지 소모하면 TypeError를 낸다. 유효한 compile 결과의 co_code는 실제 list로 끝까지 소모됐다. modulefinder.run_script가 import/from/relative/nested import를 포함한 그래프 [__main__, first, nested_dependency, package, package.second]를 찾았고 missing=([],[]) assertion이 통과했다. 목표 커밋의 기존 ModuleFinderTest 17개는 양쪽 모두 skip/xfail 없이 통과했다. 추가로 PR #3863에서 가져온 원래 437줄 test 파일도 assertion/data를 수정하지 않고 두 인터프리터에서 17개 전부 실행·통과했다. 각각 testsRun=17, skips=0, expectedFailures=0, unexpectedSuccesses=0이다.

대표 원시 출력 `3846-original-rp` (stdout/stderr 구분은 record 참조):

```text
LOAD_CONST 82
EXTENDED_ARG 69
constructed generator
invalid integer exhausted TypeError object of type 'int' has no len()
valid exhausted [(0, 0, 128, 0), (2, 2, 94, 0), (4, 4, 82, 1), (6, 6, 73, 0), (8, 8, 116, 0), (10, 10, 94, 42), (12, 12, 116, 1), (14, 14, 82, 1), (16, 16, 35, None)]
```

원문·본문·실행 입력 대조: 공유 probes.py에서 해당 함수만 표시한 초안은 imports/dispatcher와 검사 논리가 동등하다. 예전 generator 생성만으로는 요구 기능 사용을 증명하지 못했지만 이번엔 실제 소모·modulefinder·원래 suite를 실행했다. CPython 배포판에 test 패키지가 없어 repository test 패키지 경로만 제공했고 CPython stdlib는 유지했다.

과거 5631d2102bfeb8e0ace727ba539258beb6cdbb7e의 세 개별 probe는 각각 AttributeError: module 'dis' has no attribute 'opmap', 'EXTENDED_ARG', '_unpack_opargs'를 보고했다. 새 결과는 속성 존재를 넘어 실제 iteration과 modulefinder 사용을 검증했다.

과거 증거는 [기존 reused-history.json](../../agent-a/old-evidence/tools/issue-repros/recheck/cases/3846/reused-history.json)의 이전 입력·revision·출력 기록이다. 이번 실행과 혼합하지 않았고 과거 바이너리는 재실행하지 않았다. 과거 기록만으로 실제 use-path 성공이나 최초 수정 commit을 판단하지 않는다.

관련 변경: 093ba251abbb671b0c3870b4dcb467f65c567c86 (#5377)의 첫 부모 diff에 dis opcode export, _unpack_opargs, _find_imports가 추가된 것을 확인했다. 현재 모든 modulefinder 동작이 이 PR 하나로 완성됐다고 단정하지 않는다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: 모든 import hook·namespace package·가능한 bytecode 조합을 인증하지 않는다. 원래 정수 100 입력의 generator 생성은 정상적인 bytecode 사용 성공으로 세지 않았다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 실제 bytecode iteration과 local import graph가 작동하며, 목표 커밋 및 연결된 원래 PR의 ModuleFinderTest 17개가 각기 skip/xfail 없이 통과했다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
