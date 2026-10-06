# 24건 종료 권고 독립 재검증

2026년 10월 6일(KST)에 수집한 새 증거로 **24건 모두 원문 범위의 해결을 확인**했다. 종료 권고는 **24건 유지 가능**하다. 제출 초안과 세부 보고서의 처리 권고는 **그대로 유지 22건, 문구 수정 2건**이다. 철회·보류·종료 요청 불필요는 각각 0건이다. GitHub 이슈는 조회 시 모두 open이었다.

초안의 “24건이 해결됐다”는 기술적 결론과 다른 판정은 나오지 않았다. 다만 **#4690의 타입 설명은 틀렸고, #8494의 세부 보고서는 변형 입력을 원문 그대로라고 잘못 표시했다.** 두 문구는 제출 전에 수정해야 한다. 다른 범위의 알려진 차이까지 해결됐다는 뜻은 아니다.

## 대상과 판정

인터프리터 기준은 `f39b054b9c8cbbf884f53123eef028131789990c`, 검토한 보고서는 `ad600eb347fd7de31a453dd56cd377d6ae948c10`이다. 서로 다른 두 커밋을 구분했다. 고정 보고서의 대상 절에는 지정된 24건이 정확히 한 번씩 있고 누락·중복·추가 대상은 없다. [초안 목록 검사](parent/draft-inventory.json), [고정 초안](parent/submission-draft.md), [원문 조회 상태](parent/current-issue-states.json)에 근거를 보존했다.

**초안 그대로 유지 가능한 22건:** [#2527](cases/2527/README.md), [#3418](cases/3418/README.md), [#3430](cases/3430/README.md), [#3846](cases/3846/README.md), [#4506](cases/4506/README.md), [#4527](cases/4527/README.md), [#4541](cases/4541/README.md), [#4762](cases/4762/README.md), [#4769](cases/4769/README.md), [#4784](cases/4784/README.md), [#4786](cases/4786/README.md), [#4856](cases/4856/README.md), [#4907](cases/4907/README.md), [#4908](cases/4908/README.md), [#4937](cases/4937/README.md), [#4950](cases/4950/README.md), [#4970](cases/4970/README.md), [#5179](cases/5179/README.md), [#5656](cases/5656/README.md), [#5699](cases/5699/README.md), [#6429](cases/6429/README.md), [#8052](cases/8052/README.md).

**문구 수정 후 종료 권고 가능한 2건:** [#4690](cases/4690/README.md), [#8494](cases/8494/README.md).

**철회·보류·종료 요청 불필요:** 없음. 부분 해결·미해결·검증 불가로 분류한 원문도 없다. 각 사례의 기술 판정과 초안 처리 권고는 [results.json](results.json)에 별도 필드로 저장했다.

## 필요한 문구 수정

**#4690 — 제출 초안과 세부 보고서의 타입 설명.** 원문의 두 조회는 서로 다른 타입을 반환한다. 새 RustPython/CPython 실행 모두 원시 `dict.__dict__["fromkeys"]`는 `classmethod_descriptor`, 바인딩된 `dict.fromkeys`는 `builtin_function_or_method`다. 기존 “Both original native descriptor queries now return classmethod_descriptor”는 실제 출력과 모순된다. 다음으로 교체할 수 있다.

> The raw descriptor `dict.__dict__["fromkeys"]` now has type `classmethod_descriptor`, while the bound `dict.fromkeys` has type `builtin_function_or_method`, matching CPython. Descriptor binding and the additional native descriptors checked also agree with CPython.

**#8494 — 세부 보고서의 원문/변형 구분.** 기존 보고서의 `# This is the literal original` 주석이 붙은 예제는 `issue8494()` 내부로 옮겨져 있다. 원문의 module-level `Missing` 조회와 동일한 입력이라고 부르면 안 된다. 이번에는 모듈 최상위 원문과 함수 내부 변형을 각각 실행해 둘 다 통과했다. 제출 초안의 동작 결론은 유지 가능하며, 세부 보고서의 주석과 설명을 다음처럼 고친다.

> The module-level example from the issue and a separate function-local variant were both executed. For both `classmethod` and `staticmethod`, reads cache the two annotation attributes on the wrapper; assignment and deletion leave the wrapped function unchanged. The existing regression test also passes.

변형 코드의 주석은 `# Function-local variant of the issue example; the module-level original is tested separately.`로 바꾸는 것이 정확하다. 기존 파일은 수정하지 않았다.

## 새 실행으로 확인한 범위

모든 사례는 원문 본문과 범위에 영향을 주는 댓글을 읽고 계획을 저장한 뒤 고정 초안의 추가 주장까지 대응시켰다. 대화 이력을 받지 않는 새 에이전트 2개(`fork_turns="none"`)가 A/B를 각각 독점했다. [담당·실행 순서](parent/execution-allocation.json)와 최초 계획 해시([A](parent/phase-gate-A.json), [B](parent/phase-gate-B.json))를 보존했다. 원문 계획은 이후 바뀌지 않았다.

- #2527은 실제 PTY에서 원문 loop의 0–9, with 블록의 5, 각 프롬프트를 확인했다. #4541은 script/-c/-m/symlink/실제 REPL × 7개 flag/env 설정 × 두 인터프리터의 70회 실행으로 실제 경로와 import를 검사했다.
- #3846은 실제 bytecode를 끝까지 순회하고 local import graph를 실행했다. 기준 커밋의 17개 테스트와 원문 연결 PR #3863에서 추출한 수정 없는 437줄의 17개 테스트를 각각 두 인터프리터에서 실행해 skip/expectedFailure 없이 통과했다.
- #4506은 실제 SymPy 1.11.1/mpmath 1.2.1 경로를 확인하고 원래 실패한 `power.py:378` 대입을 trace했다. #4527은 정상 종료에서 `deleted!`, exit 0, 빈 stderr를 확인했다.
- #4769는 정수 pickle 오타의 예상 AttributeError와 의도한 deque 입력을 구분했다. protocol 0–5의 36회 상태 보존과 기존 회귀 테스트를 확인했다. #4856은 원문의 컴파일 성공/미정의 BaseFTests NameError와 보정 앱의 실행 성공을 구분했다.
- #4907은 실제 event loop의 두 await 완료, #4908은 7개 입력의 재파싱과 AST 구조를 확인했다. #4950은 명시된 17개 spec × 두 bool의 34행 및 실제 적용한 네 locale을 확인했다.
- #4970은 LC_ALL을 실제 제거하고 en_US.UTF-8 grouping을 적용했다. 원래 test_locale와 int/float locale 테스트 3개가 skip/expectedFailure 없이 통과했다.
- #5179는 buffer 읽기·쓰기·해제, export 중 resize 차단과 해제 후 resize를 확인했다. #5656은 SyntaxWarning 및 warning-as-error, #5699는 네 blocker와 실제 미처리 예외 네 종류의 ANSI·제안 문구를 확인했다.
- #8052는 name/repr·두 alias·JSON 회귀 테스트 2개, #8494는 두 wrapper와 두 annotation 속성의 읽기/cache/대입/삭제·함수 독립성 및 회귀 테스트를 확인했다. 나머지 원문 및 추가 표본도 각 보고서에 입력과 결과를 수록했다.
- #4784는 기준 README의 실제 목적지 응답 본문과 별도 API 페이지를 읽어 RustPython 0.6.0 crate/API 문서임을 확인했다. HTTP 상태 코드만으로 판정하지 않았다.

350개의 실행·조회 기록 중 인터프리터 호출 기록은 194개다. 이것은 테스트 개수가 아니며 환경 식별 호출도 포함한다. [통합 실행 기록](executions.jsonl)은 argv/cwd/env, 입력 및 실행 파일 hash, 시작·종료 시각, stdout/stderr 경로, 종료 코드, timeout과 판정 근거를 담는다. 기록상 슬롯 내 실행 중첩은 0, 최대 동시 인터프리터 실행은 2이다. [기록 감사](parent/evidence-audit.json)에서 중복 ID·누락 로그·기록된 전후 hash 불일치는 발견되지 않았다.

## 환경과 남는 한계

A는 macOS ARM64 RustPython이며 SHA-256은 `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`다. B는 x86_64 RustPython이며 SHA-256은 `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`이다. 비교 CPython은 3.14.6 ARM64, SHA-256 `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`다.

B는 실제로 A의 `Lib`를 먼저 읽는다. 로드 경로를 확인했고 그곳의 추적된 Lib 파일 2,324개가 기준 커밋과 일치했다. 소스 HEAD 일치만으로 바이너리를 판정하지 않았다. 내장 배너, 보존된 성공 빌드 기록, 해당 산출물 hash 및 B로의 동일 hash 복사 기록을 함께 확인했다. 새로 빌드하거나 과거 빌드의 모든 입력을 재현한 것은 아니다. 자세한 근거는 [A 식별](agent-a/environment/identity.json), [B 식별](agent-b/environment/IDENTITY.md)에 있다.

- #3430은 유효 XML의 원래 TypeError가 해결됐다. 잘못된 닫는 태그 `<a></b>`를 허용하는 차이는 남아 있으므로 XML 전체 호환성을 주장하지 않는다.
- #4786의 원래 단일 surrogate 입력은 CPython과 같은 UnicodeEncodeError다. 연속 surrogate 보강 입력의 오류 `end`는 서로 달랐다.
- #4970에서 `en_US.UTF8` 별칭은 없다. 테스트의 다음 후보 `""`는 명시한 en_US.UTF-8의 실제 grouping을 사용했으며 C fallback이나 skip을 통과로 세지 않았다.
- #2527/#4541 PTY는 출력과 프롬프트 확인 후 flush와 `os._exit(0)`로 사용자 history 저장을 피했다. REPL 정상 종료 검증은 아니다. 정상 종료가 핵심인 #4527은 우회 없이 따로 실행했다.
- #5699는 강제 색상 설정의 pipe 캡처다. 모든 터미널의 자동 색상 탐지를 확인한 것은 아니다. #4784의 현재 외부 문서는 기준 커밋에서 새로 빌드한 문서가 아니다.
- 명시된 초안의 동작 주장 중 미실행 항목은 없다. 전체 플랫폼/라이브러리 호환성, 과거 revision 재실행, 최초 수정 커밋은 확인하지 않았다. 관련 변경의 실제 diff와 기준 커밋 조상 여부만 확인했다.

## 과거 증거와 보존 확인

원문·초안 입력을 새로 실행한 결과와 과거 로그를 구분했다. 과거 실패 로그와 관련 빌드/복사 기록은 보존된 자료를 읽고 hash로 확인해 재사용했으며, 과거 실행 파일은 다시 실행하지 않았다. 코드 표시와 저장 입력 사이의 서식·경로 익명화·공유 함수 추출 차이도 사례별로 설명했다. [초안 입력 대조](parent/report-fidelity-audit.json)는 텍스트 수준의 차이 목록이며, 동작 동등성 판정은 각 사례에 있다.

세 기존 워크트리의 시작·종료 HEAD와 Git 상태를 대조했다. 추적 파일은 A 3,470개, B 3,470개, 보고서 4,635개, 합계 11,575개이며 내용 변경은 0건이다. 새 결과 경로를 제외한 Git 상태의 추가·제거도 0건이다. [전후 비교](parent/preservation-comparison.json)에 결과가 있다.

A는 선택해 재사용한 기존 파일 190개와 과거 survey 입력·로그 70개, B는 기존 증거 182개·패키지 1,601개·로드 Lib 2,324개를 추가 대조했다. 변경은 없었고 패키지 경로에 새 파일도 없었다. 실행 입력/실행 파일의 전후 hash도 대조했다. 이 수는 범위가 겹치므로 합산한 고유 파일 수가 아니다. 읽거나 hash하지 않은 모든 ignored 파일·빌드 캐시·사용자 파일까지 보존을 검증했다는 주장은 하지 않는다.

이번 새 출력 경로의 A 초기 source-collector는 sandbox 네트워크 실패 로그를 성공한 재시도 로그로 덮어썼으며 실패 metadata만 남았다. 이 수집 기록의 한계를 공개한다. 기존 자료 손실이나 재현 실행 결과의 삭제는 아니다. 별도 XML 보강 입력의 생성 실수로 두 인터프리터가 SyntaxError를 낸 시도도 입력/로그를 보존했고, 새 파일의 올바른 입력 결과만 기술 판정에 사용했다.

소스·기존 테스트·assertion·skip/expectedFailure·기존 보고서·기존 의존성 파일은 수정하지 않았다. 새 clone/worktree/target/venv/container, 빌드, commit, push, 업로드, GitHub 이슈/PR/댓글 작성 및 이슈 종료는 수행하지 않았다. 코드 변경이 없는 지정 재현 검증으로 범위를 제한했으므로 전체 Cargo 테스트·clippy·문서 빌드는 실행하지 않았다.

AI assistance: OpenAI Codex가 독립 실행 검증, 자료 대조 및 새 보고서 작성을 수행했다.
