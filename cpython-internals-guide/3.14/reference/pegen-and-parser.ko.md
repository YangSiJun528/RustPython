# Pegen 문법은 표기·생성 관계·명령으로 찾아본다

이 문서는 CPython 3.14의 Pegen 문법을 읽고 관련 파일을 찾기 위한 참조다.
문법의 작동 원리를 처음 이해하려면
[PEG 파서는 순서 있는 선택으로 토큰에서 AST 하나를 만든다](../explanations/peg-parser.ko.md)를
먼저 읽는다.

> 아래 표기, 경로, 명령은 CPython 3.14 기준이다. 생성 파일과 도구의 위치는 다른
> 버전에서 바뀔 수 있다.

## 문법 표현식은 입력 소비와 선택 방식을 지정한다

| 표기 | 의미 |
|---|---|
| `e1 e2` | `e1` 다음에 `e2`를 매치한다. |
| `e1 \| e2` | `e1`을 먼저 시도하고 실패할 때만 `e2`를 시도한다. |
| `(e)` | 표현식을 그룹화한다. |
| `[e]`, `e?` | `e`를 선택적으로 매치한다. |
| `e*`, `e+` | `e`를 각각 0회 이상, 1회 이상 매치한다. |
| `s.e+` | 구분자 `s`로 나뉜 `e`를 1회 이상 매치한다. 결과에는 보통 `e`만 모인다. |
| `&e` | 입력을 소비하지 않고 `e`가 성공하는지 검사한다. |
| `!e` | 입력을 소비하지 않고 `e`가 실패하는지 검사한다. |
| `~` | 이 지점 이후 실패해도 현재 대안에서 다른 대안으로 돌아가지 않는다. |
| `$` | 입력 끝을 요구한다. |

규칙의 기본 형태는 다음과 같다.

```text
rule_name[return_type]: expression
```

반환 타입을 생략하면 생성 대상이 C일 때 `void *`, Python일 때 `Any`가 기본이다.
`name=item`으로 하위 결과에 이름을 붙이면 action에서 사용할 수 있다.

```text
expr[expr_ty]:
    | l=expr '+' r=term { _PyAST_BinOp(l, Add, r, EXTRA) }
    | term
```

## 따옴표와 이름 모양도 문법 요소의 종류를 정한다

| 표기 | 뜻 |
|---|---|
| `'class'` | hard keyword |
| `"match"` | soft keyword |
| `NAME`, `NUMBER` | `Grammar/Tokens`에 정의된 토큰 |
| `invalid_*` | 두 번째 오류 진단 패스에서 사용하는 규칙 |
| `rule[type] (memo):` | 결과를 메모이제이션할 규칙 |

왼쪽 재귀 규칙은 표기 여부와 관계없이 메모이제이션을 사용한다. action에서 사용할 수
있는 대표 자동 값은 파서 상태 `p`와 소스 위치·arena 인수로 확장되는 `EXTRA`다.

규칙 실패는 다음 대안을 시험할 수 있는 정상 결과다. action이나 C API가 예외를 설정한
경우에는 전체 파싱을 중단하고 예외를 전파한다. `invalid_` 규칙은 반드시 구체적인
`SyntaxError` 또는 하위 예외를 발생시키도록 작성한다.

메모이제이션된 결과에는 AST 노드가 포함될 수 있으므로 action은 전달받은 노드를
제자리에서 변경하지 않는다. 변경이 필요하면 새 노드를 만든다.

## 정본과 생성 명령 대응표

| 정본 | 역할 | 명령 | 주요 생성 결과 |
|---|---|---|---|
| `Grammar/python.gram` | Python 문법과 AST action | `make regen-pegen` | `Parser/parser.c` |
| `python.gram`의 hard·soft keyword | keyword 목록 | `make regen-keyword` | `Lib/keyword.py` |
| `Grammar/Tokens` | 토큰 종류 | `make regen-token` | `pycore_token.h`, `Parser/token.c`, `Lib/token.py`, 토큰 문서 목록 |
| `Parser/Python.asdl` | AST 노드와 필드 | `make regen-ast` | `pycore_ast.h`, `Python/Python-ast.c` |
| `Tools/peg_generator/pegen/metagrammar.gram` | `.gram` 자체의 문법 | `make regen-pegen-metaparser` | Pegen 메타 파서 |

토큰과 문법을 함께 바꾸면 `regen-token`을 먼저 실행한다. hard keyword나 soft
keyword가 달라졌다면 `regen-keyword`도 필요하다. Windows에서는 다음 명령으로 관련
생성 작업을 수행할 수 있다.

```dos
PCbuild/build.bat --regen
```

생성 파일은 직접 편집하지 않는다.

## 파서 코드 위치

| 위치 | 역할 |
|---|---|
| `Tools/peg_generator/pegen/` | `.gram`에서 Python 또는 C 파서를 만드는 생성기 |
| `Parser/parser.c` | `python.gram`에서 생성된 CPython의 C 파서 |
| `Parser/pegen.c`, `Parser/pegen.h` | 생성 규칙이 사용하는 토큰·AST·오류 처리 지원 코드 |
| `Parser/peg_api.c` | 문자열이나 파일에서 AST 생성을 시작하는 고수준 내부 API |
| `Parser/action_helpers.c` | 문법 action에서 쓰는 복잡한 AST 구성 도우미 |
| `Parser/lexer/`, `Parser/tokenizer/` | 문자 입력을 토큰 스트림으로 변환 |

## 문법 실험과 C 파서 추적 명령

CPython 실행 파일을 다시 만들기 전에 Python으로 된 시험용 파서를 생성할 수 있다.

```shell
cd Tools/peg_generator
python -m pegen python <grammar-file>
python parse.py <source-file>
```

pydebug 빌드에서는 `python -d <source-file>`로 C 파서의 상세 추적을 볼 수 있다.

| 추적 문자 | 뜻 |
|---|---|
| `>` | 규칙 시도 |
| `-` | 규칙 실패 |
| `+` | 규칙 성공 |
| `!` | 예외를 감지하고 파서 스택을 되감음 |

대화형 모드는 별도 입력 처리가 섞이므로 상세 추적을 읽을 때는 파일 입력이 단순하다.

## 관심사별 테스트 위치

| 관심사 | 대표 위치 |
|---|---|
| 정상 문법과 실행 | `Lib/test/test_grammar.py` |
| 구문 오류 메시지·위치 | `Lib/test/test_syntax.py` |
| 파싱 중 예외 전파 | `Lib/test/test_exceptions.py` |
| Pegen 생성기 기능 | `Lib/test/test_peg_generator/` |

전체 메타 문법, action 예제와 오류 규칙의 배경은 기존 상세 문서
[제1부: 파서 가이드](../../../cpython-internals-notes/3.14/compiling-python-source-code/README.ko.md#제1부-파서-가이드)에
보존되어 있다. 실제 변경 절차는
[문법 변경은 영향 범위를 먼저 나눠야 빠짐없이 끝난다](../how-to/guide-change-cpython-grammar.ko.md)를
따른다.

[가이드 홈](../README.ko.md)
