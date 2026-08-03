# CPython은 서로 다른 결정을 단계별로 CodeObject에 굳힌다

Python 소스는 문장과 표현식의 구조만 말한다. 평가 루프가 실행하려면 이름을 어느
저장소에서 찾을지, 조건에 따라 어느 명령으로 이동할지, 상수와 이름을 몇 번
인덱스로 가리킬지까지 정해야 한다. 이 결정들은 왜 한 번에 내려지지 않고 AST,
심볼 테이블, 명령 시퀀스, CFG를 차례로 거치는가?

**각 중간 표현이 서로 다른 범위의 결정을 맡기 때문이다.** AST는 소스 구조를,
심볼 테이블은 코드 블록별 이름 분류를, 명령 시퀀스와 CFG는 연산과 실행 경로를,
assembler는 실제 opcode 배치와 메타데이터를 확정한다. 마지막 CodeObject는 이
결과를 재사용 가능한 실행 설계로 묶지만, 특정 호출의 인수·지역 값·현재 명령
위치는 담지 않는다.

예제 출력은 CPython 3.14.6에서, 단계는 공식 `Python/compile.c`, `codegen.c`,
`symtable.c`, `flowgraph.c`, `assemble.c`에서 확인했다. 내부 명령과 최적화는 호환
규격이 아니므로 다른 버전에서는 출력이 달라질 수 있다.

## 한 함수가 거치는 결정을 실행 가능한 코드로 관찰한다

```python
scale = 3

def adjust(x):
    y = x + scale
    return y if y > 0 else 0
```

다음 검사 스크립트를 CPython 3.14.6에서 실행해 공개 API로 관찰 가능한 AST,
심볼 분류, 최종 바이트코드와 CodeObject 값을 한 번에 확인한다.

```python
import ast
import dis
import symtable
import types

source = """scale = 3

def adjust(x):
    y = x + scale
    return y if y > 0 else 0
"""

tree = ast.parse(source, filename="example.py")
print(ast.dump(tree))

top = symtable.symtable(source, "example.py", "exec")
function = next(c for c in top.get_children() if c.get_name() == "adjust")
for table in (top, function):
    print(f"[{table.get_name()}]")
    for name in table.get_identifiers():
        symbol = table.lookup(name)
        kinds = [kind for kind in
                 ("parameter", "local", "global", "assigned", "referenced")
                 if getattr(symbol, f"is_{kind}")()]
        print(name, ", ".join(kinds))

module_code = compile(source, "example.py", "exec")
adjust_code = next(
    value for value in module_code.co_consts if isinstance(value, types.CodeType)
)
dis.dis(module_code, depth=0, adaptive=False, show_caches=False)
dis.dis(adjust_code, adaptive=False, show_caches=False)
print("module co_names =", module_code.co_names)
print("module constants =", tuple(
    v.co_name if isinstance(v, types.CodeType) else v
    for v in module_code.co_consts
))
print("adjust =", adjust_code.co_names, adjust_code.co_varnames,
      adjust_code.co_consts, adjust_code.co_stacksize)
```

내부 명령 시퀀스와 CFG는 공개 Python 객체가 아니다. 다음 절에서는 공개 출력
사이를 공식 컴파일러 단계로 연결한다.

## AST는 표면 문법에서 프로그램 구조만 남긴다

AST 출력을 읽기 쉽게 줄바꿈했다. 위치 속성은 생략된다.

```text
Module(body=[Assign(targets=[Name(id='scale', ctx=Store())],
value=Constant(value=3)), FunctionDef(name='adjust',
args=arguments(args=[arg(arg='x')]), body=[Assign(targets=[Name(id='y',
ctx=Store())], value=BinOp(left=Name(id='x', ctx=Load()), op=Add(),
right=Name(id='scale', ctx=Load()))), Return(value=IfExp(
test=Compare(left=Name(id='y', ctx=Load()), ops=[Gt()],
comparators=[Constant(value=0)]), body=Name(id='y', ctx=Load()),
orelse=Constant(value=0)))])])
```

AST는 대입 대상을 `Store`, 식의 이름을 `Load`로 구분한다. 그러나 `scale`을 지역
슬롯과 globals 중 어디서 읽을지는 코드 블록 전체를 보기 전에는 확정할 수 없다.

괄호와 공백은 대부분 사라진다. AST는 제어 흐름이나 바이트코드가 아니다. 앞 단계는
[PEG 파서는 토큰 위치와 대안 순서로 AST 하나를 확정한다](peg-parser.ko.md)에서
설명한다.

## 심볼 테이블은 코드 블록마다 이름 경로를 고정한다

`Python/symtable.c`는 AST를 코드 블록 단위로 순회한다. 예제 스크립트의 실제
출력은 다음과 같다.

```text
[top]
scale local, global, assigned
adjust local, global, assigned
[adjust]
x parameter, local, referenced
y local, assigned, referenced
scale global, referenced
```

모듈의 `local, global` 표시는 함수의 빠른 지역 슬롯이라는 뜻이 아니라 모듈
namespace에 속한다는 뜻이다.

`adjust` 블록에서는 `x`가 매개변수 local, `y`가 대입되는 local이다. 함수 어디에도
`scale` 대입이나 `global scale` 선언이 없으므로 `scale`은 implicit global로
분류된다. 이 결과가 이후 이름 연산을 가른다.

```text
x, y      → 함수의 locals-plus 슬롯 → LOAD_FAST 계열, STORE_FAST
scale     → 함수의 globals/builtins  → LOAD_GLOBAL
모듈 이름 → 모듈 namespace          → LOAD_NAME, STORE_NAME
```

심볼 테이블 자체는 CodeObject에 복사되지 않는다. 분류가 `co_varnames`·`co_names`
같은 메타데이터와 opcode 선택으로 남는다. closure가 있으면 같은 분석에서 cell과
free도 정해진다.

## 코드 생성은 AST를 명령 시퀀스로 낮춘다

`_PyAST_Compile()`은 `codegen.c`의 함수들을 호출해 내부 instruction sequence를
만든다. 이 시점의 핵심 계획은 다음처럼 읽을 수 있다.

```text
모듈 코드
  LOAD_CONST 3
  STORE_NAME scale
  LOAD_CONST <adjust CodeObject>
  MAKE_FUNCTION
  STORE_NAME adjust
  RETURN None

adjust 코드
  LOAD_FAST x
  LOAD_GLOBAL scale
  BINARY_OP +
  STORE_FAST y
  LOAD_FAST y
  LOAD_CONST 0
  COMPARE_OP >
  조건이 거짓이면 else 블록으로 이동
  LOAD_FAST y
  RETURN_VALUE
else 블록:
  LOAD_CONST 0
  RETURN_VALUE
```

이것은 공개 `dis`가 아니라 code generation 단계의 개념도다. 내부 시퀀스에는
논리 label과 pseudo instruction이 있을 수 있고, 적재 명령도 아직 최종의
`LOAD_SMALL_INT`, `LOAD_FAST_BORROW` 형태가 아닐 수 있다.

## CFG는 조건 분기와 스택 상태를 블록 관계로 드러낸다

`Python/flowgraph.c`는 instruction sequence에서 CFG를 만들고 최적화를 수행한다.
예제의 조건 표현식은 일렬 목록보다 다음 세 basic block으로 이해하기 쉽다.

```text
[entry]
  y = x + scale
  y > 0 검사
  거짓이면 [else]로 이동
       │참                 │거짓
       ↓                   ↓
[then]                 [else]
  y 적재                 0 적재
  반환                   반환
```

CFG에서는 도달 불가능한 블록, 불필요한 점프, 분기 합류점의 평가 스택 깊이를
검사한다. 3.14.6의
`optimize_and_assemble_code_unit()`은 CFG 최적화 뒤 최대 스택 깊이와
locals-plus 크기를 계산하고, 최적화된 instruction sequence로 다시 평탄화한다.

## assembler가 실제 opcode와 CodeObject 값을 확정한다

`Python/assemble.c`는 최종 instruction sequence의 명령 크기를 계산하고 jump
label을 실제 거리로 바꾼다. 이어 opcode bytes, 소스 위치 테이블, 예외 테이블,
상수·이름·지역 메타데이터를 `PyCodeObject` 생성 인수로 묶는다.

CPython 3.14.6의 실제 함수 바이트코드는 다음과 같다.

```text
  3           RESUME                   0

  4           LOAD_FAST_BORROW         0 (x)
              LOAD_GLOBAL              0 (scale)
              BINARY_OP                0 (+)
              STORE_FAST               1 (y)

  5           LOAD_FAST_BORROW         1 (y)
              LOAD_SMALL_INT           0
              COMPARE_OP             148 (bool(>))
              POP_JUMP_IF_FALSE        3 (to L1)
              NOT_TAKEN
              LOAD_FAST_BORROW         1 (y)
              RETURN_VALUE
      L1:     LOAD_SMALL_INT           0
              RETURN_VALUE
```

`LOAD_FAST_BORROW 0`과 `STORE_FAST 1`은 `x`, `y`의 지역 슬롯을 사용한다.
`LOAD_GLOBAL 0`은 `scale`을 globals와 builtins에서 조회한다.
`POP_JUMP_IF_FALSE`와 `L1`은 CFG의 거짓 경로가 실제 점프로 바뀐 결과다.

관찰 가능한 CodeObject 값도 단계별 결정을 반영한다.

```text
module co_names = ('scale', 'adjust')
module constants = (3, 'adjust', None)
adjust = ('scale',) ('x', 'y') (0,) 2
```

`module constants`는 중첩 CodeObject의 주소 대신 `co_name`을 출력한 값이다. 실제
`module_code.co_consts[1]`은 함수 본문의 CodeObject다. 함수 CodeObject는 전역
`scale`의 현재 값 `3`이 아니라 이름과 조회 방식만 담는다. `adjust` 줄은 차례로
`co_names`, `co_varnames`, `co_consts`, `co_stacksize`다.

## CodeObject는 실행 결과가 아니라 버전별 실행 설계다

- `compile()`이 성공해도 모듈 대입과 함수 호출은 아직 실행되지 않았다.
- AST의 `Name` 하나만 보고 local·global opcode를 정할 수 없다. 코드 블록 전체의
  심볼 분석이 필요하다.
- `dis`는 AST의 직렬화가 아니라 CFG 최적화, 명령 선택, label 해소를 거친 결과다.
- opcode, raw 인자, inline cache 배치는 버전 간 호환 규격이 아니다. 비교할 때는
  CPython 버전과 `dis` 옵션을 먼저 고정한다.

정확한 필드와 raw operand를 조회할 때는
[CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)를
사용한다. CodeObject가 함수 객체와 호출별 Frame에 연결되는 과정은 다음 설명에서
이어진다.

---

[설명 문서 목록](README.ko.md)

이전:

[설명 문서 목록](README.ko.md)

다음:

[실행 설계와 호출 상태](execution-model.ko.md)

관련 글:

- [PEG 파서의 순서 있는 선택](peg-parser.ko.md)
- [짧은 함수를 소스에서 반환값까지 추적하기](../tutorial/guide-source-to-execution.ko.md)
- [CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)
