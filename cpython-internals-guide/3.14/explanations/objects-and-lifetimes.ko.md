# 바인딩, 변경, 객체 수명은 서로 다른 문제다

Python의 이름, Frame 슬롯, 컨테이너 항목에는 값의 독립된 복사본이 아니라 객체를
가리키는 참조가 놓인다. 이름을 다시 대입하는 재바인딩은 한 화살표를 다른 객체로
돌리고, 리스트에 항목을 추가하는 변경은 기존 화살표가 가리키는 객체의 내용을
바꾼다. 객체 수명은 또 별개의 문제다. 몇 개의 이름이 보이는지가 아니라 누가 강한
참조를 소유하는지에 따라 결정된다.

이 글은 CPython 3.14.6의 객체 모델을 설명한다. 일반적인 GIL 빌드에서는 참조 횟수가
0이 되는 경로가 즉시 deallocation으로 이어지는 경우가 많지만, 자유 스레딩 빌드의
biased·deferred reference counting은 실제 정리를 늦출 수 있다. `sys.getrefcount()`의
숫자를 곧바로 소유자 수나 소멸 시점으로 해석해서는 안 된다.

![이름 재바인딩과 객체 변경은 서로 다른 화살표를 바꾼다](../assets/04-pyobject-bindings.png)

## 최소 예제는 두 종류의 변화를 분리한다

```python
a = []
b = a
a.append(1)
a = []
```

각 문장이 끝날 때의 참조 상태를 따라가 보자.

```text
1. a = []
   a ─→ list A []

2. b = a
   a ─┐
      ├→ list A []
   b ─┘

3. a.append(1)
   a ─┐
      ├→ list A [1]
   b ─┘

4. a = []
   a ─→ list B []
   b ─→ list A [1]
```

2번은 리스트를 복사하지 않고 `b`라는 바인딩을 같은 객체로 향하게 한다. 3번은
어느 이름의 화살표도 바꾸지 않고 list A의 내부 항목을 바꾼다. 4번은 list A를
비우거나 list B로 변환하지 않고 `a`만 새 객체에 묶는다. 그래서 마지막에는
`a == []`, `b == [1]`, `a is not b`가 모두 참이다.

“변수에 리스트가 들어 있다”는 말은 Python 수준의 편리한 표현이지만, CPython
구조를 설명할 때는 “이름 또는 슬롯이 리스트 객체 참조를 보관한다”가 더 정확하다.
대입 뒤 두 이름이 같은 객체를 가리키는지와 두 객체의 값이 같은지는 각각 `is`와
`==`라는 서로 다른 질문이다.

## 함수 호출도 객체 참조를 새 슬롯에 연결한다

```python
def add_tag(items):
    items.append("new")

records = []
add_tag(records)
```

호출자가 가진 `records`와 피호출자 Frame의 매개변수 슬롯 `items`는 호출 동안 같은
리스트 객체를 가리킨다.

```text
호출 전    module records ─→ list A []
호출 직후  module records ─┐
                           ├→ list A []
           Frame items ────┘
append 후                  └→ list A ["new"]
반환 후    items 슬롯 정리, module records ─→ list A ["new"]
```

함수에 “참조로 전달”과 “값으로 전달” 중 하나의 다른 문법이 있는 것이 아니다.
Python 호출 규약은 인수 객체에 대한 참조를 새 Frame의 매개변수 슬롯에 결합한다.
함수 안에서 `items = []`로 재바인딩하면 그 Frame 슬롯만 바뀌므로 호출자의
`records`는 그대로다. `items.append(...)`는 공유 객체를 바꾸므로 호출자에게도
보인다.

기본 인수도 같은 원리다. `def f(bucket=[]): ...`에서 리스트 객체는 함수 정의가
실행될 때 한 번 만들어져 함수 객체의 defaults에 강하게 보관된다. 인수를 생략한
호출마다 그 객체 참조가 새 Frame 슬롯에 놓이므로 변경 내용이 다음 호출에 남는다.
이 현상은 Frame 재사용이나 “static local” 때문이 아니라 함수 객체가 같은 mutable
기본값을 계속 소유하기 때문이다.

## 슬롯과 컨테이너는 강한 참조를 소유할 수 있다

CPython의 구체 객체는 공통 `PyObject` 머리와 타입별 데이터를 가진다.

```text
구체 객체
┌────────────────────────┐
│ 타입·참조 상태         │  PyObject 공통 부분
├────────────────────────┤
│ 타입별 데이터          │  숫자, 문자, 항목, 코드 등
└────────────────────────┘
```

Frame의 일반 local 슬롯, 리스트 항목, 딕셔너리 key와 value, 함수의 `__code__`,
defaults, `__closure__`는 각각 객체 수명을 책임지는 강한 참조를 가질 수 있다.
한 소유자가 참조를 놓아도 다른 강한 참조가 남아 있으면 객체는 살아 있다. 앞 예제의
4번에서 `a`가 list A를 놓았어도 `b`가 계속 소유하므로 list A는 사라지지 않는다.

반대로 C 포인터가 객체 주소를 담았다는 이유만으로 언제나 소유권이 생기는 것은 아니다.
C API는 다음과 같은 계약으로 수명 책임을 구분한다.

- new reference는 호출자가 새 강한 참조를 소유한다.
- borrowed reference는 다른 소유자가 객체를 살려 두는 동안만 빌려 쓴다.
- steals a reference는 호출 대상이 호출자의 기존 소유권을 넘겨받는다.

borrowed reference에 `DECREF`를 하거나, 원래 소유자가 사라진 뒤 빌린 포인터를 쓰면
use-after-free 같은 메모리 오류가 된다. 반대로 새 참조를 끝까지 놓지 않으면 누수가
생긴다. Python 코드의 자동 수명 관리 아래에는 이런 명시적 C 계약이 있다.

CPython 3.14의 평가 스택과 일부 Frame 필드는 `_PyStackRef`를 쓴다. 이는 strong
참조뿐 아니라 안전한 borrowed 형태와 특수 태그를 표현할 수 있다. 예를 들어
`LOAD_FAST_BORROW`는 Frame 안의 supporting reference가 평가 스택의 borrowed
reference보다 오래 유효하다고 컴파일러가 증명한 경로에서 쓸 수 있다. local 슬롯이
언제나 독립된 strong owner라는 뜻은 아니다. 모든 opcode 이동이 `INCREF`와 `DECREF`
한 쌍을 만든다고 가정하면 실제 구현을 잘못 읽게 된다.

## 마지막 참조와 실제 정리 시점은 빌드에 따라 다르다

전통적인 GIL 빌드의 보통 객체는 강한 참조가 해제되어 참조 횟수가 0이 되는 순간
타입의 deallocation 함수로 들어간다. 이 경로는 결정론적으로 보이지만 다음 예외와
주의점이 있다.

```text
마지막 소유 참조 해제
        ↓
참조 횟수 0
        ↓
tp_dealloc과 타입별 자원 정리
```

불멸 객체는 보통의 0 도달 규칙으로 정리되지 않는다. 임시 참조는
`sys.getrefcount(obj)`를 호출하는 순간에도 추가되며, interpreter·캐시·traceback처럼
눈에 잘 띄지 않는 소유자도 있다. `__del__`이나 weakref callback은 정리 경로에
Python 코드를 다시 끌어들일 수 있고 객체 부활 가능성도 고려해야 한다. 참조 횟수의
구체 숫자를 프로그램 의미로 사용하면 안 된다.

자유 스레딩 빌드는 객체별 local/shared 참조 상태, biased reference counting,
deferred reference counting을 사용한다. 어떤 감소는 즉시 전역적으로 합쳐지지 않을 수
있으므로 마지막 Python 수준 소유자가 사라진 시점과 실제 deallocation 시점이 같다고
보장할 수 없다. 두 빌드 모두 “강한 참조가 수명을 책임진다”는 의미는 공유하지만,
그 책임을 표현하고 합산하는 기계적 과정은 다르다.

## 참조 횟수만으로 끝나지 않는 순환은 GC가 찾는다

```python
a = []
b = [a]
a.append(b)
del a, b
```

삭제 전 참조 그래프에는 다음 순환이 있다.

```text
list A ─→ list B
   ↑         │
   └─────────┘
```

이름 `a`, `b`를 지워 외부 진입점이 사라져도 두 리스트의 내부 강한 참조는 서로를
붙잡는다. 각 참조 횟수가 자연스럽게 0이 되지 않으므로 단순 참조 감소만으로는
정리할 수 없다. cyclic GC는 GC 추적 대상 컨테이너의 내부 참조를 분석해 외부에서
도달할 수 없는 순환 집합을 찾고 정리한다.

GC가 “참조 횟수 0인 모든 객체를 나중에 모으는 장치”라는 설명은 틀리다. 일반 GIL
경로에서 0이 된 비순환 객체는 보통 즉시 deallocation되고, cyclic GC의 핵심 대상은
내부 참조 때문에 0이 되지 않는 추적 객체 집합이다. 원자적인 정수나 문자열처럼
다른 객체를 순회할 필요가 없는 타입과 리스트·딕셔너리·Frame처럼 참조 그래프를
만드는 타입의 GC 참여 방식도 다르다.

실제 Python 실행에서는 예외가 traceback을, traceback이 Frame을, Frame local이 다시
예외를 가리키는 순환이 생길 수 있다. 실행이 끝난 Frame에 `frame.clear()`를 호출하면
지역 참조를 놓아 순환을 끊는 데 도움이 된다. 그러나 지역 객체 하나가 살아 있다는
사실만으로 그 객체가 원래 Frame을 역으로 소유한다고 추정해서는 안 된다. 참조 화살표의
방향을 실제로 확인해야 한다.

## closure는 값 복사보다 공유 바인딩에 가깝다

`PyCellObject`는 현재 값 객체를 가리키는 공유 가능한 저장소다. outer Frame의 cell
슬롯, 반환된 함수의 `__closure__`, 실행 중인 inner Frame의 free 슬롯은 같은 cell을
가리킬 수 있다. outer Frame이 끝나도 함수 객체가 cell을 소유하면 cell과 그 내용은
계속 살아 있다.

`nonlocal x; x = other`는 cell의 화살표를 `other` 객체로 바꾸는 재바인딩이다.
`x.append(other)`는 cell 화살표를 유지한 채 대상 리스트를 변경한다. closure라고 해서
바인딩과 변경의 기본 구분이 달라지지는 않는다. Frame 전체를 보존한다고 생각하기보다
필요한 바인딩 저장소만 별도 객체로 공유한다고 이해하는 편이 정확하다.

문자열처럼 불변 객체의 대표 인스턴스를 공유하는 최적화는 일반 binding과 별개의
주제다. 문자열 인터닝은 `is`의 의미를 값 비교로 바꾸지 않으며, 객체 수명 정책도
빌드에 따라 달라진다.

---

[설명 문서 목록](README.ko.md)

이전:

[평가 루프와 세 가지 스택](evaluation-loop.ko.md)

다음:

[주 경로를 마치고 설명 문서 목록으로 돌아가기](README.ko.md)

심화 글:

- [문자열 인터닝](string-interning.ko.md)
- [제너레이터·코루틴과 Frame](generators-and-coroutines.ko.md)
- [이름 분류와 closure](names-and-closures.ko.md)
