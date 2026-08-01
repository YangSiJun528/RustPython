# CPython 내부 구현 학습 문서

CPython `InternalDocs`를 한국어로 해설하고 학습 내용을 기록하는
최상위 디렉터리다.

문서는 다음 계층으로 관리한다.

```text
cpython-internals-notes/
└── <CPython 버전>/
    └── <InternalDocs 주제 또는 통합 주제>/
        └── README.ko.md
```

## 문서 목록

### CPython 3.14

- [Python 컴파일에서 실행까지](3.14/compilation-to-execution/README.ko.md)
  - 소스 코드, CodeObject, 바이트코드, 프레임을 한 예제로 연결하는 입문 설명

- [Python 소스 코드 컴파일](3.14/compiling-python-source-code/README.ko.md)
  - Guide to the parser
  - Compiler design
  - Changing CPython's grammar

- [런타임 객체](3.14/runtime-objects/README.ko.md)
  - Code Objects
  - Generators
  - Frames
  - String Interning

- [객체 모델과 런타임 객체 확장 해설](3.14/object-model-and-runtime-objects/README.ko.md)
  - 런타임 객체 문서의 전체 내용
  - PyObject, 참조 소유권과 객체 수명
  - 코드 객체, 함수 객체, frame과 슬롯의 관계
  - generator와 문자열 인터닝을 포함한 통합 예제

- [프로그램 실행](3.14/program-execution/README.ko.md)
  - The Bytecode Interpreter
  - The JIT
  - Garbage Collector Design
  - Exception Handling
