# RustPython Compiler Tour

RustPython의 실제 소스를 읽으며 `sample.py`가 CLI 진입점에서 AST, 심볼 테이블, CFG, `CodeObject`, VM 실행으로 넘어가는 과정을 추적하는 독립 프로젝트다. 핵심은 컴파일러와 심볼 테이블이며 parser와 VM은 경계만 다룬다.

## 빠른 시작

필요한 도구, 실행 방식별 절차와 문제 해결은 [guide_running.md](guide_running.md)에 정리되어 있다.

저장소 루트에서 실제 컴파일 결과를 출력한다.

```bash
cargo run --manifest-path example_projects/compiler-tour/Cargo.toml
```

출력에는 다음 세 결과가 포함된다.

1. Ruff AST
2. `Symbol.scope`와 `Symbol.flags`를 분리한 심볼 테이블 트리
3. module, `make_counter`, `bump`의 `CodeObject` metadata와 bytecode

인터랙티브 투어는 저장소 루트에서 정적 서버를 실행해야 실제 Rust 파일을 읽을 수 있다.

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

브라우저에서 다음 주소를 연다.

```text
http://127.0.0.1:8000/example_projects/compiler-tour/tour/
```

투어는 좌우 화살표 키, 이전/다음 버튼, 좌측 breakpoint 목록으로 이동한다. 코드 줄이나 오른쪽 설명을 누르면 서로 대응하는 줄이 강조된다. 고정 줄 번호 대신 함수 시그니처 anchor로 현재 저장소 파일을 찾는다.

## 문서

- [guide_running.md](guide_running.md): artifact 도구, 웹 투어, RustPython sample 실행 방법
- [tutorial_compiler_pipeline.md](tutorial_compiler_pipeline.md): 텍스트로 읽는 순차 튜토리얼
- [guide_debugging.md](guide_debugging.md): LLDB, 내장 trace log, disassembly 재현 절차
- [reference_source_map.md](reference_source_map.md): 파일·함수·자료구조·opcode 대응 레퍼런스

## 읽는 범위

집중 범위의 상한은 17,233줄이다.

- `crates/codegen/src/compile.rs`의 대형 `tests` module 전까지: 13,803줄
- `crates/codegen/src/symboltable.rs`의 `tests` module 전까지: 3,430줄

실제로 고정 예제가 통과하는 branch만 투어에 나온다. 나머지 문법 branch는 레퍼런스에서 역할만 설명한다. Ruff parser 내부, optimizer 세부 pass, VM opcode dispatch 전체, PEP 649/695와 PEP 709 특수 경로는 첫 학습 범위에서 제외한다.

Python 3.14 동작 때문에 annotation이 없는 함수에도 내부 `__annotate__` table이 생성된다. 실행 도구는 이를 그대로 출력하지만, 인터랙티브 scope 지도는 사용자 코드의 세 scope만 표시한다.

## 검증

```bash
node example_projects/compiler-tour/validate.mjs
node --check example_projects/compiler-tour/tour/app.js
cargo fmt --manifest-path example_projects/compiler-tour/Cargo.toml -- --check
cargo test --manifest-path example_projects/compiler-tour/Cargo.toml
cargo clippy --manifest-path example_projects/compiler-tour/Cargo.toml --all-targets -- -D warnings
target/debug/rustpython -S example_projects/compiler-tour/sample.py
```

`validate.mjs`는 모든 투어 단계의 실제 파일, 시작·끝 anchor, 줄별 설명 anchor가 현재 표시 범위 안에 있는지 검사한다.
