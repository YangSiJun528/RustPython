# CPython 3.14에 바이트코드 명령 추가하기

새 opcode는 생성된 `case` 파일이 아니라 `Python/bytecodes.c`의 DSL 정의에서
시작한다. 이 정의와 컴파일러의 명령 방출을 수정한 뒤 실행 `case`를 다시
생성하고, 바이트코드 형식 변경을 알리는 `.pyc` 매직 넘버와 frozen importlib도
갱신한다. 마지막에는 재생성 결과가 더 이상 바뀌지 않고 새 인터프리터가 새
명령을 컴파일·표시·실행하는지 확인한다.

이 절차는 CPython 3.14 소스 트리에서 새 바이트코드를 실제로 추가할 때 사용한다.
기존 opcode의 의미나 인자만 바꾸더라도 `.pyc` 호환성이 달라진다면 매직 넘버와
오래된 캐시를 확인해야 한다.

## 1. 원본 정의와 명령 방출을 먼저 고친다

1. `Python/bytecodes.c`에 opcode를 DSL로 정의한다. 입력·출력 stack effect와
   오류 경로를 명시하고, 특수화 대상이면 family와 inline cache 배치도 함께
   설계한다.
2. `Doc/library/dis.rst`에 사용 목적과 인자 의미, stack effect를 문서화한다.
3. `Python/codegen.c`가 필요한 구문에서 새 opcode를 방출하도록 수정한다.
4. 제어 흐름이나 block stack에 영향을 주면 `Python/flowgraph.c`의 최적화와
   `Objects/frameobject.c`의 `frame_setlineno()` 처리를 점검한다.
5. `oparg`를 특별하게 해석하면 `Lib/dis.py`의 표시와 분석 코드도 갱신한다.

`Python/generated_cases.c.h`나 `Include/opcode_ids.h`를 직접 편집하지 않는다.
두 파일은 DSL에서 만들어지는 결과물이다. opcode 번호도 생성기가 배정하게 둔다.

## 2. 실행 case를 다시 생성한다

CPython 저장소 루트에서 다음 명령을 실행한다.

```sh
make regen-cases
```

이 단계는 적어도 opcode ID, interpreter case, stack effect와 opcode 메타데이터를
같은 정의에서 다시 만든다. 명령을 실행한 뒤 diff를 확인해 새 opcode와 관련 없는
생성물이 예상 밖으로 바뀌지 않았는지 살핀다.

다시 `make regen-cases`를 실행했을 때 추가 diff가 생기지 않아야 한다. 생성 결과가
매번 달라지면 정본과 생성 환경부터 바로잡는다.

## 3. `.pyc` 호환 표식을 갱신한다

바이트코드 출력이나 의미가 바뀌면
`Include/internal/pycore_magic_number.h`의 `PYC_MAGIC_NUMBER`를 해당 브랜치의
규칙에 맞춰 올린다. CPython 3.14의
`Lib/importlib/_bootstrap_external.py`는 `_imp.pyc_magic_number_token`으로부터
`MAGIC_NUMBER`를 계산하므로 이 파일에 숫자를 직접 쓰지 않는다. Windows launcher가
인식하는 범위를 벗어났다면 `PC/launcher.c`의 `magic_values` 범위도 갱신한다.

새 opcode 정의와 생성된 `case`가 존재하는 상태에서 다음을 실행한다.

```sh
make regen-importlib
make
```

순서를 바꾸면 frozen importlib을 만드는 인터프리터가 아직 모르는 opcode를 만나
실패할 수 있다. 개발 중 매직 넘버를 아직 올리지 않았다면 저장소와 빌드
디렉터리를 확인한 뒤 그 범위 안의 오래된 `.pyc`만 제거한다. 다른 작업 디렉터리나
사용자 환경의 cache까지 넓게 삭제하지 않는다.

## 4. 컴파일 결과와 실행 의미를 검증한다

새로 빌드한 CPython으로 작은 소스를 컴파일하고 `dis` 결과를 확인한다.

- 의도한 구문에서만 새 opcode가 나오는가?
- `oparg`가 올바른 테이블 항목이나 플래그를 가리키는가?
- 분기 합류점의 평가 스택 깊이가 모두 일치하는가?
- 정상 결과와 오류·예외 경로가 기존 Python 의미와 맞는가?
- inline cache가 있다면 generic, specialized, deopt 경로가 모두 안전한가?

최소한 컴파일과 dis 회귀 테스트를 실행하고, opcode가 구현하는 언어 기능의 관련
테스트도 함께 실행한다.

```sh
./python -m test test_compile test_dis
./python -m test <관련_테스트_모듈>
```

변경 범위에 맞는 전체 테스트와 저장소의 generated-file 검사를 마지막에 실행한다.
정확한 명령은 작업 중인 CPython 브랜치의 개발 가이드를 따른다.

## 완료 조건

- `Python/bytecodes.c`와 compiler의 명령 방출이 새 명령의 한 가지 의미를 공유한다.
- 생성 파일을 직접 수정하지 않았고 재생성 명령을 다시 실행해도 diff가 없다.
- 매직 넘버와 frozen importlib이 새 바이트코드 형식과 맞는다.
- `dis`가 opcode와 인자를 올바르게 표시한다.
- 정상, 분기, 예외, 특수화 대상 경로의 stack effect가 일관된다.
- 관련 테스트와 변경 범위에 필요한 전체 테스트가 통과한다.

파일별 역할과 오래된 `.pyc`를 다루는 상세 배경은 기존
[새 바이트코드 명령 도입 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md#새-바이트코드-명령-도입)를
참고한다.

[가이드 홈](../README.ko.md)
