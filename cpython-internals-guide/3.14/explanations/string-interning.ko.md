# 문자열 인터닝은 같은 불변 객체를 공유하게 한다

문자열 인터닝은 내용이 같은 여러 `PyUnicodeObject` 대신 대표 객체 하나를 공유하는
최적화다. 식별자와 속성 이름처럼 같은 문자열을 반복해서 다루는 CPython 내부에서
메모리를 아끼고, 이미 같은 대표 객체임을 확인한 비교를 빠르게 끝낼 수 있다. 그러나
인터닝은 문자열 값 비교 규칙을 바꾸지 않고, 모든 같은 문자열을 자동으로 하나로 만들지도
않는다.

이 글은 CPython 3.14.6의 정적 문자열과 동적 인터닝을 설명한다. interning state,
런타임 전역 캐시, interpreter별 딕셔너리와 내부 API는 공개 호환 규격이 아니며 GIL
빌드와 자유 스레딩 빌드에서 수명 정책이 다르다.

## 동적으로 만든 같은 문자열은 먼저 다른 객체일 수 있다

컴파일러가 문자열 리터럴을 미리 합치거나 식별자를 인터닝하는 효과를 피하려고 실행 중
문자열을 만들어 보자.

```python
import sys

a = "".join(["na", "me"])
b = "".join(["n", "ame"])

print(a == b)  # True
print(a is b)  # False: CPython 3.14.6에서 이 예제의 관찰값

a = sys.intern(a)
b = sys.intern(b)

print(a is b)  # True
```

처음 두 문자열은 내용과 hash가 같아도 별도 할당에서 나온 객체다. `sys.intern(a)`는
대표 객체를 찾아 반환하고, 호출자는 반드시 그 반환값을 다시 사용해야 한다.
`sys.intern(s)`가 인자로 받은 모든 기존 참조를 마법처럼 바꾸는 것은 아니다.

```text
인터닝 전
a ─→ "name" 객체 A
b ─→ "name" 객체 B

첫 sys.intern 후
a ─→ 대표 "name" 객체 A
b ─→ "name" 객체 B

둘째 sys.intern 후
a ─┐
   ├→ 대표 "name" 객체 A
b ─┘
```

어느 기존 객체가 대표가 되는지는 API와 현재 캐시 상태의 결과다. 프로그램은 “첫 번째
인자가 언제나 대표가 된다” 같은 구체 선택에 의존해서는 안 된다. 보장받고 싶은 것은
반환된 문자열의 값이며, 객체 identity는 CPython 내부 최적화의 관찰값이다.

## `==`와 `is`는 인터닝 뒤에도 다른 질문이다

`a == b`는 문자열 내용을 비교하고, `a is b`는 두 참조가 같은 객체를 가리키는지
묻는다. 인터닝된 두 문자열은 identity가 같을 수 있으므로 내부 비교가 포인터 비교로
끝나는 빠른 경우가 생긴다. 그렇다고 일반 Python 코드에서 `==`를 `is`로 바꿔도 되는
것은 아니다.

```python
left = "py" + user_input
right = load_name()

if left == right:
    ...
```

두 함수가 같은 내용의 별도 문자열을 만들 수 있으므로 값 비교에는 항상 `==`가 맞다.
소스의 같은 리터럴이 우연히 같은 객체이거나, 짧은 식별자가 자동 인터닝되어 `is`가
참으로 나온다는 실험은 언어 보장이 아니다. 컴파일 단위, 최적화, 생성 경로와 CPython
버전이 바뀌면 identity 결과가 달라질 수 있다.

인터닝이 모든 문자열 비교를 상수 시간으로 만드는 것도 아니다. 두 객체가 같은 대표라는
빠른 확인은 가능하지만, 인터닝 테이블에서 대표를 찾는 과정에는 hash와 값 비교가 필요할
수 있다. 일반 문자열도 hash를 계산한 뒤 객체 안에 캐시하므로 “인터닝하지 않으면 매번
모든 문자를 다시 hash한다”는 설명도 지나치다. 인터닝은 반복되는 제한된 문자열 집합에서
공유와 빠른 identity 확인을 활용하는 최적화다.

## 정적 singleton과 동적 인터닝은 저장 범위가 다르다

CPython은 인터닝 문자열을 한 종류의 전역 딕셔너리에 모두 넣지 않는다. 먼저 런타임이
정적으로 준비한 문자열이 있다. 한 글자 Latin-1 문자열 256개, `_Py_ID(name)`으로
생성한 식별자, `_Py_STR(...)` 계열의 정적 문자열은 프로세스 런타임의 singleton
저장소와 전역 정적 interning cache를 사용한다. 초기화 중 이 객체들은
`SSTATE_INTERNED_IMMORTAL_STATIC` 상태가 된다.

실행 중 `sys.intern()`이나 내부 API가 받은 문자열도 먼저 Latin-1 singleton과 전역
static intern cache에서 대표를 찾는다. 여기서 찾지 못한 일반 동적 문자열은 현재
`PyInterpreterState.cached_objects.interned_strings`가 가리키는 딕셔너리에 들어간다.
보통 interpreter가 자체 딕셔너리를 쓰지만, main interpreter의 object allocator를
사용하는 일부 subinterpreter는 main의 딕셔너리를 공유한다. 서로 다른 interpreter가
동적 대표 객체를 반드시 공유하거나 반드시 분리한다고 가정할 수 없다.
반면 정적으로 할당된 singleton은 런타임 범위에서 공유된다.

```text
프로세스 런타임
└─ 정적 interned strings
   ├─ Latin-1 한 글자 singleton
   ├─ _Py_ID 문자열
   └─ _Py_STR 문자열

Main interpreter ───────────────→ main 동적 interned_strings 딕셔너리
Subinterpreter A ───────────────→ 자체 동적 딕셔너리
Subinterpreter B ───────────────→ 자체 딕셔너리 또는 main 딕셔너리 공유
```

동적 딕셔너리는 논리적으로 대표 문자열의 집합이지만 CPython 3.14에서는 key와 value가
같은 문자열 객체인 딕셔너리로 구현된다. 이 배치는 대표를 찾은 뒤 그 객체 자체를 값으로
얻기 편하게 한다. 평범한 딕셔너리라면 key와 value가 각각 강한 참조 하나를 만들지만,
GIL 빌드의 mortal interned string에는 수명이 영원히 늘어나지 않도록 별도 참조 횟수
처리가 필요하다.

## GIL 빌드의 mortal 문자열은 테이블에서 빠질 수 있다

GIL 빌드에서 동적 문자열은 `SSTATE_INTERNED_MORTAL` 또는
`SSTATE_INTERNED_IMMORTAL`일 수 있다. `sys.intern()`의 일반 경로로 mortal 대표가
생겼다고 가정하면 수명은 다음처럼 진행된다.

1. 인터닝 딕셔너리의 key와 value가 같은 대표 객체를 가리킨다.
2. CPython은 이 두 딕셔너리 참조를 대표 객체의 유효 참조 횟수에서 제외한다.
3. 함수·Frame·컨테이너 같은 외부 소유자가 있는 동안 대표 객체는 살아 있다.
4. 외부의 마지막 소유 참조가 사라지면 `unicode_dealloc`이 인터닝 딕셔너리 항목을
   제거할 수 있다.
5. interpreter 종료 때 딕셔너리를 정상적으로 비우려면 제외했던 두 참조를 복구한 뒤
   정리한다.

이 특수 처리가 없으면 인터닝 딕셔너리가 자신의 key와 value를 영원히 붙잡아 mortal
문자열이 사실상 immortal이 된다. “인터닝하면 프로그램 종료까지 무조건 산다”는 설명은
GIL 빌드의 동적 mortal 문자열에는 틀리다. 정적 문자열과 명시적으로 immortal로
승격된 문자열은 이 경로와 다르다.

내부 `_PyUnicode_InternMortal`, `_PyUnicode_InternImmortal`,
`_PyUnicode_InternStatic`은 `PyObject **`가 가리키는 기존 소유 참조를 가져가고 대표
객체의 새 소유 참조로 갱신하는 reference-neutral 계약을 사용한다. 빌린 참조를 그대로
넘기면 함수가 가져갈 소유권이 없으므로 계약 위반이다. 이 API는 CPython 내부용이며
Python 코드에서는 반환값을 받는 `sys.intern()`을 사용한다.

## 자유 스레딩 빌드는 동적 인터닝 문자열도 immortal로 만든다

자유 스레딩 빌드에서는 여러 스레드가 동시에 인터닝 테이블과 객체 참조 상태를 만진다.
CPython 3.14는 이 복잡한 수명 경쟁을 피하기 위해 인터닝 문자열을 최종적으로 모두
immortal로 만든다. 이미 다른 스레드가 소유하고 있어 안전하게 immortalize할 수 없는
순간에는 현재 스레드가 소유할 복사본을 만든 뒤 대표로 등록하는 경로도 있다.

이 차이는 Python 언어 의미를 바꾸지 않는다. 두 빌드 모두 같은 내용 비교에는 `==`를
사용하고, `sys.intern()`은 대표 객체를 반환한다. 달라지는 것은 대표 객체를 얼마나 오래
살려 두고 참조 상태를 어떻게 동기화하는가다. GIL 빌드에서 관찰한 mortal 제거 시점을
자유 스레딩 빌드에 적용하거나, 자유 스레딩 빌드의 immortal 정책을 일반 Python 보장으로
일반화하면 안 된다.

## 인터닝은 바인딩과 불변성을 이용하지만 둘을 대체하지 않는다

문자열이 불변이기 때문에 여러 사용자가 대표 객체를 공유해도 한 사용자의 변경이 다른
사용자에게 보이는 문제가 없다. 문자열 연산은 기존 객체를 제자리에서 바꾸는 대신 새
문자열 결과를 만든다. 이름을 새 결과에 재바인딩해도 다른 이름이 가리키는 기존 대표는
바뀌지 않는다.

```text
s ─→ interned "name"
t ─→ 같은 interned "name"

s = s + "s"

s ─→ 새 문자열 "names"
t ─→ 기존 interned "name"
```

인터닝은 일반 참조·바인딩 모델 위에 놓인 공유 정책이다. 값 자체의 불변성,
강한 참조가 정하는 수명, `==`와 `is`의 차이는 그대로 유지된다. 식별자 lookup처럼
CPython이 인터닝을 알고 활용하는 내부 경로에서는 이점이 크지만, 모든 애플리케이션
문자열을 무조건 `sys.intern()`하는 것이 이득이라는 뜻도 아니다. 종류가 많고 한 번만
쓰는 문자열은 테이블 조회와 수명 비용이 이득보다 클 수 있다.

---

[설명 문서 목록](README.ko.md)

기준 글:

- [객체 참조와 수명](objects-and-lifetimes.ko.md)

다른 갈래:

- [제너레이터·코루틴과 Frame](generators-and-coroutines.ko.md)
- [특수화와 JIT](specialization-and-jit.ko.md)
- [예외 처리](exceptions.ko.md)

관련 글:

- [런타임 객체의 문자열 인터닝 조회표](../reference/runtime-objects.ko.md#문자열-인터닝-조회표)
- [이름 분류와 closure](names-and-closures.ko.md)
