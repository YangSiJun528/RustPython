# Frame, 위치 테이블, 문자열 인터닝 참고 자료

이 문서는 CPython 3.14의 런타임 표현, `_PyInterpreterFrame` 필드,
`co_linetable` 형식, 문자열 인터닝 상태를 조회하는 참조 자료다. 개념 설명은
[실행 설계와 호출 상태](../explanations/execution-model.ko.md),
[객체와 수명](../explanations/objects-and-lifetimes.ko.md),
[제너레이터와 코루틴](../explanations/generators-and-coroutines.ko.md)에 있다. Function,
CodeObject, Frame, Cell, Method 사이의 전체 저장 위치는
[함수 관련 정보의 저장 위치](function-and-runtime-storage.ko.md)에서 조회한다.

아래 내용은 CPython 3.14 기준이다. `_Py` 구조와 함수, adaptive bytecode, Frame 필드와 문자열 상태는 공개 API가 아니다. 상세 번역은 [기존 런타임 객체 문서](../../../cpython-internals-notes/3.14/runtime-objects/README.ko.md)와 [객체 모델 확장판](../../../cpython-internals-notes/3.14/object-model-and-runtime-objects/README.ko.md)에 있다.

## 런타임 표현

| 표현 | `PyObject`인가 | 용도 |
| --- | ---: | --- |
| `PyCodeObject` | 예 | 바이트코드, 상수·이름 메타데이터, 소스 위치 |
| `PyFunctionObject` | 예 | code, globals, 기본 인수, closure를 결합 |
| `_PyInterpreterFrame` | 아니요 | 호출별 실행 상태를 담는 내부 레코드 |
| `PyFrameObject` | 예 | traceback·debugger·`sys._getframe()`에 노출되는 Frame |
| `PyGenObject` | 예 | 제너레이터 상태와 내장 `_PyInterpreterFrame` |
| `PyCoroObject`·`PyAsyncGenObject` | 예 | 네이티브 코루틴·비동기 제너레이터와 내장 Frame |
| `PyCellObject` | 예 | closure가 공유하는 바인딩 저장소 |

## `_PyInterpreterFrame` 주요 필드

정의: `Include/internal/pycore_interpframe_structs.h`

| 필드 | CPython 3.14 의미·소유권 |
| --- | --- |
| `f_executable` | code object 또는 `None`의 deferred/strong `_PyStackRef` |
| `previous` | 활성 실행 체인의 이전 Frame. 이름 조회 경로가 아님 |
| `f_funcobj` | 함수 객체의 deferred/strong `_PyStackRef`; C stack Frame에서는 유효하지 않음 |
| `f_globals`·`f_builtins` | 빌린 참조; C stack Frame에서는 유효하지 않음 |
| `f_locals` | 강한 참조 또는 `NULL`; 동적 locals mapping |
| `frame_obj` | 강한 `PyFrameObject` 참조 또는 `NULL` |
| `instr_ptr` | 현재 실행 중이거나 재개할 code unit |
| `stackpointer` | 평가 스택 꼭대기 |
| `tlbc_index` | 자유 스레딩 빌드의 thread-local bytecode 인덱스 |
| `return_offset` | Python 피호출자가 반환할 호출자 쪽 상대 위치 |
| `owner` | 아래 소유자 상태 |
| `localsplus[]` | 지역·cell·free 변수 슬롯과 평가 스택 저장 영역 |

| `owner` 값 | 소유자 |
| ---: | --- |
| `0` | thread (`FRAME_OWNED_BY_THREAD`) |
| `1` | 제너레이터 |
| `2` | `PyFrameObject` |
| `3` | interpreter |
| `4` | C stack |

배치는 `special fields → locals → evaluation stack`이다. 보통 Frame은 thread-state 저장 영역에, 제너레이터·코루틴 Frame은 해당 객체 안에, shim Frame은 C stack에 놓인다.

`instr_ptr`는 상태에 따라 다르게 읽는다.

| 상태 | 가리키는 위치 |
| --- | --- |
| 실행 중 | 현재 명령 |
| 중단됨 | 재개하면 실행할 명령 |
| `frame.f_lineno` 설정 직후 | 다음에 실행할 명령 |
| 하위 Python 함수 호출 중 | traceback에 남길 호출 명령 |

`return_offset`은 `CALL`, `SEND`, `BINARY_OP_SUBSCR_GETITEM`처럼 Python Frame 호출을 구현하는 명령에서 설정한다. 피호출자가 없으면 의미가 없다.

## `co_linetable` 조회표

`co_linetable`은 code unit을 소스 위치에 연결한다. traceback은 `tb_lasti`로 이를 조회한다. `co_positions()`는 명령별 `(line, end_line, column, end_column)`, `co_lines()`는 구간별 `(start, end, line)`을 반환한다. `co_lnotab`은 3.10 이하 호환용이며 지연 생성된다.

각 entry의 첫 바이트는 bit 7이 `1`, bit 3–6이 `Code`, bit 0–2가 `length-1`이다. 길이는 이 entry가 담당하는 code unit 수다. 뒤에는 최상위 비트가 0인 바이트가 이어진다. 시작 줄 delta의 기준은 이전 entry의 시작 줄이며, 첫 entry만 `co_firstlineno`를 쓴다. 끝 줄 delta의 기준은 같은 entry의 시작 줄이다.

| Code | 형식 | 위치 데이터 |
| ---: | --- | --- |
| `0–9` | short | 같은 줄, 두 번째 바이트로 열 범위 표현 |
| `10–12` | one-line | 시작 줄 delta=`Code-10`, 열은 각 1바이트 |
| `13` | no-column | 시작 줄 `svarint`, 열 없음 |
| `14` | long | 시작 줄 `svarint`, 끝 줄·열 `varint` |
| `15` | no-location | 위치 없음 |

short 형식의 두 번째 바이트를 `b`라고 하면 시작 열은 `(Code*8)+((b>>4)&7)`, 끝 열은 `start_column+(b&15)`다.

long 형식의 시작 열과 끝 열은 각각 `column + 1`을 `varint`로 저장한다. 조회할 때
다시 `1`을 빼며, 저장값 `0`은 열 정보가 없음을 나타내는 `-1`로 복원된다.

`varint`는 하위 6비트 조각부터 저장하고 마지막이 아닌 조각의 bit 6을 켠다. `svarint`는 음수를 홀수, 0과 양수를 짝수로 바꾼 뒤 같은 형식을 쓴다. 기존 CPython 3.14 문서의 `encode_varint()` 예제는 bit 6을 켠 직후 `& 0x3F`로 다시 지우는 오류가 있다. 설명의 `200 → 0x48, 0x03`과 맞추려면 해당 마스크를 그대로 구현하면 안 된다.

## 문자열 인터닝 조회표

| 구분 | 저장 위치·수명 |
| --- | --- |
| 한 글자 Latin-1, `_Py_ID`, `_Py_STR` | 정적 singleton; 런타임 전역 테이블에서 공유 |
| 동적 인터닝 문자열 | `PyInterpreterState.cached_objects.interned_strings`; key와 value가 같은 객체 |
| GIL 빌드 | mortal 또는 immortal 가능 |
| 자유 스레딩 빌드 | 인터닝 문자열은 항상 immortal |

| 상태 | 값 | 허용 전이 |
| --- | ---: | --- |
| `SSTATE_NOT_INTERNED` | `0` | 동적 문자열은 `1` 또는 `2`, 정적 singleton은 `3`으로 |
| `SSTATE_INTERNED_MORTAL` | `1` | `2`로 승격 가능 |
| `SSTATE_INTERNED_IMMORTAL` | `2` | 역전이 없음 |
| `SSTATE_INTERNED_IMMORTAL_STATIC` | `3` | 정적 singleton의 최종 상태 |

| 내부 API | 계약 |
| --- | --- |
| `_PyUnicode_InternMortal` | 동적 문자열을 mortal 상태로 인터닝 |
| `_PyUnicode_InternImmortal` | 인터닝하고 immortal로 만듦 |
| `_PyUnicode_InternStatic` | 정적 singleton 전용 |

세 API는 `PyObject **`가 가리키는 기존 참조를 가져가고 대표 객체의 새 참조로 갱신하므로 참조 수 관점에서 neutral이다. 빌린 참조를 인자로 넘기면 안 된다. 일반 Python 문자열 비교에는 인터닝 여부와 무관하게 `is`가 아니라 `==`를 사용한다.

GIL 빌드의 mortal 문자열은 인터닝 딕셔너리의 key와 value가 만드는 두 참조를 참조 횟수에서 제외한다. 외부 소유 참조가 사라지면 `unicode_dealloc`이 항목을 제거하며, 인터프리터 종료 때에는 제외했던 두 참조를 복구한 뒤 딕셔너리를 비운다.

[가이드 홈](../README.ko.md)
