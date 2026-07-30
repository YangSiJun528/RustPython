# CPython 내부 구현 학습 문서

CPython `InternalDocs`를 한국어로 해설하고 학습 내용을 기록하는
최상위 디렉터리다.

문서는 다음 계층으로 관리한다.

```text
cpython-internals-notes/
└── <CPython 버전>/
    └── <InternalDocs 주제>/
        └── README.ko.md
```

## 문서 목록

### CPython 3.14

- [Python 소스 코드 컴파일](3.14/compiling-python-source-code/README.ko.md)
  - Guide to the parser
  - Compiler design
  - Changing CPython's grammar

- [런타임 객체](3.14/runtime-objects/README.ko.md)
  - Code Objects
  - Generators
  - Frames
  - String Interning
