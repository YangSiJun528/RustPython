//! Print the compiler artifacts used by this project without starting the VM.

use rustpython_compiler::{
    CompileOpts, Mode,
    ast::Mod,
    codegen::symboltable::{SymbolFlags, SymbolTable},
    compile, compile_symtable,
    core::bytecode::{CodeObject, ConstantData, OpArgState},
    parser,
};
use std::{env, fs, path::PathBuf, process::ExitCode};

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("compiler-tour: {error}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<(), String> {
    let source_path = env::args().nth(1).map_or_else(
        || PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("sample.py"),
        PathBuf::from,
    );
    let source_name = source_path.display().to_string();
    let source = fs::read_to_string(&source_path)
        .map_err(|error| format!("cannot read {source_name}: {error}"))?;

    println!("=== 0. SOURCE: {source_name} ===\n{source}");

    let parsed = parser::parse(&source, parser::Mode::Module.into())
        .map_err(|error| format!("parse failed: {error}"))?;
    let ast = parsed.into_syntax();
    println!("=== 1. PARSED AST ===");
    print_ast_summary(&ast);

    let table = compile_symtable(&source, Mode::Exec, &source_name)
        .map_err(|error| format!("symbol-table analysis failed: {error}"))?;
    println!("\n=== 2. ANALYZED SYMBOL TABLE ===");
    print_symbol_table(&table, 0);

    let code = compile(&source, Mode::Exec, &source_name, CompileOpts::default())
        .map_err(|error| format!("bytecode generation failed: {error}"))?;
    println!("\n=== 3. CODE OBJECTS AND BYTECODE ===");
    print_code_object(&code, 0);

    Ok(())
}

fn print_ast_summary(ast: &Mod) {
    match ast {
        Mod::Module(module) => {
            println!("Module(body_len={})", module.body.len());
            for (index, statement) in module.body.iter().enumerate() {
                println!("  [{index}] {statement:#?}");
            }
        }
        Mod::Expression(expression) => println!("Expression({:#?})", expression.body),
    }
}

fn print_symbol_table(table: &SymbolTable, depth: usize) {
    let indent = "  ".repeat(depth);
    println!(
        "{indent}scope {:?} {:?} line={} nested={} varnames={:?}",
        table.name, table.typ, table.line_number, table.is_nested, table.varnames
    );
    for symbol in table.symbols.values() {
        println!(
            "{indent}  {:<18} scope={:<14?} flags={}",
            symbol.name,
            symbol.scope,
            format_flags(symbol.flags)
        );
    }
    for child in &table.sub_tables {
        print_symbol_table(child, depth + 1);
    }
}

fn format_flags(flags: SymbolFlags) -> String {
    let known = [
        (SymbolFlags::DEF_GLOBAL, "DEF_GLOBAL"),
        (SymbolFlags::DEF_LOCAL, "DEF_LOCAL"),
        (SymbolFlags::DEF_PARAM, "DEF_PARAM"),
        (SymbolFlags::DEF_NONLOCAL, "DEF_NONLOCAL"),
        (SymbolFlags::USE, "USE"),
        (SymbolFlags::DEF_FREE_CLASS, "DEF_FREE_CLASS"),
        (SymbolFlags::DEF_IMPORT, "DEF_IMPORT"),
        (SymbolFlags::DEF_ANNOT, "DEF_ANNOT"),
        (SymbolFlags::DEF_COMP_ITER, "DEF_COMP_ITER"),
        (SymbolFlags::DEF_TYPE_PARAM, "DEF_TYPE_PARAM"),
        (SymbolFlags::DEF_COMP_CELL, "DEF_COMP_CELL"),
    ];
    let names: Vec<_> = known
        .into_iter()
        .filter_map(|(flag, name)| flags.contains(flag).then_some(name))
        .collect();
    if names.is_empty() {
        "-".to_owned()
    } else {
        names.join("|")
    }
}

fn print_code_object(code: &CodeObject, depth: usize) {
    let indent = "  ".repeat(depth);
    println!(
        "{indent}code {:?}: qualname={:?} flags={:?} stack={}",
        &code.obj_name, &code.qualname, code.flags, code.max_stackdepth
    );
    println!("{indent}  names={:?}", code.names);
    println!("{indent}  varnames={:?}", code.varnames);
    println!("{indent}  cellvars={:?}", code.cellvars);
    println!("{indent}  freevars={:?}", code.freevars);

    let mut arg_state = OpArgState::default();
    for (offset, unit) in code.instructions.iter().copied().enumerate() {
        let (instruction, arg) = arg_state.get(unit);
        println!(
            "{indent}  {offset:04}  {instruction:<36?} arg={}",
            u32::from(arg)
        );
    }

    for constant in code.constants.iter() {
        if let ConstantData::Code { code: child } = constant {
            println!();
            print_code_object(child, depth + 1);
        }
    }
}
