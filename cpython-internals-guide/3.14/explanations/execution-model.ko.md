# 실행 설계와 호출 상태는 서로 다른 객체에 놓인다

CPython은 함수 실행에 필요한 정보를 `CodeObject`, 함수 객체, Frame으로 나눈다. `CodeObject`는 재사용할 실행 설계를, 함수 객체는 그 설계에 결합할 환경을, Frame은 한 번의 호출에서 변하는 상태를 맡는다. 이 구분 덕분에 같은 함수를 여러 번 호출해도 바이트코드는 공유하면서 인수와 지역 변수, 실행 위치는 호출마다 따로 유지할 수 있다.

셋은 위에서 아래로 소유되는 계층이 아니라 서로를 가리키는 참조 그래프다. 함수 객체와 실행 중인 Frame은 같은 `CodeObject`를 참조할 수 있지만, 함수 객체가 자신에게서 만들어진 모든 Frame을 보관하지는 않는다. 재귀 호출에서는 하나의 함수 객체와 `CodeObject`를 여러 Frame이 동시에 공유한다.

이 글은 CPython 3.14의 실행 모델을 설명한다. 구조체 필드와 바이트코드 피연산자의 정확한 형식은 버전에 따라 바뀔 수 있다.

## 컴파일은 여러 실행이 공유할 설계를 만든다

컴파일러는 모듈과 그 안의 함수·클래스 본문마다 `PyCodeObject`를 만든다. 코드 객체에는 다음 실행 정보가 모인다.

- 바이트코드와 예외 처리 정보
- `co_consts`에 들어가는 상수와 중첩 코드 객체
- 이름과 지역 변수 슬롯을 해석할 메타데이터
- 바이트코드 위치를 소스 줄과 열에 연결하는 정보

코드 객체는 Python에서 관찰할 수 있는 `PyObject`다. 프로그램의 의미를 나타내는 부분은 불변으로 취급하지만, CPython 3.14가 실행하는 `co_code_adaptive`와 inline cache 같은 최적화 상태는 실행 중 달라질 수 있다.

## `def`를 실행하면 코드에 환경이 결합된다

함수 정의를 컴파일했다고 함수 객체가 이미 존재하는 것은 아니다. 실행이 `def` 문에 도달하면 해당 코드 객체를 사용해 `PyFunctionObject`를 만든다. 함수 객체는 대략 다음 대상을 참조한다.

```text
PyFunctionObject
├── __code__ ─────→ PyCodeObject
├── __globals__ ──→ 모듈 전역 namespace
├── builtins
├── 기본 인수와 키워드 기본값
└── __closure__ ──→ 필요한 cell 객체들
```

함수 객체는 실행 전의 준비물이다. 특정 호출의 인수, 계산 중간값, 현재 명령어 위치는 아직 들어 있지 않다.

## 호출할 때마다 현재 실행 상태가 따로 생긴다

함수를 호출하면 CPython은 호출별 `_PyInterpreterFrame`을 준비한다. 여기에는 인수와 지역 변수·cell·free 변수용 `localsplus` 슬롯, 평가 스택, 현재 명령어 위치, globals와 builtins, 호출 관계를 잇는 링크 등이 들어간다.

```text
                         ┌─→ Frame A: x=3,  현재 명령 12
PyFunctionObject ── 호출 ┼─→ Frame B: x=20, 현재 명령 8
        │                └─→ Frame C: 재귀 호출의 별도 상태
        └──→ PyCodeObject ←──────── 각 Frame도 같은 코드를 참조
```

`_PyInterpreterFrame`은 실행에 쓰는 내부 C 레코드이지 `PyObject`가 아니다. `sys._getframe()`이나 traceback처럼 Python에서 관찰해야 할 때에는 별도의 `PyFrameObject`가 지연 생성되어 내부 Frame을 노출한다.

## 평가 루프는 고정된 정보와 현재 값을 함께 읽는다

바이트코드는 혼자 실행되지 않는다. 평가 루프가 현재 Frame의 명령어를 읽고, opcode가 요구하는 `CodeObject` 메타데이터와 현재 저장소를 함께 해석한다.

| 명령 | `CodeObject`가 정하는 것 | 현재 값을 읽거나 쓰는 곳 |
| --- | --- | --- |
| `LOAD_CONST` | 상수 인덱스 | `co_consts`의 객체를 평가 스택에 올림 |
| `LOAD_FAST`·`STORE_FAST` | 지역 슬롯 번호 | 현재 Frame의 `localsplus` 슬롯 |
| `LOAD_DEREF`·`STORE_DEREF` | closure 슬롯 번호 | 슬롯이 가리키는 `PyCellObject` |
| `LOAD_GLOBAL` | 이름 메타데이터 | Frame의 globals, 이어서 builtins |
| `CALL` | 호출 동작과 피연산자 | Python 함수라면 현재 호출 대상과 인수로 새 Frame을 만듦 |

따라서 `LOAD_FAST 0`이 가리키는 슬롯 번호는 같은 코드에서 고정이지만, 그 슬롯에 든 객체는 호출마다 다르다. `LOAD_GLOBAL`의 이름도 고정되어 있지만 globals의 현재 바인딩은 실행 중 바뀔 수 있다. 코드 객체는 “어떤 방식으로 찾을지”를 정하고, 함수 객체와 Frame은 “이번 실행에서 무엇을 찾게 될지”를 제공한다.

이름 분류와 namespace 조회의 전체 흐름은 [기존 컴파일에서 실행까지 해설](../../../cpython-internals-notes/3.14/compilation-to-execution/README.ko.md)을, 필드 단위 정보는 [런타임 객체 참고 자료](../reference/runtime-objects.ko.md)를 참고한다.

[가이드 홈](../README.ko.md) · 이전: [소스에서 CodeObject까지](source-to-code-object.ko.md) · 다음: [이름과 저장소](names-and-closures.ko.md)
