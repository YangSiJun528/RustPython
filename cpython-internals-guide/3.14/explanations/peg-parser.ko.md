# PEG 파서는 토큰 위치와 대안 순서로 AST 하나를 확정한다

Python 문법에는 같은 토큰으로 시작하는 대안이 많다. `NAME`으로 시작한 한 줄은
대입문일 수도 있고 표현식 문장일 수도 있다. 그렇다면 CPython은 어느 대안을
선택하고, 실패한 시도와 성공한 결과를 어떻게 구분해 AST 하나를 만드는가?

CPython 3.14의 Pegen은 현재 토큰 위치에서 문법 대안을 적힌 순서대로 시험하고,
해당 규칙을 만족시키는 첫 대안의 action이 만든 값을 AST에 남긴다. lookahead와
cut은 대안을 시험할 경계를 좁히고, 메모이제이션과 왼쪽 재귀 처리는 같은 구간을
불필요하게 다시 읽지 않게 한다. 정상 문법이 모두 실패한 경우에만 `invalid_`
규칙을 켠 두 번째 패스를 시도한다. 이때 알려진 잘못된 모양과 일치하면 구체적인
`SyntaxError`를 만들고, 일치하지 않으면 첫 패스의 일반 오류 위치를 사용한다.

이 글의 출력과 문법 경로는 CPython 3.14.6에서 확인했다. `Grammar/python.gram`,
생성된 `Parser/parser.c`, 파서 런타임인 `Parser/pegen.c`는 CPython 내부 구현이며
다른 마이너·마이크로 버전에서 대안, action, AST 모양이 달라질 수 있다.

## 한 줄을 토큰과 AST로 함께 관찰한다

다음 예제는 표준 라이브러리의 `tokenize`와 `ast`를 사용한다. CPython 3.14.6에서
그대로 실행된다.

```python
import ast
import io
import tokenize

source = "result = value + 1\n"

for token in tokenize.generate_tokens(io.StringIO(source).readline):
    print(tokenize.tok_name[token.type], repr(token.string))

print(ast.dump(ast.parse(source, filename="example.py"), indent=2))
```

실제 출력은 다음과 같다.

```text
NAME 'result'
OP '='
NAME 'value'
OP '+'
NUMBER '1'
NEWLINE '\n'
ENDMARKER ''
Module(
  body=[
    Assign(
      targets=[
        Name(id='result', ctx=Store())],
      value=BinOp(
        left=Name(id='value', ctx=Load()),
        op=Add(),
        right=Constant(value=1)))])
```

이 출력은 출발점과 결과만 보여 준다. 중간에서 Pegen은 토큰을 문법 규칙에
대입하고, 대입문의 왼쪽과 오른쪽을 서로 다른 문맥의 AST 노드로 바꾼다.

## 토크나이저는 문법이 읽을 경계를 먼저 고정한다

Pegen은 소스 문자를 직접 한 글자씩 비교하지 않는다. `Parser/pegen.c`의
`_PyPegen_fill_token()`은 CPython 토크나이저에서 다음 토큰을 받아 파서의 토큰
배열에 채운다. 예제의 흐름은 다음처럼 단순화된다.

```text
result = value + 1\n
    ↓ tokenizer
NAME  '='  NAME  '+'  NUMBER  NEWLINE  ENDMARKER
    ↓ generated PEG parser
Module → Assign → Name(Store), BinOp(Name(Load), Add, Constant)
```

공개 `tokenize` 출력에서 `=`와 `+`는 모두 `OP`로 보인다. 그러나 생성된 C 파서는
문법의 `'='`, `'+'` 같은 리터럴에 대응하는 정확한 토큰 종류를 사용한다. 위
스크립트는 토큰 경계를 관찰하는 재현 도구이지, 내부 `Token` 구조체를 그대로
인쇄하는 도구는 아니다. 인코딩, 들여쓰기, 줄 계속, 괄호 깊이도 먼저 토크나이저가
정리한 뒤 파서로 넘어간다.

## 대입 대안이 표현식 대안보다 먼저 성공한다

3.14.6의 `Grammar/python.gram`에서 예제가 지나는 핵심 규칙만 줄이면 다음과 같다.

```text
file: [statements] ENDMARKER
statements: statement+
statement:
    | compound_stmt
    | simple_stmts
simple_stmts:
    | simple_stmt !';' NEWLINE
    | ';'.simple_stmt+ [';'] NEWLINE
simple_stmt (memo):
    | assignment
    | &"type" type_alias
    | star_expressions
    | ...
assignment:
    | NAME ':' expression ...
    | ...
    | (star_targets '=')+ annotated_rhs !'='
    | single_target augassign ~ annotated_rhs
    | invalid_assignment
```

파서는 다음 순서로 결과를 좁힌다.

1. `file`은 줄 끝까지 문장들을 읽고 마지막 `ENDMARKER`까지 요구한다.
2. 첫 토큰 `result`는 `def`, `if`, `class` 같은 compound statement를 시작하지
   않으므로 `statement`의 `simple_stmts` 대안으로 간다.
3. `simple_stmt`는 `assignment`를 `star_expressions`보다 먼저 시험한다. 문법 원본도
   이 순서가 뒤집히면 단순 대입이 `SyntaxError`가 된다고 명시한다.
4. `result =`가 `(star_targets '=')+`에 맞고, 오른쪽 `value + 1`이
   `annotated_rhs`에 맞으며, 뒤에 또 `=`이 없다는 `!'='` 검사까지 성공한다.
5. 하위 target 규칙의 action이 왼쪽 `Name`에 `Store` 문맥을 설정하고, 바깥 대안의
   action은 `_PyAST_Assign()`으로 `Assign` 노드를 만든다.

순서 있는 선택은 “여러 해석 중 가장 그럴듯한 것을 나중에 고른다”는 뜻이 아니다.
같은 규칙과 토큰 위치에서는 앞 대안의 성공이 그 규칙의 결과다. 그래서 공통
접두사가 있는 대안은 긴 형태나 더 구체적인 형태가 짧은 형태에 가려지지 않는지
검토해야 한다.

## 오른쪽 식은 왼쪽 재귀를 성장시켜 덧셈 구조를 만든다

대입문의 오른쪽 `value + 1`은 표현식 규칙을 내려가 `sum`에 도달한다. 실제 문법의
핵심은 다음과 같다.

```text
sum:
    | sum '+' term  { BinOp(left, Add, right) }
    | sum '-' term  { BinOp(left, Sub, right) }
    | term
```

이 규칙은 왼쪽에서 자신을 다시 부르므로 순진한 재귀 하강 파서라면 입력을 소비하기
전에 무한 재귀한다. Pegen은 해당 규칙과 시작 위치의 결과를 메모하고, 먼저 얻은
짧은 결과를 더 긴 일치가 나오지 않을 때까지 성장시킨다. 예제에서는 `value`만
읽은 결과가 `value + 1`까지 확장되어 `BinOp`가 된다. 같은 구조가
`a + b + c`를 왼쪽 결합인 `(a + b) + c`로 만드는 기반이다.

`(memo)`가 붙은 규칙도 `(규칙, 토큰 위치)`에서 성공 여부, 만들어진 값, 다음 토큰
위치를 재사용한다. 모든 규칙을 무조건 캐시하는 전형적인 packrat 설명과 달리,
CPython의 생성 문법은 필요한 규칙에 `(memo)`를 표시한다. 왼쪽 재귀 규칙은 성장
알고리즘 자체가 캐시에 의존하므로 표시 여부와 관계없이 메모이제이션된다.

## lookahead와 cut은 소비가 아니라 선택 경계를 바꾼다

긍정 lookahead `&e`와 부정 lookahead `!e`는 현재 위치를 움직이지 않고 다음 입력의
모양만 검사한다. 예제의 `!';'`는 세미콜론이 바로 오지 않을 때 첫
`simple_stmts` 대안을 허용하고, 대입문의 `!'='`은 연쇄 대입의 오른쪽을 덜 읽은
채 성공하는 일을 막는다.

cut `~`는 위치를 검사하는 연산자가 아니다. 해당 지점을 지난 뒤 같은 대안이
실패하면 그 규칙 안의 뒤쪽 대안으로 돌아가지 못하게 한다. 3.14.6의 증강 대입 규칙은
`single_target augassign ~ annotated_rhs`에서 연산자를 확인한 뒤 cut을 둔다.
`x +=`까지 읽고 오른쪽 식에서 실패하면 `assignment` 규칙의 나머지 대안은 시험하지
않는다. 다만 호출자인 `simple_stmt`는 이후 `star_expressions` 같은 자기 대안을 시험할
수 있다. cut 자체가 “오른쪽 식이 없다”는 전용 오류를 만드는 것도 아니다.

lookahead와 cut을 “성능 힌트”로만 보면 안 된다. 둘은 어느 입력이 어떤 대안에서
성공하거나 실패하는지와 오류 위치를 바꿀 수 있다. 반대로 cut 하나가 파서 전체의
모든 백트래킹을 영구히 끄는 것도 아니다. 효력은 그 cut이 놓인 대안과 규칙의
선택 경계에 한정된다.

## action은 토큰열을 소스 의미가 있는 AST로 바꾼다

문법 대안이 성공하면 중괄호 안 action이 하위 결과를 받아 AST 값을 만든다.
예제에서 중요한 변환은 다음과 같다.

```text
result              → Name(id='result', ctx=Store())
value               → Name(id='value', ctx=Load())
value + 1           → BinOp(left=..., op=Add(), right=Constant(1))
result = value + 1  → Assign(targets=[...], value=...)
파일 전체           → Module(body=[...])
```

괄호와 공백 같은 표면 정보는 대부분 AST 구조에서 사라진다. 반면 이름을 읽는지
쓰는지, 연산자가 무엇인지, 어느 소스 범위에서 왔는지는 이후 심볼 분석과 오류
표시에 필요하므로 AST 노드와 위치 정보에 남는다. action은 “문법을 한 번 더
검사하는 임의의 C 코드”가 아니다. 문법이 이미 인정한 구조를 AST로 표현하는
역할에 집중해야 공개 문법과 구현이 어긋나지 않는다.

메모이제이션된 규칙의 AST 값은 다른 탐색 경로에서 다시 쓰일 수 있다. action이
전달받은 노드를 제자리에서 바꾸면 캐시에 든 결과까지 오염될 수 있다.
CPython 문법은 문맥 변경이 필요할 때 새 노드나 안전한 도우미를 사용한다.

## 정상 실패와 구문 오류는 두 패스로 분리된다

대안 하나의 실패는 흔히 오류가 아니라 “다음 대안을 시험하라”는 제어 흐름이다.
action이나 C API가 실제 예외를 설정한 경우와도 구분해야 한다. 정상 규칙만으로
파일 전체를 만들지 못했을 때 `Parser/pegen.c`의 `_PyPegen_run_parser()`는 상태를
초기화하고 `call_invalid_rules`를 켜 두 번째 패스를 실행한다.

```text
1차: 정상 규칙만 사용
├─ 성공 → AST 반환
└─ 실패
   ↓
2차: 정상 규칙 + invalid_ 규칙
├─ 알려진 잘못된 모양 감지 → 구체적인 SyntaxError
└─ 감지 못함 → 1차 패스의 일반 오류 위치 사용
```

`invalid_` 규칙은 오류 AST를 복구해 실행을 계속하기 위한 규칙이 아니다. 유효한
입력의 빠른 경로를 무겁게 만들지 않으면서, 흔한 잘못된 패턴에 정확한 메시지와
위치를 부여하는 진단 규칙이다.

## AST 하나는 유일한 표면 표현이나 영구 규격을 뜻하지 않는다

- PEG의 순서 있는 선택은 소스에 가능한 의미가 하나뿐임을 수학적으로 증명하지
  않는다. 문법 작성자가 대안 순서와 제어 연산자로 하나의 결과를 정한다.
- 토큰 스트림은 AST가 아니다. 같은 AST를 만드는 괄호·공백 차이는 토큰에는
  보이지만 AST에서 사라질 수 있다.
- AST는 바이트코드가 아니다. 이름의 local·global 분류와 제어 흐름 배치는 이후
  컴파일 단계에서 결정된다.
- `ast.parse()`의 공개 결과와 `Grammar/python.gram`의 구체적인 대안·C action을
  같은 안정성 수준으로 보면 안 된다. 후자는 CPython 버전에 종속된 내부 구현이다.

문법 표기와 생성 파일·명령을 조회하려면
[Pegen 문법은 표기·생성 관계·명령으로 찾아본다](../reference/pegen-and-parser.ko.md)를
사용한다. AST 이후 이름과 실행 경로가 굳는 과정은 다음 설명에서 이어진다.

---

[설명 문서 목록](README.ko.md)

이전:

[설명 모음 소개](README.ko.md)

다음:

[소스에서 CodeObject까지](source-to-code-object.ko.md)

관련 글:

- [Pegen 문법과 파서 파일](../reference/pegen-and-parser.ko.md)
