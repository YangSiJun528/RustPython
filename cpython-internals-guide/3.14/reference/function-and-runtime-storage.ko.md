# Python 함수 정보의 저장 위치 참조

이 문서는 사용자 정의 Python 함수와 관련된 정보가 Function, CodeObject, Frame,
Cell, Method, Module 중 어디에 저장되는지 조회하는 참조 자료다. 개념과 실행 흐름은
[실행 설계와 호출 상태](../explanations/execution-model.ko.md)와
[이름 분류와 closure](../explanations/names-and-closures.ko.md)에서 설명한다.

공개 속성은 Python 3.14 데이터 모델을 기준으로 한다. CPython 내부의
`_PyInterpreterFrame`과 locals-plus 배치는 공개 API가 아니며 다른 버전이나 Python
구현에서 달라질 수 있다.

## 한눈에 보는 저장 위치

| 정보 종류 | 저장 위치 | 공유 범위 |
|---|---|---|
| 바이트코드·상수·이름표·슬롯 설계 | CodeObject | 같은 함수를 호출하는 모든 Frame이 공유 |
| globals·builtins·기본값·closure | Function | 같은 함수 객체의 모든 호출이 공유 |
| free variable의 현재 객체 | Cell | 같은 cell을 캡처한 함수들이 공유 |
| 인수·local·평가 스택·현재 명령 위치 | Frame | 호출마다 별도 |
| 바인딩된 인스턴스와 원래 함수 | Method | 해당 bound method 객체에 속함 |
| 모듈 전역 이름과 현재 객체 | Module namespace 딕셔너리 | 그 딕셔너리를 globals로 쓰는 함수들이 공유 |
| 정수·문자열·리스트 같은 실제 값 | 각각의 Python 객체 | 참조를 가진 모든 저장소가 공유 가능 |

```text
Method ── __func__ ─→ Function ── __code__ ─→ CodeObject
   │                     ├── __globals__  ──→ Module namespace
   │                     ├── __builtins__ ──→ Builtins namespace
   │                     ├── __defaults__ ──→ 기본값 객체
   │                     └── __closure__  ──→ Cell ──→ 현재 객체
   └── __self__ ─→ 바인딩된 인스턴스 또는 클래스

Function 호출 ─→ 새 Frame ─→ 인수·local·cell/free 슬롯·평가 스택
```

## Function 객체의 공개 특수 속성

아래 표는 Python 3.14의 사용자 정의 Function 객체가 제공하는 특수 속성 전체다.
`__builtins__`, `__globals__`, `__closure__` 자체는 읽기 전용이고 나머지는 타입 제한
안에서 변경할 수 있다.

| 정보 | 저장 위치 | 내용 |
|---|---|---|
| 컴파일된 함수 본문 | `function.__code__` | 함수 본문을 나타내는 CodeObject |
| 모듈 전역 namespace | `function.__globals__` | 함수가 정의된 모듈의 namespace 딕셔너리 |
| builtins namespace | `function.__builtins__` | built-in 이름을 찾는 딕셔너리 |
| free-variable cell | `function.__closure__` | `co_freevars`와 대응하는 cell 튜플, 없으면 `None` |
| 위치·키워드 매개변수 기본값 | `function.__defaults__` | 뒤쪽 위치 매개변수의 기본값 튜플, 없으면 `None` |
| 키워드 전용 매개변수 기본값 | `function.__kwdefaults__` | 매개변수 이름과 기본값을 연결한 딕셔너리 |
| 단순 이름 | `function.__name__` | 함수 이름 문자열 |
| 정규화된 이름 | `function.__qualname__` | 바깥 클래스·함수 경로를 포함한 이름 |
| 정의된 모듈 이름 | `function.__module__` | 모듈 이름 문자열 또는 `None` |
| 문서 문자열 | `function.__doc__` | docstring 또는 `None` |
| annotation | `function.__annotations__` | 매개변수 이름과 `return` annotation을 담은 딕셔너리 |
| 지연 annotation 계산기 | `function.__annotate__` | annotation을 계산하는 함수 또는 `None`; 3.14에서 추가 |
| 제네릭 타입 매개변수 | `function.__type_params__` | 타입 매개변수 튜플; 3.12에서 추가 |
| 임의 함수 속성 | `function.__dict__` | decorator나 사용자가 붙인 메타데이터 |

`__wrapped__`, `__signature__`처럼 도구와 decorator가 사용하는 속성은 Function의
고정 필드가 아니다. 필요하면 일반 사용자 속성으로 `function.__dict__`에 저장된다.

기본값 표현식은 `def` 문을 실행할 때 평가된다. 따라서 매개변수 이름과 호출 규칙은
CodeObject에 있지만 실제 기본값 객체는 Function의 `__defaults__` 또는
`__kwdefaults__`에 있다. Python 3.14의 annotation은 지연 평가될 수 있으므로
`__annotations__`를 조회할 때 `__annotate__`가 사용될 수 있다.

## CodeObject에 저장되는 실행 설계

CodeObject는 현재 호출의 값이나 namespace를 담지 않는다. 어떤 명령을 어떤 이름표와
슬롯을 사용해 실행할지만 기록한다.

| 정보 | 저장 위치 |
|---|---|
| 바이트코드 | `code.co_code` |
| 상수와 중첩 CodeObject | `code.co_consts` |
| global·attribute·import 등에 사용하는 이름 | `code.co_names` |
| 매개변수와 일반 local 이름 | `code.co_varnames` |
| 중첩 블록과 공유하는 현재 블록의 local 이름 | `code.co_cellvars` |
| 바깥 렉시컬 블록에서 전달받는 이름 | `code.co_freevars` |
| 위치·위치 전용·키워드 전용 매개변수 수 | `co_argcount`, `co_posonlyargcount`, `co_kwonlyargcount` |
| 일반 local 수 | `code.co_nlocals` |
| 필요한 평가 스택 최대 깊이 | `code.co_stacksize` |
| generator·coroutine·가변 인수 등의 성질 | `code.co_flags` |
| 코드 이름과 정규화된 이름 | `code.co_name`, `code.co_qualname` |
| 소스 파일과 시작 행 | `code.co_filename`, `code.co_firstlineno` |
| 명령과 소스 위치의 대응 | `code.co_linetable`, `co_positions()`, `co_lines()` |
| 예외 처리 범위와 handler 정보 | `code.co_exceptiontable` |

Function의 `__name__`과 `__qualname__`은 변경 가능한 함수 메타데이터다. CodeObject의
`co_name`과 `co_qualname`은 컴파일 당시 이름이므로 Function 쪽을 나중에 변경하면 두
값이 달라질 수 있다.

필드별 opcode 연결과 raw 인자 해석은
[CodeObject 필드와 바이트코드 인자](code-object-and-bytecode.ko.md)에서 조회한다.

## Frame에 저장되는 호출별 상태

Function과 CodeObject는 반복 호출이 공유하지만 Frame은 호출마다 새로 생긴다.
CPython의 최적화된 함수에서는 local·cell·free 슬롯과 평가 스택이 내부 locals-plus
영역에 놓인다. Python에서 `frame.f_locals`를 조회하면 이 local 상태를 매핑 또는
write-through proxy로 볼 수 있다.

| 이번 호출의 정보 | 공개 조회 위치 | CPython 내부 저장 위치 |
|---|---|---|
| 전달받은 인수와 일반 local | `frame.f_locals` | locals-plus의 local 슬롯 |
| 현재 블록이 제공하는 cell | `frame.f_locals`를 통해 값 관찰 가능 | locals-plus의 cell 슬롯 |
| closure에서 전달받은 free cell | `frame.f_locals`를 통해 값 관찰 가능 | locals-plus의 free 슬롯 |
| 계산 중간값 | 직접 공개하지 않음 | locals-plus 뒤의 평가 스택 |
| 실행 중인 CodeObject | `frame.f_code` | `f_executable` |
| global namespace | `frame.f_globals` | `f_globals` |
| builtins namespace | `frame.f_builtins` | `f_builtins` |
| 현재 명령 위치 | `frame.f_lasti` | `instr_ptr` |
| 호출자 Frame | `frame.f_back` | 활성 Frame의 `previous` 관계 |
| trace 함수와 단위 | `f_trace`, `f_trace_lines`, `f_trace_opcodes` | Frame 관찰 상태 |
| 소유 generator·coroutine | `frame.f_generator` | Frame owner와 포함 관계 |

함수 객체는 자신을 호출해 만든 Frame 목록을 소유하지 않는다. 실행 중인 호출 체인,
generator·coroutine 객체, traceback, debugger 등이 필요한 Frame을 참조한다.
`frame.f_back`과 내부 `previous`는 호출·복귀 관계이며 렉시컬 이름 조회 경로가 아니다.

내부 필드와 소유권은 [Frame과 런타임 객체 필드](runtime-objects.ko.md)에서 조회한다.

## Cell과 closure의 대응

| 정보 | 저장 위치 |
|---|---|
| 바깥 함수가 중첩 함수에 제공하는 이름 | 바깥 CodeObject의 `co_cellvars` |
| 안쪽 함수가 바깥에서 받아야 하는 이름 | 안쪽 CodeObject의 `co_freevars` |
| 안쪽 Function이 실제로 받은 cell | `function.__closure__` |
| cell이 현재 가리키는 객체 | `cell.cell_contents` |
| 호출 중 Frame이 사용할 cell 참조 | locals-plus의 cell·free 슬롯 |

`co_freevars`의 이름과 `__closure__`의 cell은 같은 인덱스로 대응한다.

```text
function.__code__.co_freevars[i]  ↔  function.__closure__[i]
이름                                  그 이름의 cell
```

바깥 함수가 cell을 제공한다고 해서 그 바깥 Function의 `__closure__`에 cell이 들어가는
것은 아니다. `__closure__`는 그 함수가 바깥에서 전달받은 free cell만 담는다. 바깥
함수가 자신의 local로 만든 cell은 실행 중 Frame에 생기고, 생성된 안쪽 Function의
`__closure__`로 전달된다.

여러 Function의 `__closure__`가 같은 cell을 참조할 수 있다. `nonlocal` 대입은 새
cell을 만드는 대신 기존 cell의 `cell_contents`를 바꾸므로 모든 Function이 새 객체를
보게 된다.

## 바인딩된 Method 객체

클래스에 저장된 사용자 정의 Function을 인스턴스를 통해 조회하면 Function과
인스턴스를 묶은 bound Method 객체가 만들어질 수 있다.

| 정보 | 저장 위치 |
|---|---|
| 원래 Function | `method.__func__` |
| 바인딩된 인스턴스 | `method.__self__` |
| `classmethod`에 바인딩된 클래스 | `method.__self__` |
| 이름·문서·모듈과 임의 함수 속성 | 기본적으로 `method.__func__`에서 조회 |

Method 호출은 개념적으로 `method.__func__(method.__self__, *args, **kwargs)`와 같다.
`staticmethod`는 인스턴스나 클래스를 결합하지 않고 원래 callable을 반환하므로 이런
bound Method의 `__self__`를 만들지 않는다. built-in function과 built-in method는
사용자 정의 Function·Method와 다른 객체 종류이며 같은 속성 집합을 보장하지 않는다.

## 자주 혼동하는 위치

| 오해 | 실제 위치 |
|---|---|
| 기본값이 CodeObject에 있다 | 실제 기본값 객체는 Function의 `__defaults__`·`__kwdefaults__`에 있다. |
| global 값이 CodeObject에 있다 | CodeObject에는 이름만 있고 값은 Function의 `__globals__`가 가리키는 딕셔너리에 있다. |
| `co_freevars`에 closure 값이 있다 | `co_freevars`에는 이름만 있고 cell은 Function의 `__closure__`에 있다. |
| Function에 호출별 local이 쌓인다 | 인수와 local은 호출마다 생성되는 Frame에 있다. |
| bound method의 `self`가 Function에 붙는다 | `self`는 별도 Method 객체의 `__self__`에 있다. |
| closure가 바깥 Frame 전체를 보관한다 | 필요한 바인딩의 Cell을 참조하며 Frame 전체를 이름 조회에 사용하지 않는다. |

## 공개 문서와 관련 글

- [Python 3.14 데이터 모델: 사용자 정의 함수](https://docs.python.org/3.14/reference/datamodel.html#user-defined-functions)
- [Python 3.14 데이터 모델: 인스턴스 메서드](https://docs.python.org/3.14/reference/datamodel.html#instance-methods)
- [Python 3.14 데이터 모델: CodeObject](https://docs.python.org/3.14/reference/datamodel.html#code-objects)
- [Python 3.14 데이터 모델: Frame](https://docs.python.org/3.14/reference/datamodel.html#frame-objects)
- [Python 3.14 `types.CellType`](https://docs.python.org/3.14/library/types.html#types.CellType)
- [실행 설계와 호출 상태](../explanations/execution-model.ko.md)
- [이름 분류와 closure](../explanations/names-and-closures.ko.md)

[가이드 홈](../README.ko.md)
