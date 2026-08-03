# 예외 테이블과 Frame 되감기가 전파를 나눠 맡는다

CPython은 `try` 블록을 실행할 때마다 현재 handler를 별도 스택에 넣었다 빼지
않는다. 컴파일러가 보호 범위와 handler 위치를 CodeObject의
`co_exceptiontable`에 기록해 두고, opcode가 실제로 실패했을 때만 현재 명령
위치로 이 테이블을 조회한다. 이것이 CPython에서 말하는 zero-cost exception의
핵심이다.

handler를 찾으면 평가 스택을 약속된 깊이로 복구하고 그 위치에서 실행을
재개한다. 현재 Frame에 handler가 없으면 Frame을 빠져나가 호출자의 `CALL`
위치에서 같은 검색을 반복한다. 이때 빠져나온 Frame의 위치가 traceback에
추가된다.

## 컴파일러가 정상 경로 밖에 처리 정보를 둔다

다음 코드에는 `divide(0)`을 실행하는 정상 경로와 실패를 처리하는 경로가 있다.

```python
try:
    result = divide(0)
except ZeroDivisionError:
    result = None
```

컴파일 과정에서는 `try`의 시작과 끝을 나타내는 의사 명령을 사용할 수 있지만,
최종 바이트코드에는 이를 매번 실행할 opcode로 남기지 않는다. 대신 예외
테이블에 다음 정보를 압축해 저장한다.

- 보호할 바이트코드 범위
- 예외를 넘길 handler 위치
- handler가 시작할 때 필요한 평가 스택 깊이
- 원래 실패한 명령 위치인 `lasti`를 스택에 보존할지 여부

따라서 예외가 발생하지 않는 동안에는 이 테이블을 조회할 이유가 없다.
zero-cost는 예외 객체 생성과 Frame 되감기(unwind)까지 공짜라는 뜻이 아니라, 정상
경로에서 handler 상태를 계속 관리하는 비용을 피한다는 뜻이다.

## 실패한 opcode가 공통 예외 경로를 연다

opcode 구현이 실패하면 예외 상태를 설정하고 평가 루프의 공통 unwind 경로로
이동한다. 이후 제어 흐름은 다음 순서로 갈린다.

```text
opcode 실패
    ↓
현재 명령 오프셋으로 co_exceptiontable 검색
    ├─ handler 있음 → 평가 스택 복구 → 예외 정보 push → handler로 점프
    └─ handler 없음 → 현재 Frame 되감기 → 호출자 Frame에서 다시 검색
```

예외는 표현식 계산 중에도 발생한다. 이때 평가 스택에는 아직 쓰지 못한
피연산자와 중간 결과가 남아 있을 수 있다. handler는 임의의 스택 모양에서
시작할 수 없으므로, 인터프리터는 테이블에 기록된 깊이까지 값을 버린다.
필요하면 `lasti`를 올리고 예외를 올린 뒤 handler의 첫 명령으로 이동한다.

`lasti`는 특히 `finally`를 실행한 뒤 예외를 다시 발생시킬 때 필요하다.
현재 명령 위치는 이미 `finally` 안으로 이동했으므로, 원래 어느 명령에서
실패했는지를 별도로 보존해야 traceback과 디버깅 위치를 복구할 수 있다.

## handler가 없으면 Frame 단위로 전파된다

현재 CodeObject의 예외 테이블에 맞는 항목이 없으면 인터프리터는 그 Frame의
실행을 끝내고 호출자로 예외를 넘긴다. 호출자에서는 피호출자를 실행하던
`CALL` 위치가 새 검색 기준이 된다. 호출자 쪽 `try`가 그 호출을 감싸고 있었다면
그 handler가 예외를 받을 수 있다.

인터프리터는 handler를 찾거나 최상위 Frame에 도달할 때까지 이 과정을 반복한다.
Frame을 하나씩 빠져나올 때 해당 실행 위치가 traceback에 기록된다. 끝까지
handler가 없으면 평가 함수는 실패를 나타내고, 사용자는 예외가 지나온 호출
경로를 traceback으로 보게 된다.

예외 전파는 일반 이름 조회와 다르다. 이름을 찾을 때는 호출자 Frame을 탐색하지
않지만, 처리되지 않은 예외는 실제 호출 관계를 따라 올라간다. Frame stack이
필요한 대표적인 이유가 이 되감기와 traceback 구성이다.

예외 테이블의 가변 길이 인코딩, code unit 기준 오프셋, `__context__`와
`__cause__` 설정까지 확인하려면 기존
[예외 처리 상세 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md#제4부-예외-처리)를
참고한다.

[가이드 홈](../README.ko.md) · 기준 흐름: [평가 루프와 세 가지 스택](evaluation-loop.ko.md)
