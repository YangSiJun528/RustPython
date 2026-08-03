# 문법 변경은 영향 범위를 먼저 나눠야 빠짐없이 끝난다

CPython 문법을 바꿀 때 `Grammar/python.gram`만 고쳐서는 작업이 끝나지 않는다.
변경이 기존 토큰과 AST를 재사용하는지, 토큰화까지 건드리는지, AST 구조나 실행
의미까지 바꾸는지부터 가려야 한다. 이 판단에 맞춰 정본 파일과 생성물, 소비자를
차례로 갱신한다.

이 가이드는 영향 범위 분류 → 정본 수정 → 재생성 → 소비자 갱신 → 검증 순서로
진행한다. 모든 파일을 무조건 수정하는 체크리스트는 아니다. 실제로 영향받는 층을
빠뜨리지 않도록 작업 범위를 좁혀 주는 절차다.

> 명령과 파일 경로는 CPython 3.14 브랜치를 기준으로 한다. 다른 버전에서는 먼저
> 해당 브랜치의 `InternalDocs`와 `Makefile`을 확인한다.

## 1. 새 구문이 처음 바꾸는 층부터 찾는다

| 변경 유형 | 판단 질문 | 최소 확인 범위 |
|---|---|---|
| 기존 토큰·AST 재사용 | 기존 토큰 조합과 AST 노드만으로 표현 가능한가? | `Grammar/python.gram`, 테스트, 언어 문서 |
| 토큰화 변경 | 문자 경계나 새 토큰 종류가 필요한가? | 위 범위 + `Grammar/Tokens`, `Parser/lexer/`, `Lib/tokenize.py` |
| AST·의미 변경 | 새 노드·필드 또는 새 실행 규칙이 필요한가? | 위 범위 + `Parser/Python.asdl`, AST 검증, compiler, unparser, AST 문서 |

새 키워드를 추가해도 새 토큰 타입이 필요하지 않을 수 있다. 새 표면 문법을 기존 AST로
표현할 수 있다면 ASDL도 그대로 둔다. 변경 범위를 필요 이상으로 넓히면 생성 파일과
공개 API까지 불필요하게 달라진다.

## 2. 생성 파일이 아니라 정본을 수정한다

- 구문과 AST 생성 action: `Grammar/python.gram`
- 토큰 종류: `Grammar/Tokens`
- 문자를 토큰으로 읽는 방식: `Parser/lexer/`
- AST 노드와 필드: `Parser/Python.asdl`
- AST 제약: `Python/ast.c`
- 컴파일 단계 조율: `Python/compile.c`
- AST에서 의사 명령 생성: `Python/codegen.c`

`Parser/parser.c`, `Python/Python-ast.c`, `Include/internal/pycore_ast.h` 같은 파일은
생성 결과다. 직접 수정하면 다음 재생성 때 변경이 사라진다.

`python.gram`의 인식 조건은 문법 규칙에 쓴다. action은 이미 인식에 성공한 구문을
AST로 만드는 역할만 맡는다. action 안에서 AST를 검사해 구문을 추가로 거부하면 공개
문법과 실제 동작이 어긋날 수 있다.

## 3. 의존하는 정의부터 재생성한다

변경한 정본에 맞춰 필요한 명령만 실행한다.

```shell
make regen-token          # Grammar/Tokens를 바꾼 경우
make regen-ast            # Parser/Python.asdl을 바꾼 경우
make regen-pegen          # Grammar/python.gram을 바꾼 경우
make regen-keyword        # hard·soft keyword 목록이 바뀐 경우
```

토큰과 문법을 함께 바꿨다면 `regen-token`을 `regen-pegen`보다 먼저 실행한다. AST와
문법 action을 함께 바꿨다면 새 AST 정의를 만든 뒤 파서를 생성한다. 이 순서가 변경
결과를 확인하기도 쉽다. hard keyword나 soft keyword를 추가하거나 없앴다면
`regen-keyword`로 `Lib/keyword.py`도 갱신한다. Windows에서는 저장소의 Visual Studio
재생성 기능이나 다음 명령을 쓴다.

```dos
PCbuild/build.bat --regen
```

동작이 이전 상태에 머무는 것처럼 보이면 오래된 빌드 산출물을 의심하고 `make clean` 후
다시 빌드한다. 생성 뒤에는 정본 변경에 대응하는 생성 diff만 생겼는지 확인한다.

## 4. 새 표현을 읽는 모든 소비자를 확인한다

| 변경 내용 | 함께 확인할 소비자 |
|---|---|
| 새 AST 노드·필드 | `Python/ast.c`, compiler, `Python/ast_unparse.c`, `Lib/ast.py`, `Doc/library/ast.rst` |
| 새 리터럴·주석·토큰 경계 | `Parser/lexer/`, `Lib/tokenize.py`, 토큰 API 문서 |
| 함수·클래스 선언 모양 | `pyclbr`처럼 소스를 부분적으로 읽는 도구 |
| 새 언어 구문과 의미 | `Doc/reference/`의 관련 언어 레퍼런스 |

파서가 AST를 만들었어도 기능은 아직 완성되지 않았다. compiler가 새 AST를 명령으로
낮추지 못하면 실행할 수 없다. 공개 `ast` API와 unparser가 새 구조를 모르면 관련 도구도
깨진다.

## 5. 정상 입력과 실패 입력을 따로 검증한다

검증 범위는 작은 정상 예제부터 넓힌다.

1. 가장 작은 정상 예제가 의도한 AST를 만드는지 확인한다.
2. 그 AST가 컴파일되고 예상한 의미로 실행되는지 확인한다.
3. 경계 사례와 중첩된 문맥을 확인한다.
4. 잘못된 입력이 기대한 `SyntaxError` 위치와 메시지를 내는지 확인한다.
5. 유효한 코드 뒤에 별도 오류를 붙여 `invalid_` 규칙이 앞부분을 과하게 잡지 않는지 확인한다.
6. 영향받는 `ast.unparse()`, `tokenize`, `pyclbr` 동작을 확인한다.

테스트 위치는 보통 다음 관심사로 고른다.

- 문법 수용과 실행: `Lib/test/test_grammar.py`
- 오류 메시지와 위치: `Lib/test/test_syntax.py`
- 예외 전파: `Lib/test/test_exceptions.py`
- Pegen 자체 기능: `Lib/test/test_peg_generator/`

## 6. 생성물·구현·문서가 같은 기능을 말하면 끝난다

아래 조건을 모두 만족해야 작업이 끝난다.

- 정본과 생성 파일이 일치한다.
- 외부에서 직접 만든 같은 형태의 AST도 올바르게 검증된다.
- compiler가 실행 가능한 CodeObject를 만든다.
- 관련 unparser와 소스 분석 도구가 새 표현을 처리한다.
- 정상·오류 회귀 테스트가 모두 있다.
- AST API 문서와 언어 레퍼런스가 실제 동작을 설명한다.

각 파일의 역할과 예외적인 변경 지점은 기존 상세 문서의
[CPython 문법 변경](../../../cpython-internals-notes/3.14/compiling-python-source-code/README.ko.md#제3부-cpython-문법-변경)을
참고한다. Pegen 표기와 재생성 명령만 찾고 싶다면
[Pegen 참조](../reference/pegen-and-parser.ko.md)를 사용한다.

[가이드 홈](../README.ko.md)
