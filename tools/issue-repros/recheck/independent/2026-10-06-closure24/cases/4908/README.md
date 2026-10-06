# #4908 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4908)는 2026-10-05T16:10:24.041496+00:00 UTC 조회 시 **open**였다. 본문과 댓글 0개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

Ubuntu 18.04/RustPython 0.2.0/471ec26에서 A[1:2, *l]의 AST를 unparse하면 A[(1:2, *l)]가 되어 다시 parse하지 못한다. 최소 범위는 parse→unparse→reparse와 구조 보존이다.

초안은 원문 재파싱 성공과 추가 slice/starred 조합의 AST 구조 보존을 주장한다.

양쪽 원문 출력은 A[1:2, *l]이며 reparse가 성공했다. 원문을 포함한 7개 표현에서 위치를 제외한 ast.dump가 모두 같았다. 별도 assert에서 Subscript의 slice가 Tuple이고 첫 원소가 Slice, 두 번째가 Starred임을 확인했다.

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

입력 파일 `4908-original.py` ([저장된 파일](../../agent-b/inputs/4908-original.py.txt)):

```python
import ast

code_1 = "A[1:2, *l]"
tree_1 = ast.parse(code_1)  # work normally

code_2 = ast.unparse(tree_1)
print(code_2)  # str "A[1:2, *l]"
tree_2 = ast.parse(code_2)  # fail
```

입력 파일 `4908-draft-boundaries.py` ([저장된 파일](../../agent-b/inputs/4908-draft-boundaries.py.txt)):

```python
import ast

for source in [
    "A[1:2, *l]",
    "A[:, *l]",
    "A[*l, 1:2]",
    "A[1:2:3, *l, :]",
    "A[*l]",
    "A[()]",
    "A[1,]",
]:
    tree = ast.parse(source)
    emitted = ast.unparse(tree)
    reparsed = ast.parse(emitted)
    print(source, "->", emitted, "equivalent", ast.dump(tree) == ast.dump(reparsed))
```

입력 파일 `4908-structure.py` ([저장된 파일](../../agent-b/inputs/4908-structure.py.txt)):

```python
import ast

one = ast.parse("A[1:2, *l]")
two = ast.parse(ast.unparse(one))
assert ast.dump(one, include_attributes=False) == ast.dump(
    two, include_attributes=False
)
node = two.body[0].value
assert isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Tuple)
assert isinstance(node.slice.elts[0], ast.Slice) and isinstance(
    node.slice.elts[1], ast.Starred
)
print(ast.dump(two, include_attributes=False))
```

```sh
"$RP" -B "$IN/4908-original.py"
"$CP" -B "$IN/4908-original.py"
"$RP" -B "$IN/4908-draft-boundaries.py"
"$CP" -B "$IN/4908-draft-boundaries.py"
"$RP" -B "$IN/4908-structure.py"
"$CP" -B "$IN/4908-structure.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4908-original-rp](../../agent-b/records/4908-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4908-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4908-original-cp](../../agent-b/records/4908-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4908-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4908-boundaries-rp](../../agent-b/records/4908-boundaries-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4908-draft-boundaries.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4908-boundaries-cp](../../agent-b/records/4908-boundaries-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4908-draft-boundaries.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4908-structure-rp](../../agent-b/records/4908-structure-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4908-structure.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4908-structure-cp](../../agent-b/records/4908-structure-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4908-structure.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4908-boundaries-rp`

```text
A[1:2, *l] -> A[1:2, *l] equivalent True
A[:, *l] -> A[:, *l] equivalent True
A[*l, 1:2] -> A[*l, 1:2] equivalent True
A[1:2:3, *l, :] -> A[1:2:3, *l, :] equivalent True
A[*l] -> A[*l,] equivalent True
A[()] -> A[()] equivalent True
A[1,] -> A[1,] equivalent True
```

`4908-structure-rp`

```text
Module(body=[Expr(value=Subscript(value=Name(id='A', ctx=Load()), slice=Tuple(elts=[Slice(lower=Constant(value=1), upper=Constant(value=2)), Starred(value=Name(id='l', ctx=Load()), ctx=Load())], ctx=Load()), ctx=Load()))])
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4908.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문 입력은 공백·주석을 정리했을 뿐 원래 표현과 세 연산을 유지한다. 추가 7개 사례는 저장 boundary 입력을 해시 확인 후 동일하게 실행했다.

471ec268737c 저장 입력은 원문과 같은 parse/unparse/reparse이다. 출력 A[(1:2, *l)] 뒤 콜론 위치 SyntaxError로 실패한다. 기존 입력은 구조 동일성까지 확인하지 않았으며 새 검증이 이를 추가했다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #5121의 4d6a18063은 visit_Subscript에서 nonempty tuple slice의 바깥 괄호를 생략하며 Starred 예외 조건을 제거한다. 현재 해당 Python 구현은 Lib/_ast_unparse.py에 있다.

[4d6a180638f3 diff](../../agent-b/logs/change-4908-4d6a18063.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4908-4d6a18063.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

임의 AST 변환이나 실제 A/l 객체 실행의 의미까지 검증한 것은 아니다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 원문 starred subscript는 유효한 구문으로 unparse되고 reparse되며, 확인한 7개 slice/starred 사례의 AST 구조가 보존된다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
