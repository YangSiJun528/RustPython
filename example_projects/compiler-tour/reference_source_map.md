# Reference: compiler source map

이 문서는 현재 checkout에서 compiler tour가 참조하는 파일, 함수, 자료구조, 의미를 빠르게 찾기 위한 레퍼런스다. 순서대로 학습하려면 [tutorial_compiler_pipeline.md](tutorial_compiler_pipeline.md)를 사용한다.

## 범위와 줄 수

| 범위 | 현재 줄 수 | 취급 |
|---|---:|---|
| `crates/codegen/src/compile.rs` L1–L13803 | 13,803 | 대형 `tests` module 전까지의 읽기 상한 |
| `crates/codegen/src/symboltable.rs` L1–L3430 | 3,430 | `tests` module 전까지의 읽기 상한 |
| 합계 | 17,233 | 2만 줄 이하 핵심 범위 |
| `crates/compiler/src/lib.rs` L5161–L5303 | 143 | parser/codegen facade 진입부만 |

`compile.rs` 상한에는 짧은 test-only helper가 일부 포함된다. 17,233은 “처음부터 읽어도 넘지 않는 상한”이며, 인터랙티브 투어는 고정 예제가 실제 통과하는 branch만 표시한다.

다음은 합계에서 제외한다.

- Ruff parser 내부: 외부 git dependency
- `ir.rs` 전체: `finalize_code` 주변만 설명
- compiler-core 전체: `CodeObject` 구조만 설명
- VM 전체: compiler 연결과 execution 경계만 설명
- `compile.rs`, `symboltable.rs`의 대형 test modules

## 호출 경로

| 순서 | 파일 | 함수/anchor | 책임 |
|---:|---|---|---|
| 1 | `src/main.rs` | `main` | Builder 생성, `rustpython::run` 호출 |
| 2 | `src/lib.rs` | `run` | CLI parse, Interpreter 생성 |
| 3 | `src/lib.rs` | `run_rustpython` | `RunMode` 분기 |
| 4 | `src/lib.rs` | `run_file` | 파일 실행 setup |
| 5 | `crates/vm/src/vm/python_run.rs` | `run_simple_file_inner` | bytes read, UTF-8, compile/run 분리 |
| 6 | `crates/vm/src/vm/compile.rs` | `compile_with_opts` | warning adapter, `PyCode` wrapping |
| 7 | `crates/compiler/src/lib.rs` | `compile` | `SourceFile` 생성 |
| 8 | 같은 파일 | `_compile_with_syntax_warning_handler` | Ruff mode, parse, AST 추출 |
| 9 | `crates/codegen/src/compile.rs` | `compile_top_with_syntax_warning_handler` | future/preprocess/mode 분기 |
| 10 | 같은 파일 | `scan_module_symbols` | 심볼 분석 진입 |
| 11 | `crates/codegen/src/symboltable.rs` | `scan_program_with_options` | Builder 수명주기 |
| 12 | 같은 파일 | `scan_statement`, `scan_expression` | raw DEF/USE 수집 |
| 13 | 같은 파일 | `register_name` | `SymbolUsage` → flags |
| 14 | 같은 파일 | `finish` | 수집/분석 경계 |
| 15 | 같은 파일 | analyzer `analyze_symbol_table` | child free 전파 |
| 16 | 같은 파일 | `analyze_symbol` | 최종 scope 판정 |
| 17 | `crates/codegen/src/compile.rs` | `Compiler::compile_program` | 두 번째 AST walk 시작 |
| 18 | 같은 파일 | `compile_statement`, `compile_expression` | 구문별 codegen |
| 19 | 같은 파일 | `compile_name` | scope → opcode family |
| 20 | 같은 파일 | `_emit` | CFG `InstructionInfo` 추가 |
| 21 | `crates/codegen/src/ir.rs` | `CodeInfo::finalize_code` | optimize, assemble, `CodeObject` |
| 22 | `crates/vm/src/vm/mod.rs` | `run_code_obj_with_closure` | VM 실행 경계 |

## compiler facade

`crates/compiler/src/lib.rs`는 다음 crate를 묶고 re-export한다.

| 이름 | 실제 제공자 |
|---|---|
| `parser`, `ast` | RustPython Ruff fork |
| `codegen` | `rustpython-codegen` |
| `core`, `Mode`, `CodeObject` | `rustpython-compiler-core` |

요청에서 예상할 수 있는 `crates/compiler/core/src/symboltable.rs` 경로는 현재 없다. 심볼 테이블 실제 구현은 `crates/codegen/src/symboltable.rs`다.

## 주요 자료구조

### `SymbolTable`

| 필드 | 의미 |
|---|---|
| `name` | `top`, 함수명, 클래스명 등 block 이름 |
| `typ` | `CompilerScope` |
| `line_number` | block 시작 행 |
| `is_nested` | enclosing function-like scope 여부 |
| `symbols` | 현재 block의 이름 → `Symbol` |
| `sub_tables` | AST 방문 순서의 child blocks |
| `next_sub_table` | codegen의 child 소비 cursor |
| `varnames` | builder 단계의 parameter 순서 |
| `needs_class_closure` | implicit `__class__` cell 필요 여부 |
| `is_generator`, `is_coroutine` | code flags 입력 |
| annotation/comprehension fields | PEP 649/695/709용 합성 block 상태 |

### `CompilerScope`

기본 scope:

- `Module`
- `Class`
- `Function`
- `AsyncFunction`
- `Lambda`
- `Comprehension`

Python 3.14 합성 평가 scope:

- `TypeParams`
- `Annotation`
- `TypeAlias`
- `TypeVariable`

### `SymbolScope`

| 값 | 의미 |
|---|---|
| `Unknown` | 아직 미분류 또는 root의 미정의 이름 |
| `Local` | 현재 block binding |
| `GlobalExplicit` | `global` 선언 |
| `GlobalImplicit` | enclosing function binding 없는 함수 내 이름 |
| `Free` | 바깥 function의 cell 참조 |
| `Cell` | 자식에게 closure storage를 제공하는 현재 binding |

### `SymbolFlags`

| flag | 수집 사실 |
|---|---|
| `DEF_GLOBAL` | `global` 선언 |
| `DEF_LOCAL` | assignment/delete binding |
| `DEF_PARAM` | parameter |
| `DEF_NONLOCAL` | `nonlocal` 선언 |
| `USE` | load |
| `DEF_IMPORT` | import binding |
| `DEF_ANNOT` | annotation binding |
| `DEF_COMP_ITER` | comprehension iteration target |
| `DEF_TYPE_PARAM` | PEP 695 type parameter |
| `DEF_COMP_CELL` | PEP 709 inlined comprehension cell |

`flags`와 `scope`는 별도 축이다. `DEF_LOCAL`이라고 최종 `Local`인 것은 아니다.

## 심볼 분석 규칙

### 첫 pass

```text
AST context/statement
→ SymbolUsage
→ Symbol.flags
→ scope tree
```

즉시 scope까지 정하는 경우:

- `global` → `GlobalExplicit`
- `nonlocal` → `Free` 후보

나중으로 미루는 경우:

- assignment/parameter/import → bound 여부만 기록
- load → use 여부만 기록

### 두 번째 pass

```text
children analyze
→ child free sets collect
→ current symbols analyze
→ current unresolved free set return
```

결정 규칙:

| 현재 사실 | 관계 | 결론 |
|---|---|---|
| bound | child가 같은 이름을 Free로 요구 | `Cell` |
| bound | child 요구 없음 | `Local` |
| unbound | enclosing function에 bound 이름 | `Free` |
| unbound | enclosing function binding 없음 | `GlobalImplicit` |
| root unbound | ancestor 없음 | `Unknown` |

일반 module/class binding은 closure outer 검색에서 제외된다. `__class__`, `__classdict__` 등은 class 특수 규칙이 있다.

## scope에서 name opcode로

`Compiler::compile_name`의 기본 대응:

| `SymbolScope` | 함수 내부 | module/class 기본 |
|---|---|---|
| `Local` | `Load/Store/DeleteFast` | `Load/Store/DeleteName` |
| `Cell` | `Load/Store/DeleteDeref` | scope별 특수 처리 |
| `Free` | `Load/Store/DeleteDeref` | Deref |
| `GlobalExplicit` | `Load/Store/DeleteGlobal` | Global |
| `GlobalImplicit` | `LoadGlobal` | Name |
| root `Unknown` | 오류 또는 특수 이름 | Name |

Python 3.14 annotation/class visibility는 `LoadFromDictOrGlobals` 같은 추가 branch를 사용한다.

## 현재 sample의 최종 결과

| block | name | flags | scope | 대표 opcode |
|---|---|---|---|---|
| top | `rate` | `DEF_LOCAL` | `Local` | `StoreName` |
| top | `make_counter` | `DEF_LOCAL|USE` | `Local` | `StoreName`, `LoadName` |
| top | `counter` | `DEF_LOCAL|USE` | `Local` | `StoreName`, `LoadName` |
| top | `print` | `USE` | `Unknown` | `LoadName` |
| make_counter | `start` | `DEF_PARAM|USE` | `Local` | `LoadFastBorrow` |
| make_counter | `total` | `DEF_LOCAL` | `Cell` | `MakeCell`, `StoreDeref` |
| make_counter | `bump` | `DEF_LOCAL|USE` | `Local` | `StoreFast`, `LoadFastBorrow` |
| bump | `step` | `DEF_PARAM|USE` | `Local` | `LoadFastBorrow` |
| bump | `total` | `DEF_LOCAL|DEF_NONLOCAL|USE` | `Free` | `LoadDeref`, `StoreDeref` |
| bump | `rate` | `USE` | `GlobalImplicit` | `LoadGlobal` |

CodeObject metadata:

| code | varnames | cellvars | freevars | names |
|---|---|---|---|---|
| module | `[]` | `[]` | `[]` | `rate, make_counter, counter, print` |
| make_counter | `start, bump` | `total` | `[]` | `[]` |
| bump | `step` | `[]` | `total` | `rate` |

## IR와 bytecode 경계

`Compiler::_emit`의 출력은 `ir::InstructionInfo`다.

```text
AnyInstruction
OpArg(u32)
BlockIdx target
start/end SourceLocation
exception handler metadata
```

`CodeInfo::finalize_code`가 이를 다음으로 바꾼다.

```text
CFG Blocks
→ optimized InstructionSequence
→ resolved jumps
→ assembled CodeUnits + linetable + exceptiontable
→ CodeObject
```

`CodeUnit`은 opcode byte와 argument byte로 이루어진 2-byte 구조다. 큰 argument는 `ExtendedArg`를 사용한다.

## 알려진 introspection 제한

`crates/vm/src/stdlib/_symtable.rs`의 Python adapter는 현재 각 이름에 `symbol.flags.bits()`만 노출한다. `Lib/symtable.py`는 CPython처럼 상위 비트에 scope가 포함되었다고 가정한다. 결과적으로 공개 Python `symtable`에서 local/free/cell/global 분류가 유실된다.

이 프로젝트는 그 adapter를 우회하고 Rust `compile_symtable` 반환값의 `Symbol.scope`와 `Symbol.flags`를 직접 출력한다. 해당 제한을 고치는 일은 별도 호환성 작업이며 이 교육 프로젝트에는 포함하지 않는다.

## anchor 검증

인터랙티브 투어는 고정 줄 번호 대신 source anchor 문자열을 사용한다. 다음 명령은 파일과 모든 anchor를 검사한다.

```bash
node example_projects/compiler-tour/validate.mjs
```

검사 항목:

- step/phase ID 유효성
- source file 존재
- start/end anchor 존재와 순서
- 줄별 설명 anchor 존재
- 설명 대상 줄이 실제 표시 범위 안에 있는지
