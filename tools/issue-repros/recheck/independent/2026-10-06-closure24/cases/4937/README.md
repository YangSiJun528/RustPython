# #4937 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4937)는 2026-10-05T16:10:19.890677+00:00 UTC 조회 시 **open**였다. 본문과 댓글 1개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

Ubuntu 18.04, RustPython 0.2.0/0284059에서 Subject:=?us-ascii?X?value?=를 email.policy.default로 파싱한 뒤 get("Subject")가 KeyError("x")를 낸다. charset은 us-ascii이고 알 수 없는 transfer encoding X가 문제다. CPython 3.8/3.9/3.11은 중단되지 않는다고 보고됐다.

초안은 원문 Subject 조회가 KeyError 없이 끝나고, 추가 unknown-encoding/malformed header 사례도 확인됐다고 주장한다.

원문 전체 경로는 양쪽에서 stdout/stderr 없이 종료 0. 추가 확인에서 X와 x는 원문 encoded word를 그대로 반환하고 defects는 빈 목록이었다. Q/B는 value로 디코딩됐다. 앞뒤 일반 텍스트가 있는 X 사례도 보존되었다. 반환 타입, 문자열, defects 출력이 양쪽에서 정확히 같다.

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

입력 파일 `4937-original.py` ([저장된 파일](../../agent-b/inputs/4937-original.py.txt)):

```python
import email
import email.policy

mytext = "Subject:=?us-ascii?X?value?="
em = email.message_from_string(mytext, policy=email.policy.default)
em.get("Subject")
```

입력 파일 `4937-draft-boundaries.py` ([저장된 파일](../../agent-b/inputs/4937-draft-boundaries.py.txt)):

```python
import email
import email.policy

for source in [
    "Subject:=?us-ascii?X?value?=",
    "Subject:=?us-ascii?x?value?=",
    "Subject:=?us-ascii?Q?value?=",
    "Subject:=?us-ascii?B?dmFsdWU=?=",
    "Subject:before =?us-ascii?X?value?= after",
]:
    message = email.message_from_string(source, policy=email.policy.default)
    header = message.get("Subject")
    print(
        repr(source),
        type(header).__name__,
        repr(str(header)),
        [(type(item).__name__, str(item)) for item in header.defects],
    )
```

```sh
"$RP" -B "$IN/4937-original.py"
"$CP" -B "$IN/4937-original.py"
"$RP" -B "$IN/4937-draft-boundaries.py"
"$CP" -B "$IN/4937-draft-boundaries.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4937-original-rp](../../agent-b/records/4937-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4937-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4937-original-cp](../../agent-b/records/4937-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4937-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4937-boundaries-rp](../../agent-b/records/4937-boundaries-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4937-draft-boundaries.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4937-boundaries-cp](../../agent-b/records/4937-boundaries-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4937-draft-boundaries.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4937-boundaries-rp`

```text
'Subject:=?us-ascii?X?value?=' _UniqueUnstructuredHeader '=?us-ascii?X?value?=' []
'Subject:=?us-ascii?x?value?=' _UniqueUnstructuredHeader '=?us-ascii?x?value?=' []
'Subject:=?us-ascii?Q?value?=' _UniqueUnstructuredHeader 'value' []
'Subject:=?us-ascii?B?dmFsdWU=?=' _UniqueUnstructuredHeader 'value' []
'Subject:before =?us-ascii?X?value?= after' _UniqueUnstructuredHeader 'before =?us-ascii?X?value?= after' []
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4937.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

원문 코드는 공백·따옴표 표기만 정리한 것이며 연산은 같다. 반환값을 확인하지 않는 원문에 추가 입력으로 text/type/defects 관찰을 보강했다.

02840593bc56 저장 입력은 같은 mytext, policy.default, get 연산이다. 저장 stderr에서 _cte_decoders[cte]의 KeyError: x가 확인된다. 경로 익명화와 줄바꿈 외 원문 연산이 유지된다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #5663의 d52081fe4 첫 부모 대비 diff는 get_encoded_word가 (ValueError, KeyError)를 잡고 _InvalidEwError를 발생시켜 파서 복구 경로로 넘기도록 바꾼다.

[d52081fe41e5 diff](../../agent-b/logs/change-4937-d52081fe4.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4937-d52081fe4.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

Ubuntu 18.04나 모든 email 문법을 검증하지 않았다. 원문 및 나열한 다섯 Subject 입력에 대한 결론이다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 원문의 email Subject 조회는 KeyError 없이 끝나며, X/x encoded word 보존과 확인한 Q/B·앞뒤 텍스트 사례도 CPython과 일치한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
