# 평가 루프는 Frame의 상태를 바꾸며 바이트코드를 실행한다

CodeObject만으로는 프로그램이 실행되지 않는다. CodeObject에는 바이트코드와
상수·이름 같은 정적 정보가 있고, Frame에는 이번 호출의 인수, 지역 변수,
평가 스택, 현재 명령 위치가 있다. CPython의 평가 루프는 현재 Frame에서 명령을
가져와 해독하고 실행하면서 이 상태를 갱신한다.

정상 실행은 `fetch → decode → execute`의 반복이다. 평가 루프가 다음 code unit에서
`opcode`와 `oparg`를 읽고, opcode가 요구하는 값을 Frame에서 꺼내 연산한 뒤 결과와
다음 명령 위치를 기록한다. 함수 호출도 별도의 실행 엔진을 시작하는 대신 현재
Frame을 피호출자의 Frame으로 바꾸는 방식으로 이 반복 안에서 처리한다.

## 한 명령은 현재 Frame에 적용된다

다음 함수가 호출되었다고 하자.

```python
def add(a, b):
    return a + b
```

핵심 바이트코드는 다음 순서로 실행된다.

```text
LOAD_FAST a
LOAD_FAST b
BINARY_OP +
RETURN_VALUE
```

`LOAD_FAST`는 현재 Frame의 지역 변수 슬롯에서 객체 참조를 읽어 평가 스택에
올린다. `BINARY_OP`는 두 참조를 꺼내 연산하고 결과 객체의 참조를 다시 올린다.
`RETURN_VALUE`는 그 결과를 꺼내 호출자에게 넘긴다. opcode 자체에는 실제
`a`, `b` 값이 없다. 두 값은 호출할 때 생긴 Frame에 있다.

CodeObject의 `co_stacksize`는 이 평가 스택에 필요한 최대 깊이다. 컴파일러가 이를
미리 계산하므로 Frame을 만들 때 필요한 슬롯 수를 정할 수 있다.

## 세 가지 스택은 맡은 일이 다르다

| 구분 | 무엇을 보관하는가 | 언제 변하는가 |
|---|---|---|
| 평가 스택 | 한 Frame 안의 피연산자와 중간 결과 | 대부분의 opcode를 실행할 때 |
| Frame stack | 호출별 `_PyInterpreterFrame`과 호출 관계 | Python 함수를 호출하거나 반환할 때 |
| C stack | CPython을 구현한 C 함수의 호출 상태 | C 함수가 다른 C 함수를 호출할 때 |

평가 스택은 함수 호출 관계를 나타내지 않는다. 반대로 Frame stack은 `a + b`의
두 피연산자를 보관하지 않는다. CPython 3.11 이후의 일반적인 Python-to-Python
호출은 같은 평가 루프에서 현재 Frame을 바꾸므로, Python 호출 하나마다
`_PyEval_EvalFrameDefault()`의 C 호출이 하나씩 중첩되지도 않는다.

Frame 연결은 이름 조회 경로도 아니다. `LOAD_FAST`는 현재 Frame의 슬롯을 읽고,
`LOAD_GLOBAL`은 globals와 builtins를 조회한다. 호출자의 지역 변수를 찾으려고
Frame stack을 거슬러 올라가지 않는다. 자세한 규칙은
[이름 분류가 저장소와 opcode를 정한다](names-and-closures.ko.md)에서 설명한다.

## CALL은 현재 Frame을 바꾼다

정상적인 Python 함수 호출은 이 경로를 지난다.

```text
호출자의 평가 스택에 callable과 인수를 준비한다
    ↓
CALL이 함수의 CodeObject·globals·closure를 확인한다
    ↓
인수를 지역 슬롯에 연결한 새 Frame을 만든다
    ↓
같은 평가 루프가 피호출자 Frame의 첫 명령부터 실행한다
    ↓
RETURN_VALUE가 Frame을 끝내고 결과를 호출자 평가 스택에 올린다
```

같은 함수를 재귀 호출하면 CodeObject는 하나지만 Frame은 호출마다 하나씩 생긴다.
각 Frame이 서로 다른 인수, 지역 변수, 평가 스택과 복귀 위치를 보관하기 때문이다.
CPython 3.14은 내부 Frame의 소유권과 복귀 위치로 평가 루프의 경계를 처리한다.
이 실행 모델에 오래된 `is_entry` 필드는 필요하지 않다.

호출 도중 opcode가 실패하면 정상 반환 대신 예외 경로로 들어간다. 현재 Frame의
처리기를 찾고, 없으면 호출자 Frame으로 전파하는 과정은
[예외 테이블과 Frame 되감기가 전파를 나눠 맡는다](exceptions.ko.md)에서 이어진다.
제너레이터는 Frame을 없애지 않고 객체 안에 보관한다는 점에서 일반 반환과 다르다.
그 과정은 [제너레이터와 코루틴은 중단된 Frame을 보관한다](generators-and-coroutines.ko.md)에서
다룬다.

## 더 깊이 볼 지점

`_Py_CODEUNIT`, `EXTENDED_ARG`, inline cache의 정확한 배치와 Frame 필드는 각각
[CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md),
[Frame·위치 테이블·문자열 인터닝 내부 구조](../reference/runtime-objects.ko.md)에서 찾을 수
있다. 평가 루프의 생성 DSL과 C 구현까지 확인하려면 기존
[프로그램 실행 상세 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md)를
참고한다.

[가이드 홈](../README.ko.md) · 이전: [이름과 저장소](names-and-closures.ko.md) · 다음: [바인딩과 객체 수명](objects-and-lifetimes.ko.md) · 갈래: [예외](exceptions.ko.md), [제너레이터와 코루틴](generators-and-coroutines.ko.md), [특수화와 JIT](specialization-and-jit.ko.md)
