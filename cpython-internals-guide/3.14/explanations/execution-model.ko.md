# 실행 설계와 호출 상태는 서로 다른 객체에 놓인다

CPython은 함수 실행에 필요한 정보를 CodeObject, 함수 객체, Frame으로 나눈다.
CodeObject는 여러 실행이 공유할 설계이고, 함수 객체는 그 설계를 globals·기본
인수·closure 같은 환경과 결합하며, Frame은 호출별로 분리된 인수·지역 변수·평가
스택·현재 명령 위치를 보관한다. 이 셋을 구분하면 “함수 하나를 두 번
호출했는데 지역 변수는 왜 섞이지 않는가”와 “함수를 반환한 뒤에도 closure는 왜
살아 있는가”를 같은 참조 그래프로 설명할 수 있다.

이 글의 관찰값과 opcode 이름은 CPython 3.14.6에서 `adaptive=False`,
`show_caches=False`로 확인했다. CodeObject와 `_PyInterpreterFrame`, adaptive
bytecode는 버전 간 호환 형식이 아니다.

## 짧은 함수 하나에도 세 종류의 상태가 필요하다

```python
def scale(x):
    y = x * 2
    return y
```

컴파일된 함수 본문에서 확인되는 값은 다음과 같다.

```text
scale.__code__.co_varnames  = ('x', 'y')
scale.__code__.co_consts    = (2,)
scale.__code__.co_stacksize = 2
```

실제 바이트코드는 다음과 같다.

```text
RESUME                   0
LOAD_FAST_BORROW         0 (x)
LOAD_SMALL_INT           2
BINARY_OP                5 (*)
STORE_FAST               1 (y)
LOAD_FAST_BORROW         1 (y)
RETURN_VALUE
```

여기에는 `x == 3`이나 `y == 6`이라는 호출별 값이 없다. `LOAD_FAST_BORROW 0`은
“현재 Frame의 locals-plus 슬롯 0을 읽는다”는 설계만 기록한다. 반대로 Frame은
슬롯 0과 1의 현재 객체를 보관하지만, 곱셈의 의미나 다음에 `STORE_FAST`를 실행해야
한다는 계획을 자체적으로 만들지 않는다. 평가 루프가 CodeObject의 명령과 Frame의
현재 값을 함께 읽어야 비로소 실행이 된다.

## 컴파일은 CodeObject를 만들고 `def` 실행은 함수 객체를 만든다

소스 전체를 `compile()`했다고 `scale` 함수 객체가 이미 생기는 것은 아니다.
컴파일 결과인 모듈 CodeObject의 `co_consts` 안에는 함수 본문을 위한 중첩
CodeObject가 들어 있다. 모듈 코드를 실행해 `def scale`에 도달하면
`MAKE_FUNCTION`이 그 CodeObject와 현재 모듈 globals를 결합해
`PyFunctionObject`를 만든다.

```text
PyFunctionObject scale
├─ func_code / __code__ ─────→ scale CodeObject
├─ func_globals / __globals__ → 모듈 namespace
├─ func_builtins ─────────────→ builtins namespace
├─ defaults·kwdefaults
└─ func_closure / __closure__ → 이 예에서는 NULL
```

함수 객체는 호출 전에 준비된 환경이다. `scale(3)`의 인수 `3`, 계산 중간값 `6`,
현재 명령 위치는 아직 없다. 기본 인수가 있다면 그 객체는 함수 객체에 붙지만,
기본 인수를 실제 매개변수 슬롯에 놓는 일은 호출 시점에 한다. closure가 있다면
함수 객체가 값의 복사본이 아니라 cell 객체들의 튜플을 보관한다.

흔한 오해는 CodeObject가 “함수” 그 자체라는 생각이다. 같은 CodeObject를 서로
다른 globals와 결합한 함수 객체를 만들 수 있고, 한 함수 객체를 여러 번 호출해
서로 다른 Frame을 만들 수도 있다. 세 객체는 위에서 아래로 한 번씩 소유되는 트리가
아니라 서로를 참조하는 그래프다.

## Python 함수 호출은 인수를 새 Frame 슬롯에 배치한다

`scale(3)`의 일반적인 Python 함수 호출 경로를 단계별로 보면 다음과 같다.

1. 호출자 평가 스택에는 호출 대상과 인수 객체 참조가 준비된다.
2. 호출 경로는 함수 객체에서 CodeObject와 globals를 얻고, C `PyCodeObject`의 내부
   필드 `co_framesize`에 맞는 `_PyInterpreterFrame` 공간을 준비한다.
   `co_framesize`는 Python에서 조회하는 공개 CodeObject 속성이 아니다.
3. `_PyFrame_Initialize()`가 `_PyInterpreterFrame`의 내부 필드 `f_funcobj`,
   `f_executable`, globals·builtins, 이전 Frame 연결과 초기 명령 위치를 설정한다.
4. `initialize_locals()`가 위치·키워드 인수를 매개변수에 맞춰 locals-plus 슬롯에
   옮긴다. 이 예에서는 슬롯 0이 정수 객체 `3`을 가리키고 슬롯 1은 미설정이다.
5. 평가 루프가 새 Frame을 현재 Frame으로 삼아 첫 명령부터 실행한다.

명령마다 상태가 어떻게 바뀌는지 좁혀 보면 다음과 같다.

```text
호출 직후       localsplus: [x → 3, y → 미설정]   평가 스택: []
LOAD_FAST       localsplus: [x → 3, y → 미설정]   평가 스택: [3]
LOAD_SMALL_INT  localsplus: [x → 3, y → 미설정]   평가 스택: [3, 2]
BINARY_OP       localsplus: [x → 3, y → 미설정]   평가 스택: [6]
STORE_FAST      localsplus: [x → 3, y → 6]        평가 스택: []
LOAD_FAST       localsplus: [x → 3, y → 6]        평가 스택: [6]
RETURN_VALUE    현재 Frame 정리, 호출자 평가 스택에 결과 6 전달
```

여기서 슬롯과 평가 스택에는 Python 객체 전체가 복사되는 것이 아니라 내부 객체
참조가 놓인다. CPython 3.14의 `_PyStackRef`는 strong·borrowed 성질을 태그와 함께
나타낼 수 있으므로 모든 슬롯 이동을 단순한 `PyObject *` 복사나 매번의
`INCREF`로 이해해서도 안 된다.

`CALL`이 항상 Python Frame을 만든다는 뜻은 아니다. built-in 함수, 확장 타입,
일반 `__call__` 객체를 부르는 경로는 C 구현이나 다른 호출 규약으로 갈 수 있다.
위 과정은 호출 대상이 보통의 `PyFunctionObject`이고 Python-to-Python 호출 최적화가
적용되는 경우를 설명한다. PEP 523의 사용자 eval-frame 함수나 tracing·instrumentation
상태도 세부 경로를 바꿀 수 있다.

## CodeObject는 공유되지만 Frame은 호출마다 분리된다

`scale(3)`이 끝난 뒤 `scale(20)`을 호출하면 함수 객체와 CodeObject는 재사용하지만
새 Frame의 슬롯 0에는 `20`이 들어간다. 첫 Frame의 `y == 6`이 둘째 호출로 넘어가지
않는다. 두 호출은 시간 순서부터 나눠 보는 편이 정확하다.

```text
t1: scale(3), RETURN_VALUE 직전

Frame A: x=3, y=6
├─ f_funcobj ─────→ scale 함수 객체
└─ f_executable ──→ scale CodeObject

scale 함수 객체 ── __code__ ─→ 같은 scale CodeObject

t2: scale(3) 반환

Frame A의 활성 실행은 끝난다.
단, traceback·debugger 등이 보관하면 Python Frame 객체와 필요한 상태는 남을 수 있다.

t3: scale(20), RETURN_VALUE 직전

Frame B: x=20, y=40
├─ f_funcobj ─────→ 같은 scale 함수 객체
└─ f_executable ──→ 같은 scale CodeObject

scale 함수 객체 ── __code__ ─→ 같은 scale CodeObject
```

재귀 호출은 별개의 예다. 다음 함수가 `countdown(2)`를 실행 중이라면 세 Frame이
동시에 활성 상태일 수 있다.

```python
def countdown(n):
    if n == 0:
        return 0
    return countdown(n - 1)
```

가장 안쪽 호출까지 내려간 순간의 관계는 다음과 같다.

```text
Frame C: n=0 ── previous ─→ Frame B: n=1 ── previous ─→ Frame A: n=2

Frame A, B, C 각각
├─ f_funcobj ─────→ 같은 countdown 함수 객체
└─ f_executable ──→ 같은 countdown CodeObject

countdown 함수 객체 ── __code__ ─→ 같은 countdown CodeObject

각 Frame만 따로 보관: 인수, locals-plus, 평가 스택, instr_ptr, 복귀 정보
```

호출이 Frame을 만들며, 함수 객체가 자신을 호출해 만든 Frame 목록을 소유하는 것은
아니다. 활성 Frame의 `previous`는 호출 관계를 이어 반환과 예외 전파에 사용한다. 그러나
일반 이름 조회가 이 링크를 따라 호출자 지역 변수를 검색하지는 않는다. local은 현재
Frame 슬롯에서, global은 함수가 가진 globals와 builtins에서, free variable은 함수
객체의 closure에서 전달받은 cell을 통해 찾는다.

`_PyInterpreterFrame`은 `PyObject`가 아닌 실행용 내부 레코드다. `sys._getframe()`,
traceback, debugger처럼 Python 수준의 관찰이 필요할 때 `PyFrameObject`가 지연
생성되어 이 레코드를 노출한다. 실행이 끝난 뒤에도 외부에서 Frame 객체를 보관하면
필요한 실행 상태와 지역 객체의 수명이 길어질 수 있다.

## “불변 CodeObject”와 실행 중 최적화는 층이 다르다

Python 수준에서 `co_consts`, 이름 표, 공개 `co_code`가 표현하는 프로그램 의미는
불변 설계로 다룬다. 그러나 CPython 3.14의 C `PyCodeObject` 내부 실행 버퍼
`co_code_adaptive`와 inline cache, executor 연결은 관찰한 타입과 namespace 상태에
따라 바뀔 수 있다. `co_code_adaptive`는 Python의 공개 속성이 아니다. 같은
CodeObject가 특수화되어도 `LOAD_FAST 0`이 갑자기 다른 지역 이름을 뜻하거나 곱셈이
다른 Python 의미를 갖는 것은 아니다. guard가 깨지면 더 일반적인 경로로 돌아간다.

GIL 빌드와 자유 스레딩 빌드도 이 관계의 의미는 공유한다. 다만 자유 스레딩 빌드는
thread-local bytecode와 `tlbc_index`, 원자적 참조 상태 같은 추가 구현이 필요하다.
Frame 배치와 `_PyStackRef` 소유권, 특수화 데이터의 공유 방식은 빌드에 따라 다르므로
3.14 내부 필드를 공개 ABI처럼 사용하면 안 된다.

정리하면 CodeObject는 “무엇을 어떤 슬롯과 표를 사용해 실행할지”, 함수 객체는
“어느 환경에서 실행할지”, Frame은 “이번 호출에서 지금 어떤 객체와 위치에 있는지”에
답한다. 어느 하나만으로는 Python 함수 실행을 완성할 수 없다.

---

[설명 문서 목록](README.ko.md)

이전:

[소스에서 CodeObject까지](source-to-code-object.ko.md)

다음:

[이름 분류와 closure](names-and-closures.ko.md)

관련 글:

- [평가 루프와 세 가지 스택](evaluation-loop.ko.md)
- [함수 관련 정보의 저장 위치](../reference/function-and-runtime-storage.ko.md)
- [CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)
