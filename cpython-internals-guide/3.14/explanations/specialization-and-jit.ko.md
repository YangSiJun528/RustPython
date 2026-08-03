# 관찰한 실행은 특수화된 opcode와 JIT trace가 된다

컴파일러는 `obj.attr`의 실제 객체 타입이나 전역 이름이 어느 딕셔너리에 있을지
미리 알 수 없으므로 범용 바이트코드를 만든다. CPython의 적응형 인터프리터는
실행 중 반복되는 경우를 관찰해 opcode 하나를 더 좁고 빠른 형태로 특수화한다.
guard가 관찰 당시의 가정을 확인하므로 가정이 깨지면 범용 경로로 돌아갈 수
있다.

JIT는 같은 생각을 연속된 명령 경로로 넓힌다. 뜨거운 바이트코드 trace를 더 작은
uop 시퀀스로 바꾸고 여러 명령에 걸쳐 최적화한 뒤, uop 인터프리터나 네이티브
코드로 실행한다. opcode 특수화와 JIT는 별개 계층이지만 둘 다 관찰한 실행에만
비용을 쓰고, 실패한 가정에서는 기본 인터프리터로 복귀한다.

## opcode 하나는 관찰을 거쳐 빠른 형태로 바뀐다

특수화는 네 단계를 거친다.

```text
generic → adaptive 관찰 → specialized
   ↑                           │
   └──────── guard 실패 ───────┘
              deopt
```

이 그림의 `adaptive`는 관찰 단계를 가리키는 개념 이름이다. CPython 3.14에서
반드시 별도의 `*_ADAPTIVE` opcode가 있다는 뜻은 아니다. 대개 instruction family의
범용 명령 자체가 counter와 특수화 진입점을 가진다.

generic 명령은 가능한 모든 Python 값을 처리한다. adaptive 단계에서는 명령 바로
옆의 inline cache에 실행 횟수와 관찰값을 기록한다. 충분히 반복되면 specializer가
같은 instruction family에서 현재 값에 맞는 specialized 명령을 고른다.

`LOAD_GLOBAL`을 예로 들면 이름은 module globals에 있을 수도 있고 builtins에
있을 수도 있다. 반복 실행에서 module 딕셔너리의 같은 항목을 계속 읽는다면
딕셔너리 key 구조의 version과 찾은 index를 cache에 저장하고
`LOAD_GLOBAL_MODULE` 같은 빠른 경로를 사용할 수 있다. 다음 실행의 guard가
version을 확인하므로 key 구조가 바뀌지 않았다면 hash와 이름 탐색을 반복하지
않는다.

specialized 명령도 Python의 동적 변경을 무시할 수는 없다. 타입이나 딕셔너리
구조가 달라져 guard가 실패하면 de-optimize하여 더 일반적인 명령으로 돌아간다.
빠른 명령이 틀린 결과를 내는 대신, 가정이 유효한 동안만 검사를 줄이는 구조다.

instruction family의 구성원은 같은 수의 inline cache entry를 차지한다. 실행 중
opcode가 바뀌어도 뒤 명령의 위치와 점프 거리가 변하지 않아야 하기 때문이다.

## JIT는 여러 명령의 반복 경로를 한꺼번에 본다

opcode 특수화는 한 명령 안의 빠른 경우를 찾는다. 그러나 앞 명령에서 확인한
타입 정보를 뒤 명령까지 이용하거나 여러 중간 검사를 함께 없애려면 더 긴 실행
단위가 필요하다. CPython 3.14의 실험적 JIT는 반복해서 실행된 trace를 그 단위로
사용한다.

대표적인 진입점은 반복문 끝의 뜨거운 `JUMP_BACKWARD`다. 실행 횟수가 임계값에
도달하면 옵티마이저가 현재 Frame과 명령 위치에서 trace를 만들고, 바이트코드를
uop 시퀀스로 펼친 뒤 분석한다. 준비된 executor는 CodeObject에 연결되고 이후
해당 지점에서 최적화된 경로로 들어간다.

```text
바이트코드 trace
    ↓ uop으로 펼치기
최적화된 uop 시퀀스
    ├─ uop 인터프리터에서 실행
    └─ JIT가 만든 네이티브 코드에서 실행
```

trace는 함수 전체나 모든 분기를 덮지 않는다. 예상하지 않은 분기를 만나거나
guard가 실패하거나 trace의 끝에 도달하면 출구를 통해 적응형 인터프리터로
돌아간다. 다른 최적화 trace로 이어질 수 있는 출구도 있다.

완전한 JIT는 미리 컴파일한 기계어 조각을 복사하고 현재 주소와 상수를 채우는
copy-and-patch 방식을 쓴다. 런타임에 전체 컴파일러를 다시 돌리지 않아 trace
컴파일 지연을 줄이기 위한 선택이다. 이 JIT는 CPython 3.14에서 실험적 기능이므로
세부 구조와 설정은 안정적인 호환 규격이 아니다.

inline cache의 필드, 특수화 통계, uop 생성 파일과 JIT stencil 생성 과정은 기존
[프로그램 실행 상세 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md#특수화)에서
확인할 수 있다.

[가이드 홈](../README.ko.md) · 기준 흐름: [평가 루프와 세 가지 스택](evaluation-loop.ko.md)
