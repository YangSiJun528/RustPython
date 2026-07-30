# CPython 3.14가 Python 소스 코드를 컴파일하는 방법

이 문서는 CPython 3.14 저장소의 `InternalDocs` 중 **Compiling Python
Source Code** 아래에 있는 세 문서를 한 흐름으로 읽기 위한 한국어
해설서다.

- [Guide to the parser](https://github.com/python/cpython/blob/3.14/InternalDocs/parser.md)
- [Compiler design](https://github.com/python/cpython/blob/3.14/InternalDocs/compiler.md)
- [Changing CPython's grammar](https://github.com/python/cpython/blob/3.14/InternalDocs/changing_grammar.md)

## 대상 독자와 읽는 방법

독자가 nand2tetris를 수료해 다음 개념은 이미 알고 있다고 가정한다.

- 소스 문자열을 토큰으로 나누는 과정
- 문법에 따라 구문 트리나 AST를 만드는 과정
- 심볼 테이블과 변수의 범위
- 중간 표현과 코드 생성
- 스택 기반 가상 머신과 바이트코드

따라서 일반적인 컴파일러 단계를 다시 설명하기보다는 CPython에서만
나타나는 설계와 구현상의 선택에 집중한다. PEG의 ordered choice,
packrat parsing, 문법 action, ASDL, arena, pseudo-instruction, code object
같은 개념은 처음 등장할 때 별도로 해설한다.

원문의 문맥만으로 뜻이 충분한 문장은 번역만 제시한다. 배경지식이
필요하거나 표현만으로 오해하기 쉬운 문단에는 다음과 같은 인용문
형태의 해설을 붙인다.

> **해설:** 이 형식의 문단은 원문 번역이 아니라 독자를 위한 추가 설명이다.

### 편집 범위

`Guide to the parser`는 사용자가 대화에 원문 전체를 제공했으므로 모든
문장을 원래 순서대로 번역한다. `Compiler design`과 `Changing CPython's
grammar`는 공식 원문의 절과 개념을 빠짐없이 따라가되, 외부 문서를
그대로 재현하지 않고 한국어 설명문으로 재구성한다. 코드, 식별자,
명령과 파일 경로는 정확한 대응이 필요하므로 원형을 유지한다.

이 문서는 Python 언어 명세가 아니라 **CPython 3.14의 내부 구현**
설명이다. 다른 Python 구현이나 다른 CPython 버전에는 그대로 적용되지
않을 수 있다.

### 문서 구조

- [전체 지도](#전체-지도)
- [제1부: 파서 가이드](#제1부-파서-가이드)
- [제2부: 컴파일러 설계](#제2부-컴파일러-설계)
- [제3부: CPython 문법 변경](#제3부-cpython-문법-변경)
- [핵심 용어 찾아보기](#핵심-용어-찾아보기)

## 전체 지도

세 문서는 서로 다른 질문에 답한다.

1. **Guide to the parser**: CPython의 PEG 파서는 문법을 어떻게 읽고
   AST를 만드는가?
2. **Compiler design**: 만들어진 AST는 어떻게 바이트코드와 code
   object가 되는가?
3. **Changing CPython's grammar**: Python 문법을 실제로 바꾸려면 어떤
   원본 파일, 생성 파일, 검증 코드와 문서를 함께 수정해야 하는가?

전체 컴파일 경로는 다음과 같다.

```text
소스 코드
  ↓ tokenizer
토큰 스트림
  ↓ PEG parser
AST
  ↓ symbol-table analysis + code generation
pseudo-instruction sequence
  ↓ CFG 구성과 최적화
최적화된 instruction sequence
  ↓ assembler
bytecode + metadata를 담은 PyCodeObject
  ↓ evaluation loop
실행
```

> **nand2tetris와의 대응:** Jack 컴파일러가 소스 코드를 VM 명령으로
> 내보냈다면, CPython 컴파일러는 Python 소스를 CPython 바이트코드로
> 내보낸다. 차이는 중간 단계가 훨씬 많고, 함수의 lexical scope,
> 예외 처리, 정확한 소스 위치, 동적 이름 조회 같은 Python의 의미를
> 보존하기 위한 메타데이터가 함께 생성된다는 점이다.


---

## 제1부: 파서 가이드

### 개요

현재 Python 파서는 [`PEG`(Parsing Expression Grammar, 파싱 표현 문법)](https://en.wikipedia.org/wiki/Parsing_expression_grammar) 파서다. 이 파서는 기존 [`LL(1)`](https://en.wikipedia.org/wiki/LL_parser) 파서를 대체하기 위해 [PEP 617: CPython을 위한 새로운 PEG 파서](https://peps.python.org/pep-0617/)에서 도입되었다.

> **해설 — LL(1)에서 PEG로 바꾼 이유를 이해하는 최소 배경**
>
> nand2tetris의 Jack 파서처럼 LL 계열 파서는 보통 현재 토큰과 제한된 수의 다음 토큰을 보고 어느 문법 규칙을 적용할지 결정한다. `LL(1)`의 `1`은 결정을 위해 미리 보는 토큰이 하나라는 뜻이다. 이 방식은 빠르고 예측하기 쉽지만, 문법을 LL(1)에 맞게 변형해야 하는 제약이 있다.
>
> PEG는 선택지를 적힌 순서대로 직접 시험하고, 필요하면 실패한 지점에서 되돌아가 다음 선택지를 시도한다. 그래서 Python처럼 오랜 기간 복잡해진 문법을 더 자연스러운 형태로 표현하기 쉽다.

파서를 구현하는 코드는 [파서 생성기](https://en.wikipedia.org/wiki/Compiler-compiler)가 문법 정의로부터 생성한다. 따라서 Python 언어를 변경할 때는 [문법 파일](https://github.com/python/cpython/blob/3.14/Grammar/python.gram)을 수정한다. 개발자가 생성기 자체를 수정해야 하는 경우는 드물다.

> **해설 — 파서 생성기**
>
> 파서 생성기는 “문법을 입력받아 파서 프로그램을 출력하는 프로그램”이다. nand2tetris 식으로 비유하면 VM 명령을 직접 반복해서 해석하는 코드를 쓰는 대신, 명령 형식을 선언하면 그 선언으로부터 해석기 일부를 만들어 주는 도구에 가깝다. CPython에서는 대략 다음 관계가 성립한다.
>
> ```text
> Grammar/python.gram  ──Pegen──>  Parser/parser.c
> 문법과 AST 생성 규칙              실제 C 파서
> ```
>
> `Parser/parser.c`는 생성 결과이므로 일반적으로 직접 고치지 않는다.

문법과 문법 변경 절차에 대한 자세한 설명은 [CPython 문법 변경하기](https://github.com/python/cpython/blob/3.14/InternalDocs/changing_grammar.md)를 참고하라.

### PEG 파서의 작동 방식

PEG(Parsing Expression Grammar) 문법은 [문맥 자유 문법](https://en.wikipedia.org/wiki/Context-free_grammar)과 다르다. PEG 문법은 문법이 작성된 모습 자체가 파서가 실제로 파싱하는 방식에 더 가깝다. 근본적인 기술적 차이는 선택 연산자에 순서가 있다는 점이다. 즉 다음과 같이 작성하면,

```
    rule: A | B | C
```

문맥 자유 문법을 구현하는 파서(예: `LL(1)` 파서)는 입력 문자열이 주어졌을 때 어느 대안(`A`, `B`, `C`)을 전개해야 하는지 *추론*하는 구조를 생성한다. 반면 PEG 파서는 각 대안을 지정된 순서대로 검사하고, 가장 먼저 성공한 대안을 선택한다.

> **해설 — “선택에 순서가 있다”**
>
> 여기서 `|`는 수학적인 집합의 합집합이 아니다. 다음처럼 동작하는 제어 흐름에 가깝다.
>
> ```text
> A를 시도한다.
> ├─ 성공: A를 선택하고 종료한다.
> └─ 실패: 입력 위치를 되돌리고 B를 시도한다.
>            ├─ 성공: B를 선택하고 종료한다.
>            └─ 실패: C를 시도한다.
> ```
>
> 따라서 PEG 문법은 “어떤 문자열이 문법에 속하는가”뿐 아니라 “파서가 어떤 순서로 판단하는가”까지 규정한다.

이는 PEG 문법에서 선택 연산자가 교환 법칙을 만족하지 않는다는 뜻이다. 또한 문맥 자유 문법과 달리 PEG 문법에 따른 유도는 모호할 수 없다. 어떤 문자열의 파싱에 성공한다면, 그 문자열에는 유효한 구문 분석 트리(parse tree)가 정확히 하나만 존재한다.

> **해설 — 교환 법칙과 모호성**
>
> `A | B`와 `B | A`의 결과가 다를 수 있으므로 교환 법칙이 성립하지 않는다. “구문 분석 트리가 하나”라는 말은 입력이 본질적으로 한 가지 의미만 가진다는 뜻이 아니다. 겹치는 해석이 있더라도 문법에 적힌 우선순위가 하나를 강제로 고른다는 뜻이다.

PEG 파서는 보통 재귀 하강 파서로 구성된다. 이 구조에서는 문법의 각 규칙이 파서를 구현한 프로그램의 함수 하나에 대응하고, 파싱 표현식(규칙의 “전개” 또는 “정의”)은 그 함수 안의 “코드”를 나타낸다. 개념적으로 각 파싱 함수는 입력 문자열을 인수로 받고 다음 결과 중 하나를 내놓는다.

- “성공” 결과: 해당 규칙으로 표현식을 파싱할 수 있다는 뜻이다. 함수는 선택적으로 앞으로 이동하여, 주어진 입력 문자열에서 하나 이상의 문자를 소비할 수 있다.
- “실패” 결과: 이 경우에는 입력을 전혀 소비하지 않는다.

> **해설 — 실제 CPython에서는 문자열보다 토큰을 다룬다**
>
> 이 절은 PEG 일반론이라 “문자”와 “입력 문자열”이라고 설명한다. 그러나 뒤에서 설명하듯 CPython의 Pegen은 별도 토크나이저가 만든 토큰 배열을 입력으로 받는다. 따라서 CPython에 적용해 읽을 때는 대체로 `문자`를 `토큰`, `문자열 위치`를 `토큰 인덱스`로 바꾸어 생각하면 된다.
>
> 재귀 하강이라는 말은 `expression()` 함수가 `term()`을 호출하고, `term()`이 다시 `factor()`를 호출하는 식으로 문법의 중첩이 함수 호출의 중첩으로 나타난다는 뜻이다.

“실패” 결과가 프로그램이 잘못되었다는 뜻은 아니며, 파싱 전체가 실패했다는 뜻도 아니다. 선택 연산자에는 순서가 있으므로, 실패는 흔히 단지 “다음 선택지를 시도하라”는 뜻일 뿐이다. PEG 파서를 재귀 하강 파서로 곧바로 구현하면 최악의 경우 실행 시간이 지수적으로 증가한다. PEG 파서에는 무한 룩어헤드가 있기 때문이다. 이는 규칙을 결정하기 전에 임의 개수의 토큰을 살펴볼 수 있다는 뜻이다. 보통 PEG 파서는 [“팩랫 파싱(packrat parsing)”](https://pdos.csail.mit.edu/~baford/packrat/thesis/)이라는 기법을 사용하여 이 지수 시간 복잡도를 피한다. 팩랫 파싱은 파싱을 시작하기 전에 프로그램 전체를 메모리에 올릴 뿐 아니라, 파서가 제한 없이 백트래킹할 수 있게 한다. 각 입력 위치에서 이미 매치한 규칙을 메모이제이션하면 이 과정을 효율적으로 만들 수 있다. 메모이제이션 캐시의 대가는 파서가 보통 테이블 기반인 단순 `LL(1)` 파서보다 자연스럽게 더 많은 메모리를 사용한다는 점이다.

> **해설 — 백트래킹, 지수 시간, 팩랫 파싱**
>
> 선택지 하나가 뒤늦게 실패하면 파서는 이전 입력 위치로 돌아가 다른 선택지를 시도한다. 이것이 백트래킹이다. 여러 규칙이 중첩되어 같은 구간을 여러 방식으로 다시 파싱하면, 동일한 계산이 폭발적으로 반복될 수 있다.
>
> 메모이제이션은 `(규칙, 입력 위치) → 결과`를 저장한다. 예를 들어 `expr` 규칙을 토큰 17에서 이미 시도했다면, 다시 같은 요청이 왔을 때 함수를 재실행하지 않고 저장된 성공·실패 결과와 종료 위치를 돌려준다.
>
> ```text
> memo[(expr, 17)] = 성공, 다음 위치 26, 생성된 AST
> ```
>
> 모든 위치와 규칙을 캐시하는 전형적인 팩랫 파서는 이론적으로 선형 시간 파싱을 제공하지만 메모리를 더 쓴다. CPython은 뒤의 “메모이제이션” 절에서 설명하듯 실제로는 성능을 위해 모든 규칙을 무조건 캐시하지 않는다.

#### 핵심 개념

- 대안에는 순서가 있다(`A | B`는 `B | A`와 같지 않다).
- 어떤 규칙이 실패를 반환해도 파싱 전체가 실패한 것은 아니다. 이는 단지 “다른 것을 시도하라”는 뜻이다.
- 기본적인 PEG 파서는 지수 시간에 실행되지만, 메모이제이션을 사용하면 선형 시간으로 최적화할 수 있다.
- 파싱이 완전히 실패하면, 즉 입력 텍스트 전체를 파싱하는 규칙이 하나도 성공하지 못하면 PEG 파서 자체에는 “[`SyntaxError`](https://docs.python.org/3/library/exceptions.html#SyntaxError)가 어디에 있는가”라는 개념이 없다.

> **해설 — 마지막 항목이 중요한 이유**
>
> 어떤 하위 규칙의 실패는 정상적인 선택지 탐색일 수 있다. 따라서 “처음 실패한 곳”이나 “가장 최근에 실패한 곳”을 곧바로 문법 오류 위치로 볼 수 없다. CPython은 뒤에서 설명하는 “가장 멀리 진행했다가 실패한 토큰” 휴리스틱과 `invalid_` 규칙을 함께 사용해 사람이 이해할 만한 오류 위치와 메시지를 만든다.

> [!IMPORTANT]
> PEG 문법을 [EBNF](https://en.wikipedia.org/wiki/Extended_Backus–Naur_form)나 문맥 자유 문법과 같은 방식으로 추론하려 하지 말라. PEG는 입력 문자열을 **어떻게** 파싱할지를 기술하는 데 최적화되어 있다. 반면 문맥 자유 문법은 자신이 기술하는 언어의 문자열을 생성하는 데 최적화되어 있다. EBNF에서는 어떤 문자열이 해당 언어에 속하는지 문법만 보고 즉시 알기 어려우므로, 이를 알아내기 위한 작업이 필요하다.

> **해설 — 인식기 관점과 생성기 관점**
>
> CFG/EBNF의 `A | B`는 대체로 “A로 만들 수 있거나 B로 만들 수 있는 문자열의 집합”을 뜻한다. PEG의 `A | B`는 “현재 위치에서 A를 먼저 실행하고, 실패했을 때만 B를 실행하라”는 절차다. 겉모양이 비슷해도 전자는 언어를 수학적으로 기술하는 관점이고, 후자는 입력을 인식하는 알고리즘에 가까운 관점이다.

#### 순서 있는 선택 연산자의 결과

PEG는 EBNF처럼 보일 수 있지만 의미는 상당히 다르다. PEG 문법에서 대안에 순서가 있다는 사실은 PEG 파서 작동 방식의 핵심이며, 모호성을 없애는 것 외에도 큰 영향을 미친다.

어떤 규칙에 두 대안이 있고 첫 번째 대안이 성공하면, 호출한 상위 규칙이 나머지 입력을 파싱하지 못하더라도 두 번째 대안은 **시도하지 않는다**. 그래서 이 파서를 “즉시 확정적(eager)”이라고 한다. 이를 설명하기 위해 다음 두 규칙을 보자. 이 예제에서 토큰 하나는 문자 하나다.

```
    first_rule:  ( 'a' | 'aa' ) 'a'
    second_rule: ('aa' | 'a'  ) 'a'
```

일반적인 EBNF 문법에서는 두 규칙 모두 `{aa, aaa}`라는 언어를 나타낸다. 그러나 PEG에서는 둘 중 한 규칙이 문자열 `aaa`를 받아들이고 `aa`는 받아들이지 않으며, 다른 규칙은 그 반대로 `aa`를 받아들이고 `aaa`는 받아들이지 않는다. `('a'|'aa')'a'` 규칙은 `aaa`를 받아들이지 않는다. `'a'|'aa'`가 첫 번째 `a`를 소비하고, 규칙 마지막의 `a`가 두 번째 `a`를 소비하여 세 번째 `a`가 남기 때문이다. 해당 선택 부분은 이미 성공했으므로, `'a'|'aa'`가 두 번째 대안을 시도하도록 되돌아가는 일은 없다. `('aa'|'a')'a'` 표현식은 `aa`를 받아들이지 않는다. `'aa'|'a'`가 `aa` 전체를 받아들여 마지막 `a`가 소비할 입력을 하나도 남기지 않기 때문이다. 이때도 `'aa'|'a'`의 두 번째 대안은 시도하지 않는다.

> **해설 — 실패가 어느 범위까지 되돌림을 일으키는가**
>
> 괄호 안의 선택 `('a' | 'aa')`은 `'a'`가 성공하는 즉시 확정된다. 뒤의 최종 `'a'`까지 포함한 더 큰 규칙이 나중에 문제를 겪더라도, 이미 성공한 내부 선택을 다시 열어 보지 않는다. PEG의 순서 있는 선택은 정규표현식 엔진의 모든 백트래킹 동작과 같다고 가정하면 안 된다.
>
> 또한 일반적으로 시작 규칙은 입력 끝(`ENDMARKER`)까지 소비해야 성공한 것으로 본다. 그래서 `first_rule`이 `aaa`의 앞 두 글자만 소비한 상태는 전체 입력의 성공이 아니다.
>
> | 규칙 | `aa` | `aaa` |
> | --- | --- | --- |
> | <code>('a' &#124; 'aa') 'a'</code> | 성공 | 실패 |
> | <code>('aa' &#124; 'a') 'a'</code> | 실패 | 성공 |
>
> 입력 끝까지 소비해야 성공이라고 볼 때의 결과다. 첫 규칙은 짧은 `'a'`를 먼저 선택하고, 둘째 규칙은 가능한 경우 긴 `'aa'`를 먼저 선택한다. 한번 성공한 선택은 뒤에서 문제가 생겨도 바뀌지 않는다.

> [!CAUTION]
> 위 예처럼 순서 있는 선택이 일으키는 효과는 여러 단계의 규칙 아래에 숨어 있을 수 있다.

따라서 한 대안이 다음 대안에 포함되는 형태로 규칙을 작성하는 것은 거의 언제나 실수다. 예를 들면 다음과 같다.

```
    my_rule:
      | 'if' expression 'then' block
      | 'if' expression 'then' block 'else' block
```

이 예제에서는 첫 번째 대안이 먼저 성공하므로 두 번째 대안은 절대 시도되지 않는다. 입력 문자열 뒤에 `'else' block`이 이어지더라도 마찬가지다. 이 규칙을 올바르게 작성하려면 순서만 바꾸면 된다.

```
    my_rule:
      | 'if' expression 'then' block 'else' block
      | 'if' expression 'then' block
```

이 경우 입력 문자열에 `'else' block`이 없으면 첫 번째 대안이 실패하고 두 번째 대안을 시도한다.

> **해설 — 긴 대안을 먼저 두는 실전 규칙**
>
> 공통 접두사가 있을 때는 보통 더 구체적이고 긴 대안을 먼저 두고, 짧고 일반적인 대안을 뒤에 둔다. 다만 단순히 길이만 비교하는 기계적인 법칙은 아니다. 실제로 앞 대안이 어디까지 성공한 것으로 확정되는지와 `~`(cut)의 위치까지 함께 살펴야 한다.

### 문법 구문

문법은 다음 형태의 규칙들이 이어진 구조로 이루어진다.

```
    rule_name: expression
```

선택적으로 규칙 이름 바로 뒤에 타입을 포함할 수 있다. 이 타입은 해당 규칙에 대응하는 C 또는 Python 함수의 반환 타입을 지정한다.

```
    rule_name[return_type]: expression
```

반환 타입을 생략하면 C에서는 `void *`, Python에서는 `Any`를 반환한다.

> **해설 — 규칙은 값을 반환한다**
>
> Pegen 규칙은 단지 입력의 참·거짓만 판정하지 않는다. 성공하면 토큰, 하위 규칙의 결과, 또는 생성한 AST 노드를 반환할 수 있다. C 파서에서는 정적 타입이 필요하므로 `expr_ty`, `stmt_ty` 같은 반환 타입을 문법에 적는다.

#### 문법 표현식

| 표현식 | 설명과 예 |
|---|---|
| `# comment` | Python 방식의 주석이다. |
| `e1 e2` | `e1`을 매치한 다음 `e2`를 매치한다.<br>`rule_name: first_rule second_rule` |
| `e1 \| e2` | `e1` 또는 `e2`를 매치한다.<br>`rule_name[return_type]:`<br>`    \| first_alt`<br>`    \| second_alt` |
| `( e )` | 그룹화 연산자다. `e`를 매치한다.<br>`rule_name: (e)`<br>`rule_name: (e1 e2)*` |
| `[ e ]` 또는 `e?` | 선택적으로 `e`를 매치한다.<br>`rule_name: [e]`<br>`rule_name: e (',' e)* [',']` |
| `e*` | `e`가 0번 이상 나타나는 것을 매치한다.<br>`rule_name: (e1 e2)*` |
| `e+` | `e`가 1번 이상 나타나는 것을 매치한다.<br>`rule_name: (e1 e2)+` |
| `s.e+` | 구분자 `s`로 나뉜 `e`가 1번 이상 나타나는 것을 매치한다.<br>`rule_name: ','.e+` |
| `&e` | 긍정 룩어헤드다. 입력을 소비하지 않고 `e`를 파싱할 수 있으면 성공한다. |
| `!e` | 부정 룩어헤드다. 입력을 소비하지 않고 `e`를 파싱할 수 있으면 실패한다.<br>`primary: atom !'.' !'(' !'['` |
| `~` | 파싱에 실패하더라도 현재 대안으로 확정한다(cut).<br>`rule_name: '(' ~ some_rule ')' \| some_alt` |

> **해설 — 반복과 구분 목록**
>
> `','.e+`는 `e (',' e)*`와 비슷하지만, 결과에는 보통 구분자인 쉼표가 아니라 `e`의 결과만 모인다. 예를 들어 `NAME`을 `a,b,c`에 적용하면 이름 세 개의 시퀀스를 얻는다.
>
> `e*`는 아무것도 매치하지 않아도 성공하지만 `e+`는 최소 한 번 성공해야 한다.

> **해설 — 룩어헤드**
>
> 룩어헤드는 현재 입력 위치를 움직이지 않는 검사다.
>
> - `&e`: “다음 입력이 `e` 모양인지 확인만 하라.”
> - `!e`: “다음 입력이 `e` 모양이면 안 된다.”
>
> 예제 `atom !'.' !'(' !'['`는 `atom` 뒤에 속성 접근(`.`), 호출(`(`), 인덱싱(`[`처럼 primary 표현식을 계속 확장하는 문자가 오지 않는지 확인한다. 정확한 규칙의 전체 문맥에 따라 의미는 달라지지만, 핵심은 토큰을 소비하지 않고 경계를 판정한다는 점이다.

> **해설 — cut(`~`)**
>
> `~`를 지난 뒤 실패하면 같은 규칙의 다른 대안으로 돌아가지 않는다. 예를 들어 여는 괄호까지 봐서 특정 구조임이 충분히 확실해진 뒤에는, 내부 오류를 다른 대안으로 숨기지 않고 그 구조의 오류로 보고할 수 있다. 탐색 공간을 줄여 성능을 높이거나 더 정확한 오류를 내는 데 유용하지만, 너무 일찍 넣으면 원래 유효한 다른 대안을 막을 수 있다.

#### 왼쪽 재귀

PEG 파서는 일반적으로 왼쪽 재귀를 지원하지 않는다. 그러나 CPython의 파서 생성기는 [Medeiros 외](https://arxiv.org/pdf/1207.0443)가 설명한 것과 유사한 기법을 구현하되, 정적 변수 대신 메모이제이션 캐시를 사용한다. 이 접근은 [Warth 외](http://web.cs.ucla.edu/~todd/research/pepm08.pdf)가 설명한 방식에 더 가깝다. 덕분에 단순한 왼쪽 재귀 규칙뿐 아니라 다음처럼 간접적인 왼쪽 재귀가 포함된 더 복잡한 규칙도 작성할 수 있다.

```
    rule1: rule2 | 'a'
    rule2: rule3 | 'b'
    rule3: rule1 | 'c'
```

또한 다음과 같은 “숨은 왼쪽 재귀”도 작성할 수 있다.

```
    rule: 'optional'? rule '@' some_other_rule
```

> **해설 — 왼쪽 재귀가 무엇이고 왜 필요한가**
>
> `expr: expr '+' term | term`처럼 규칙의 맨 왼쪽에서 자기 자신을 다시 호출하면 왼쪽 재귀다. 순진한 재귀 하강 구현은 입력을 한 토큰도 소비하기 전에 `expr()`이 다시 `expr()`을 호출하므로 무한 재귀에 빠진다.
>
> 하지만 왼쪽 재귀는 `1 + 2 + 3`을 `(1 + 2) + 3`처럼 왼쪽 결합으로 표현하기 자연스럽다. Pegen은 메모이제이션된 결과를 씨앗(seed)으로 두고, 더 긴 매치가 나오지 않을 때까지 결과를 성장시키는 계열의 알고리즘으로 이를 처리한다.
>
> 간접 왼쪽 재귀는 `rule1 → rule2 → rule3 → rule1`처럼 여러 규칙을 거쳐 자신으로 돌아오는 경우다. 숨은 왼쪽 재귀는 앞의 선택적 표현식이 입력을 하나도 소비하지 않을 수 있어 실질적으로 자기 호출이 맨 앞에 놓이는 경우다.

#### 문법의 변수

하위 표현식 앞에 식별자와 `=` 기호를 붙여 이름을 지정할 수 있다. 다음처럼 지정한 이름은 액션에서 사용할 수 있다. 액션은 다음 절에서 설명한다.

```
    rule_name[return_type]: '(' a=some_other_rule ')' { a }
```

> **해설**
>
> `a=some_other_rule`의 `a`는 Python 소스 코드에 등장해야 하는 변수가 아니다. 파서 생성기가 만든 함수 안에서 하위 규칙의 반환값을 붙잡아 두는 로컬 변수에 가깝다. 이 예제는 괄호 자체가 아니라 괄호 안 `some_other_rule`의 결과를 반환한다.

#### 문법 액션

PEG 파서는 문법과 AST 생성 사이의 관계를 가리는 중간 단계를 피하기 위해 문법 액션을 통해 규칙에서 AST 노드를 직접 생성할 수 있게 한다. 문법 액션은 문법 규칙을 성공적으로 파싱했을 때 평가되는, 대상 언어에 특화된 표현식이다. 파서 생성기가 어떤 출력을 만들게 할 것인지에 따라 이 표현식을 Python이나 C로 작성할 수 있다. 이는 Python 파서 하나와 C 파서 하나를 만들고 싶다면 문법 파일도 두 개 작성해야 한다는 뜻이다. 두 파일은 액션 집합만 서로 다르고, 액션 이외의 모든 내용은 동일하게 유지해야 한다. Python 액션을 사용한 문법의 예로, 문법 파일을 파싱하는 파서 생성기 부분은 Python 액션을 담은 메타 문법 파일로부터 부트스트랩된다. 이 액션들은 파싱 결과로 문법 트리를 생성한다.

> **해설 — 액션과 부트스트랩**
>
> 문법의 오른쪽에 `{ ... }`로 적는 액션은 매치에 성공했을 때 실행할 값 생성 코드다. C 파서를 생성하는 문법이라면 액션도 C 표현식이고, Python 파서를 생성하는 문법이라면 Python 표현식이다.
>
> “메타 문법”은 Python 프로그램의 문법이 아니라 `.gram` 문법 파일 자체의 문법이다. “부트스트랩”은 Pegen이 자신이 읽을 문법 형식을 Pegen 문법으로 정의하고, 그 정의로 문법 파일 파서를 만들어 자기 자신을 떠받치는 구조를 말한다.
>
> ```text
> metagrammar.gram
>     ↓ 이미 생성된 메타 파서가 읽음
> 새 메타 파서
>     ↓ python.gram을 읽음
> Python 소스 파서
> ```

Python용 PEG 문법의 구체적인 경우, 액션을 사용하면 AST가 어떻게 구성되는지를 문법 자체에서 직접 서술할 수 있으므로 더 명확하고 유지보수하기 쉬워진다. 이 AST 생성 과정은 공통적인 AST 객체 조작과 문법에 직접 관련되지 않은 다른 필수 작업을 뽑아낸 여러 도우미 함수의 지원을 받는다.

각 대안 뒤의 중괄호 안에 액션 코드를 붙여 액션을 표시한다. 이 코드는 해당 대안의 반환값을 지정한다.

```
    rule_name[return_type]:
       | first_alt1 first_alt2 { first_alt1 }
       | second_alt1 second_alt2 { second_alt1 }
```

액션을 생략하면 기본 액션이 생성된다.

- 규칙에 이름이 하나만 있으면 그 값을 반환한다.
- 규칙에 이름이 여러 개 있으면 파싱한 모든 표현식을 담은 컬렉션을 반환한다. 컬렉션 타입은 C와 Python에서 서로 다르다.

이 기본 동작은 주로 매우 단순한 상황과 디버깅 용도로 마련된 것이다.

> [!WARNING]
> 액션은 다른 규칙을 참조하는 변수를 통해 전달받은 AST 노드를 변경해서는 안 된다. 변경을 허용하지 않는 이유는 AST 노드가 메모이제이션으로 캐시되어, 해당 변경이 유효하지 않은 다른 문맥에서 재사용될 가능성이 있기 때문이다. 액션에서 AST 노드를 변경해야 한다면, 그 노드의 새 복사본을 만든 뒤 복사본을 변경해야 한다.

> **해설 — 캐시에 AST도 들어간다**
>
> 메모이제이션 결과에는 단순한 성공 여부뿐 아니라 규칙이 반환한 AST 노드도 포함될 수 있다. 같은 `(규칙, 위치)` 결과가 여러 탐색 경로에서 공유되므로 한 액션이 그 객체를 제자리에서 바꾸면 다른 경로의 결과까지 오염된다. 함수형 프로그래밍에서 불변 값을 다루듯 기존 노드는 읽기만 하고, 변형이 필요하면 새 노드를 만들어야 한다.

PEG 생성기가 지원하는 문법의 전체 메타 문법은 다음과 같다.

```
    start[Grammar]: grammar ENDMARKER { grammar }

    grammar[Grammar]:
        | metas rules { Grammar(rules, metas) }
        | rules { Grammar(rules, []) }

    metas[MetaList]:
        | meta metas { [meta] + metas }
        | meta { [meta] }

    meta[MetaTuple]:
        | "@" NAME NEWLINE { (name.string, None) }
        | "@" a=NAME b=NAME NEWLINE { (a.string, b.string) }
        | "@" NAME STRING NEWLINE { (name.string, literal_eval(string.string)) }

    rules[RuleList]:
        | rule rules { [rule] + rules }
        | rule { [rule] }

    rule[Rule]:
        | rulename ":" alts NEWLINE INDENT more_alts DEDENT {
                Rule(rulename[0], rulename[1], Rhs(alts.alts + more_alts.alts)) }
        | rulename ":" NEWLINE INDENT more_alts DEDENT { Rule(rulename[0], rulename[1], more_alts) }
        | rulename ":" alts NEWLINE { Rule(rulename[0], rulename[1], alts) }

    rulename[RuleName]:
        | NAME '[' type=NAME '*' ']' {(name.string, type.string+"*")}
        | NAME '[' type=NAME ']' {(name.string, type.string)}
        | NAME {(name.string, None)}

    alts[Rhs]:
        | alt "|" alts { Rhs([alt] + alts.alts)}
        | alt { Rhs([alt]) }

    more_alts[Rhs]:
        | "|" alts NEWLINE more_alts { Rhs(alts.alts + more_alts.alts) }
        | "|" alts NEWLINE { Rhs(alts.alts) }

    alt[Alt]:
        | items '$' action { Alt(items + [NamedItem(None, NameLeaf('ENDMARKER'))], action=action) }
        | items '$' { Alt(items + [NamedItem(None, NameLeaf('ENDMARKER'))], action=None) }
        | items action { Alt(items, action=action) }
        | items { Alt(items, action=None) }

    items[NamedItemList]:
        | named_item items { [named_item] + items }
        | named_item { [named_item] }

    named_item[NamedItem]:
        | NAME '=' ~ item {NamedItem(name.string, item)}
        | item {NamedItem(None, item)}
        | it=lookahead {NamedItem(None, it)}

    lookahead[LookaheadOrCut]:
        | '&' ~ atom {PositiveLookahead(atom)}
        | '!' ~ atom {NegativeLookahead(atom)}
        | '~' {Cut()}

    item[Item]:
        | '[' ~ alts ']' {Opt(alts)}
        |  atom '?' {Opt(atom)}
        |  atom '*' {Repeat0(atom)}
        |  atom '+' {Repeat1(atom)}
        |  sep=atom '.' node=atom '+' {Gather(sep, node)}
        |  atom {atom}

    atom[Plain]:
        | '(' ~ alts ')' {Group(alts)}
        | NAME {NameLeaf(name.string) }
        | STRING {StringLeaf(string.string)}

    # Mini-grammar for the actions

    action[str]: "{" ~ target_atoms "}" { target_atoms }

    target_atoms[str]:
        | target_atom target_atoms { target_atom + " " + target_atoms }
        | target_atom { target_atom }

    target_atom[str]:
        | "{" ~ target_atoms "}" { "{" + target_atoms + "}" }
        | NAME { name.string }
        | NUMBER { number.string }
        | STRING { string.string }
        | "?" { "?" }
        | ":" { ":" }
```

> **해설 — 이 메타 문법을 읽는 방법**
>
> 전체를 외울 필요는 없다. 앞에서 배운 표기법이 실제로 그 표기법 자체를 정의하는 데 쓰인다는 점만 확인하면 된다.
>
> - `rule`은 `규칙 이름 : 대안들`이라는 `.gram` 한 규칙을 읽고 `Rule(...)` 객체를 만든다.
> - `rulename`은 `NAME`, `NAME[type]`, `NAME[type*]` 형태를 읽는다.
> - `alt`, `items`, `named_item`은 대안 안의 항목들과 `name=item` 바인딩을 읽는다.
> - `lookahead`는 `&`, `!`, `~`를 각각 객체로 바꾼다.
> - `item`은 `?`, `*`, `+`, `s.e+` 표기법을 객체로 바꾼다.
> - 마지막의 미니 문법은 `{ ... }` 안의 액션 텍스트를 모은다.
>
> 즉 이 코드 블록의 출력은 Python 프로그램 AST가 아니라 “문법 파일의 AST”다.

설명을 위한 예로, 다음과 같은 단순한 문법 파일만으로 간단한 산술 표현식을 파싱하고 유효한 C 기반 Python AST를 반환하는 완전한 파서를 직접 생성할 수 있다.

```
    start[mod_ty]: a=expr_stmt* ENDMARKER { _PyAST_Module(a, NULL, p->arena) }
    expr_stmt[stmt_ty]: a=expr NEWLINE { _PyAST_Expr(a, EXTRA) }

    expr[expr_ty]:
        | l=expr '+' r=term { _PyAST_BinOp(l, Add, r, EXTRA) }
        | l=expr '-' r=term { _PyAST_BinOp(l, Sub, r, EXTRA) }
        | term

    term[expr_ty]:
        | l=term '*' r=factor { _PyAST_BinOp(l, Mult, r, EXTRA) }
        | l=term '/' r=factor { _PyAST_BinOp(l, Div, r, EXTRA) }
        | factor

    factor[expr_ty]:
        | '(' e=expr ')' { e }
        | atom

    atom[expr_ty]:
        | NAME
        | NUMBER
```

> **해설 — 이 문법이 연산자 우선순위와 결합 방향을 만드는 방법**
>
> `expr`은 덧셈·뺄셈을 처리하고 오른쪽 피연산자로 더 높은 우선순위의 `term`을 요구한다. `term`은 곱셈·나눗셈을 처리하고 더 높은 우선순위의 `factor`를 요구한다. 따라서 `1 + 2 * 3`에서 곱셈이 먼저 묶인다.
>
> `expr: expr '+' term`과 `term: term '*' factor`는 왼쪽 재귀이므로 같은 우선순위의 연산은 왼쪽 결합한다. `1 - 2 - 3`은 `1 - (2 - 3)`이 아니라 `(1 - 2) - 3`이 된다.
>
> 액션 `_PyAST_BinOp(l, Add, r, EXTRA)`는 토큰을 단순히 인식하는 데 그치지 않고, 왼쪽 노드 `l`과 오른쪽 노드 `r`를 자식으로 갖는 이항 연산 AST를 즉시 만든다.

여기서 `EXTRA`는 `start_lineno, start_col_offset, end_lineno, end_col_offset, p->arena`로 확장되는 매크로다. 이 변수들은 파서가 자동으로 주입한다. `p`는 파서의 모든 상태를 보관하는 객체를 가리킨다.

> **해설 — 위치 정보와 arena**
>
> 줄·열 시작/끝 위치는 오류 표시, 디버깅, `ast` 모듈 등에 필요하다. `p->arena`는 파싱 중 생성한 여러 C 객체의 수명을 한꺼번에 관리하는 arena 할당자다. 개별 AST 노드마다 해제 시점을 복잡하게 추적하는 대신, 파싱 작업이 끝날 때 arena 단위로 메모리를 관리한다.

Python AST 객체를 대상으로 작성한 비슷한 문법은 다음과 같다.

```
    start[ast.Module]: a=expr_stmt* ENDMARKER { ast.Module(body=a or [] }
    expr_stmt: a=expr NEWLINE { ast.Expr(value=a, EXTRA) }

    expr:
        | l=expr '+' r=term { ast.BinOp(left=l, op=ast.Add(), right=r, EXTRA) }
        | l=expr '-' r=term { ast.BinOp(left=l, op=ast.Sub(), right=r, EXTRA) }
        | term

    term:
        | l=term '*' r=factor { ast.BinOp(left=l, op=ast.Mult(), right=r, EXTRA) }
        | l=term '/' r=factor { ast.BinOp(left=l, op=ast.Div(), right=r, EXTRA) }
        | factor

    factor:
        | '(' e=expr ')' { e }
        | atom

    atom:
        | NAME
        | NUMBER
```

> **해설**
>
> 문법의 구조는 C 대상 버전과 같고 액션만 Python `ast` 객체 생성식으로 바뀌었다. 원문 첫 줄의 `{ ast.Module(body=a or [] }`에는 닫는 괄호 `)`가 빠진 것으로 보인다. 원문 보존을 위해 코드 블록은 그대로 두었으며, 의도한 형태는 `{ ast.Module(body=a or []) }`로 추정된다.

### Pegen

Pegen은 CPython에서 인터프리터가 사용하는 최종 PEG 파서를 만들기 위해 사용하는 파서 생성기다. Pegen은 [`Grammar/python.gram`](https://github.com/python/cpython/blob/3.14/Grammar/python.gram)에 있는 Python 문법을 읽어 최종 C 파서를 생성하는 프로그램이다. Pegen은 다음 요소로 구성된다.

- 문법 파일을 읽어, 그 문법을 파싱할 수 있는 Python 또는 C로 작성된 PEG 파서를 생성하는 파서 생성기. 생성기는 [`Tools/peg_generator/pegen`](https://github.com/python/cpython/tree/3.14/Tools/peg_generator/pegen)에 있다.
- 파서 생성기 자체에서 사용하는 Python 파서를 자동으로 생성하는 PEG 메타 문법. 이는 수작업으로 작성한 파서가 하나도 없다는 뜻이다. 메타 문법은 [`Tools/peg_generator/pegen/metagrammar.gram`](https://github.com/python/cpython/blob/3.14/Tools/peg_generator/pegen/metagrammar.gram)에 있다.
- 파서 생성기를 사용해 생성되었으며 C 및 Python AST 객체를 직접 만들 수 있는 파서.

> **해설 — 세 구성 요소의 관계**
>
> “파서 생성기”와 “생성된 파서”를 구분해야 한다.
>
> ```text
> Pegen 생성기 프로그램
> ├─ metagrammar.gram → 문법 파일(.gram)을 읽는 메타 파서
> └─ python.gram      → Python 소스를 읽는 C 파서
> ```
>
> 첫 번째 결과는 Pegen의 입력 언어를 읽고, 두 번째 결과는 Python 언어를 읽는다. 둘 다 같은 생성기 기술을 사용한다.

Pegen의 소스 코드는 [`Tools/peg_generator/pegen`](https://github.com/python/cpython/tree/3.14/Tools/peg_generator/pegen)에 있지만, 파서 생성기와 상호작용하는 일반적인 명령은 보통 최상위 Makefile을 통해 실행한다.

#### 파서를 다시 생성하는 방법

문법 파일을 변경한 뒤 인터프리터가 사용하는 `C` 파서를 다시 생성하려면 다음 명령만 실행하면 된다.

```shell
$ make regen-pegen
```

이 명령은 최상위 디렉터리의 `Makefile`을 사용해 실행한다. Windows에서는 Visual Studio 프로젝트 파일을 사용해 파서를 다시 생성하거나 다음 명령을 실행할 수 있다.

```dos
PCbuild/build.bat --regen
```

생성된 파서 파일은 [`Parser/parser.c`](https://github.com/python/cpython/blob/3.14/Parser/parser.c)에 있다.

> **해설**
>
> 작업 흐름은 `python.gram`을 수정하고 `make regen-pegen`으로 `parser.c`를 갱신한 뒤, 생성 파일까지 함께 검토·테스트하는 방식이다. 생성된 `parser.c`를 직접 수정하면 다음 재생성 때 변경이 사라지고 문법 원본과도 불일치하게 된다.

#### 메타 파서를 다시 생성하는 방법

메타 문법, 즉 문법 파일 자체의 문법을 설명하는 문법은 [`Tools/peg_generator/pegen/metagrammar.gram`](https://github.com/python/cpython/blob/3.14/Tools/peg_generator/pegen/metagrammar.gram)에 있다. 이 파일을 수정해야 할 가능성은 매우 낮다. 하지만 새로운 Pegen 기능을 구현하기 위해 이 파일을 수정했다면, 문법 파일을 파싱하는 파서인 메타 파서를 다시 생성해야 한다. 다음 명령만 실행하면 된다.

```shell
$ make regen-pegen-metaparser
```

Windows에서는 Visual Studio 프로젝트 파일을 사용해 파서를 다시 생성하거나 다음 명령을 실행할 수 있다.

```dos
PCbuild/build.bat --regen
```

> **해설**
>
> `regen-pegen`은 Python 언어 문법이 바뀔 때 쓰고, `regen-pegen-metaparser`는 `.gram` 파일에서 사용할 수 있는 표기 자체를 바꿀 때 쓴다. 예를 들어 Python에 새 문(statement)을 추가하는 일은 전자이고, Pegen 문법에 새로운 연산자를 추가하는 일은 후자다.

#### 문법 요소와 규칙

Pegen에는 몇 가지 특별한 문법 요소와 규칙이 있다.

- 작은따옴표(`'`)로 둘러싼 문자열(예: `'class'`)은 키워드(`KEYWORD`)를 나타낸다.
- 큰따옴표(`"`)로 둘러싼 문자열(예: `"match"`)은 소프트 키워드(`SOFT KEYWORD`)를 나타낸다.
- 대문자 이름(예: `NAME`)은 [`Grammar/Tokens`](https://github.com/python/cpython/blob/3.14/Grammar/Tokens) 파일에 정의된 토큰을 나타낸다.
- 이름이 `invalid_`로 시작하는 규칙은 특화된 문법 오류를 만드는 데 사용한다.

  - 이 규칙들은 파서의 첫 번째 패스에서는 사용하지 **않는다**.
  - 첫 번째 패스의 파싱이 실패한 경우에만 invalid 규칙을 포함한 두 번째 패스를 실행한다.
  - 두 번째 단계에서 파서가 일반적인 문법 오류와 함께 실패하면 첫 번째 패스의 일반 실패 위치를 사용한다. 이렇게 하면 invalid 규칙 때문에 잘못된 위치가 보고되는 것을 피할 수 있다.
  - 다른 모든 PEG 규칙과 마찬가지로 invalid 규칙이 포함된 대안의 순서도 중요하다.

> **해설**
>
> 이 목록은 `.gram` 파일의 따옴표 종류와 이름의 대소문자가 단순한 스타일이 아니라 의미를 가진다는 뜻이다. `'class'`, `"match"`, `NAME`, `invalid_assignment`는 서로 다른 종류의 문법 요소다. `invalid_` 규칙의 2단계 처리 방식은 뒤의 “문법 오류를 보고하는 방법” 절에서 자세히 설명한다.

#### 토큰화

PEG 파서 프레임워크에서는 파서가 파싱과 토큰화를 모두 담당하는 경우가 흔하지만 Pegen은 그렇지 않다. Python 언어에는 들여쓰기 경계, 호환성을 위한 `ASYNC`와 `AWAIT` 같은 일부 특수 키워드, 닫히지 않은 괄호 같은 백트래킹 오류, 인코딩, 대화형 모드 등을 처리하는 사용자 정의 토크나이저가 필요하기 때문이다. 이 이유 중 일부는 역사적인 사정으로 남아 있으며, 일부는 오늘날에도 유용하다.

> **해설 — Pegen 앞에 별도 토크나이저가 있다**
>
> CPython 파이프라인은 다음처럼 나뉜다.
>
> ```text
> 소스 문자
>   ↓ CPython 전용 토크나이저
> NAME, NUMBER, INDENT, DEDENT, NEWLINE, ...
>   ↓ Pegen으로 생성한 파서
> AST
> ```
>
> 들여쓰기가 블록을 결정하는 Python에서는 `INDENT`와 `DEDENT`를 만드는 작업이 특히 중요하다. 인코딩 선언, 대화형 입력의 불완전한 문장, 괄호가 아직 닫히지 않은 상태 등도 단순한 문자 단위 PEG만으로 처리하기보다 기존 토크나이저 계층에서 다루는 편이 적합하다.

사용할 수 있는 토큰, 즉 문법에 등장하는 모든 대문자 이름의 목록은 [`Grammar/Tokens`](https://github.com/python/cpython/blob/3.14/Grammar/Tokens) 파일에서 찾을 수 있다. 새 토큰을 추가하기 위해 이 파일을 변경했다면 다음 명령을 실행하여 관련 파일을 반드시 다시 생성하라.

```shell
$ make regen-token
```

Windows에서는 Visual Studio 프로젝트 파일을 사용해 토큰을 다시 생성하거나 다음 명령을 실행할 수 있다.

```dos
PCbuild/build.bat --regen
```

토큰을 생성하는 방법과 이를 지배하는 규칙은 전적으로 토크나이저([`Parser/lexer`](https://github.com/python/cpython/tree/3.14/Parser/lexer)와 [`Parser/tokenizer`](https://github.com/python/cpython/tree/3.14/Parser/tokenizer))가 담당한다. 파서는 토크나이저로부터 토큰을 받기만 한다.

#### 메모이제이션

앞에서 설명했듯 파서의 지수 시간 복잡도를 피하기 위해 메모이제이션을 사용한다.

Python이 사용하는 C 파서는 고도로 최적화되어 있으며, 메모이제이션은 메모리와 실행 시간 모두에서 비용이 클 수 있다. 메모리 비용은 명백하다. 파서는 이전 결과를 캐시에 저장할 메모리가 필요하다. 실행 시간 비용은 주어진 규칙의 캐시 적중 여부를 계속 확인해야 한다는 데서 발생한다. 많은 상황에서는 규칙을 그냥 다시 파싱하는 편이 더 빠를 수 있다. Pegen은 규칙 이름과 타입(있다면) 뒤에 특수 표식 `memo`가 붙은 규칙을 제외하면 메모이제이션을 **기본적으로 비활성화한다**.

```
rule_name[typr] (memo):
  ...
```

소수의 규칙에만 선택적으로 메모이제이션을 켜면 파서가 더 빨라지고 사용하는 메모리도 줄어든다.

> **해설 — 이론과 CPython 실무의 차이**
>
> 앞에서는 팩랫 파싱이 메모이제이션으로 지수 시간을 선형 시간으로 바꾼다고 설명했지만, 실제 프로그램의 성능은 빅오만으로 결정되지 않는다. 짧고 실패가 거의 없는 규칙까지 모두 캐시하면 해시 조회·분기·메모리 할당 비용이 재파싱 비용보다 커질 수 있다. CPython은 측정 결과가 유리한 규칙만 `memo`로 표시하는 절충안을 쓴다.
>
> 원문 예제의 `typr`는 `type`의 오타로 보인다. 코드 블록은 원문대로 보존했다.

> [!NOTE]
> 왼쪽 재귀 규칙은 항상 메모이제이션을 사용한다. 왼쪽 재귀 구현 자체가 메모이제이션에 의존하기 때문이다.

새 규칙에 메모이제이션이 필요한지 판단하려면 벤치마크가 필요하다. 메모이제이션을 켠 경우와 끈 경우에 상당히 큰 파일 몇 개의 실행 시간과 메모리 사용량을 비교해야 한다. 생성된 C 파서 코드에는 각 규칙이 메모이제이션을 얼마나 사용하는지 측정할 수 있는 매우 단순한 계측 API가 마련되어 있다. 자세한 내용은 [`Parser/pegen.c`](https://github.com/python/cpython/blob/3.14/Parser/pegen.c)를 참고하라. 단, 이 API는 수동으로 활성화해야 한다.

> **해설 — “필요한지는 벤치마크로 결정”**
>
> 캐시 적중률만 높다고 반드시 빠른 것은 아니다. 시간뿐 아니라 최고 메모리 사용량과 여러 종류의 입력을 함께 비교해야 한다. 작은 합성 예제보다 실제로 큰 Python 소스 파일 묶음을 측정 대상으로 삼으라는 의미다.

#### 자동 변수

액션을 더 쉽게 작성할 수 있도록 Pegen은 액션을 작성할 때 사용할 수 있는 네임스페이스에 몇 가지 자동 변수를 주입한다. C 파서에서 사용하는 자동 변수 이름에는 다음이 있다.

- `p`: 파서 구조체.
- `EXTRA`: `(_start_lineno, _start_col_offset, _end_lineno, _end_col_offset, p->arena)`로 확장되는 매크로. 거의 모든 AST 생성자가 이 속성들을 요구하므로, 보통 AST 노드를 만들 때 사용한다. 모든 위치 변수는 현재 토큰의 위치 정보에서 가져온다.

> **해설**
>
> 문법 액션에서 매번 위치 필드 다섯 개를 반복해서 적지 않도록 `EXTRA`가 축약 표기 역할을 한다. `p`에는 현재 토큰 위치, 오류 상태, 메모이제이션 캐시, arena 등 파싱 작업 전반의 상태가 연결된다.

#### 하드 키워드와 소프트 키워드

> [!NOTE]
> 문법 파일에서 키워드는 **작은따옴표**로 정의하고(예: `'class'`), 소프트 키워드는 **큰따옴표**로 정의한다(예: `"match"`).

Pegen 문법에서는 *하드* 키워드와 *소프트* 키워드라는 두 종류의 키워드를 사용할 수 있다. 하드 키워드는 문법적으로 말이 되지 않는 위치에서도 항상 예약어라는 점에서 소프트 키워드와 다르다. 예를 들어 `x = class + 1`에서 `class`는 예약어다. 반면 소프트 키워드는 특정 문맥에서만 특별한 의미를 얻는다. 하드 키워드를 변수로 사용하려 하면 언제나 실패한다.

```pycon
>>> class = 3
File "<stdin>", line 1
    class = 3
        ^
SyntaxError: invalid syntax
>>> foo(class=3)
File "<stdin>", line 1
    foo(class=3)
        ^^^^^
SyntaxError: invalid syntax
```

반면 소프트 키워드는 키워드로 정의된 문맥 이외에서 사용할 때 이런 제한이 없다.

```pycon
>>> match = 45
>>> foo(match="Yeah!")
```

`match`와 `case`는 소프트 키워드다. 따라서 각각 match 문이나 case 블록의 시작에서는 키워드로 인식되지만, 다른 위치에서는 변수 이름이나 인수 이름으로 사용할 수 있다.

> **해설 — 소프트 키워드가 필요한 이유**
>
> `match`를 하드 키워드로 추가했다면 새 Python 버전에서 기존의 `match = 45` 코드가 갑자기 문법 오류가 된다. 소프트 키워드는 새 문법을 도입하면서 기존 코드와의 호환성을 지키는 장치다. 파서는 현재 위치가 `match_stmt`가 가능한 문맥일 때만 `"match"`를 키워드로 해석하고, 그렇지 않으면 일반 `NAME`처럼 다룰 수 있다.

Python에서 문법에 정의된 모든 키워드 목록을 가져올 수 있다.

```pycon
>>> import keyword
>>> keyword.kwlist
['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for',
'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or',
'pass', 'raise', 'return', 'try', 'while', 'with', 'yield']
```

소프트 키워드도 마찬가지로 가져올 수 있다.

```pycon
>>> import keyword
>>> keyword.softkwlist
['_', 'case', 'match']
```

> [!CAUTION]
> 소프트 키워드는 관리하기 조금 까다로울 수 있다. PEG 파서의 대안 순서가 작동하는 방식 때문에 의도하지 않은 위치에서도 소프트 키워드가 받아들여질 수 있기 때문이다. 이에 관한 배경은 [순서 있는 선택 연산자의 결과](#순서-있는-선택-연산자의-결과) 절을 참고하라. 일반적으로 대안이 많지 않은 위치에 소프트 키워드를 정의하라.

> **해설**
>
> 소프트 키워드는 일반 이름과 겹치므로 여러 대안의 공통 접두사에 배치하면 먼저 성공한 해석이 이후 해석을 가릴 수 있다. 문법을 작성할 때는 소프트 키워드가 키워드로 해석되는 문맥을 가능한 한 좁게 만들고, 선택지 순서를 실제 입력으로 검증해야 한다.

#### 오류 처리

Pegen으로 생성된 파서가 예외가 발생한 것을 감지하면 파서의 현재 상태와 관계없이 파싱을 **자동으로 중단**하고, 스택을 되감은 뒤 예외를 보고한다. 즉 [규칙 액션](#문법-액션)이 예외를 일으키면 바로 그 지점에서 모든 파싱이 중단된다. 이는 Python C API 함수를 호출하면서 설정된 모든 예외를 올바르게 전파하기 위한 동작이다. [`SyntaxError`](https://docs.python.org/3/library/exceptions.html#SyntaxError) 예외도 여기에 포함되며, 파서는 주로 이 메커니즘을 사용해 사용자 정의 문법 오류 메시지를 보고한다.

> **해설 — 일반적인 규칙 실패와 예외는 다르다**
>
> 규칙의 “실패”는 다음 대안을 시험하라는 정상적인 제어 흐름이지만, “예외”는 복구해서 다른 대안을 시험할 대상이 아니다.
>
> ```text
> 규칙 실패 → 입력 위치 복원 → 다음 대안 시도 가능
> 예외 발생 → 전체 파싱 중단 → 호출 스택을 거슬러 예외 반환
> ```
>
> C API에서 메모리 부족이나 명시적인 `SyntaxError`가 설정되었는데 이를 단순한 매치 실패로 취급하면, 실제 원인을 숨긴 채 엉뚱한 대안을 계속 탐색할 수 있다.

> [!NOTE]
> 토크나이저 오류는 보통 예외를 발생시켜 보고한다. 그러나 닫히지 않은 괄호 같은 일부 특수한 토크나이저 오류는 파서가 아무것도 반환하지 못하고 끝난 뒤에야 보고한다.

> **해설**
>
> 닫히지 않은 괄호는 대화형 모드에서 “오류”가 아니라 “입력이 아직 덜 들어왔다”는 신호일 수도 있다. 토크나이저와 파서의 최종 결과를 함께 본 뒤 적절한 메시지를 선택해야 하는 경우가 있다는 뜻이다.

#### 문법 오류를 보고하는 방법

앞의 [PEG 파서의 작동 방식](#peg-파서의-작동-방식) 절에서 설명했듯 PEG 파서에는 문법의 어느 지점에서 오류가 발생했는지에 대한 명확한 개념이 없다. 문맥 자유 문법에서와 달리 규칙 하나의 실패가 파싱 실패를 뜻하지 않기 때문이다. 따라서 문법에 어떤 구성이 오류라고 명시적으로 선언되어 있지 않다면 일반 오류를 보고하기 위해 휴리스틱을 사용해야 한다.

일반 문법 오류를 보고하기 위해 Pegen은 PEG 파서에서 흔히 사용하는 휴리스틱을 사용한다. *일반적인* 문법 오류의 위치는 매치를 시도했지만 실패한 토큰 중 입력에서 가장 멀리 있는 토큰으로 보고한다. 이는 파싱이 실패하여 파서가 C에서는 `NULL`, Python에서는 `None`을 반환했지만 어떤 예외도 발생하지 않은 경우에만 적용한다.

> **해설 — 가장 멀리 진행한 실패 지점**
>
> 여러 대안을 시도한 기록 중 가장 오른쪽까지 토큰을 소비한 경로가 사용자의 의도에 가장 가까웠을 가능성이 높다고 가정한다.
>
> ```text
> 대안 A: 토큰 12에서 실패
> 대안 B: 토큰 27에서 실패  ← 일반 오류 위치로 선택
> 대안 C: 토큰 19에서 실패
> ```
>
> 이는 증명된 정답이 아니라 경험적으로 잘 작동하는 휴리스틱이다. 문법이 입력을 시험하는 방식에 따라 사람이 기대하는 위치와 달라질 수 있다.

Python 문법은 원래 `LL(1)` 문법으로 작성되었으므로 이 휴리스틱은 매우 높은 확률로 성공한다. 그러나 룩어헤드 같은 일부 PEG 기능은 이 결과에 영향을 줄 수 있다.

> [!CAUTION]
> 긍정 및 부정 룩어헤드는 토큰 매치를 시도하므로 일반 문법 오류의 위치에 영향을 준다. 규칙 사이의 경계에서 룩어헤드를 신중하게 사용하라.

> **해설**
>
> 룩어헤드는 입력을 소비하지 않지만 내부적으로는 앞쪽 토큰들을 시험한다. 그 시험 중의 실패가 “가장 멀리 실패한 토큰” 기록을 갱신하면 실제로 값을 소비한 본 경로보다 오류 위치가 앞이나 뒤로 왜곡될 수 있다.

더 정확한 문법 오류를 만들기 위해 사용자 정의 규칙을 사용한다. 이는 문맥 자유 문법에서도 흔히 사용하는 방식이다. 파서는 특정한 문법 오류를 보고하기 위해 잘못된 것으로 알려진 구문을 의도적으로 받아들이려 시도한다. Pegen 문법에서 이러한 규칙은 `invalid_` 접두사로 시작한다. 이 규칙들의 매치를 평소에도 시도하면 파싱 성능에 영향을 주고, 규칙 순서에 따라 까다로운 경우 올바른 문법 자체에도 영향을 줄 수 있다. 따라서 생성된 파서는 두 단계로 작동한다.

1. 첫 번째 단계에서는 `invalid_` 접두사로 시작하는 규칙을 고려하지 않고 입력 스트림을 파싱한다. 파싱에 성공하면 생성된 AST를 반환하고 두 번째 단계는 건너뛴다.

2. 첫 번째 단계가 실패하면 `invalid_` 접두사로 시작하는 규칙을 포함하여 두 번째 파싱을 시도한다. 설계상 이 시도는 성공할 수 **없으며**, invalid 규칙이 더 구체적이고 정밀한 사용자 정의 문법 오류를 발생시킬 수 있는 특정 상황을 탐지할 기회를 주기 위해서만 실행한다. 이 방식은 오류 보고의 정확성을 얻는 대신 성능을 조금 희생할 수 있게 한다. 입력 텍스트가 잘못되었다는 사실을 이미 알고 있으므로, 실행은 어차피 중단될 것이고 일반적으로 빠르게 처리할 필요가 없다.

> **해설 — invalid 규칙은 “오류 AST”를 만드는 규칙이 아니다**
>
> 두 번째 패스의 목적은 잘못된 입력을 정상적으로 받아들이는 것이 아니라, 잘못된 패턴을 정확히 알아본 순간 `SyntaxError`를 발생시키는 것이다.
>
> ```text
> 1차 패스: 정상 문법만 사용
> ├─ 성공 → AST 반환
> └─ 실패
>     ↓
> 2차 패스: 정상 문법 + invalid_ 규칙
> ├─ invalid_ 규칙이 특정 패턴 감지 → 정밀한 SyntaxError
> └─ 감지 못함 → 1차 패스의 일반 오류 위치 사용
> ```
>
> 올바른 Python 코드에는 두 번째 패스 비용이 전혀 들지 않는다는 것도 핵심이다.

> [!IMPORTANT]
> invalid 규칙을 정의할 때는 다음 사항을 지켜야 한다.
>
> - 모든 사용자 정의 invalid 규칙이 [`SyntaxError`](https://docs.python.org/3/library/exceptions.html#SyntaxError) 또는 그 하위 클래스의 예외를 발생시키는지 확인하라.
> - 올바른 Python 코드를 파싱하는 성능에 영향을 주지 않도록 **모든** invalid 규칙의 이름이 `invalid_` 접두사로 시작하는지 확인하라.
> - invalid 규칙을 도입했을 때 파서가 일반 규칙에 대해 이전과 다르게 동작하지 않는지 확인하라. 자세한 내용은 [PEG 파서의 작동 방식](#peg-파서의-작동-방식) 절을 참고하라.

특화된 문법 오류를 발생시키기 위한 매크로 모음은 [`Parser/pegen.h`](https://github.com/python/cpython/blob/3.14/Parser/pegen.h) 헤더 파일에서 찾을 수 있다. 이 매크로를 사용하면 사용자 정의 오류의 범위도 보고할 수 있으며, 오류가 보고될 때 표시되는 트레이스백에서 해당 범위가 강조된다.

> **해설**
>
> 오류 “위치”가 한 점이라면 오류 “범위”는 시작과 끝 위치다. 예를 들어 잘못된 표현식 전체에 밑줄을 그어 사용자가 어느 부분을 고쳐야 하는지 더 분명히 보여줄 수 있다.

> [!TIP]
> invalid 규칙이 기대한 때에 작동하는지 시험하는 좋은 방법은 유효한 코드 **뒤에** 문법 오류를 넣었을 때도 그 규칙이 발동하는지 확인하는 것이다. 예를 들면 다음과 같다.

```
<valid python code> $ 42
```

위 입력에서는 `$` 문자에서 문법 오류가 발생해야 한다. 규칙이 올바르게 정의되지 않았다면 그렇게 되지 않는다. 또 다른 예로, 더 나은 오류 메시지를 만들기 위해 Python 2 스타일 `print` 문을 매치하는 규칙을 다음처럼 정의했다고 하자.

```
invalid_print: "print" expression
```

이 규칙은 **겉보기에는** 작동한다. `print(something)`은 유효한 코드이므로 파서가 올바르게 파싱하고 두 번째 단계를 실행하지 않기 때문이다. 그러나 `print(something) $ 3`을 파싱하면 첫 번째 패스가 `$` 때문에 실패한다. 두 번째 단계에서는 이 규칙이 `print(something)`을 `print` 뒤에 괄호로 감싼 변수 `something`이 오는 형태로 매치한다. 그 결과 오류가 `$` 문자가 아니라 그 앞부분에서 보고된다.

> **해설 — 이 테스트가 잡아내는 과잉 매치**
>
> invalid 규칙이 유효한 코드의 접두사를 너무 넓게 잡아먹으면, 입력 뒤쪽의 실제 오류보다 먼저 잘못된 진단을 내린다. `print`는 소프트 키워드가 아니며 이 예제의 큰따옴표 표기는 `"print"`를 소프트 키워드처럼 취급한다. 일반 이름으로도 유효한 `print` 호출을 invalid 규칙이 오인할 수 있다는 점까지 보여주는 예다.
>
> 핵심 테스트 패턴은 “이 규칙이 잡으려는 코드 뒤에 명백한 별도 오류를 붙여도, 별도 오류의 위치가 유지되는가?”이다.

#### AST 객체 생성

[문법 파일](https://github.com/python/cpython/blob/3.14/Grammar/python.gram)에서 생성되어 CPython이 사용하는 C 파서의 출력은 C 구조체로 표현된 Python AST 객체다. 즉 문법 파일의 액션은 성공할 때 AST 객체를 생성한다. 이 객체를 직접 구성하는 작업은 상당히 번거로울 수 있으므로, 객체 구성 방법과 컴파일러에서의 사용 방식에 관한 자세한 내용은 [AST 컴파일러 절](https://github.com/python/cpython/blob/3.14/InternalDocs/compiler.md#abstract-syntax-trees-ast)을 참고하라. 그래서 특수한 도우미 함수를 사용한다. 이 함수들은 [`Parser/pegen.h`](https://github.com/python/cpython/blob/3.14/Parser/pegen.h) 헤더 파일에 선언되어 있고 [`Parser/action_helpers.c`](https://github.com/python/cpython/blob/3.14/Parser/action_helpers.c) 파일에 정의되어 있다. 도우미에는 AST 시퀀스를 결합하고, 시퀀스에서 특정 원소를 가져오며, 생성된 트리에 추가 처리를 수행하는 함수들이 포함된다.

> **해설**
>
> 파서의 최종 산출물은 바이트코드가 아니라 AST다. 문법 액션은 `_PyAST_*` 생성자와 도우미를 호출하고, 이후 심볼 테이블과 컴파일러 단계가 이 AST를 받아 바이트코드 쪽으로 진행한다.
>
> 복잡한 리스트 평탄화, 문맥(`Load`/`Store`) 설정, 여러 문법 조각을 한 AST 노드로 합치는 일은 문법 파일에 길게 적기보다 `action_helpers.c`에 이름 있는 함수로 분리한다.

> [!CAUTION]
> 액션은 규칙을 받아들이거나 거부하는 데 **절대로** 사용해서는 안 된다. 매우 일반적인 규칙을 작성한 뒤 생성된 AST를 검사해 유효성을 판단하고 싶을 수 있지만, 그렇게 하면 [공식 문법](https://docs.python.org/3/reference/grammar.html)이 부분적으로 부정확해진다. 공식 문법에는 액션이 포함되지 않기 때문이다. 또한 다른 Python 구현체가 자신의 필요에 맞게 문법을 적용하기도 더 어려워진다.

> **해설 — 인식 조건은 문법에, 객체 생성은 액션에**
>
> `{ ... }` 액션은 매치 성공 후 실행되므로 외부에 공개된 액션 없는 문법만 봐서는 그 안의 추가 거부 조건을 알 수 없다. 그러면 문법 명세와 CPython 실제 동작이 달라진다.
>
> - 문법 규칙: 어떤 토큰열이 유효한 Python인가?
> - 액션: 유효하다고 판정한 토큰열로 어떤 AST 값을 만들 것인가?
>
> 이 경계를 지켜야 공식 문법이 독립적인 명세로 남고 PyPy, RustPython 같은 다른 구현체도 같은 문법을 재사용할 수 있다.

일반적으로 액션이 여러 줄에 걸치거나 C 코드의 단일 표현식보다 더 복잡한 작업을 요구한다면, [`Parser/action_helpers.c`](https://github.com/python/cpython/blob/3.14/Parser/action_helpers.c)에 사용자 정의 도우미를 만들고 [`Parser/pegen.h`](https://github.com/python/cpython/blob/3.14/Parser/pegen.h) 헤더 파일에 노출하여 문법에서 사용할 수 있게 하는 편이 낫다.

파싱에 성공하면 파서는 **반드시** **유효한** AST 객체를 반환해야 한다.

### 테스트

문법과 파서 테스트가 들어 있는 파일은 세 개다.

- [`test_grammar.py`](https://github.com/python/cpython/blob/3.14/Lib/test/test_grammar.py)
- [`test_syntax.py`](https://github.com/python/cpython/blob/3.14/Lib/test/test_syntax.py)
- [`test_exceptions.py`](https://github.com/python/cpython/blob/3.14/Lib/test/test_exceptions.py)

새로 추가하는 기능의 성격에 따라 새 테스트를 어느 파일에 넣는 것이 가장 적절한지 판단하려면 이 파일들의 내용을 확인하라.

파서 생성기 자체의 테스트는 [`test_peg_generator`](https://github.com/python/cpython/tree/3.14/Lib/test/test_peg_generator) 디렉터리에서 찾을 수 있다.

> **해설 — 대략적인 테스트 관심사**
>
> 파일 이름이 암시하듯 일반 문법 구성의 수용 여부는 `test_grammar.py`, 구문 오류 메시지와 위치는 `test_syntax.py`, 예외 전파 동작은 `test_exceptions.py`가 후보가 된다. 다만 실제 분류 기준은 기존 테스트를 열어 가장 유사한 사례를 확인해야 한다. Pegen 자체 표기나 생성 동작을 바꾸는 테스트는 Python 언어 문법 테스트와 분리해 `test_peg_generator`에 둔다.

### 생성된 파서 디버깅

#### 실험하기

생성된 C 파서는 Python 자체가 사용하는 파서다. 따라서 문법에 새 규칙을 추가하는 과정에서 문제가 생기면 Python을 올바르게 컴파일하고 실행할 수 없게 된다. 특히 실험 중에 문제가 발생하면 이 특성 때문에 디버깅이 조금 까다롭다.

따라서 먼저 Python 파서를 생성하여 실험하는 것이 좋다. CPython 저장소의 [`Tools/peg_generator`](https://github.com/python/cpython/tree/3.14/Tools/peg_generator) 디렉터리로 이동한 뒤 다음 명령으로 파서 생성기를 직접 호출하면 된다.

```shell
$ python -m pegen python <PATH TO YOUR GRAMMAR FILE>
```

그러면 같은 디렉터리에 `parse.py`라는 파일이 생성된다. 이 파일을 사용해 입력을 파싱할 수 있다.

```shell
$ python parse.py file_with_source_code_to_test.py
```

생성된 `parse.py` 파일은 평범한 Python 코드이므로, 파일을 수정하고 중단점을 추가하여 복잡한 상황을 디버깅하거나 더 잘 이해할 수 있다.

> **해설 — 왜 Python 대상 파서를 먼저 쓰는가**
>
> C 파서는 빠르고 최종 제품과 같지만, 문법을 잘못 바꾸면 새 CPython 실행 파일 자체를 빌드하지 못할 수 있다. 생성된 Python 파서는 기존에 정상 작동하는 Python 위에서 실행할 수 있고, 함수 호출과 입력 위치를 디버거로 바로 관찰할 수 있다. 문법 아이디어를 검증한 뒤 C 파서를 재생성하는 편이 피드백 주기가 짧다.

#### 상세 출력 모드

Python을 디버그 모드로 컴파일했다면 생성된 파서에서 **매우** 상세한 출력 모드를 활성화할 수 있다. Linux에서 configure 단계를 실행할 때 `--with-pydebug`를 추가하거나, [`PCbuild/build.bat`](https://github.com/python/cpython/blob/3.14/PCbuild/build.bat)을 호출할 때 `-d`를 추가하면 디버그 모드로 컴파일할 수 있다. 이 출력은 생성된 파서를 디버깅하고 작동 방식을 이해하는 데 매우 유용하지만, 처음에는 이해하기 조금 어려울 수 있다.

> [!NOTE]
> Python 파서의 상세 출력 모드를 활성화할 때는 대화형 모드를 사용하지 않는 편이 낫다. 대화형 모드에는 일반 파싱과 다른 특수 단계가 포함되어 있어 출력을 이해하기 훨씬 어려울 수 있기 때문이다.

상세 출력 모드를 활성화하려면 Python을 실행할 때 `-d` 플래그를 추가하면 된다.

```shell
$ python -d file_to_test.py
```

이 명령은 `stderr`에 **매우 많은** 출력을 기록하므로, 나중에 분석할 수 있도록 파일에 저장하는 편이 좋다. 출력은 다음 구조의 추적 행으로 이루어진다.

```
<indentation> ('>'|'-'|'+'|'!') <rule_name>[<token_location>]: <alternative> ...
```

각 행은 호출 스택의 깊이에 따라 서로 다른 양(`<indentation>`)만큼 들여쓰기된다. 그다음 문자는 추적의 종류를 나타낸다.

- `>`는 어떤 규칙의 파싱을 시도하려 한다는 뜻이다.
- `-`는 어떤 규칙의 파싱에 실패했다는 뜻이다.
- `+`는 어떤 규칙을 올바르게 파싱했다는 뜻이다.
- `!`는 예외나 오류를 감지하여 파서가 스택을 되감고 있다는 뜻이다.

`<token_location>` 부분은 토큰 배열에서 현재 인덱스를 나타낸다. `<rule_name>` 부분은 현재 파싱 중인 규칙을 나타내며, `<alternative>` 부분은 그 규칙 안에서 현재 시도 중인 대안을 나타낸다.

> **해설 — 추적을 읽는 요령**
>
> 들여쓰기를 재귀 호출 깊이로 보고, 같은 토큰 위치에서 `-` 다음에 다른 대안의 `>`가 나타나는 흐름을 찾으면 백트래킹이 보인다. `+` 뒤의 토큰 위치가 얼마나 전진했는지를 보면 규칙이 소비한 범위를 알 수 있다. `!`는 정상적인 대안 실패가 아니라 예외 전파이므로 별도로 구분해야 한다.
>
> 출력이 방대하므로 관심 있는 규칙 이름이나 예상 오류 토큰 위치를 기준으로 범위를 좁히는 것이 현실적이다.

> [!NOTE]
> **문서 이력**
>
> - Pablo Galindo Salgado — 최초 작성자
> - Irit Katriel, Jacob Coffee — Markdown으로 변환

---

## 제2부: 컴파일러 설계

### 1. 전체 개요

CPython의 소스 컴파일은 다음 다섯 단계로 요약된다.

1. [`Parser/lexer/`](https://github.com/python/cpython/tree/3.14/Parser/lexer)와
   [`Parser/tokenizer/`](https://github.com/python/cpython/tree/3.14/Parser/tokenizer)가
   소스를 토큰으로 나눈다.
2. 생성된 토큰 스트림을
   [`Parser/parser.c`](https://github.com/python/cpython/blob/3.14/Parser/parser.c)가
   AST(Abstract Syntax Tree)로 만든다.
3. [`Python/compile.c`](https://github.com/python/cpython/blob/3.14/Python/compile.c)가
   AST를 바이트코드와 비슷한 의사 명령어 열로 바꾼다.
4. [`Python/flowgraph.c`](https://github.com/python/cpython/blob/3.14/Python/flowgraph.c)가
   CFG(Control Flow Graph)를 만들고 최적화한다.
5. [`Python/assemble.c`](https://github.com/python/cpython/blob/3.14/Python/assemble.c)가
   CFG에서 돌아온 명령어 열을 실제 바이트코드와 `PyCodeObject`로 조립한다.

이 다섯 항목에는 상세 절에서 별도로 설명하는 **심볼 테이블 생성**이 생략되어 있다. 실제로는
AST를 명령어로 바꾸기 전에 이름이 지역 변수인지, 전역 변수인지, 클로저 변수인지 분석한다.

> **해설 — nand2tetris 컴파일러보다 중간 단계가 많은 이유**
>
> Jack 언어와 Hack VM은 비교적 단순하므로 구문을 읽는 동안 VM 명령을 바로 내보내도 된다.
> Python은 중첩 함수, 클로저, 예외 처리, 동적 이름 탐색, 정확한 오류 위치, 디버깅 정보를
> 지원한다. 따라서 AST와 최종 바이트코드 사이에 심볼 테이블, 의사 명령어, CFG, 예외
> 테이블, 위치 테이블 같은 표현이 추가된다. 각 표현은 특정 문제를 풀기 좋은 모양이다.

공식 문서는 전체 구현을 완전히 명세하려는 문서가 아니다. 파싱은 이후 컴파일 단계를 이해할
정도로만 설명하며, 정확한 세부 동작은 결국 연결된 C 소스를 확인해야 한다.

---

### 2. 파싱

Python 3.9부터 CPython은 PEG 파서를 사용한다. 일반적인 PEG 구현은 문자 스트림을 직접
입력으로 받는 경우가 많지만, CPython의 PEG 파서는 앞 단계의 토크나이저가 만든 **토큰
스트림**을 받는다.

예를 들어 소스가 다음과 같다면,

```python
if total >= 10:
    print(total)
```

파서는 개별 문자 `i`, `f`, 공백을 보는 대신 대략 `if`, `NAME`, `>=`, `NUMBER`, `:`,
`NEWLINE`, `INDENT` 같은 단위를 본다. 들여쓰기도 토크나이저가 `INDENT`와 `DEDENT`
토큰으로 표현한다.

Python 문법은
[`Grammar/python.gram`](https://github.com/python/cpython/blob/3.14/Grammar/python.gram)에
기술되어 있고, 토큰 종류는
[`Grammar/Tokens`](https://github.com/python/cpython/blob/3.14/Grammar/Tokens)에
정의되어 있다. `Parser/parser.c`를 비롯한 여러 C 파일은 이 정의들로부터 생성된다.
즉 `parser.c`는 보통 사람이 직접 편집하는 파일이 아니다.

PEG 자체와 문법 변경 절차는 다음 문서를 함께 보면 된다.

- [`InternalDocs/parser.md`](https://github.com/python/cpython/blob/3.14/InternalDocs/parser.md):
  PEG 파서와 Pegen의 동작
- [`InternalDocs/changing_grammar.md`](https://github.com/python/cpython/blob/3.14/InternalDocs/changing_grammar.md):
  CPython 문법을 실제로 바꾸는 절차

---

### 3. 추상 구문 트리(AST)

AST는 소스의 문법적 모양을 프로그램 구조 중심으로 줄여 놓은 트리다. 원래 소스 전체를
보존할 필요는 없다. 괄호, 콜론, 공백 같은 표면 문법은 대부분 사라지고, 함수 정의·대입·호출·
연산처럼 컴파일에 필요한 관계가 남는다.

```python
answer = left + right
```

이 코드는 개념적으로 다음 구조가 된다.

```text
Assign
├── target: Name("answer")
└── value: BinOp
    ├── left: Name("left")
    ├── op: Add
    └── right: Name("right")
```

#### 3.1 ASDL은 AST의 스키마다

CPython은 AST 노드의 종류와 필드를
[`Parser/Python.asdl`](https://github.com/python/cpython/blob/3.14/Parser/Python.asdl)에
ASDL(Zephyr Abstract Syntax Definition Language)로 정의한다. ASDL은 Python 소스를
파싱하는 문법이 아니라, **파싱 결과인 AST가 어떤 데이터 모양을 가져야 하는지** 정의하는
언어다.

원문이 사용하는 예를 개념만 남겨 단순화하면 다음과 같다.

```text
stmt =
    FunctionDef(identifier name, arguments args, stmt* body, expr* decorators)
  | Return(expr? value)
  | Yield(expr? value)
```

여기에서 `stmt`는 여러 형태 중 하나를 가질 수 있는 상위 타입이다.

- `FunctionDef`, `Return`, `Yield`는 `stmt`가 될 수 있는 서로 다른 변형이다.
- `expr?`의 `?`는 값이 없거나 하나임을 뜻한다.
- `stmt*`, `expr*`의 `*`는 0개 이상의 노드가 들어가는 순서를 뜻한다.
- 수식어가 없으면 정확히 하나가 필요하다.
- `arguments`처럼 이름이 복수형이어도 ASDL 타입 선언에 `*`가 없으면 노드 하나다.

각 노드에는 소스 위치 같은 공통 속성도 붙을 수 있다. ASDL의 `attributes`는 특정 변형
하나가 아니라 해당 상위 타입의 모든 변형에 공통으로 적용되는 필드를 선언한다.

> **해설 — ASDL과 `python.gram`의 차이**
>
> `python.gram`은 “어떤 토큰 배열이 올바른 Python 문장인가?”를 설명한다.
> `Python.asdl`은 “올바른 문장을 읽은 결과를 어떤 트리 데이터로 저장할 것인가?”를
> 설명한다. nand2tetris식으로 보면 전자는 `CompilationEngine`이 인식할 문법이고, 후자는
> 컴파일러 내부에서 사용할 AST 클래스들의 타입 선언에 가깝다.

#### 3.2 ASDL에서 C 타입이 생성되는 방식

ASDL의 `stmt` 같은 합 타입은 C에서 대략 **태그가 붙은 공용체(tagged union)**로 구현된다.

```c
struct statement {
    enum statement_kind kind;
    union {
        struct function_def_fields function_def;
        struct return_fields return_stmt;
        struct yield_fields yield_expr;
    } value;
    int lineno;
};
```

실제 생성 타입과 필드 이름은 위 예시와 다르지만 구조는 같다.

1. `kind`가 현재 노드의 변형을 표시한다.
2. `union`에서는 그 변형에 해당하는 필드 묶음만 사용한다.
3. 줄 번호 같은 공통 속성은 공용체 밖에 둔다.

ASDL 도구는 C 구조체뿐 아니라 각 변형을 올바르게 초기화하는 생성 함수도 만든다. 예를 들어
함수 정의 생성자는 태그를 함수 정의 종류로 설정한 뒤 이름, 인자, 본문, 데코레이터, 위치
정보를 채운다.

> **해설 — 태그가 필요한 이유**
>
> C의 `union`만으로는 현재 어떤 멤버가 유효한지 알 수 없다. `kind`를 함께 저장해야
> `switch (node->kind)`로 안전하게 `FunctionDef`와 `Return`을 구분할 수 있다. 이는
> Rust의 `enum`, Haskell의 대수적 데이터 타입, TypeScript의 discriminated union과
> 같은 아이디어를 C로 구현한 것이다.

AST를 Python 차원에서 탐색하는 방법이 필요하면 원문이 연결한
[Green Tree Snakes](https://greentreesnakes.readthedocs.io/)도 참고할 수 있다.

---

### 4. 컴파일 중 메모리 관리

컴파일 과정에서는 짧은 시간 동안 수많은 AST 노드와 보조 자료구조가 생긴다. 이를 하나씩
`malloc()`하고 각각 정확한 시점에 `free()`하면 구현이 복잡해진다. CPython은 이 영역에
**arena**를 사용한다.

arena의 사용 모델은 다음과 같다.

1. `PyArena_New()`로 컴파일 한 건에 사용할 arena를 만든다.
2. 컴파일 중 필요한 메모리를 할당하고 그 주소를 arena에 등록한다.
3. 중간 객체를 하나씩 해제하지 않는다.
4. 컴파일이 끝나거나 실패하면 `PyArena_Free()` 한 번으로 등록된 메모리를 모두 정리한다.

관련 구현은 다음 파일에 있다.

- [`Include/internal/pycore_pyarena.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_pyarena.h)
- [`Python/pyarena.c`](https://github.com/python/cpython/blob/3.14/Python/pyarena.c)

대부분의 컴파일러 코드를 수정할 때는 arena의 내부를 신경 쓰지 않아도 된다. 컴파일 진입점이나
종료·실패 처리처럼 수명 경계를 다루는 코드를 수정할 때만 직접적인 관심이 필요하다.

> **해설 — arena는 일반 가비지 컬렉터가 아니다**
>
> arena는 객체가 더 이상 사용되지 않는 순간을 추적하지 않는다. “이 컴파일 작업에서 만든
> 임시 데이터는 모두 같은 때에 버릴 수 있다”는 수명 특성을 이용한다. 중간 노드 하나가
> 일찍 필요 없어져도 즉시 반환하지 않고 전체 컴파일이 끝날 때 함께 반환한다. 메모리를 조금
> 더 오래 잡아 두는 대신 할당·해제 코드와 오류 경로를 단순하게 만든다.

#### 4.1 `PyObject`는 별도 주의가 필요하다

일반 arena 메모리와 달리 `PyObject`는 CPython의 참조 카운팅 규칙을 따른다. 컴파일 중
새 `PyObject`를 만들어 arena의 수명과 함께 정리하고 싶다면
`PyArena_AddPyObject()`로 알려야 한다. 그러면 arena가 해제될 때 필요한 참조 정리도 함께
수행할 수 있다. 이런 경우는 컴파일러의 일반적인 수정 작업에서는 드물다.

---

### 5. 소스 코드에서 AST까지

문자열이나 파일에서 AST 생성을 시작하는 고수준 함수는
`_PyParser_ASTFromString()`과 `_PyParser_ASTFromFile()`이며,
[`Parser/peg_api.c`](https://github.com/python/cpython/blob/3.14/Parser/peg_api.c)에 있다.

초기 검사 뒤에는 생성된 `Parser/parser.c`의 규칙 함수들이 토큰을 재귀적으로 맞춘다.
문법 규칙 이름이 `xx`라면 대응 함수는 대체로 `xx_rule` 형태다. 이 함수들은
[`Tools/peg_generator/pegen/c_generator.py`](https://github.com/python/cpython/blob/3.14/Tools/peg_generator/pegen/c_generator.py)가
`Grammar/python.gram`에서 자동으로 만든다.

#### 5.1 규칙 함수의 역할

각 규칙 함수는 대략 다음 작업을 한다.

1. 현재 토큰 위치에서 자신의 문법 규칙을 시도한다.
2. 터미널 토큰은 토큰 검사 함수로 확인한다.
3. 비터미널은 대응하는 다른 규칙 함수를 호출한다.
4. 한 대안이 성공하면 필요한 AST 노드를 만든다.
5. 실패하면 입력 위치를 되돌리고 다음 대안을 시도한다.
6. 가능한 대안이 모두 실패하면 상위 호출자에게 실패를 돌려준다.

> **해설 — 터미널과 비터미널**
>
> 터미널은 `import`, `:`, `NAME`처럼 파서 입력에 실제로 나타나는 토큰이다.
> 비터미널은 `expression`, `dotted_as_names`처럼 여러 토큰이나 다른 규칙으로 정의되는
> 문법 개념이다. 파싱이 진행되면 비터미널 규칙 호출이 더 작은 규칙으로 내려가고, 결국
> 터미널 토큰 검사에 도달한다.

AST 생성 함수는 `_PyAST_{노드명}` 형태다. 선언의 근원은 `Parser/Python.asdl`이며,
[`Parser/asdl_c.py`](https://github.com/python/cpython/blob/3.14/Parser/asdl_c.py)가
[`Python/Python-ast.c`](https://github.com/python/cpython/blob/3.14/Python/Python-ast.c)를
생성한다. 여러 AST 노드는 `asdl_seq` 계열 순서 자료구조에 담긴다.

#### 5.2 `import sys`가 AST가 되는 흐름

문법 규칙을 단순화하면 다음과 같다.

```text
import_name: 'import' dotted_as_names
```

생성된 `import_name_rule(Parser *p)`의 핵심 흐름을 의사 코드로 표현하면 다음과 같다.

```c
if (expect_token(p, IMPORT) &&
    (aliases = dotted_as_names_rule(p))) {
    result = make_import_ast(aliases, source_location, p->arena);
    return result;
}
return NULL;
```

여기서 일어나는 일은 세 가지뿐이다.

- 현재 토큰이 `import`인지 확인한다.
- 뒤의 이름 목록을 다른 규칙 함수로 읽는다.
- 성공했다면 해당 목록을 가진 Import AST 노드를 만든다.

실제 생성 C 함수에는 캐시, 오류 전달, 토큰 위치 복원, 디버깅 추적 코드가 더 들어간다.

#### 5.3 일부 규칙의 메모이제이션

PEG 파서는 실패한 대안에서 되돌아가 다른 대안을 시도할 수 있다. 같은 토큰 위치에서 같은
규칙을 반복 실행하면 비용이 커질 수 있으므로, 문법에서 `(memo)`로 표시한 일부 규칙은
결과를 캐시한다.

규칙 함수는 먼저 “이 규칙을 이 토큰 위치에서 이미 계산했는가?”를 확인한다. 캐시가 있으면
이전 결과와 이동 위치를 재사용하고, 없으면 규칙을 실행한다.

> **해설 — 무엇을 캐시하는가**
>
> 일반 함수 메모이제이션의 키가 함수 인자라면, 파서에서는 보통 **규칙 식별자와 토큰
> 위치**가 키다. 값은 성공 여부, 만들어진 AST 조각, 성공했을 때의 다음 토큰 위치 등이다.
> 모든 규칙에 캐시를 쓰면 조회 비용과 메모리 사용량도 생기므로 CPython은 필요한 규칙을
> 선택해 사용한다.

#### 5.4 ASDL 순서 자료구조

AST 필드에 `*`가 붙으면 여러 노드를 담아야 한다. CPython은 이를 위해 `asdl_xx_seq *`
계열 타입과 생성·접근 매크로를 제공한다.

수동으로 정의된 주요 순서 타입은 다음 세 범주다.

- `generic`: 일반 포인터 요소
- `identifier`: 이름 식별자 요소
- `int`: 정수 요소

할당 함수는 길이와 arena를 받는다.

- `_Py_asdl_generic_seq_new(Py_ssize_t, PyArena *)`
- `_Py_asdl_identifier_seq_new(Py_ssize_t, PyArena *)`
- `_Py_asdl_int_seq_new(Py_ssize_t, PyArena *)`

다른 AST 전용 순서 타입은 `Parser/asdl_c.py`가 자동 생성하며, 선언은
[`Include/internal/pycore_ast.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_ast.h)에
들어간다.

요소를 다루는 대표 매크로는 다음과 같다.

- `asdl_seq_GET(seq, index)`: 지정한 위치의 요소를 읽는다.
- `asdl_seq_SET(seq, index, value)`: 지정한 위치에 요소를 넣는다.
- `asdl_seq_GET_UNTYPED(...)`, `asdl_seq_SET_UNTYPED(...)`: 일반 `asdl_seq`를 다루는
  비타입 버전이다.
- `asdl_seq_LEN(seq)`: 타입 유무와 관계없이 순서 길이를 얻는다.

가능하면 타입이 있는 매크로를 사용해야 한다. 디버그 빌드에서 타입 관련 검사가 추가되어,
`void *`를 잘못 캐스팅한 오류를 찾기 쉽기 때문이다.

문장 AST를 만들 때에는 어떤 소스 위치에서 생성되었는지도 함께 추적한다. 이 정보는
traceback, 디버거, `ast` 모듈, 위치 테이블 생성 등에 필요하다.

PEG 파서 도입의 배경은
[`PEP 617`](https://peps.python.org/pep-0617/)에서 더 자세히 설명한다.

---

### 6. 제어 흐름 그래프(CFG)

CFG는 프로그램이 실행될 수 있는 경로를 방향 그래프로 나타낸 것이다. CFG의 노드는
바이트코드 한 개가 아니라 **basic block**이다. basic block은 중간으로 뛰어들거나 중간에서
빠져나가지 않고, 한 번 진입하면 마지막 명령까지 순서대로 실행되는 명령어 묶음이다.

점프 명령 `a`가 다른 명령 `b`로 이동한다면 다음 경계가 필요하다.

- `a`는 자신이 속한 basic block의 마지막 명령이어야 한다.
- `b`는 목적지 basic block의 첫 명령이어야 한다.

다음 코드를 보자.

```python
if x < 10:
    f1()
    f2()
else:
    g()
end()
```

개념적인 CFG는 다음과 같다.

```text
               ┌─ 참 ─→ [f1(); f2()] ─┐
[x < 10 검사] ─┤                      ├─→ [end()]
               └─ 거짓 → [g()] ───────┘
```

- 조건 블록은 `x < 10`을 계산한 뒤 조건부 점프로 끝난다.
- 참 블록은 `f1()`과 `f2()`를 실행한 뒤 합류 블록으로 간다.
- 거짓 블록도 `g()`를 실행한 뒤 같은 합류 블록으로 간다.
- 합류 블록이 `end()`를 실행한다.

소스의 한 구역이 항상 basic block 하나가 되는 것은 아니다. 예를 들어
`if x or y:`는 단락 평가 때문에 `x`를 검사하는 블록과, 필요할 때만 `y`를 검사하는
블록으로 나뉜다. `x`가 참이면 `y`를 건너뛰고 바로 본문으로 가야 하기 때문이다.

> **해설 — 왜 CFG에서 최적화하는가**
>
> 일렬로 늘어선 명령어만 보면 “이 명령 다음에 실제로 도달할 수 있는 곳”을 매번 점프
> 주소를 따라가며 계산해야 한다. CFG는 경로와 합류 지점을 구조로 드러낸다. 따라서 도달할
> 수 없는 블록 제거, 점프 단순화, 블록 간 스택 상태 분석처럼 흐름에 의존하는 작업이
> 쉬워진다.

---

### 7. AST에서 CFG를 거쳐 바이트코드까지

AST 컴파일은 [`Python/compile.c`](https://github.com/python/cpython/blob/3.14/Python/compile.c)의
`_PyAST_Compile()`에서 시작한다.

#### 7.1 먼저 심볼 테이블을 만든다

첫 작업은 [`Python/symtable.c`](https://github.com/python/cpython/blob/3.14/Python/symtable.c)의
`_PySymtable_Build()`가 AST를 순회하며 심볼 테이블을 만드는 것이다.

AST 노드 종류마다 `symtable_visit_{xx}` 형태의 방문 함수가 있다. 함수, 클래스, 람다,
컴프리헨션처럼 새 이름 범위를 여는 구조를 만나면 `symtable_enter_block()`으로 들어가고,
처리가 끝나면 `symtable_exit_block()`으로 나온다.

예를 들어 다음 코드에서 이름 `x`의 의미는 위치마다 다르다.

```python
x = 10

def outer():
    x = 20

    def inner():
        return x

    return inner
```

- 모듈의 `x`는 전역 이름이다.
- `outer`의 `x`는 지역 변수이면서 `inner`가 참조할 cell 변수다.
- `inner`에서 보이는 `x`는 바깥 함수에서 가져오는 free 변수다.

이 구분에 따라 이후 생성할 명령어 계열이 달라진다. 지역 변수, 전역 이름, 클로저 변수는
서로 다른 저장 위치와 조회 절차를 사용한다.

> **해설 — AST 생성과 동시에 이름을 확정하지 않는 이유**
>
> 이름의 성격은 그 이름이 나타난 한 지점만 보고 정할 수 없다. 함수 전체에 대입이 있는지,
> `global`이나 `nonlocal` 선언이 있는지, 중첩 함수가 참조하는지를 함께 봐야 한다.
> 그래서 AST를 먼저 완성한 뒤 별도 순회로 범위 정보를 계산한다.

#### 7.2 AST를 의사 명령어 열로 바꾼다

심볼 테이블이 준비되면 `compiler_codegen()`이 AST를 **pseudo-instruction
sequence**, 즉 의사 명령어 열로 변환한다. 이 명령들은 실제 바이트코드와 비슷하지만,
아직 논리 레이블을 사용하거나 더 추상적인 연산을 포함할 수 있다. 최종 opcode와 정확한
오프셋은 뒤 단계에서 확정한다.

AST 종류별 방문 함수 이름은 `compiler_visit_{xx}` 형식이다. 각 함수는 컴파일 상태
`struct compiler *`와 해당 AST 노드를 받으며, 보통 노드의 `kind`에 따른 큰 `switch`로
구성된다.

- 단순한 노드는 `switch` 분기 안에서 바로 처리한다.
- 복잡한 변환은 `compiler_{설명적인 이름}` 보조 함수로 위임한다.
- 임의의 자식 노드는 `VISIT(c, expr, node)`처럼 `VISIT()` 매크로로 방문한다.
- `*` 필드처럼 노드가 여러 개인 경우에는 `VISIT_SEQ()`를 사용한다.

이는 AST 방문자 패턴을 C 매크로와 `switch`로 구현한 형태다.

#### 7.3 명령어를 추가하는 매크로

`compile.c`는 여러 `ADDOP...` 매크로로 의사 명령어를 기록한다.

| 매크로 | 역할 |
|---|---|
| `ADDOP` | 인자 없는 opcode를 추가한다. |
| `ADDOP_IN_SCOPE` | opcode를 추가하면서 현재 컴파일 범위의 종료 처리도 수행한다. 람다나 클로저의 반환 명령처럼 범위를 마무리할 때 사용한다. |
| `ADDOP_I` | 정수 인자를 갖는 opcode를 추가한다. |
| `ADDOP_O` | 주어진 `PyObject`가 `names` 또는 `varnames` 같은 테이블에서 차지하는 위치를 명령 인자로 사용한다. 이 버전은 이름 맹글링을 처리하지 않는다. |
| `ADDOP_N` | `ADDOP_O`와 비슷하지만 전달받은 `PyObject` 참조의 소유권을 가져간다. |
| `ADDOP_NAME` | 객체 테이블 인덱스를 사용하면서 Python 이름 맹글링도 처리한다. 속성 접근이나 이름 기반 import 등에 사용한다. |
| `ADDOP_LOAD_CONST` | 상수 테이블에서 객체의 인덱스를 구해 `LOAD_CONST`를 추가한다. |
| `ADDOP_LOAD_CONST_NEW` | 위와 같지만 전달받은 객체 참조의 소유권을 가져간다. |
| `ADDOP_JUMP` | 대상 `basicblock`으로 이동하는 점프 명령을 추가한다. |

> **해설 — “참조를 훔친다(steal a reference)”**
>
> CPython C API에서 이 표현은 함수나 매크로가 호출자로부터 해당 `PyObject *` 참조의
> 소유 책임을 넘겨받는다는 뜻이다. 호출자는 성공 후 같은 소유 참조를 다시 `Py_DECREF()`하면
> 안 된다. 메모리를 몰래 복사한다는 뜻이 아니라 참조 카운트 관리 책임의 이전이다.

> **해설 — 이름 맹글링**
>
> 클래스 본문 안의 `__secret` 같은 이름을 `_ClassName__secret` 형태로 변환하는 규칙이다.
> `ADDOP_NAME`은 이런 변환이 필요한 이름 경로에 사용되고, 이름이 이미 확정되었거나 변환
> 대상이 될 수 없는 경우에는 `ADDOP_O` 계열을 쓸 수 있다.

각 명령에는 `location`이 함께 전달된다. 이 구조체는 해당 명령과 연결할 소스 줄·열 범위를
담으며, 보통 AST 노드에서 `LOC` 매크로로 얻는다.

컴파일러가 자체적으로 삽입한 명령은 대응하는 소스 구문이 없을 수 있다. 이때
`NO_LOCATION`을 사용할 수 있다. 대표적인 예는 함수 끝에 자동으로 붙는 암시적
`return None`이다.

`compiler_list()`, `compiler_boolop()`처럼 특정 구조의 명령을 방출하는 보조 함수도 있다.
특히 `compiler_nameop()`은 심볼 테이블에서 이름의 범위를 확인하고 AST의 문맥이 읽기,
쓰기, 삭제 중 무엇인지에 따라 알맞은 opcode를 선택한다.

#### 7.4 명령어 열과 CFG 사이를 왕복한다

의사 명령어 열이 만들어지면 다음 순서가 이어진다.

1. `_PyCfg_FromInstructionSequence()`가 명령어 열을 CFG로 만든다.
2. `_PyCfg_OptimizeCodeUnit()`이 CFG에 최적화를 적용한다.
3. `_PyCfg_OptimizedCfgToInstructionSequence()`가 최적화된 CFG를 다시 명령어 열로
   평탄화한다.

이 변환과 최적화는 `Python/flowgraph.c`에 있다. 원문은 이 최적화를 peephole
optimization이라고 부른다.

> **해설 — peephole 최적화**
>
> 작은 명령어 구간이나 인접한 블록 패턴을 보고 더 단순한 형태로 치환하는 최적화다.
> “전체 프로그램의 수학적 의미를 다시 증명한다”기보다, 불필요한 점프나 알려진 작은
> 패턴을 국소적으로 정리한다고 이해하면 된다. CFG에서 수행되므로 단순한 인접 명령뿐
> 아니라 블록 사이의 흐름도 활용할 수 있다.

#### 7.5 assembler가 실제 바이트코드와 테이블을 만든다

마지막으로 의사 명령어를 실제 실행 형식으로 낮춘다.

- 의사 opcode를 실제 opcode로 바꾼다.
- 점프의 논리 레이블을 실제 명령 위치에 대한 상대 오프셋으로 바꾼다.
- 예외 처리 범위와 핸들러 위치를 담는
  [exception table](https://github.com/python/cpython/blob/3.14/InternalDocs/exception_handling.md)을
  만든다.
- 바이트코드 위치와 소스 위치를 연결하는
  [locations table](https://github.com/python/cpython/blob/3.14/InternalDocs/code_objects.md#source-code-locations)을
  만든다.
- `consts`, `names`, 파일명, 함수의 소스 관련 정보 등 메타데이터를 붙인다.

이 결과를 `PyCodeObject`로 만드는 함수가
[`Python/assemble.c`](https://github.com/python/cpython/blob/3.14/Python/assemble.c)의
`_PyAssemble_MakeCodeObject()`다.

> **해설 — 논리 레이블과 상대 오프셋**
>
> 코드 생성 중에는 “else 블록으로 이동”처럼 블록 자체를 목적지로 삼는 편이 편하다.
> 하지만 실행기는 바이트코드 배열의 어느 위치로 이동할지 알아야 한다. 모든 명령의 최종
> 크기와 배치가 정해진 뒤에야 `현재 위치에서 몇 칸 이동` 같은 상대 오프셋을 계산할 수
> 있으므로 이 작업을 assembler까지 미룬다. nand2tetris assembler가 심볼 레이블을 ROM
> 주소로 확정하는 과정과 유사하다.

---

### 8. 코드 객체

`_PyAST_Compile()`의 최종 반환값은
[`Include/cpython/code.h`](https://github.com/python/cpython/blob/3.14/Include/cpython/code.h)에
정의된 `PyCodeObject`다. 이 객체에는 실행할 바이트코드뿐 아니라 실행과 디버깅에 필요한
상수, 이름, 지역 변수 정보, 스택 크기, 플래그, 위치·예외 테이블 등의 정보가 함께 들어간다.

코드 객체는
[`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)의
`_PyEval_EvalFrameDefault()`가 실행한다. 이 함수가 CPython 바이트코드 평가 루프의 중심이다.

> **해설 — 코드 객체와 함수 객체는 다르다**
>
> 코드 객체는 “무슨 명령을 실행할지”를 담은 설계도다. Python 함수 객체는 코드 객체에
> 전역 네임스페이스, 기본 인자, 클로저 등의 런타임 환경을 결합한 객체다. 같은 코드
> 객체라도 어떤 환경과 결합되는지에 따라 실제 함수가 가진 상태는 달라질 수 있다.

또한 `.pyc` 파일 자체가 컴파일 결과의 본질은 아니다. 메모리에 만들어진 코드 객체가
핵심 결과이며, import 시스템이 이를 재사용하기 위해 직렬화한 캐시 형식이 `.pyc`다.

---

### 9. 중요 파일 지도

다음 목록은 원문의 파일 목록을 같은 분류 순서로 정리한 것이다. 파일을 처음부터 모두 읽기보다,
관심 단계의 진입점과 생성 관계를 찾는 지도로 사용하는 편이 낫다.

#### 9.1 `Parser/`

| 파일 | 역할 |
|---|---|
| [`Parser/Python.asdl`](https://github.com/python/cpython/blob/3.14/Parser/Python.asdl) | Python AST 타입의 ASDL 스키마 |
| [`Parser/asdl.py`](https://github.com/python/cpython/blob/3.14/Parser/asdl.py) | ASDL 정의 파일을 읽어 ASDL 자체의 AST를 만드는 파서 |
| [`Parser/asdl_c.py`](https://github.com/python/cpython/blob/3.14/Parser/asdl_c.py) | ASDL 설명에서 `Python/Python-ast.c`와 `pycore_ast.h` 같은 C 코드를 생성 |
| [`Parser/parser.c`](https://github.com/python/cpython/blob/3.14/Parser/parser.c) | `python.gram`에서 생성된 PEG 파서. 소스 토큰에서 Python AST를 생성 |
| [`Parser/peg_api.c`](https://github.com/python/cpython/blob/3.14/Parser/peg_api.c) | 인터프리터가 소스에서 AST 생성을 요청할 때 쓰는 고수준 API |
| [`Parser/pegen.c`](https://github.com/python/cpython/blob/3.14/Parser/pegen.c) | 생성 규칙 함수가 사용하는 AST 구성·토큰 처리·오류 보고 보조 함수 |
| [`Parser/pegen.h`](https://github.com/python/cpython/blob/3.14/Parser/pegen.h) | `pegen.c`의 선언과 `Parser`, `Token` 구조체 정의 |

#### 9.2 `Python/`

| 파일 | 역할 |
|---|---|
| [`Python/Python-ast.c`](https://github.com/python/cpython/blob/3.14/Python/Python-ast.c) | ASDL 타입에 대응하는 C 구조와 생성 코드를 포함하는 자동 생성 파일. AST 직렬화 관련 코드도 포함 |
| [`Python/asdl.c`](https://github.com/python/cpython/blob/3.14/Python/asdl.c) | ASDL 순서 타입과 identifier·number 같은 핵심 ASDL 값 처리 |
| [`Python/ast.c`](https://github.com/python/cpython/blob/3.14/Python/ast.c) | AST 유효성 검사 |
| [`Python/ast_preprocess.c`](https://github.com/python/cpython/blob/3.14/Python/ast_preprocess.c) | 컴파일 전에 AST를 전처리 |
| [`Python/ast_unparse.c`](https://github.com/python/cpython/blob/3.14/Python/ast_unparse.c) | AST 표현식 노드를 다시 문자열로 표현. 문자열 annotation 처리 등에 사용 |
| [`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c) | 바이트코드 평가 루프 |
| [`Python/symtable.c`](https://github.com/python/cpython/blob/3.14/Python/symtable.c) | AST에서 심볼 테이블 생성 |
| [`Python/pyarena.c`](https://github.com/python/cpython/blob/3.14/Python/pyarena.c) | arena 메모리 관리자 구현 |
| [`Python/compile.c`](https://github.com/python/cpython/blob/3.14/Python/compile.c) | AST에서 의사 명령어를 생성 |
| [`Python/flowgraph.c`](https://github.com/python/cpython/blob/3.14/Python/flowgraph.c) | CFG 변환과 peephole 최적화 |
| [`Python/assemble.c`](https://github.com/python/cpython/blob/3.14/Python/assemble.c) | 의사 명령어 열에서 코드 객체를 조립 |
| [`Python/instruction_sequence.c`](https://github.com/python/cpython/blob/3.14/Python/instruction_sequence.c) | 바이트코드와 비슷한 의사 명령어 열 자료구조 |

`Python/Python-ast.c`는 자동 생성물이지만 저장소에 포함된다. AST 문법이 바뀌면 생성 스크립트와
프로젝트의 재생성 절차를 따라 함께 갱신해야 한다. 이 파일에 기록되는 `__version__` 값은
AST 문법 변경 이력을 가리키므로, 원문은 문법 변경과 생성 파일 갱신을 각각 명확히 기록하도록
주의를 준다.

#### 9.3 `Include/`

| 파일 | 역할 |
|---|---|
| [`Include/cpython/code.h`](https://github.com/python/cpython/blob/3.14/Include/cpython/code.h) | `PyCodeObject` 정의와 `Objects/codeobject.c` 관련 선언 |
| [`Include/opcode.h`](https://github.com/python/cpython/blob/3.14/Include/opcode.h) | opcode 관련 헤더. Python 쪽 opcode 정의·유틸리티가 바뀔 때 함께 일관성을 확인해야 하는 파일 |
| [`Include/internal/pycore_ast.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_ast.h) | ASDL에서 생성된 C AST 구조와 AST 관련 내부 선언 |
| [`Include/internal/pycore_asdl.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_asdl.h) | ASDL 핵심 자료구조의 내부 선언 |
| [`Include/internal/pycore_symtable.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_symtable.h) | `struct symtable`, `PySTEntryObject` 등 심볼 테이블 내부 타입 |
| [`Include/internal/pycore_parser.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_parser.h) | `Parser/peg_api.c`에 대응하는 내부 헤더 |
| [`Include/internal/pycore_pyarena.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_pyarena.h) | arena API 내부 헤더 |
| [`Include/opcode_ids.h`](https://github.com/python/cpython/blob/3.14/Include/opcode_ids.h) | opcode 식별자 목록. `Python/bytecodes.c`에서 생성 |

`Include/opcode_ids.h`는
[`Tools/cases_generator/opcode_id_generator.py`](https://github.com/python/cpython/blob/3.14/Tools/cases_generator/opcode_id_generator.py)가
[`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)를 입력으로
만든다.

#### 9.4 `Objects/`

| 파일 | 역할 |
|---|---|
| [`Objects/codeobject.c`](https://github.com/python/cpython/blob/3.14/Objects/codeobject.c) | `PyCodeObject` 생성·검사·부가 동작 |
| [`Objects/frameobject.c`](https://github.com/python/cpython/blob/3.14/Objects/frameobject.c) | 프레임 객체 관련 코드. `frame_setlineno()`는 디버거가 바이트코드 위치 사이를 이동해도 되는지 판단 |

#### 9.5 `Lib/`와 바이트코드 버전

| 파일 | 역할 |
|---|---|
| [`Lib/opcode.py`](https://github.com/python/cpython/blob/3.14/Lib/opcode.py) | Python 코드에 노출되는 opcode 유틸리티 |
| [`Include/internal/pycore_magic_number.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_magic_number.h) | 바이트코드 캐시 버전을 구분하는 `MAGIC_NUMBER`의 위치 |

`MAGIC_NUMBER`가 맞지 않는 `.pyc`를 현재 인터프리터가 그대로 읽지 않게 함으로써, opcode나
코드 객체 직렬화 형식이 달라졌을 때 오래된 캐시를 잘못 실행하는 일을 막는다.

---

### 10. 코드 객체 주변의 추가 내부 문서

원문은 컴파일 결과와 직접 연결되는 다음 문서를 안내한다.

- [Locations](https://github.com/python/cpython/blob/3.14/InternalDocs/code_objects.md#source-code-locations):
  바이트코드와 소스 위치의 대응
- [Frames](https://github.com/python/cpython/blob/3.14/InternalDocs/frames.md):
  프레임과 프레임 스택
- [Object layout](https://github.com/python/cpython/blob/3.14/Objects/object_layout.md):
  Python 3.11 이후 객체 배치
- [Exception handling](https://github.com/python/cpython/blob/3.14/InternalDocs/exception_handling.md):
  예외 테이블과 실행 시 예외 처리

이 중 컴파일 흐름을 이어서 이해하려면 `code_objects.md`와 `exception_handling.md`를 먼저
읽는 편이 자연스럽다. `frames.md`는 생성된 코드 객체가 실행 상태로 바뀌는 경계를 설명한다.

---

### 11. ASDL 참고 문헌

CPython 문서가 사용하는 ASDL의 배경은 다음 자료에서 확인할 수 있다.

- Daniel C. Wang, Andrew W. Appel, Jeff L. Korn, Chris S. Serra,
  *The Zephyr Abstract Syntax Description Language* (1997)
- [Princeton 기술 보고서: The Zephyr Abstract Syntax Description Language](https://www.cs.princeton.edu/research/techreps/254)

ASDL 논문까지 읽지 않아도 CPython 컴파일 파이프라인은 이해할 수 있다. 실무적으로는
`Parser/Python.asdl`을 “AST 노드 스키마이며 C 코드를 생성하는 입력”으로 이해하면 충분하다.

---

### 12. 한 예제로 전체 흐름 다시 연결하기

다음 함수를 각 단계에서 어떻게 보는지 정리해 보자.

```python
def choose(x):
    if x:
        return 1
    return 0
```

#### 12.1 토큰

토크나이저는 `def`, `NAME`, `(`, `)`, `:`, `NEWLINE`, `INDENT`, `if`, `return`,
`NUMBER`, `DEDENT` 같은 토큰을 만든다.

#### 12.2 AST

파서는 이를 `FunctionDef` 아래에 `If`와 `Return` 노드가 있는 트리로 만든다. ASDL은
각 노드가 가질 필드를 규정하고, 생성된 `_PyAST_*` 함수가 실제 C AST 노드를 만든다.

#### 12.3 심볼 테이블

`x`는 `choose`의 매개변수이자 지역 이름으로 분류된다. 따라서 코드 생성기는 전역 이름
조회가 아니라 빠른 지역 변수 접근 계열을 선택할 수 있다.

#### 12.4 의사 명령어와 CFG

개념적인 명령 흐름은 다음과 같다.

```text
load local x
jump if false → false_block
load constant 1
return

false_block:
load constant 0
return
```

조건 검사 블록과 두 반환 경로가 CFG의 블록으로 표현된다.

#### 12.5 assembler와 코드 객체

assembler는 `false_block`이라는 논리 목적지를 실제 상대 오프셋으로 바꾸고, 상수 `1`과
`0`의 테이블 인덱스, 소스 위치, 예외 정보 등을 확정한다. 그런 다음 바이트코드와 모든
메타데이터를 `PyCodeObject` 하나로 묶는다. 실행 시 평가 루프가 이 코드 객체를 프레임의
실행 코드로 사용한다.

이 연결을 기억하면 세부 C 함수가 많아도 현재 보고 있는 코드가 어느 단계에 속하는지
판단할 수 있다.

---

## 제3부: CPython 문법 변경

### 먼저 알아둘 핵심

CPython에 새로운 문법을 넣는 일은 파서 규칙 하나를 고치는 것으로 끝나지 않는다. 문법 변경은 상황에 따라 토큰의 종류, AST의 형태, AST 검증, 바이트코드 생성, AST를 다시 소스로 표현하는 기능, 표준 라이브러리의 소스 분석 도구, 테스트와 언어 문서까지 영향을 준다.

전체 관계를 단순화하면 다음과 같다.

```text
Python 소스
  ↓
토크나이저                         Parser/lexer/
  ↓ token
PEG 파서                           Grammar/python.gram
  ↓ AST                            Parser/Python.asdl
AST 검증                           Python/ast.c
  ↓
컴파일러                           Python/compile.c 등
  ↓
바이트코드와 Code Object
```

이 주 흐름 바깥에도 AST를 다시 Python 코드처럼 출력하는 unparser, Python 수준의 토큰화 API, `pyclbr` 같은 정적 분석 도구가 있다. 그래서 변경한 문법이 파서에서만 동작한다고 해서 작업이 완료된 것은 아니다.

> **nand2tetris와 연결해서 보기**
>
> Jack 컴파일러에서 토크나이저의 출력 형식을 바꾸면 `CompilationEngine`과 테스트도 함께 바뀌어야 한다. 새 구문 트리 종류를 도입하면 그 노드를 VM 명령으로 내보내는 처리도 필요하다. CPython에서도 같은 의존 관계가 존재하지만, AST 공개 API와 여러 개발 도구까지 포함하므로 영향 범위가 더 넓다.

### 생성 파일과 `make clean`

CPython 저장소에는 사람이 직접 관리하는 원본 파일과, 그 원본에서 자동으로 만들어지는 파생 파일이 함께 들어 있다. 예를 들어 `Grammar/python.gram`은 원본이고 `Parser/parser.c`는 생성 결과다.

문법 관련 원본을 바꾼 뒤에는 해당 재생성 명령을 실행해야 한다. 변경 내용이 맞는데도 빌드나 테스트가 이전 동작을 보인다면 오래된 중간 산출물이 남았을 수 있으므로 `make clean`이 도움이 될 수 있다.

> **파생 파일이란**
>
> 다른 파일이나 정의를 입력으로 삼아 도구가 자동 생성한 파일이다. 파생 파일을 직접 고치면 다음 재생성 때 수정 내용이 사라지고, 원본과 결과가 서로 어긋난다. 따라서 아래 항목에서는 항상 “어느 파일이 원본인가”와 “무엇을 재생성해야 하는가”를 함께 봐야 한다.

### 변경 지점 체크리스트

#### 1. PEG 문법과 AST 생성 액션: `Grammar/python.gram`

[`Grammar/python.gram`](https://github.com/python/cpython/blob/3.14/Grammar/python.gram)은 Python의 구문 규칙을 정의하는 중심 파일이다. 이 파일에는 어떤 토큰 배열을 문법적으로 받아들일지뿐 아니라, 규칙이 성공했을 때 어떤 AST 노드를 만들지도 액션으로 적혀 있다.

이 파일을 바꾼 뒤에는 다음 명령으로 C 파서를 다시 생성한다.

```shell
make regen-pegen
```

Windows에서는 다음 명령을 사용한다.

```dos
build.bat --regen
```

재생성 결과는 [`Parser/parser.c`](https://github.com/python/cpython/blob/3.14/Parser/parser.c)에 반영된다. 이 작업을 수행하는 파서 생성기가 [`Tools/peg_generator`](https://github.com/python/cpython/tree/3.14/Tools/peg_generator), 즉 Pegen이다.

> **문법 규칙과 액션**
>
> 문법 규칙은 “이 입력이 어떤 구문인가”를 판정한다. 액션은 “그 구문을 어떤 AST 값으로 표현할 것인가”를 정한다. nand2tetris식으로 비유하면, 토큰을 문법 구조로 묶는 처리와 그 결과를 내부 표현으로 만드는 처리가 한 문법 파일 안에 같이 기술되어 있는 셈이다.

`Parser/parser.c`는 생성 파일이므로 일반적인 문법 변경에서는 직접 편집하지 않는다.

#### 2. 토큰 종류: `Grammar/Tokens`

새로운 **토큰 타입**이 필요하면 [`Grammar/Tokens`](https://github.com/python/cpython/blob/3.14/Grammar/Tokens)을 수정한다. 문법에 새 표현을 추가했다고 항상 새 토큰이 필요한 것은 아니다. 기존 `NAME`, `NUMBER`, 연산자 토큰 등의 조합만으로 표현할 수 있다면 문법 파일만 바뀔 수도 있다. 반면 토크나이저가 이전과 다른 종류의 단위로 입력을 구분해야 한다면 토큰 정의 변경을 검토해야 한다.

수정 후에는 다음 명령을 실행한다.

```shell
make regen-token
```

이 명령은 토큰 정의를 여러 소비자에게 맞는 형태로 펼쳐 다음 파일들을 다시 만든다.

- [`Include/internal/pycore_token.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_token.h): C 내부에서 사용하는 토큰 상수
- [`Parser/token.c`](https://github.com/python/cpython/blob/3.14/Parser/token.c): 토큰 관련 C 테이블과 변환 정보
- [`Lib/token.py`](https://github.com/python/cpython/blob/3.14/Lib/token.py): Python 코드에서 사용하는 토큰 상수와 보조 정보
- [`Doc/library/token-list.inc`](https://github.com/python/cpython/blob/3.14/Doc/library/token-list.inc): 토큰 문서에 삽입되는 생성 목록

`Grammar/Tokens`와 `Grammar/python.gram`을 모두 변경했다면 다음 순서를 지킨다.

```shell
make regen-token
make regen-pegen
```

파서를 생성할 때 최신 토큰 정의가 필요하기 때문이다. Windows의 `build.bat --regen`은 두 종류의 재생성을 함께 처리한다.

> **토큰 타입과 실제 문자열의 차이**
>
> `if`라는 두 글자와 “이 입력은 특정 문법 요소로 취급되는 토큰이다”라는 내부 분류는 다르다. 파서는 원문 문자보다 토크나이저가 만든 토큰 스트림을 본다. 따라서 파서가 참조하는 토큰 번호와 토크나이저가 내놓는 번호가 일치해야 한다.

#### 3. AST 스키마: `Parser/Python.asdl`

문법 변경으로 AST의 노드 종류나 필드 구성이 달라진다면 [`Parser/Python.asdl`](https://github.com/python/cpython/blob/3.14/Parser/Python.asdl)도 바꿔야 한다. 문법만 새로워도 기존 AST 조합으로 표현할 수 있다면 이 파일을 바꾸지 않을 수 있다.

ASDL을 수정한 뒤에는 다음 명령으로 AST용 C 정의와 구현을 다시 생성한다.

```shell
make regen-ast
```

주요 생성 결과는 다음과 같다.

- [`Include/internal/pycore_ast.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_ast.h)
- [`Python/Python-ast.c`](https://github.com/python/cpython/blob/3.14/Python/Python-ast.c)

> **ASDL의 역할**
>
> ASDL은 구체적인 Python 소스 문법이 아니라 AST 데이터 구조의 스키마다. 예를 들어 “이 노드는 왼쪽 식, 연산자, 오른쪽 식을 가진다”처럼 컴파일러가 다룰 데이터의 형태를 정의한다. nand2tetris 구현에서 직접 만든 `Expression`, `Statement` 구조체나 클래스의 선언부에 해당한다고 보면 된다.

#### 4. 문자에서 토큰으로: `Parser/lexer/`

[`Parser/lexer/`](https://github.com/python/cpython/tree/3.14/Parser/lexer)은 토큰화 코드를 담고 있다. 새로운 주석 형식이나 문자열 리터럴처럼 **문자를 읽는 방식 자체**가 달라지는 기능이라면 이 계층을 수정해야 한다.

문법 파일은 이미 만들어진 토큰을 조합한다. 따라서 기존 토크나이저가 새 입력을 원하는 토큰으로 만들 수 없다면 PEG 규칙만 추가해도 기능이 구현되지 않는다.

> **문법 변경과 어휘 변경의 경계**
>
> `if expression ':' block`처럼 기존 토큰을 새 순서로 조합하는 것은 주로 문법 문제다. 반대로 새 따옴표 규칙, 주석의 종료 조건, 숫자 리터럴 표기처럼 개별 문자를 어디까지 하나의 단위로 읽을지 바꾸는 것은 어휘 분석 문제다.

#### 5. AST 유효성 검사: `Python/ast.c`

문법 변경에 관련된 AST 객체의 제약이 달라지면 [`Python/ast.c`](https://github.com/python/cpython/blob/3.14/Python/ast.c)의 검증 코드도 조정해야 한다.

파서가 만든 AST만 컴파일러에 들어오는 것은 아니다. 사용자는 `ast` 모듈로 AST 객체를 직접 만들고 `compile()`에 넘길 수 있다. 따라서 컴파일러는 노드 종류, 필수 필드, 컨텍스트와 같은 AST 불변 조건을 별도로 확인한다.

> **왜 파서가 성공했는데도 검증이 필요한가**
>
> 정상 파서의 액션이 항상 올바른 AST를 만든다고 가정하더라도, 외부에서 직접 조립한 AST나 다른 내부 경로에서 온 AST가 존재한다. 검증 계층은 컴파일러가 잘못된 구조를 전제로 동작하지 않도록 막는 경계다.

#### 6. 내부 C unparser: `Python/ast_unparse.c`

AST 변경이 AST를 다시 문자열 형태로 바꾸는 내부 처리에 영향을 준다면 [`Python/ast_unparse.c`](https://github.com/python/cpython/blob/3.14/Python/ast_unparse.c)도 바꿔야 한다.

원문은 이 C unparser가 [PEP 563](https://peps.python.org/pep-0563/)과 관련해 annotation AST를 문자열로 바꾸는 데 사용된다는 점을 예로 든다. 핵심은 새 AST 노드가 생겼거나 기존 노드의 필드가 달라졌다면, 역방향 변환도 그 구조를 이해해야 한다는 것이다.

> **unparse**
>
> parse가 `소스 → AST`라면 unparse는 대략 `AST → 소스와 비슷한 문자열`이다. 원래 소스의 공백이나 괄호를 그대로 복원하는 것이 아니라, 같은 의미를 나타내는 코드를 다시 구성한다.

#### 7. AST에서 바이트코드로: compiler

AST가 달라지면 [컴파일러](https://github.com/python/cpython/blob/3.14/InternalDocs/compiler.md)도 변경해야 할 수 있다. 파서가 새 AST 노드를 잘 만들더라도 컴파일러가 그 노드를 방문해 명령어를 생성하지 못하면 실제 Python 프로그램으로 실행할 수 없다.

기존 AST 노드로 새 문법을 표현했다면 컴파일러 변경이 필요하지 않을 수도 있다. 반대로 새 노드나 새로운 의미 규칙을 도입했다면 코드 생성, 심볼 처리, 제어 흐름 처리 등을 확인해야 한다.

> **nand2tetris와의 직접 대응**
>
> Jack 구문 분석기가 새 statement 노드를 만들었는데 이를 VM 명령으로 변환하는 메서드가 없다면 컴파일은 끝나지 않는다. CPython에서도 AST 생성과 바이트코드 생성은 서로 다른 단계다.

#### 8. 공개 Python unparser: `Lib/ast.py`의 `_Unparser`

AST 노드가 변경되면 [`Lib/ast.py`](https://github.com/python/cpython/blob/3.14/Lib/ast.py)의 `_Unparser`도 변경할 수 있다. 이 클래스는 `ast.unparse()`가 AST에서 Python 코드를 구성할 때 사용하는 Python 구현이다.

앞 항목의 `Python/ast_unparse.c`와 이름은 비슷하지만 같은 구현은 아니다.

- `Python/ast_unparse.c`: CPython 내부의 C 기반 변환
- `Lib/ast.py`의 `_Unparser`: 공개 `ast.unparse()` 기능을 뒷받침하는 Python 기반 변환

새 노드를 추가했다면 두 경로 중 어느 쪽이 해당 노드를 소비하는지 각각 확인해야 한다.

#### 9. AST API 문서: `Doc/library/ast.rst`

AST 노드의 종류, 필드, 의미가 달라졌다면 [`Doc/library/ast.rst`](https://github.com/python/cpython/blob/3.14/Doc/library/ast.rst)를 업데이트해야 한다.

Python의 AST는 CPython 내부 구현에만 숨겨진 구조가 아니다. 사용자가 `ast.parse()`로 관찰하고 직접 구성할 수 있는 공개 API이므로, 스키마 변경은 문서화 대상이다.

#### 10. 문법 테스트: `test_grammar.py`

새 구문이 실제로 사용되는 사례를 [`Lib/test/test_grammar.py`](https://github.com/python/cpython/blob/3.14/Lib/test/test_grammar.py)에 추가한다.

단순히 파서 생성이 성공하는지를 보는 것이 아니라, 새 문법을 포함한 Python 코드가 의도한 형태로 받아들여지고 실행 또는 컴파일되는지를 회귀 테스트로 남기는 단계다.

문법 변경의 성격에 따라 올바른 사용뿐 아니라 경계 사례와 잘못된 사용에 대한 별도 문법·구문 오류 테스트도 필요할 수 있지만, 원문의 체크리스트가 직접 지목하는 기본 위치는 `test_grammar.py`다.

#### 11. 소스 구조 분석기: `pyclbr`

어떤 문법 변경은 표준 라이브러리 모듈 [`pyclbr`](https://docs.python.org/3.14/library/pyclbr.html)를 수정해야 한다.

`pyclbr`는 모듈을 import해서 실행하지 않고 Python 소스를 읽어 클래스와 함수 정의 등의 정보를 찾는다. 따라서 함수·클래스 선언 형식이나 이를 둘러싼 토큰 패턴이 바뀌면, CPython 본체의 파서는 정상이어도 `pyclbr`가 새 코드를 잘못 해석할 수 있다.

> **왜 별도 도구가 영향을 받는가**
>
> 모든 Python 소스 도구가 CPython의 완전한 PEG 파서를 그대로 호출하는 것은 아니다. 목적에 맞게 토큰을 훑거나 일부 문법만 이해하는 도구도 있으므로, 언어 문법 변경은 이러한 보조 소비자를 깨뜨릴 수 있다.

#### 12. Python 수준 토크나이저: `Lib/tokenize.py`

토크나이저 동작을 바꾸었다면 [`Lib/tokenize.py`](https://github.com/python/cpython/blob/3.14/Lib/tokenize.py)도 일치하도록 변경해야 한다.

CPython 실행기가 사용하는 저수준 토큰화 경로와 Python 사용자가 접근하는 `tokenize` 모듈은 역할과 구현 경로가 완전히 같지 않다. 포매터, 린터, 편집기, 코드 분석 도구는 흔히 `tokenize`의 결과에 의존하므로, 새 리터럴이나 주석 등의 처리가 두 경로에서 어긋나지 않는지 확인해야 한다.

> **`Grammar/Tokens`와 `Lib/tokenize.py`의 차이**
>
> `Grammar/Tokens`는 사용할 토큰 종류와 상수를 정의한다. `Lib/tokenize.py`는 실제 소스 텍스트를 Python 수준에서 토큰 열로 해석하는 동작을 제공한다. “목록에 새 토큰을 등록하는 일”과 “그 토큰을 언제 만들어 내는지 구현하는 일”은 별개다.

#### 13. 언어 레퍼런스 문서: `Doc/reference/`

마지막으로 새 문법을 문서화해야 한다. 보통 [`Doc/reference/`](https://github.com/python/cpython/tree/3.14/Doc/reference) 아래의 관련 페이지 하나 이상을 수정한다.

AST 문서가 내부 표현의 공개 형태를 설명한다면, 언어 레퍼런스는 Python 사용자가 어떤 소스를 작성할 수 있고 그 구문이 어떤 의미를 갖는지 설명한다. 새 문법의 표기, 문맥 제약, 평가 방식과 오류 조건이 있다면 여기에 반영해야 한다.

### 변경 유형별로 다시 묶어 보기

원문의 체크리스트는 파일 순서로 되어 있다. 실제 영향 범위를 판단할 때는 변경을 다음 세 층으로 나누면 이해하기 쉽다.

#### 기존 토큰과 기존 AST를 재사용하는 문법 변경

주로 다음 항목을 확인한다.

- `Grammar/python.gram`
- `make regen-pegen`
- `test_grammar.py`
- 언어 레퍼런스 문서
- 새 구문을 별도로 해석하는 `pyclbr` 같은 도구

#### 토큰화 방식까지 바뀌는 변경

위 항목에 더해 다음을 확인한다.

- `Grammar/Tokens`
- `Parser/lexer/`
- `make regen-token`
- `Lib/tokenize.py`
- 토큰 API와 생성 문서

토큰과 문법을 모두 변경할 때는 토큰 재생성을 먼저 하고 파서를 재생성한다.

#### AST 형태나 의미가 바뀌는 변경

추가로 다음을 확인한다.

- `Parser/Python.asdl`과 `make regen-ast`
- `Python/ast.c`의 검증
- compiler의 코드 생성
- `Python/ast_unparse.c`
- `Lib/ast.py`의 `_Unparser`
- `Doc/library/ast.rst`

### 완료 판단 기준

새 구문을 파서가 받아들인다는 사실만으로는 충분하지 않다. 다음 질문에 모두 답할 수 있어야 한다.

- 토크나이저가 필요한 토큰을 일관되게 만드는가?
- 생성된 C 파서가 최신 문법과 토큰 정의를 반영하는가?
- 파서가 유효한 AST를 만드는가?
- 외부에서 만든 같은 형태의 AST도 올바르게 검증되는가?
- 컴파일러가 그 AST를 실행 가능한 바이트코드로 바꾸는가?
- 필요한 unparser가 새 AST를 처리하는가?
- `tokenize`, `pyclbr` 같은 관련 도구가 계속 동작하는가?
- 새 구문에 대한 회귀 테스트가 있는가?
- AST API 문서와 언어 레퍼런스가 실제 동작을 설명하는가?

이 질문 중 해당되는 범위를 확인하고 필요한 생성 명령까지 실행해야 CPython의 문법 변경이 하나의 기능으로 완결된다.

### 원문 항목 반영 확인

- [x] `Grammar/python.gram`, AST 액션, Pegen, `regen-pegen`, `Parser/parser.c`
- [x] `Grammar/Tokens`, `regen-token`, 네 종류의 생성 파일, 재생성 순서, Windows 명령
- [x] `Parser/Python.asdl`, `regen-ast`, AST 생성 파일
- [x] `Parser/lexer/`
- [x] `Python/ast.c`
- [x] `Python/ast_unparse.c`와 PEP 563
- [x] compiler
- [x] `Lib/ast.py`의 `_Unparser`
- [x] `Doc/library/ast.rst`
- [x] `test_grammar.py`
- [x] `pyclbr`
- [x] `Lib/tokenize.py`
- [x] `Doc/reference/`
- [x] 파생 파일과 `make clean` 주의사항

---

## 세 문서를 하나로 연결하기

세 문서가 설명하는 경계는 다음과 같다.

```text
parser.md
  문법 규칙이 토큰을 받아 AST를 만드는 방법
        ↓
compiler.md
  AST를 분석하고 PyCodeObject로 만드는 방법
        ↓
changing_grammar.md
  이 경로의 입력이나 중간 표현을 바꿀 때 함께 수정할 파일
```

`parser.md`를 읽을 때는 “이 규칙이 어떤 토큰을 소비하고 어떤 AST 값을
반환하는가”를 중심으로 본다. `compiler.md`에서는 “이 AST 노드가 어떤
범위 정보와 제어 흐름을 거쳐 어떤 명령으로 낮아지는가”를 본다.
`changing_grammar.md`는 앞의 두 경로를 실제로 수정할 때 빠뜨리기 쉬운
파생 파일과 외부 소비자를 확인하는 체크리스트다.

소스 코드를 직접 따라가려면 다음 순서가 비교적 단순하다.

1. `Grammar/python.gram`에서 작은 규칙 하나를 고른다.
2. 그 규칙의 액션이 만드는 노드를 `Parser/Python.asdl`에서 찾는다.
3. `Python/compile.c`에서 대응하는 `compiler_visit_*` 분기를 찾는다.
4. 생성된 의사 명령어가 `Python/flowgraph.c`에서 어떻게 블록으로
   처리되는지 확인한다.
5. `Python/assemble.c`가 이를 코드 객체로 조립하는 경계를 확인한다.

처음에는 함수 정의나 예외 처리보다 정수 상수, 이름 읽기, 단순 대입,
이항 연산처럼 범위와 제어 흐름이 작은 노드부터 따라가는 편이 낫다.

## 핵심 용어 찾아보기

| 용어 | 이 문서에서의 의미 |
|---|---|
| PEG | 대안을 적힌 순서대로 시도하는 인식 중심 문법 형식 |
| Pegen | CPython의 `.gram` 정의에서 Python 또는 C PEG 파서를 생성하는 도구 |
| ordered choice | `A \| B`에서 `A`를 먼저 시도하고 성공하면 `B`를 보지 않는 선택 |
| backtracking | 선택한 경로가 실패했을 때 이전 입력 위치로 돌아가 다른 대안을 시도하는 것 |
| lookahead | 입력 위치를 이동하지 않고 뒤의 입력 모양을 검사하는 것 |
| cut (`~`) | 해당 지점 이후에는 같은 규칙의 다른 대안으로 돌아가지 않겠다는 확정 |
| memoization | 같은 규칙과 입력 위치의 파싱 결과를 저장해 재사용하는 것 |
| grammar action | 규칙 성공 시 실행되어 AST 같은 반환값을 만드는 C 또는 Python 표현식 |
| meta-grammar | Python 코드가 아니라 Pegen 문법 파일 자체의 형식을 정의하는 문법 |
| ASDL | AST 노드의 종류와 필드를 정의하고 C 타입 생성을 이끄는 스키마 언어 |
| arena | 컴파일 한 건에서 만든 임시 메모리를 작업 종료 시 한꺼번에 정리하는 수명 관리 방식 |
| pseudo-instruction | 아직 논리 레이블이나 추상 연산을 포함해 최종 bytecode는 아닌 중간 명령 |
| basic block | 중간 진입·이탈 없이 처음부터 끝까지 순차 실행되는 명령어 묶음 |
| CFG | basic block과 블록 사이의 가능한 이동을 나타낸 방향 그래프 |
| symbol table | 이름을 지역·전역·cell·free 변수 등으로 분류한 컴파일 정보 |
| assembler | 논리 레이블과 의사 명령을 실제 opcode·오프셋·테이블로 확정하는 마지막 컴파일 단계 |
| `PyCodeObject` | bytecode와 상수·이름·위치·예외 처리 등 실행 메타데이터를 묶은 CPython 객체 |
| generated file | 문법이나 스키마 같은 원본에서 도구가 만들어 내므로 직접 수정하지 않는 파생 파일 |
