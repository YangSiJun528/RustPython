# CPython은 실행에 필요한 결정을 단계별로 CodeObject에 굳힌다

Python 소스는 곧바로 평가 루프에 들어가지 않는다. CPython은 먼저 구문을
AST로 정리하고, 이름의 범위와 제어 흐름을 분석한 뒤, 실제 명령과 메타데이터를
CodeObject에 묶는다. 각 단계가 서로 다른 질문에 답하기 때문에 이 중간 표현들이
필요하다.

핵심은 `소스 → 바이트코드`라는 한 번의 번역이 아니다. 구문, 이름, 실행 경로,
물리적 명령 배치를 차례로 확정하는 과정이다. CodeObject는 이 결정들이 끝난 뒤
남는 실행 설계도이며, 실제 지역 변수 값과 현재 실행 위치는 담지 않는다.

> 이 글은 CPython 3.14 구현을 설명한다. 파일 배치와 중간 표현은 다른 버전이나
> 다른 Python 구현에서 달라질 수 있다.

## 각 중간 표현은 한 종류의 결정을 맡는다

```text
소스 문자
  ↓ tokenizer
토큰 스트림
  ↓ PEG parser
AST
  ↓ symbol-table analysis
이름의 범위
  ↓ code generation
의사 명령어
  ↓ CFG 구성과 최적화
최적화된 명령어 열
  ↓ assembler
CodeObject
```

각 표현은 같은 프로그램에서 서로 다른 결정을 담는다.

| 표현 | 이 단계에서 답하는 질문 |
|---|---|
| 토큰 | 어떤 문자들이 이름, 숫자, 연산자, 들여쓰기 경계인가? |
| AST | 소스가 어떤 문장과 표현식으로 구성되는가? |
| 심볼 테이블 | 각 이름을 어느 범위와 저장소에서 다뤄야 하는가? |
| 의사 명령어 | AST의 의미를 어떤 VM 동작으로 낮출 것인가? |
| CFG | 조건·반복·예외 때문에 실행이 어느 블록으로 이동할 수 있는가? |
| CodeObject | 평가 루프가 실행할 명령과 정적 정보는 무엇인가? |

## 파서는 표면 문법을 버리고 프로그램 구조를 남긴다

토크나이저는 소스 문자를 `NAME`, `NUMBER`, `INDENT`, `DEDENT` 같은 토큰으로
나눈다. CPython의 PEG 파서는 이 토큰을 문법에 맞춰 읽고 AST를 만든다.

```python
answer = left + right
```

```text
Assign
├─ target: Name("answer", Store)
└─ value: BinOp
   ├─ left: Name("left", Load)
   ├─ op: Add
   └─ right: Name("right", Load)
```

괄호와 공백 같은 표면 표현은 대부분 사라지고, 대입·이름 읽기·덧셈이라는
구조가 남는다. `Parser/Python.asdl`은 이 AST가 가질 노드와 필드를 정의하는
스키마다. Python 문법 자체를 정의하는 `Grammar/python.gram`과 역할이 다르다.

PEG가 대안을 고르는 방식은 [PEG 파서는 순서 있는 선택으로 토큰에서 AST 하나를 만든다](./peg-parser.ko.md)에서
별도로 설명한다.

## 심볼 테이블은 이름마다 다른 실행 경로를 정한다

이름의 의미는 한 번 나타난 위치만 보고 확정할 수 없다. 함수 전체에 대입이
있는지, `global`·`nonlocal` 선언이 있는지, 중첩 함수가 그 이름을 사용하는지를
함께 봐야 한다. 그래서 AST가 완성된 뒤 별도 순회로 이름을 local, cell, free,
global 등으로 분류한다.

이 결과는 이후 opcode 선택에 반영된다. 일반 함수 지역 이름은 `FAST` 계열,
closure가 공유하는 이름은 `DEREF` 계열, 함수의 전역 후보는 `GLOBAL` 계열을
사용할 수 있다. 심볼 테이블 객체 전체가 CodeObject에 그대로 복사되는 것은
아니다. 분류 결과가 이름 튜플과 바이트코드에 남는다.

## CFG는 AST의 모양과 실제 실행 순서를 분리한다

AST는 `if`의 조건, 본문, `else`를 자식으로 표현하지만 세 자식을 모두 실행한다는
뜻은 아니다. 코드 생성기는 AST를 논리적인 점프 대상을 가진 의사 명령어로
낮춘다. CFG는 이 명령들을 basic block으로 묶고 가능한 이동을 드러낸다.

```text
                 ┌─ 참  → [then block] ─┐
[조건을 검사] ───┤                     ├─→ [합류 block]
                 └─ 거짓 → [else block] ┘
```

이 구조에서는 도달할 수 없는 블록, 불필요한 점프, 블록 사이의 스택 상태를
일렬로 늘어선 명령보다 쉽게 분석할 수 있다. 최적화가 끝나면 CFG는 다시
명령어 열로 평탄화된다.

## assembler가 논리적 계획을 실행 가능한 배치로 바꾼다

코드 생성 중에는 `else 블록으로 이동`처럼 논리 대상을 쓰는 편이 낫다. 실제
점프 거리는 모든 명령의 크기와 배치가 끝나야 계산할 수 있다. assembler는
마지막에 다음 정보를 확정한다.

- 실제 opcode와 인자
- 상대 점프 거리
- 상수와 이름 테이블
- 소스 위치 테이블
- 예외 처리 테이블
- 인수 수, 지역 변수 구조, 최대 평가 스택 깊이 같은 메타데이터

그 결과가 CodeObject다. 중첩 함수의 본문도 별도 CodeObject로 컴파일되어 바깥
CodeObject의 상수에 들어간다.

## CodeObject가 만들어져도 프로그램은 아직 실행되지 않았다

CodeObject에는 무엇을 실행할지가 들어 있지만 이번 호출의 인수와 지역 변수
값은 없다. `def` 문이 실행되면 CodeObject가 globals, 기본값, closure와 연결되어
함수 객체가 되고, Python 함수가 호출될 때마다 새 Frame이 만들어진다.

컴파일과 실행의 경계는 이렇게 나뉜다.

```text
컴파일: 실행 방법과 정적 구조를 CodeObject에 기록
실행:   함수 객체의 환경과 호출별 Frame을 사용해 실제 객체를 계산
```

세부 C 함수와 파일 지도는 기존 상세 문서
[CPython 3.14가 Python 소스 코드를 컴파일하는 방법](../../../cpython-internals-notes/3.14/compiling-python-source-code/README.ko.md)을
참고한다. CodeObject 이후의 실행은
[컴파일에서 실행까지](../../../cpython-internals-notes/3.14/compilation-to-execution/README.ko.md)에
이어진다.

[가이드 홈](../README.ko.md) · 이전: [소스에서 반환값까지 추적하기](../tutorial/guide-source-to-execution.ko.md) · 다음: [실행 설계와 호출 상태](execution-model.ko.md) · 심화: [PEG 파서](peg-parser.ko.md)
