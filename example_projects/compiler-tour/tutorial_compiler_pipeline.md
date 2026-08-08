# Tutorial: `sample.py`가 RustPython bytecode가 되는 과정

이 튜토리얼의 목표는 한 번의 파일 실행을 기준으로 RustPython compiler의 제어 흐름과 데이터 흐름을 연결하는 것이다. 완료하면 다음 질문에 코드 위치로 답할 수 있어야 한다.

- Python 파일은 어느 Rust 함수에서 parser로 들어가는가?
- 심볼 테이블은 왜 AST를 두 단계로 분석하는가?
- `Local`, `Cell`, `Free`, `GlobalImplicit`는 어떻게 결정되는가?
- 그 결과가 어떻게 `LoadFast`, `LoadDeref`, `LoadGlobal`로 바뀌는가?
- CFG는 어디에서 최종 `CodeObject`가 되는가?

이 문서는 학습 순서만 다룬다. 직접 debugger를 조작하는 절차는 [guide_debugging.md](guide_debugging.md)에 있다.

## 1. 관찰할 프로그램

[`sample.py`](sample.py)는 다음 세 lexical scope를 만든다.

```text
top (Module)
└── make_counter (Function)
    └── bump (Function)
```

핵심 이름은 `total`이다.

```python
def make_counter(start):
    total = start

    def bump(step=1):
        nonlocal total
        total += step * rate
        return total
```

`make_counter`는 `total`을 정의한다. `bump`는 같은 저장 공간을 읽고 갱신한다. 따라서 최종 결론은 다음과 같다.

```text
make_counter.total = Cell
bump.total         = Free
```

모듈의 `rate`는 다르다. module은 일반 이름의 closure provider가 아니므로 `bump.rate`는 `Free`가 아니라 `GlobalImplicit`다.

## 2. 전체 호출 흐름

파일 실행의 실제 경로는 다음과 같다.

```text
src/main.rs::main
→ src/lib.rs::run
→ src/lib.rs::run_rustpython
→ src/lib.rs::run_file
→ VirtualMachine::run_simple_file_inner
→ VirtualMachine::compile_with_opts
→ rustpython_compiler::_compile_with_syntax_warning_handler
→ ruff_python_parser::parse
→ compile_top_with_syntax_warning_handler
→ scan_module_symbols
→ SymbolTableBuilder AST walk
→ SymbolTableAnalyzer scope resolution
→ Compiler AST walk
→ CodeInfo::finalize_code
→ VirtualMachine::run_code_obj
```

이 중 compiler의 중심은 다음 두 파일이다.

- `crates/codegen/src/symboltable.rs`: 이름 수집과 scope 판정
- `crates/codegen/src/compile.rs`: 분석된 scope를 instruction과 CFG로 변환

`crates/compiler/src/lib.rs`는 parser와 codegen을 묶는 facade다. 이름 때문에 이 파일이 주 구현처럼 보이지만, 실제 compiler 본체는 `crates/codegen`에 있다.

## 3. CLI에서 compiler 경계까지

[`src/main.rs`](../../src/main.rs)의 `main`은 `InterpreterBuilder`를 만들고 `rustpython::run`을 부른다. [`src/lib.rs`](../../src/lib.rs)의 `run`은 argv를 `RunMode`로 바꾸고 `Interpreter` 안에서 `run_rustpython`을 호출한다.

현재 입력은 파일이므로 `RunMode::Script`가 선택된다. host filesystem 경로에서는 [`crates/vm/src/vm/python_run.rs`](../../crates/vm/src/vm/python_run.rs)의 `run_simple_file_inner`가 다음 순서로 실행된다.

1. 파일 bytes를 읽는다.
2. NUL byte를 거부한다.
3. UTF-8 `String`으로 바꾼다.
4. `self.compile(&source, Mode::Exec, path)`를 부른다.
5. 성공한 `PyCode`를 `run_code_obj`에 넘긴다.

중요한 경계는 4와 5 사이이다. 컴파일이 끝나기 전에는 Python 명령이 하나도 실행되지 않는다.

[`crates/vm/src/vm/compile.rs`](../../crates/vm/src/vm/compile.rs)의 `compile_with_opts`는 warning 처리기를 붙이고 독립 `rustpython_compiler` crate를 호출한다. 반환된 compiler-core `CodeObject`는 여기서 VM의 `PyCode`가 된다.

## 4. SourceFile과 Ruff AST

[`crates/compiler/src/lib.rs`](../../crates/compiler/src/lib.rs)의 public `compile`은 `&str`와 `source_path`를 `SourceFile`로 묶는다. `SourceFile`은 Ruff의 byte offset range를 Python 오류의 행·열로 되돌리는 기준이다.

`_compile_with_syntax_warning_handler`는 RustPython mode를 Ruff mode로 바꾼다.

| RustPython mode | Ruff mode | 용도 |
|---|---|---|
| `Exec` | `Module` | 파일과 `exec` |
| `Eval` | `Expression` | `eval` |
| `Single` | `Module` | REPL 한 입력 |
| `BlockExpr` | `Module` | embedding block expression |

`parser::parse`가 성공하면 `parsed.into_syntax()`가 `ruff_python_ast::Mod`를 반환한다. Ruff parser 자체는 root `Cargo.toml`에서 tag가 고정된 외부 RustPython fork다. 여기서는 AST 경계까지만 읽는다.

[`crates/codegen/src/compile.rs`](../../crates/codegen/src/compile.rs)의 `compile_top_with_syntax_warning_handler`는 future flags를 계산하고 AST preprocessing을 적용한 후 `Mod::Module + Mode::Exec`를 `compile_program_with_syntax_warning_handler`로 보낸다.

## 5. 왜 심볼 테이블이 먼저 필요한가

다음 코드를 생각한다.

```python
def f():
    print(x)
    global x
```

첫 `x`를 보는 순간만으로는 local, free, global 중 무엇인지 확정할 수 없다. 함수 뒤쪽의 `global x`, 중첩 함수의 사용, `nonlocal` binding 검증까지 block 전체를 보아야 한다.

그래서 `compile_program_with_syntax_warning_handler`는 다음 순서를 강제한다.

```text
let symbol_table = scan_module_symbols(...);  // 전체 분석 완료
let mut compiler = Compiler::new(...);
compiler.compile_program(ast, symbol_table);  // 분석 결과로 codegen
let code = compiler.exit_scope();             // CFG finalize
```

여기서 “2-pass”는 두 의미가 겹친다.

1. 심볼 테이블 내부: raw DEF/USE 수집 후 scope resolution
2. compiler 전체: 심볼 분석용 AST walk 후 codegen용 AST walk

## 6. 심볼 테이블 첫 단계: 사실 수집

`SymbolTable::scan_program_with_options`는 다음 세 호출로 구성된다.

```text
SymbolTableBuilder::new
→ builder.scan_statements(module.body)
→ builder.finish
```

### 6.1 scope stack

`SymbolTableBuilder::new`는 즉시 `enter_scope("top", Module, 0)`을 호출한다. `enter_scope`는 새 `SymbolTable`을 `tables` stack에 push한다. 이후 모든 이름 등록은 `tables.last_mut()`에 쓰인다.

`def make_counter`를 만나면 stack은 다음처럼 바뀐다.

```text
[top]
[top, make_counter]
[top, make_counter, bump]
```

`leave_scope`는 현재 table을 pop하고 부모의 `sub_tables`에 붙인다. `sub_tables`는 AST 방문 순서를 보존한다. codegen이 다음 child table을 이름 lookup이 아니라 cursor로 소비하기 때문에 이 순서가 의미를 가진다.

### 6.2 FunctionDef 방문 순서

`scan_statement`의 `Stmt::FunctionDef` branch는 다음 순서로 움직인다.

1. 함수 이름을 부모에 `Assigned`로 등록한다.
2. default expression을 부모에서 방문한다.
3. decorator expression을 부모에서 방문한다.
4. 함수 scope에 들어간다.
5. parameter를 등록한다.
6. 함수 body를 방문한다.
7. 함수 scope를 닫아 부모 child로 붙인다.

`bump(step=1)`의 default `1`이 `bump` 내부가 아니라 `make_counter` 실행 시 평가되는 의미와 정확히 일치한다.

### 6.3 Name에서 raw flag로

`scan_expression`의 `Expr::Name` branch는 AST context를 `SymbolUsage`로 바꾼다.

| AST context | SymbolUsage | 대표 flag |
|---|---|---|
| Load | Used | `USE` |
| Store/Delete | Assigned | `DEF_LOCAL` |
| parameter | Parameter | `DEF_PARAM` |
| `global` statement | Global | `DEF_GLOBAL` |
| `nonlocal` statement | Nonlocal | `DEF_NONLOCAL` |

`flags`는 관찰한 사실이지 최종 scope가 아니다. 첫 단계가 끝났을 때 핵심 값은 개념적으로 다음과 같다.

```text
make_counter.total: flags=DEF_LOCAL, scope=Unknown
bump.total: flags=DEF_NONLOCAL|DEF_LOCAL|USE, scope=Free(candidate)
bump.rate: flags=USE, scope=Unknown
```

## 7. 심볼 테이블 두 번째 단계: scope resolution

`SymbolTableBuilder::finish`가 두 단계의 경계다.

```text
root table pop
→ analyze_symbol_table(&mut root)
→ final SymbolTable return
```

### 7.1 자식부터 분석

`SymbolTableAnalyzer::analyze_symbol_table`은 현재 symbols를 ancestor stack에 잠시 넣고 모든 child table을 먼저 재귀 분석한다. 이유는 부모 이름이 `Cell`인지 알려면 자식이 그 이름을 `Free`로 요구하는지 먼저 알아야 하기 때문이다.

현재 예제의 핵심 순서는 다음과 같다.

```text
bump 분석
  total: nonlocal + make_counter binding 발견 → Free
  rate: enclosing function binding 없음 → GlobalImplicit
  unresolved free set {total} 반환

make_counter 분석
  total: own DEF_LOCAL + child가 Free로 요구 → Cell
  child free set에서 total 제거

top 분석
  rate, make_counter, counter → Local
  print → Unknown (root의 미정의 이름에 대한 현재 내부 표현)
```

### 7.2 Free와 Cell의 방향

`found_in_outer_scope`는 현재 block에서 binding이 없는 이름을 enclosing function에서 찾는다. 일반 module과 class는 closure provider에서 제외한다.

```text
bump.total → make_counter에서 binding 발견 → Free
bump.rate  → module은 skip → GlobalImplicit
```

`found_in_inner_scope`는 현재 bound 이름을 자식들이 `Free`로 요구하는지 검사한다.

```text
make_counter.total + bump.total(Free) → Cell
```

같은 closure storage를 참조하는 양쪽 표현이 `Cell`과 `Free`다.

## 8. 실제 분석 결과

이 프로젝트의 Rust 실행 도구는 `rustpython_compiler::compile_symtable` 결과를 직접 순회한다. 핵심 출력은 다음과 같다.

```text
scope "top" Module
  rate          scope=Local          flags=DEF_LOCAL
  make_counter  scope=Local          flags=DEF_LOCAL|USE
  counter       scope=Local          flags=DEF_LOCAL|USE
  print         scope=Unknown        flags=USE
  scope "make_counter" Function
    start       scope=Local          flags=DEF_PARAM|USE
    total       scope=Cell           flags=DEF_LOCAL
    bump        scope=Local          flags=DEF_LOCAL|USE
    scope "bump" Function
      step      scope=Local          flags=DEF_PARAM|USE
      total     scope=Free           flags=DEF_LOCAL|DEF_NONLOCAL|USE
      rate      scope=GlobalImplicit flags=USE
```

실제 전체 출력에는 Python 3.14 annotation machinery가 만든 `__annotate__` child도 나타난다. 사용자 이름의 lexical 관계를 설명할 때는 이 합성 scope를 접어 둔다.

현재 Python 공개 `symtable` API를 이 결과의 원본으로 쓰면 안 된다. `_symtable` adapter가 내부 `Symbol.scope`를 CPython 형식의 integer 상위 비트에 합치지 않아 Free/Cell 정보가 유실된다. 실행 도구가 Rust 반환값을 직접 읽는 이유다.

## 9. 두 번째 AST walk: scope를 opcode로

`Compiler`는 두 stack을 함께 유지한다.

```text
code_stack: Vec<ir::CodeInfo>
symbol_table_stack: Vec<SymbolTable>
```

module에서 `compile_program`이 root table을 push한다. `FunctionDef`를 만나면 다음 child table과 새 `CodeInfo`를 함께 push한다. 함수가 끝나면 둘을 함께 pop한다.

연결의 핵심은 `Compiler::compile_name`이다.

| 최종 scope | 함수 안 opcode family | module/class 기본 family |
|---|---|---|
| `Local` | Fast | Name |
| `Cell` | Deref | 특수 Deref/Name 처리 |
| `Free` | Deref | Deref |
| `GlobalExplicit` | Global | Global |
| `GlobalImplicit` | Global | Name |
| root `Unknown` | 해당 없음 | Name |

현재 예제에 적용하면 다음과 같다.

```text
make_counter.start  Local          → LoadFastBorrow
make_counter.total  Cell           → StoreDeref / LoadDeref
bump.step            Local          → LoadFastBorrow
bump.total           Free           → LoadDeref / StoreDeref
bump.rate            GlobalImplicit → LoadGlobal
module.rate          Local          → StoreName
```

`compile_name`이 부르는 `emit!`은 아직 byte 배열을 만들지 않는다. `_emit`이 opcode, full argument, CFG target, source range를 `ir::InstructionInfo`로 현재 block에 추가한다.

## 10. 함수와 closure 조립

`compile_function_body`는 다음 순서다.

1. `enter_function`으로 child symbol table과 `CodeInfo`를 push한다.
2. body statements를 컴파일한다.
3. 암시적 return을 추가한다.
4. `exit_scope`로 child CFG를 `CodeObject`로 만든다.
5. `make_closure`로 child `freevars`에 대응하는 부모 cell을 로드한다.
6. `MakeFunction`과 function attribute instruction을 낸다.

실제 metadata는 다음과 같다.

```text
make_counter:
  varnames = [start, bump]
  cellvars = [total]
  freevars = []

bump:
  varnames = [step]
  cellvars = []
  freevars = [total]
  names    = [rate]
```

`bump` CodeObject는 `make_counter` CodeObject의 constants에, `make_counter` CodeObject는 module CodeObject의 constants에 들어간다.

## 11. CFG에서 CodeObject로

[`crates/codegen/src/ir.rs`](../../crates/codegen/src/ir.rs)의 `CodeInfo::finalize_code`가 다음 단계를 실행한다.

1. codegen CFG 준비
2. CFG optimization
3. stack depth와 localsplus 계산
4. pseudo instruction lowering
5. jump normalization과 offset 결정
6. `assemble_emit`
7. `CodeObject` 조립

최종 [`CodeObject`](../../crates/compiler-core/src/bytecode.rs)는 다음 정보를 함께 담는다.

- `instructions`
- `constants`
- `names`
- `varnames`
- `cellvars`
- `freevars`
- source location table
- exception table

심볼 테이블 객체는 런타임으로 전달되지 않는다. 분석 결론은 선택된 opcode와 위 metadata 배열에 압축된다.

## 12. 실행 경계

[`VirtualMachine::run_code_obj_with_closure`](../../crates/vm/src/vm/mod.rs)는 module CodeObject도 `PyFunction`으로 감싸 globals/locals와 함께 호출한다. 이후 frame dispatch가 앞서 선택한 instruction을 실행한다.

실제 결과는 다음과 같다.

```text
12
18
```

`total`의 하나뿐인 cell 값은 `10 → 12 → 18`로 바뀌고, `rate`는 매번 module globals에서 `2`를 읽는다.

여기까지가 첫 학습 범위다. 다음에 확장할 때는 한 번에 하나만 추가한다.

- class의 `__class__` cell
- PEP 709 inlined comprehension
- generator/coroutine flags
- exception CFG
- PEP 649/695 annotation/type-parameter scope
