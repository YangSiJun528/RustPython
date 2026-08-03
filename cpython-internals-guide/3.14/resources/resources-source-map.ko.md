# 기존 문서와 새 문서의 대응표

이 문서는 리뉴얼판이 기존 CPython 3.14 노트를 어떻게 재구성했는지
추적한다. 새 글은 독자 질문별로 핵심 흐름을 설명하며, 원문 대응 번역과
세부 C 구조는 기존 문서에 그대로 남긴다. 따라서 문단을 일대일로 옮긴
축약본이 아니다.

## 세 종류의 정보를 구분한다

| 표시할 범위 | 예 | 새 글의 처리 |
|---|---|---|
| Python 의미 | 렉시컬 범위, 바인딩과 변경 | 구현과 분리해 설명하되 CPython 사례로 한정한다. |
| CPython 3.14 구현 | Pegen, locals-plus, `_PyInterpreterFrame` | 문서 첫머리나 해당 문단에서 버전을 밝힌다. |
| CPython 3.14.6 관찰값 | 실제 `dis` 출력, 결합 opcode, raw operand | 버전과 `dis` 옵션을 함께 적고 reference에 모은다. |

바이트코드, 내부 구조체, 생성 명령, 소스 경로는 공개 호환 규격이 아니다.
다른 버전에 그대로 적용하지 않는다.

기존 설명과 3.14.6 소스가 다른 지점은
[차이와 정정 기록](resources-known-corrections.ko.md)에서 확인한다.

## 컴파일과 입문 실행 설명을 독자 순서로 다시 나눴다

| 기존 문서와 범위 | 새 문서 | 기존 문서에 남긴 세부 |
|---|---|---|
| [컴파일에서 실행까지](../../../cpython-internals-notes/3.14/compilation-to-execution/README.ko.md) 전체 예제 | [입문 tutorial](../tutorial/guide-source-to-execution.ko.md) | 전체 `dis` 출력, PyObject·GC 보충 설명, Java 비교 |
| 같은 문서의 CodeObject·함수·Frame | [실행 모델](../explanations/execution-model.ko.md) | 더 긴 평가 스택 추적과 구현 주석 |
| 같은 문서의 이름 분류·closure | [이름과 closure](../explanations/names-and-closures.ko.md) | raw opcode별 긴 예제 |
| 같은 문서의 PyObject·바인딩 | [객체와 수명](../explanations/objects-and-lifetimes.ko.md) | 리스트·기본 인수·GC의 확장 예제 |
| 같은 문서의 필드·oparg | [CodeObject reference](../reference/code-object-and-bytecode.ko.md) | 설명용 실행 순서 |

## 파서·컴파일러·문법 변경은 문서 유형을 분리했다

| [기존 소스 컴파일 문서](../../../cpython-internals-notes/3.14/compiling-python-source-code/README.ko.md) 범위 | 새 문서 | 기존 문서에 남긴 세부 |
|---|---|---|
| 토큰 → AST → 심볼 테이블 → CFG → CodeObject | [소스에서 CodeObject까지](../explanations/source-to-code-object.ko.md) | arena, ASDL sequence, `ADDOP_*`, 함수별 C 흐름 |
| PEG ordered choice·memoization·오류 규칙 | [PEG 파서 설명](../explanations/peg-parser.ko.md) | 전체 문법 표기와 디버깅 trace 예제 |
| 문법 표기·파일·재생성 명령 | [Pegen reference](../reference/pegen-and-parser.ko.md) | 메타 문법 전문과 문서 이력 |
| CPython 문법을 바꾸는 절차 | [문법 변경 how-to](../how-to/guide-change-cpython-grammar.ko.md) | 13개 영향 파일의 문단별 해설 |
| CodeObject와 중요 파일 지도 | [CodeObject reference](../reference/code-object-and-bytecode.ko.md) | `_PyCodeConstructor`와 내부 생성 단계 |

## 런타임 객체의 중복을 한 번만 설명한다

기존 [런타임 객체](../../../cpython-internals-notes/3.14/runtime-objects/README.ko.md)는
CPython InternalDocs에 가까운 번역판이다. [객체 모델과 런타임 객체](../../../cpython-internals-notes/3.14/object-model-and-runtime-objects/README.ko.md)는
그 본문을 거의 그대로 포함하고 객체 참조·이름 조회·통합 예제를 보강한
확장판이다.

| 기존 주제 | 새 문서 | 기존 문서에 남긴 세부 |
|---|---|---|
| CodeObject·함수·Frame 관계 | [실행 모델](../explanations/execution-model.ko.md) | `co_linetable`과 정확한 내부 배치 |
| local slot·cell·namespace | [이름과 closure](../explanations/names-and-closures.ko.md) | opcode별 긴 비교와 통합 예제 |
| PyObject·reference ownership·GC | [객체와 수명](../explanations/objects-and-lifetimes.ko.md) | free-threaded 빌드 차이와 GC 세부 |
| 문자열 interning | [문자열 인터닝](../explanations/string-interning.ko.md) | 상태 전이와 내부 API |
| Frame materialization·필드·위치 테이블 | [런타임 객체 reference](../reference/runtime-objects.ko.md) | varint·short form 비트 인코딩과 내부 API |
| 제너레이터·코루틴 | [제너레이터와 코루틴](../explanations/generators-and-coroutines.ko.md) | `_PyGenObject_HEAD`, `SEND`, `CLEANUP_THROW` 세부 |

## 프로그램 실행 문서는 실행 경로별로 쪼갰다

| [기존 프로그램 실행 문서](../../../cpython-internals-notes/3.14/program-execution/README.ko.md) 범위 | 새 문서 | 기존 문서에 남긴 세부 |
|---|---|---|
| bytecode fetch·decode·평가 스택·호출 | [평가 루프](../explanations/evaluation-loop.ko.md) | code unit·endian·`EXTENDED_ARG`·eval hook |
| 예외 테이블과 Frame 되감기 | [예외 처리](../explanations/exceptions.ko.md) | varint 형식, C 함수, 예외 연결 구현 |
| 적응형 특수화·JIT | [특수화와 JIT](../explanations/specialization-and-jit.ko.md) | counter·통계·optimizer 세부 공식 |
| 새 opcode 추가 절차 | [바이트코드 추가 how-to](../how-to/guide-add-bytecode.ko.md) | DSL과 생성 코드의 장문 해설 |
| GC 설계 | [객체와 수명](../explanations/objects-and-lifetimes.ko.md) | 세대·prefetch·free-threaded GC 알고리즘 |

기존 문서에 남아 있는 `is_entry` 설명은 3.11 초기 구현의 흔적이다.
리뉴얼판은 CPython 3.14의 `owner`, shim Frame, `return_offset` 모델만
사용하고 역사적 차이는 reference에서만 언급한다.

## 그림도 원본과 함께 보존한다

리뉴얼판의 `assets/`에는 기존 HTML 원본과 PNG를 복사했다. 새 글은 같은
개념을 설명하는 그림을 다시 만들지 않고 재사용한다. 원래 그림은
[기존 diagrams 폴더](../../../cpython-internals-notes/3.14/compilation-to-execution/diagrams/)에
그대로 남아 있다.

| 그림 | 편집 가능한 HTML | 문서용 PNG |
|---|---|---|
| 컴파일 흐름 | [HTML](../assets/01-compilation-pipeline.html) | [PNG](../assets/01-compilation-pipeline.png) |
| CodeObject와 바이트코드 | [HTML](../assets/02-code-object-and-bytecode.html) | [PNG](../assets/02-code-object-and-bytecode.png) |
| Frame과 평가 스택 | [HTML](../assets/03-frame-evaluation-stack.html) | [PNG](../assets/03-frame-evaluation-stack.png) |
| PyObject와 바인딩 | [HTML](../assets/04-pyobject-bindings.html) | [PNG](../assets/04-pyobject-bindings.png) |
| 이름 조회와 Frame 체인 | [HTML](../assets/05-name-resolution-and-frame-chain.html) | [PNG](../assets/05-name-resolution-and-frame-chain.png) |

[가이드 홈](../README.ko.md)
