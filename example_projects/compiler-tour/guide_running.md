# How to run the RustPython Compiler Tour

이 가이드는 compiler tour의 세 실행 방식을 재현하는 절차를 설명한다.

1. Rust artifact 도구로 AST, 심볼 테이블, bytecode 출력
2. 브라우저에서 31단계 interactive tour 실행
3. RustPython으로 고정 sample 실행

모든 명령은 RustPython 저장소 루트에서 실행한다.

## 준비

필요한 도구:

- 저장소가 사용하는 Rust toolchain과 Cargo
- interactive tour용 Python 3 정적 HTTP 서버
- source anchor 검증을 실행할 경우 Node.js

현재 위치가 저장소 루트인지 확인한다.

```bash
test -f example_projects/compiler-tour/Cargo.toml
```

처음 빌드할 때 Cargo가 crates.io와 저장소에 고정된 Ruff Git dependency를 내려받을 수 있다.

## AST, 심볼 테이블, bytecode 출력

고정된 [`sample.py`](sample.py)를 compiler crate에 직접 넣는다.

```bash
cargo run --manifest-path example_projects/compiler-tour/Cargo.toml
```

출력은 다음 순서로 구성된다.

```text
0. 원본 source
1. Ruff AST
2. 분석이 끝난 SymbolTable 트리
3. 중첩 CodeObject와 bytecode
```

심볼 출력에서 먼저 확인할 값은 다음 세 개다.

```text
make_counter.total  scope=Cell
bump.total          scope=Free
bump.rate           scope=GlobalImplicit
```

bytecode 출력에서는 이 판정이 다음 명령으로 연결되는지 확인한다.

```text
make_counter.total  → MakeCell, StoreDeref
bump.total          → LoadDeref, StoreDeref
bump.rate           → LoadGlobal
```

### 다른 Python 파일 분석

첫 번째 command-line argument로 입력 파일을 지정한다.

```bash
cargo run \
  --manifest-path example_projects/compiler-tour/Cargo.toml \
  -- path/to/input.py
```

이 도구는 compiler artifact만 출력한다. 입력 Python 코드를 VM에서 실행하지 않는다.

## interactive tour 실행

브라우저가 실제 저장소 Rust 파일을 읽어야 하므로 HTML 파일을 직접 열지 않고 저장소 루트에서 HTTP 서버를 시작한다.

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

브라우저에서 다음 주소를 연다.

```text
http://127.0.0.1:8000/example_projects/compiler-tour/tour/
```

이동 방법:

- 좌우 화살표 키
- 화면 아래 이전/다음 버튼
- 왼쪽의 31개 breakpoint 목록
- URL의 `?step=27`과 같은 단계 번호

코드 줄 또는 오른쪽의 줄 설명을 누르면 대응하는 항목이 함께 강조된다. 상단에 `실제 저장소 소스 사용 중`이 표시되면 source fetch가 성공한 상태다.

서버를 종료할 때는 서버를 실행한 terminal에서 `Ctrl-C`를 누른다.

### 다른 포트 사용

8000번 포트를 이미 사용 중이면 예를 들어 8001번으로 바꾼다.

```bash
python3 -m http.server 8001 --bind 127.0.0.1
```

```text
http://127.0.0.1:8001/example_projects/compiler-tour/tour/
```

## sample을 RustPython에서 실행

compiler artifact가 아니라 실제 VM 결과를 확인한다.

```bash
cargo run -- -S example_projects/compiler-tour/sample.py
```

예상 출력:

```text
12
18
```

이미 debug binary를 만들었다면 Cargo 실행 단계를 생략할 수 있다.

```bash
target/debug/rustpython -S example_projects/compiler-tour/sample.py
```

`-S`는 `site` import를 생략해 sample 외의 startup Python 컴파일을 줄인다.

## source anchor 검증

interactive tour는 고정 줄 번호가 아니라 함수와 구문 anchor로 현재 source 범위를 찾는다. 저장소 source가 바뀐 뒤에는 다음 검사를 실행한다.

```bash
node example_projects/compiler-tour/validate.mjs
```

성공 결과:

```text
Validated 31 live-source steps across 7 phases.
```

## 문제 해결

### 웹 화면에 source load 오류가 표시된다

다음을 확인한다.

1. `tour/index.html`을 `file://`로 직접 열지 않았는가?
2. HTTP 서버를 RustPython 저장소 루트에서 시작했는가?
3. 주소에 `/example_projects/compiler-tour/tour/`가 포함되어 있는가?

### `target/debug/rustpython`이 없다

debug binary를 먼저 만든다.

```bash
cargo build
```

또는 binary 경로 대신 `cargo run -- -S ...` 명령을 사용한다.

### source 변경 후 특정 단계가 열리지 않는다

`validate.mjs`로 이동한 anchor를 찾는다. 실패 메시지에 나온 step의 [`tour/tour-data.js`](tour/tour-data.js)에서 `anchor`, `endAnchor`, 줄별 `match`를 현재 source 문자열에 맞춘다.

### LLDB로 같은 흐름에 멈추고 싶다

함수 이름 breakpoint와 관찰할 local 값은 [guide_debugging.md](guide_debugging.md)를 따른다.
