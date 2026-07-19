pub(crate) use _symtable::module_def;

#[pymodule]
mod _symtable {
    use crate::{
        Py, PyObjectRef, PyPayload, PyRef, PyResult, VirtualMachine,
        builtins::{PyDictRef, PyUtf8StrRef},
        compiler,
        types::Representable,
    };
    use alloc::fmt;
    use rustpython_codegen::symboltable::{
        CompilerScope, Symbol, SymbolFlags, SymbolScope, SymbolTable,
    };

    /// [CPython's `SCOPE_OFFSET`](https://github.com/python/cpython/blob/v3.14.6/Include/internal/pycore_symtable.h#L176)
    const SCOPE_OFFSET: i32 = 12;

    const SYMBOL_FLAGS_MASK: i32 = (1 << SCOPE_OFFSET) - 1;

    // Consts as defined at
    // https://github.com/python/cpython/blob/6cb20a219a860eaf687b2d968b41c480c7461909/Include/internal/pycore_symtable.h#L156

    #[pyattr]
    pub(super) const DEF_GLOBAL: i32 = SymbolFlags::DEF_GLOBAL.bits() as i32;

    #[pyattr]
    pub(super) const DEF_LOCAL: i32 = SymbolFlags::DEF_LOCAL.bits() as i32;

    #[pyattr]
    pub(super) const DEF_PARAM: i32 = SymbolFlags::DEF_PARAM.bits() as i32;

    #[pyattr]
    pub(super) const DEF_NONLOCAL: i32 = SymbolFlags::DEF_NONLOCAL.bits() as i32;

    #[pyattr]
    pub(super) const USE: i32 = SymbolFlags::USE.bits() as i32;

    #[pyattr]
    pub(super) const DEF_FREE_CLASS: i32 = SymbolFlags::DEF_FREE_CLASS.bits() as i32;

    #[pyattr]
    pub(super) const DEF_IMPORT: i32 = SymbolFlags::DEF_IMPORT.bits() as i32;

    #[pyattr]
    pub(super) const DEF_ANNOT: i32 = SymbolFlags::DEF_ANNOT.bits() as i32;

    #[pyattr]
    pub(super) const DEF_COMP_ITER: i32 = SymbolFlags::DEF_COMP_ITER.bits() as i32;

    #[pyattr]
    pub(super) const DEF_TYPE_PARAM: i32 = SymbolFlags::DEF_TYPE_PARAM.bits() as i32;

    #[pyattr]
    pub(super) const DEF_COMP_CELL: i32 = SymbolFlags::DEF_COMP_CELL.bits() as i32;

    // 외부에 노출하는 Mask 값이니까. CPython과 일치해야함.
    #[pyattr]
    pub(super) const DEF_BOUND: i32 = DEF_LOCAL | DEF_PARAM | DEF_IMPORT;

    #[pyattr]
    pub(super) const SCOPE_MASK: i32 = DEF_GLOBAL | DEF_LOCAL | DEF_PARAM | DEF_NONLOCAL;

    #[pyattr]
    pub(super) const LOCAL: i32 = SymbolScope::Local.as_i32();

    #[pyattr]
    pub(super) const GLOBAL_EXPLICIT: i32 = SymbolScope::GlobalExplicit.as_i32();

    #[pyattr]
    pub(super) const GLOBAL_IMPLICIT: i32 = SymbolScope::GlobalImplicit.as_i32();

    #[pyattr]
    pub(super) const FREE: i32 = SymbolScope::Free.as_i32();

    #[pyattr]
    pub(super) const CELL: i32 = SymbolScope::Cell.as_i32();

    #[pyattr]
    pub(super) const SCOPE_OFF: i32 = SCOPE_OFFSET;

    #[pyattr]
    pub(super) const TYPE_FUNCTION: i32 = 0;

    #[pyattr]
    pub(super) const TYPE_CLASS: i32 = 1;

    #[pyattr]
    pub(super) const TYPE_MODULE: i32 = 2;

    #[pyattr]
    pub(super) const TYPE_ANNOTATION: i32 = 3;

    #[pyattr]
    pub(super) const TYPE_TYPE_ALIAS: i32 = 4;

    #[pyattr]
    pub(super) const TYPE_TYPE_PARAMETERS: i32 = 5;

    #[pyattr]
    pub(super) const TYPE_TYPE_VARIABLE: i32 = 6;

    #[pyfunction]
    fn symtable(
        source: PyUtf8StrRef,
        filename: PyUtf8StrRef,
        mode: PyUtf8StrRef,
        vm: &VirtualMachine,
    ) -> PyResult<PyRef<PySymbolTable>> {
        let mode = mode
            .as_str()
            .parse::<compiler::Mode>()
            .map_err(|err| vm.new_value_error(err.to_string()))?;

        let symtable = compiler::compile_symtable(source.as_str(), mode, filename.as_str())
            .map_err(|err| vm.new_syntax_error(&err, Some(source.as_str())))?;

        let py_symbol_table = to_py_symbol_table(symtable);
        Ok(py_symbol_table.into_ref(&vm.ctx))
    }

    const fn to_py_symbol_table(symtable: SymbolTable) -> PySymbolTable {
        PySymbolTable { symtable }
    }

    #[pyattr]
    #[pyclass(name = "symtable entry")]
    #[derive(PyPayload)]
    struct PySymbolTable {
        symtable: SymbolTable,
    }

    impl fmt::Debug for PySymbolTable {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(f, "SymbolTable()")
        }
    }

    #[pyclass(with(Representable))]
    impl PySymbolTable {
        #[pygetset]
        fn name(&self) -> String {
            self.symtable.name.clone()
        }

        #[pygetset(name = "type")]
        fn typ(&self) -> i32 {
            match self.symtable.typ {
                CompilerScope::Function
                | CompilerScope::AsyncFunction
                | CompilerScope::Lambda
                | CompilerScope::Comprehension => TYPE_FUNCTION,
                CompilerScope::Class => TYPE_CLASS,
                CompilerScope::Module => TYPE_MODULE,
                CompilerScope::Annotation => TYPE_ANNOTATION,
                CompilerScope::TypeAlias => TYPE_TYPE_ALIAS,
                CompilerScope::TypeParams => TYPE_TYPE_PARAMETERS,
                CompilerScope::TypeVariable => TYPE_TYPE_VARIABLE,
            }
        }

        #[pygetset]
        const fn lineno(&self) -> u32 {
            self.symtable.line_number
        }

        #[pygetset]
        fn children(&self, vm: &VirtualMachine) -> Vec<PyObjectRef> {
            self.symtable
                .sub_tables
                .iter()
                .flat_map(|t| {
                    if t.comp_inlined {
                        // Flatten: replace inlined comprehension tables with their children
                        t.sub_tables.iter().collect::<Vec<_>>()
                    } else {
                        vec![t]
                    }
                })
                .map(|t| to_py_symbol_table(t.clone()).into_pyobject(vm))
                .collect()
        }

        #[pygetset]
        fn id(&self) -> usize {
            self as *const Self as *const core::ffi::c_void as usize
        }

        #[pygetset]
        fn symbols(&self, vm: &VirtualMachine) -> PyDictRef {
            let dict = vm.ctx.new_dict();
            for (name, symbol) in &self.symtable.symbols {
                dict.set_item(name, vm.new_pyobj(encode_symbol(symbol)), vm)
                    .unwrap();
            }
            dict
        }

        #[pygetset]
        const fn nested(&self) -> bool {
            self.symtable.is_nested
        }
    }

    // 피드백 말해준거 (괄호는 내 말이나 생각)
    // 지금 이 구현 자체가 임기응변에 가까워보인다.
    // 원래 RustPython에서 심볼 구현체를 쓰다가, 이러다간 한도끝도 없겠다 싶어서
    // 표준 라이브러리를 가져다 쓰고, 그에 맞게 바꾼건데,
    // 아직 남아있는 부분이 있나보다. (몰랐다고 하심)
    // 그래서 지금 해결하려는 코드가 좀 이상한거(의도를 잘 모르겠는) 같은데
    // 이런 코드를 보면 남들은 뭔 의도가 있어서 있겠지... 하는거라
    // 주석으로 명확하게 하거나
    // 아니면 근본 원인을 제거하는거 자체를 목표로 하는게 좋겠다.
    // 너무 큰 작업이라면 주석이라도 남겨서 PR을 올려야 할거 같음.
    // (CPython과 일치하게 다 갈아엎어야하나?) 흠...

    // 별개로 컴파일러 관심 있으면 공부를 해보는게 좋겠다고 함. 대학교 4학년때쯤에 있다고 함.
    // 컴파일 언어 컴파일러랑 인터프리터 언어 컴파일러랑 차이가 있고 심볼 테이블도 그런 것들에 관련있어서 그런거 찾아보라고 함.
    // (의도치 않게 학벌 노출? 을 해버렸는데 그걸 물어보시려는건 아니였던듯.
    // 부캠이랑 고졸인거? 이게 은근히 말하기가 애매함 안말하기도 애매하고...).

    // (아니면 이거 불일치 문제 정리해서 이슈를 제출해보는게 좋을거 같음).

    // 내 생각
    // 일단 컴파일러 쪽 구현이나 공부를 해봐야할거같고
    // 저거 근본 원리를 수정하기 위해 공부해보는게 좋을듯?
    // 일단 관련되서 모든 작업과 이슈를 찾아서 이걸 제출하고, 수정 가능할지 견젹을 내는걸 우선적으로 해봐야할거같음.

    fn encode_symbol(symbol: &Symbol) -> i32 {
        let mut flags = i32::from(symbol.flags.bits()) & SYMBOL_FLAGS_MASK;
        if symbol.flags.contains(SymbolFlags::ITER) {
            flags |= DEF_LOCAL;
        }
        let scope = match symbol.scope {
            // 이게 없어도 테스트는 통과
            // Unknown으로서 남아있는 상황 자체가 버그로 보임. (CPython과 일치해야한다면?)
            // 이건 별도 이슈로 빼는게 좋아보이는데, 나중에 확인하기.
            // SymbolScope::Unknown => SymbolScope::GlobalImplicit,
            scope => scope,
        };
        flags | (scope.as_i32() << SCOPE_OFFSET)
    }

    impl Representable for PySymbolTable {
        #[inline]
        fn repr_str(zelf: &Py<Self>, vm: &VirtualMachine) -> PyResult<String> {
            Ok(format!(
                "<{} {}({}), line {}>",
                Self::class(&vm.ctx).name(),
                zelf.symtable.name,
                zelf.id(),
                zelf.symtable.line_number
            ))
        }
    }
}
