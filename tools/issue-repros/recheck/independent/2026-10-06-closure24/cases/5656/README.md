# #5656 독립 검증

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/5656)는 2026-10-05T16:10:26.676214+00:00 UTC 조회 시 **open**였다. 본문과 댓글 1개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

extra_tests/snippets/builtin_bytes.py의 b"omkmok\Xaa"를 실행해도 RustPython이 CPython의 invalid escape SyntaxWarning을 내지 않는다는 보고다. CPython 버전은 원문과 댓글에 확정되지 않았다. 현재 파일에서는 해당 줄이 25행이다.

초안은 bytes 값 보존, 컴파일 중 SyntaxWarning 및 warning-as-error 처리를 주장한다.

실제 기존 builtin_bytes.py를 수정 없이 양쪽에서 실행했다. 종료 0과 함께 25행 SyntaxWarning이 발생했다. 최소 bytes assert도 성공했다. invalid bytes/string은 warnings 필터 always에서 SyntaxWarning 1개, error에서 SyntaxError였다. escape한 역슬래시/raw bytes/유효 hex는 경고 없이 허용됐다. -Werror 프로세스는 양쪽 종료 1·SyntaxError다. 이때 오류 caret 열 위치는 다르며, 진단 전체가 byte-for-byte 같다고 주장하지 않는다.

실행 환경은 [슬롯 B 출처·환경 기록](../../agent-b/environment/IDENTITY.md)과 같다. 핵심적으로 RustPython은 SHA-256 d5742929…의 x86_64 재사용 산출물, CPython은 3.14.6 arm64다. B에서 실행하지만 실제 stdlib는 주 작업 폴더의 Lib를 우선 로드하며 2,324개 추적 파일의 목표 커밋 일치를 확인했다. 목표 출처는 embedded f39b054b9 배너와 보존 빌드/복사 기록·동일 산출물 해시로 뒷받침하며, 새 재현 빌드로 완전 입증한 것은 아니다.

아래 파일들을 IN 디렉터리에 해당 이름으로 저장하면 표시된 검증을 실행할 수 있다. 원문·보정·확장 입력은 파일로 구분한다.

실행 명령의 경로 변수와 환경은 다음과 같다. 실제 argv와 모든 환경 값, 시작·종료 시간은 각 실행 기록에 있다. 각 명령은 controller.py의 timeout/process-group 정리 아래 순차 실행했다.

```sh
cd <slot-b-source>
RP=<survey>/.build/slot-b/saved/current-f39-x86/rustpython
CP=<home>/.local/bin/python3
IN=<closure24-audit>/agent-b/inputs
export RUSTPYTHONPATH=<slot-b-source>/Lib
export PYTHONDONTWRITEBYTECODE=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 LC_CTYPE=C.UTF-8 TERM=dumb
export TMPDIR=<closure24-audit>/agent-b/environment/tmp
export TMP="$TMPDIR" TEMP="$TMPDIR"
export PYTHON_HISTORY=<closure24-audit>/agent-b/environment/history
export RUSTPYTHON_HISTORY="$PYTHON_HISTORY"
export SYMPY_SITE=<survey>/verification-tools/package-history-4506-original/site
```

기존 snippet 전체의 실행은 목표 checkout의 extra_tests/snippets/builtin_bytes.py를 그대로 사용한다. 다음 최소 파일은 그 파일의 25행 invalid escape assert를 별도로 보존한 것이다. 다른 snippet 검증 전체를 경고 검증의 근거로 확장하지 않는다.

입력 파일 `5656-draft-0.py` ([저장된 파일](../../agent-b/inputs/5656-draft-0.py.txt)):

```python
assert b"omkmok\Xaa" == bytes([111, 109, 107, 109, 111, 107, 92, 88, 97, 97])
```

입력 파일 `5656-draft-1.py` ([저장된 파일](../../agent-b/inputs/5656-draft-1.py.txt)):

```python
import warnings

for literal in [
    r'b"omkmok\Xaa"',
    r'"omkmok\Xaa"',
    r'b"omkmok\\Xaa"',
    r'rb"omkmok\Xaa"',
    r'b"\xff"',
]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        code = compile(literal, "<invalid-escape-probe>", "eval")
        print(
            "always",
            literal,
            repr(eval(code)),
            [
                (warning.category.__name__, str(warning.message), warning.lineno)
                for warning in caught
            ],
        )
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("error")
        try:
            compile(literal, "<invalid-escape-probe>", "eval")
        except Exception as error:
            print("error", literal, type(error).__name__)
        else:
            print("error", literal, "accepted")
```

```sh
"$RP" -B <slot-b-source>/extra_tests/snippets/builtin_bytes.py
"$CP" -B <slot-b-source>/extra_tests/snippets/builtin_bytes.py
"$RP" -B "$IN/5656-draft-0.py"
"$CP" -B "$IN/5656-draft-0.py"
"$RP" -B "$IN/5656-draft-1.py"
"$CP" -B "$IN/5656-draft-1.py"
"$RP" -B -Werror "$IN/5656-draft-0.py"
"$CP" -B -Werror "$IN/5656-draft-0.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [5656-actual-snippet-rp](../../agent-b/records/5656-actual-snippet-rp.json): 종료 0, timeout False; [입력](https://github.com/RustPython/RustPython/blob/f39b054b9c8cbbf884f53123eef028131789990c/extra_tests/snippets/builtin_bytes.py). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. invalid escape SyntaxWarning과 보존된 bytes 값, 제어 사례 및 error 필터 결과를 별도로 확인했다.
- [5656-actual-snippet-cp](../../agent-b/records/5656-actual-snippet-cp.json): 종료 0, timeout False; [입력](https://github.com/RustPython/RustPython/blob/f39b054b9c8cbbf884f53123eef028131789990c/extra_tests/snippets/builtin_bytes.py). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. invalid escape SyntaxWarning과 보존된 bytes 값, 제어 사례 및 error 필터 결과를 별도로 확인했다.
- [5656-literal-rp](../../agent-b/records/5656-literal-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5656-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. invalid escape SyntaxWarning과 보존된 bytes 값, 제어 사례 및 error 필터 결과를 별도로 확인했다.
- [5656-literal-cp](../../agent-b/records/5656-literal-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5656-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. invalid escape SyntaxWarning과 보존된 bytes 값, 제어 사례 및 error 필터 결과를 별도로 확인했다.
- [5656-warnings-rp](../../agent-b/records/5656-warnings-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5656-draft-1.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. invalid escape SyntaxWarning과 보존된 bytes 값, 제어 사례 및 error 필터 결과를 별도로 확인했다.
- [5656-warnings-cp](../../agent-b/records/5656-warnings-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5656-draft-1.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. invalid escape SyntaxWarning과 보존된 bytes 값, 제어 사례 및 error 필터 결과를 별도로 확인했다.
- [5656-warnings-as-error-rp](../../agent-b/records/5656-warnings-as-error-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5656-draft-0.py.txt). -Werror에서 invalid escape가 SyntaxError로 승격되고 종료 1. 의도한 경고-오류 처리다.
- [5656-warnings-as-error-cp](../../agent-b/records/5656-warnings-as-error-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5656-draft-0.py.txt). -Werror에서 invalid escape가 SyntaxError로 승격되고 종료 1. 의도한 경고-오류 처리다.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다. -Werror 진단의 caret 열 위치 차이는 위에 별도로 설명했다.

`5656-warnings-rp`

```text
always b"omkmok\Xaa" b'omkmok\\Xaa' [('SyntaxWarning', '"\\X" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\\\X"? A raw string is also an option.', 1)]
error b"omkmok\Xaa" SyntaxError
always "omkmok\Xaa" 'omkmok\\Xaa' [('SyntaxWarning', '"\\X" is an invalid escape sequence. Such sequences will not work in the future. Did you mean "\\\\X"? A raw string is also an option.', 1)]
error "omkmok\Xaa" SyntaxError
always b"omkmok\\Xaa" b'omkmok\\Xaa' []
error b"omkmok\\Xaa" accepted
always rb"omkmok\Xaa" b'omkmok\\Xaa' []
error rb"omkmok\Xaa" accepted
always b"\xff" b'\xff' []
error b"\xff" accepted
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/5656.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문 최소 재현은 원문 경고 줄의 그대로인 별도 파일이다. 저장 로그에서 전체 snippet을 실행한 것으로 확대하지 않는다. 새 실제 snippet 실행으로 경로 범위를 보강했다.

c3ed002b1204의 저장 최소 입력은 동일한 bytes assert이며 stderr에 SyntaxWarning이 없다. 종료 0은 원문 문제 해결의 증거가 아니다. 과거 파일 전체 대신 추출한 한 줄을 실행했다는 한계가 있다. 새 검증은 현재 실제 파일 경로도 실행했다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #7164의 목표 조상 680de3357은 compile 경로에 string/bytes invalid-escape 스캔과 SyntaxWarning 방출을 추가한다.

[680de33572dc diff](../../agent-b/logs/change-5656-680de3357.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-5656-680de3357.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

원문의 미상 CPython 버전이나 모든 진단 caret 위치 일치를 주장하지 않는다. 검증 비교 버전은 3.14.6이다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 현재 builtin_bytes.py의 원래 invalid escape에서 SyntaxWarning이 발생하고 bytes 값은 유지된다. -Werror는 예상한 SyntaxError 종료를 만든다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
