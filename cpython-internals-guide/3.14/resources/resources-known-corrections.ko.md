# 기존 상세 노트와 CPython 3.14.6의 차이

기존 노트는 원문 대응 번역과 작업 기록을 보존한다. 새 가이드를 만들면서 CPython
3.14.6 소스와 다시 대조해 보니 일부 설명이 현재 구현과 맞지 않거나 필수 조건을
빠뜨리고 있었다. 원본은 수정하지 않고, 새 문서에는 아래 내용을 반영했다.

| 주제 | 3.14.6에서 확인한 내용 | 반영한 문서 |
|---|---|---|
| `.pyc` 매직 넘버 | 값의 정본은 `Include/internal/pycore_magic_number.h`의 `PYC_MAGIC_NUMBER`다. `_bootstrap_external.py`는 `_imp.pyc_magic_number_token`에서 값을 얻는다. | [바이트코드 추가](../how-to/guide-add-bytecode.ko.md) |
| keyword 생성 | hard·soft keyword가 바뀌면 `regen-pegen` 외에 `make regen-keyword`로 `Lib/keyword.py`를 갱신한다. | [문법 변경](../how-to/guide-change-cpython-grammar.ko.md), [Pegen 참조](../reference/pegen-and-parser.ko.md) |
| 위치 테이블 long 형식 | 열 값은 `column + 1`로 저장하고 조회할 때 `1`을 뺀다. 저장값 `0`은 열 없음인 `-1`이다. | [런타임 객체 참조](../reference/runtime-objects.ko.md#co_linetable-조회표) |
| `CLEANUP_THROW` | 일반적인 위임 종료는 `SEND → END_SEND`를 따른다. `CLEANUP_THROW`는 중단된 `YIELD_VALUE` 주위의 예외 처리 경로다. | [제너레이터와 코루틴](../explanations/generators-and-coroutines.ko.md) |

이 목록은 기존 노트 전체가 부정확하다는 뜻이 아니다. 새 가이드가 기존 설명과 다를
때 어떤 쪽을 3.14.6 기준으로 채택했는지 밝히는 변경 기록이다.

[가이드 홈](../README.ko.md) · [기존 문서 대응표](resources-source-map.ko.md)
