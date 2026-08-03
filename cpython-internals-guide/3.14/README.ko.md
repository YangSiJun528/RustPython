# CPython 3.14 내부를 실행 흐름으로 읽기

Python 소스는 CodeObject로 컴파일된다. `def`를 실행하면 이 CodeObject에 환경을
결합한 함수 객체가 생기고, Python 함수를 호출할 때마다 새 Frame이 생긴다.
이 흐름 안에 파서, 이름 범위, 바이트코드, 객체 참조, 평가 루프가 모두 들어
있다. 기존 상세 노트에는 필요한 정보가 갖춰져 있지만 번역과 해설,
변경 절차, 내부 형식이 한 문서에 섞여 있어 어디부터 읽어야 할지 판단하기
어렵다.

이 가이드는 기존 문서를 그대로 두고, 독자가 실제로 묻게 되는 질문을 중심으로
내용을 다시 배열했다. 짧은 예제를 먼저 실행한 다음 컴파일에서 런타임으로
이어지는 설명을 따라간다. 코드 수정 절차와 필드 조회 정보는 how-to와 reference로
분리했다.

> 이 문서는 CPython 3.14를 다룬다. `dis` 출력은 CPython 3.14.6에서
> `adaptive=False`, `show_caches=False`로 확인했다. 바이트코드 이름과 내부
> 구조는 버전 사이의 호환 규격이 아니다.

## 한 예제를 먼저 보면 용어가 자리를 잡는다

[소스에서 결과까지 직접 추적하기](tutorial/guide-source-to-execution.ko.md)는
`compile()`과 `dis`로 모듈·함수 CodeObject를 확인한다. 이어서 호출별 Frame의
지역 슬롯과 평가 스택이 결과를 만드는 순서를 추적한다. 내부 구현을 처음
처음 읽는 독자는 여기서 시작한다.

## 핵심 흐름은 다섯 질문으로 이어진다

이 다섯 글은 컴파일 결과가 한 번의 호출 상태로 이어지는 순서에 맞춰 읽는다.

| 순서 | 글이 답하는 질문 | 문서 |
|---|---|---|
| 1 | 소스는 왜 여러 중간 표현을 거쳐 CodeObject가 되는가? | [소스에서 CodeObject까지](explanations/source-to-code-object.ko.md) |
| 2 | CodeObject, 함수 객체, Frame은 왜 나뉘는가? | [실행 설계와 호출 상태](explanations/execution-model.ko.md) |
| 3 | local·cell·free·global의 실제 값은 어디에 있는가? | [이름과 저장소](explanations/names-and-closures.ko.md) |
| 4 | 평가 루프는 바이트코드를 Frame에 어떻게 적용하는가? | [평가 루프와 세 가지 스택](explanations/evaluation-loop.ko.md) |
| 5 | 변수와 컨테이너에는 무엇이 들어 있으며 객체는 언제 사라지는가? | [바인딩과 객체 수명](explanations/objects-and-lifetimes.ko.md) |

## 필요한 주제는 핵심 흐름에서 갈라져 읽는다

아래 글은 선형 순서에서 빼 두었다. 파싱, 중단과 재개, 실패, 최적화처럼 핵심
흐름의 한 지점을 더 깊이 설명하기 때문이다.

| 관심사 | 글이 답하는 질문 | 문서 |
|---|---|---|
| 파서 | PEG 파서는 겹치는 문법 대안에서 AST 하나를 어떻게 고르는가? | [PEG 파서의 선택 규칙](explanations/peg-parser.ko.md) |
| 중단과 재개 | 제너레이터와 코루틴은 실행 상태를 어떻게 보존하는가? | [제너레이터·코루틴과 Frame](explanations/generators-and-coroutines.ko.md) |
| 예외 | 예외는 handler를 어떻게 찾고 호출 스택을 빠져나가는가? | [예외 테이블과 Frame 되감기](explanations/exceptions.ko.md) |
| 최적화 | 특수화와 JIT는 의미를 바꾸지 않고 어떻게 빨라지는가? | [관찰한 실행을 빠른 경로로 바꾸는 법](explanations/specialization-and-jit.ko.md) |
| 문자열 | 인터닝은 같은 문자열 객체를 언제, 왜 공유하는가? | [문자열 인터닝과 객체 공유](explanations/string-interning.ko.md) |

설명 글마다 질문 하나에만 답한다. C 필드의 정확한 형식, 위치 테이블 인코딩,
생성 파일 목록처럼 전체 흐름을 읽을 때 잠시 미뤄도 되는 세부는 reference에서
다룬다.

## 수정 절차와 세부 값은 따로 찾는다

작업 절차는 순서와 완료 조건을 바로 확인할 수 있도록 설명 문서와 분리했다.

- [CPython 문법 변경하기](how-to/guide-change-cpython-grammar.ko.md)
- [바이트코드 명령 추가하기](how-to/guide-add-bytecode.ko.md)

찾을 값이나 파일을 이미 알고 있다면 reference를 먼저 연다.

- [Pegen 문법과 파서 파일](reference/pegen-and-parser.ko.md)
- [CodeObject 필드와 바이트코드 인자](reference/code-object-and-bytecode.ko.md)
- [Frame·위치 테이블·문자열 인터닝 내부 구조](reference/runtime-objects.ko.md)

## 기존 문서는 상세 근거로 남아 있다

이 가이드는 기존 문서를 요약본으로 대체하지 않는다. 원문 대응 번역과 세부
구현, 긴 예제는 그대로 보존했다. 새 글에서 다루지 않은 내용은
[기존 문서와 새 문서의 대응표](resources/resources-source-map.ko.md)로 찾을 수
있다. 재검증 과정에서 바로잡은 구현 세부는
[기존 상세 노트와 3.14.6의 차이](resources/resources-known-corrections.ko.md)에
따로 기록했다.

- [Python 소스 코드 컴파일](../../cpython-internals-notes/3.14/compiling-python-source-code/README.ko.md)
- [컴파일에서 실행까지](../../cpython-internals-notes/3.14/compilation-to-execution/README.ko.md)
- [객체 모델과 런타임 객체](../../cpython-internals-notes/3.14/object-model-and-runtime-objects/README.ko.md)
- [런타임 객체 원문 대응판](../../cpython-internals-notes/3.14/runtime-objects/README.ko.md)
- [프로그램 실행](../../cpython-internals-notes/3.14/program-execution/README.ko.md)
