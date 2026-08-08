# How to reproduce the compiler trace with LLDB

이 가이드는 `sample.py` 한 파일을 RustPython CLI에서 실행하고 compiler 핵심 지점에 직접 멈추는 절차만 다룬다. macOS의 `rust-lldb` 기준이다.

## 준비

저장소 루트에서 debug binary를 만든다.

```bash
cargo build
```

먼저 debugger 없이 결과를 확인한다.

```bash
target/debug/rustpython -S example_projects/compiler-tour/sample.py
```

예상 출력:

```text
12
18
```

`-S`는 `site` import를 생략해 sample 외의 startup Python 컴파일을 줄인다.

## 사전 기록된 compiler artifact 보기

LLDB 전에 작은 독립 도구로 AST, 심볼 트리, bytecode를 확인한다.

```bash
cargo run --manifest-path example_projects/compiler-tour/Cargo.toml
```

다른 파일도 같은 도구로 볼 수 있다.

```bash
cargo run --manifest-path example_projects/compiler-tour/Cargo.toml -- path/to/input.py
```

## 내장 trace log 보기

RustPython codegen에는 statement, expression, 최종 code object용 `trace!`가 이미 있다. core를 수정하지 않고 켤 수 있다.

```bash
RUST_LOG=rustpython_codegen=trace \
  target/debug/rustpython -S example_projects/compiler-tour/sample.py
```

이 로그는 AST 방문 순서는 보여주지만 `Symbol.scope`의 중간 변화는 보여주지 않는다. 그 부분은 LLDB를 쓴다.

## LLDB 시작

프로젝트에 포함된 함수 이름 breakpoint를 불러온다.

```bash
rust-lldb target/debug/rustpython
```

LLDB prompt에서:

```text
(lldb) command source example_projects/compiler-tour/debug/compiler-tour.lldb
(lldb) breakpoint list
(lldb) run
```

command file은 다음 함수에 breakpoint를 둔다.

| 순서 | 함수 | 관찰 목적 |
|---:|---|---|
| 1 | `_compile_with_syntax_warning_handler` | parser 직전 source/mode |
| 2 | `compile_program_with_syntax_warning_handler` | symbol pass와 codegen pass의 바깥 구조 |
| 3 | `SymbolTableBuilder::register_name` | 각 이름의 raw `SymbolUsage` |
| 4 | `SymbolTableBuilder::finish` | raw table과 분석 table의 경계 |
| 5 | `SymbolTableAnalyzer::analyze_symbol_table` | child-first block 분석 |
| 6 | `SymbolTableAnalyzer::analyze_symbol` | 이름 하나의 최종 scope 판정 |
| 7 | `Compiler::compile_name` | scope를 opcode family로 변환 |
| 8 | `CodeInfo::finalize_code` | CFG를 CodeObject로 조립 |

함수 이름 breakpoint는 줄 번호보다 변경에 강하다. 현재 debug binary에서 각 이름이 정확히 한 location으로 해석되는 것을 확인했다.

## parser 진입에서 보기

첫 breakpoint에서:

```text
(lldb) bt 12
(lldb) frame variable mode
(lldb) frame variable source_file
(lldb) source list
```

호출 stack은 다음 순서를 포함한다.

```text
run_rustpython
→ VirtualMachine::run_string 또는 run_simple_file_inner
→ VirtualMachine::compile
→ VirtualMachine::compile_with_opts
→ rustpython_compiler::_compile_with_syntax_warning_handler
```

다음 breakpoint로 이동한다.

```text
(lldb) continue
```

## 이름 등록 보기

`register_name`은 이름마다 반복해서 멈춘다.

```text
(lldb) frame variable name
(lldb) frame variable role
(lldb) frame variable self.tables
```

원하는 이름만 보고 싶으면 조건 breakpoint를 새로 만들기보다 일단 `continue`로 `total`이 나올 때까지 이동하는 편이 단순하다. 해당 함수는 optimized dependency code라 일부 local이 LLDB에서 unavailable일 수 있다. 그 경우 source line과 `self.tables`의 마지막 table을 본다.

이 breakpoint가 너무 자주 멈추면 비활성화한다.

```text
(lldb) breakpoint disable 3
```

번호가 다르면 `breakpoint list`에서 `register_name` 번호를 확인한다.

## 첫 pass와 두 번째 pass 경계 보기

`SymbolTableBuilder::finish`에서:

```text
(lldb) source list
(lldb) frame variable self.tables
```

함수 첫 줄에서는 `self.tables`에 raw flags가 들어 있고 많은 `scope`가 `Unknown`이다. `analyze_symbol_table` 호출을 지난 뒤 반환값을 확실히 보려면 현재 revision의 handoff line에 별도 breakpoint를 둔다.

```bash
rust-lldb target/debug/rustpython \
  -o "breakpoint set --file $(pwd)/crates/codegen/src/compile.rs --line 508" \
  -o "run -S example_projects/compiler-tour/sample.py"
```

멈춘 뒤:

```text
(lldb) frame variable symbol_table
(lldb) frame variable symbol_table.name
(lldb) frame variable symbol_table.symbols
(lldb) frame variable symbol_table.sub_tables
```

현재 revision에서 확인할 핵심 값:

```text
make_counter.total scope=Cell flags=DEF_LOCAL
bump.total         scope=Free flags=DEF_LOCAL|DEF_NONLOCAL|USE
bump.rate          scope=GlobalImplicit flags=USE
```

`IndexMap` 내부가 LLDB에서 읽기 불편하면 독립 artifact 도구의 출력과 같은 시점이므로 그 결과를 사용한다.

## 이름별 scope 판정 보기

`SymbolTableAnalyzer::analyze_symbol`에서:

```text
(lldb) frame variable symbol.name
(lldb) frame variable symbol.scope
(lldb) frame variable symbol.flags
(lldb) frame variable st_typ
(lldb) source list
```

함수 진입 시 scope가 아직 `Unknown`일 수 있다. 함수가 끝난 뒤 값을 보려면:

```text
(lldb) finish
(lldb) frame variable symbol
```

Rust borrow와 optimization 때문에 caller에서 해당 reference가 unavailable이면 다음 이름에서 source branch를 확인하고 최종 결과는 handoff breakpoint에서 검증한다.

## scope에서 opcode로 넘어가는 순간 보기

`Compiler::compile_name`에서:

```text
(lldb) frame variable name
(lldb) frame variable usage
(lldb) source list
```

함수 진입점에서는 `actual_scope`와 `op_type`이 아직 생성되지 않았다. 현재 revision에서 두 값이 계산된 뒤에 멈추려면:

```bash
rust-lldb target/debug/rustpython \
  -o "breakpoint set --file $(pwd)/crates/codegen/src/compile.rs --line 3256" \
  -o "run -S example_projects/compiler-tour/sample.py"
```

멈춘 뒤:

```text
(lldb) frame variable name usage actual_scope op_type
```

예상 대응:

```text
total in bump → Free → Deref
step in bump  → Local → Fast
rate in bump  → GlobalImplicit → Global
rate in top   → Local → Name
```

## 최종 CodeObject 보기

`CodeInfo::finalize_code`에서 `finish`로 반환한 뒤 code object를 보거나 독립 도구의 출력을 사용한다. Python 수준의 disassembly를 같이 보고 싶으면 RustPython 자체 `dis`를 사용한다.

```bash
target/debug/rustpython -S -c $'import dis\nsource = open("example_projects/compiler-tour/sample.py").read()\ncode = compile(source, "sample.py", "exec")\ndis.dis(code)'
```

확인할 instruction:

```text
make_counter: MAKE_CELL total, STORE_DEREF total
bump: COPY_FREE_VARS, LOAD_DEREF total, LOAD_FAST_BORROW step,
      LOAD_GLOBAL rate, STORE_DEREF total
```

## 세션 종료

```text
(lldb) quit
```

현재 줄 번호가 바뀌면 함수 이름 breakpoint는 그대로 사용할 수 있다. handoff와 `op_type`용 줄 breakpoint만 [`tour/tour-data.js`](tour/tour-data.js)의 해당 함수 anchor를 보고 갱신한다. `node example_projects/compiler-tour/validate.mjs`는 투어 anchor가 이동했는지 자동 검사한다.
