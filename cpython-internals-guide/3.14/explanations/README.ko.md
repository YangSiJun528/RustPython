# CPython 3.14 실행 원리를 깊게 읽는 설명 모음

이 폴더의 글은 Python 문법을 사용할 줄 아는 개발자가 소스 한 줄과 CPython의
실행 상태를 연결하도록 돕는다. 핵심은 opcode 이름을 외우는 데 있지 않다.
컴파일러가 미리 정한 정보와 실행할 때 생기는 값을 나누고, 각 명령이 어느
CodeObject 필드와 Frame 슬롯을 읽는지 추적해야 전체 흐름이 보인다.

설명은 `소스 → CodeObject → 함수 객체 → Frame → 평가 루프`를 주 경로로 삼는다.
파서, 예외, 중단과 재개, 문자열 인터닝, 특수화와 JIT는 이 경로의 한 지점을
확대한다. 처음부터 모든 갈래를 읽기보다 주 경로를 먼저 통과한 뒤 궁금한
실행 현상으로 돌아오는 편이 이해하기 쉽다.

> 이 문서군은 CPython 3.14를 다룬다. 예제의 CodeObject 값과 `dis` 출력은
> CPython 3.14.6에서 `adaptive=False`, `show_caches=False`를 기본으로 확인한다.
> 바이트코드와 내부 구조는 Python 언어의 호환 규격이 아니며 마이너 버전에서도
> 달라질 수 있다.

## 주 경로는 정적 결정과 실행 상태를 차례로 연결한다

주 경로의 다섯 글은 앞 글의 결과를 다음 글의 입력으로 사용한다.

| 순서 | 먼저 답할 질문 | 글을 읽고 연결할 수 있는 것 |
|---|---|---|
| 1 | 소스는 왜 여러 표현을 거쳐 CodeObject가 되는가? | AST·심볼 테이블·CFG의 결정이 최종 바이트코드와 CodeObject 필드에 남는 과정 |
| 2 | CodeObject, 함수 객체, Frame은 왜 나뉘는가? | 공유되는 실행 설계와 호출마다 달라지는 상태의 경계 |
| 3 | local·cell·free·global은 어디에 저장되는가? | 이름 분류가 opcode와 실제 저장소를 고정하는 방식 |
| 4 | 평가 루프는 바이트코드를 어떻게 실행하는가? | 평가 스택 변화, Python 함수 호출의 Frame 전환, 반환값 전달 |
| 5 | 이름과 컨테이너가 가리키는 객체는 언제까지 사는가? | 재바인딩·객체 변경·강한 참조·순환 GC의 차이 |

1. [소스에서 CodeObject까지](source-to-code-object.ko.md)
2. [실행 설계와 호출 상태](execution-model.ko.md)
3. [이름 분류와 closure](names-and-closures.ko.md)
4. [평가 루프와 세 가지 스택](evaluation-loop.ko.md)
5. [바인딩과 객체 수명](objects-and-lifetimes.ko.md)

이 순서를 따르면 `LOAD_FAST 0` 같은 명령을 단순한 문법 설명으로 읽지 않게
된다. `0`은 CodeObject가 미리 정한 슬롯이고, 그 슬롯에 든 객체는 이번 호출의
Frame이 제공한다. 같은 방식으로 `LOAD_GLOBAL`, `LOAD_DEREF`, `CALL`도 정적
정보와 현재 값으로 나눠 해석한다.

## 갈래 글은 주 경로의 특정 지점을 확대한다

갈래 글은 독립된 부록이 아니다. 아래 기준 글을 먼저 읽으면 새 용어가 어느
실행 단계에 속하는지 놓치지 않는다.

| 관심사 | 먼저 읽을 기준 글 | 심화 설명 |
|---|---|---|
| 문법 대안이 AST 하나로 정해지는 과정 | 소스에서 CodeObject까지 | [PEG 파서의 순서 있는 선택](peg-parser.ko.md) |
| 실패한 명령에서 handler와 호출자로 이어지는 과정 | 평가 루프 | [예외 테이블과 Frame 되감기](exceptions.ko.md) |
| 실행을 끝내지 않고 Frame을 보존하는 과정 | 평가 루프·객체 수명 | [제너레이터와 코루틴](generators-and-coroutines.ko.md) |
| 반복 실행을 관찰해 빠른 경로를 만드는 과정 | 평가 루프 | [특수화와 JIT](specialization-and-jit.ko.md) |
| 같은 불변 문자열 객체를 공유하는 과정 | 객체 수명 | [문자열 인터닝](string-interning.ko.md) |

파서부터 시작하고 싶다면 `PEG 파서 → 소스에서 CodeObject까지`로 읽는다.
실행 중 현상이 궁금하다면 평가 루프까지 주 경로를 읽은 뒤 예외·제너레이터·
특수화 중 하나로 이동한다.

## 각 글은 같은 관찰 순서를 따른다

설명마다 예제는 달라도 관찰 순서는 같다.

```text
Python 소스
    ↓ 어떤 정적 결정을 만드는가
AST·심볼 분류·CodeObject 필드
    ↓ 그 결정이 어느 명령으로 표현되는가
최종 바이트코드와 인자
    ↓ 명령이 실행되면 무엇이 바뀌는가
Frame 슬롯·평가 스택·함수 객체·PyObject 참조
    ↓
Python에서 관찰되는 결과
```

첫째, 소스와 결과만 비교하지 않고 그 사이의 CodeObject 값을 확인한다. 둘째,
`dis`의 명령을 한 줄씩 읽으며 평가 스택이나 Frame 슬롯이 어떻게 바뀌는지
추적한다. 셋째, 결과가 같아도 저장 위치와 수명이 다른 경우를 구분한다.

각 글의 예제는 핵심 경로만 남긴 최소 예제다. 실제 `dis`에는 `RESUME`, 결합
명령, inline cache처럼 설명의 초점 밖에 있는 명령도 나타날 수 있다. 생략한
명령이 의미에 영향을 주면 본문에서 생략 사실과 역할을 함께 밝힌다.

## 바이트코드는 이름보다 인자와 저장소를 함께 읽는다

opcode 이름만으로는 어떤 객체를 읽는지 확정할 수 없다. 다음 세 항목을 함께
본다.

- CodeObject의 `co_consts`, `co_names`, `co_varnames`, `co_cellvars`,
  `co_freevars`가 어떤 정적 대상을 기록했는가
- opcode의 raw 인자가 상수 인덱스인지, 이름 인덱스인지, locals-plus 슬롯인지,
  개수나 플래그인지
- 실행 중인 Frame과 함수 객체가 그 위치에 어떤 객체 참조를 제공하는가

CPython 3.14에서는 컴파일 중의 의사 명령과 최종 CodeObject의 명령도 다를 수
있다. 예를 들어 `LOAD_CLOSURE`는 컴파일러가 사용하는 의사 명령이지만, assembler
이전의 CFG pseudo-op 변환에서 `LOAD_FAST`로 낮아진다. 이어 load-fast 최적화가
안전한 경우 `LOAD_FAST_BORROW` 같은 명령을 고른다. 본문은 가능한 한 최종 `dis`를
먼저 보여 주고, 중간 명령이 필요할 때만 따로 표시한다.

## 설명과 조회·작업 절차는 분리한다

이 폴더는 원리와 인과관계를 설명한다. 특정 필드의 정확한 인코딩을 찾거나
CPython 소스를 고치는 절차가 필요하면 다음 문서로 이동한다.

- [CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)
- [Frame과 런타임 객체 필드](../reference/runtime-objects.ko.md)
- [Pegen 문법과 생성 파일](../reference/pegen-and-parser.ko.md)
- [CPython 문법 변경하기](../how-to/guide-change-cpython-grammar.ko.md)
- [바이트코드 명령 추가하기](../how-to/guide-add-bytecode.ko.md)

한 예제를 직접 실행하며 전체 경로를 먼저 확인하려면
[소스에서 반환값까지 추적하는 튜토리얼](../tutorial/guide-source-to-execution.ko.md)에서
시작한다.

---

[가이드 홈](../README.ko.md)

다음:

[소스에서 CodeObject까지](source-to-code-object.ko.md)

관련 글:

- [PEG 파서의 순서 있는 선택](peg-parser.ko.md)
- [소스에서 반환값까지 추적하는 튜토리얼](../tutorial/guide-source-to-execution.ko.md)
