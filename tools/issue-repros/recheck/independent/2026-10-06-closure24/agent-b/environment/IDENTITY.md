# 슬롯 B 실행 환경과 출처

목표는 `f39b054b9c8cbbf884f53123eef028131789990c`다. 현재 B checkout HEAD가 그 리비전이고 tracked diff는 비어 있다. 이것만으로 실행 파일 출처를 판단하지 않았다.

실제 실행 파일은 `<survey>/.build/slot-b/saved/current-f39-x86/rustpython`, realpath도 동일하며 SHA-256은 `d57429291c1011b8b311758237cb66a6fecc22f8647ff14094f5c00fb489d871`다. Mach-O x86_64이며 macOS 26.5.2 ARM64 호스트에서 Rosetta로 실행된다. `--version`은 `3.14.0.alpha (heads/main:f39b054b9, Oct 4 2026, 13:53:35)`와 RustPython 0.6.1/rustc 1.99.0을 보고한다. otool -L 결과도 저장했다.

보존된 `analysis/current-5419-x86.json`은 목표 full SHA, cargo +1.99.0 build --target x86_64-apple-darwin --release --locked, 성공 종료 및 동일 binary SHA를 기록한다. `logs/build-a/x86-release.stderr`는 주 작업 폴더에서 성공한 release build를 기록한다. `analysis/current-5332-pip25-checkpoint-correctexe-provenance-b.json`은 A의 보존 산출물을 B의 표준 rustpython 파일명으로 복사한 관계를 기록한다. 실제 보존 A 산출물의 해시도 B cwd에서 읽기 전용으로 확인했고 B 파일과 완전히 같다. A 실행 파일을 실행하지 않았다.

이 배너·보존 기록·산출물 해시 관계는 목표 리비전에 대한 출처를 뒷받침한다. 새로 빌드하지 않았고 빌드 당시 모든 입력 파일이 깨끗했다는 완전한 동시점 attestation은 없다. 따라서 현 HEAD나 배너만으로 임의 변경이 전혀 없었던 재현 빌드를 증명했다고 말하지 않는다. 보존 provenance의 typing 경로 주장도 현재 import 관찰을 대신하지 않는다.

중요한 실제 경로: `RUSTPYTHONPATH=<slot-b-source>/Lib`를 설정해도 sys.path에는 주 작업 폴더 `<workspace>/Lib`가 먼저 온다. ast/email/pickle/collections/asyncio/unittest.mock/traceback/types/test 모듈도 그 경로에서 로드된다. 이 현재 주 작업 폴더 Lib의 추적 파일 2,324개를 목표 Git blob과 비교했고 불일치가 없었다. B의 Lib만 사용한 것처럼 기록하지 않는다.

CPython은 `<home>/.local/bin/python3`에서 실행한 3.14.6 arm64이고 realpath는 records/env-identity-cp.json에 있다. SHA-256은 `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`다. 독립 비교는 해당 CPython의 stdlib를 사용한다. CPython 배포에 test 패키지는 없으므로 repository unittest는 RustPython에서만 실행했다.

모든 런타임 cwd는 `<slot-b-source>`다. 공통 환경은 `PYTHONDONTWRITEBYTECODE=1`, `RUSTPYTHONPATH=B/Lib`, `LANG=LC_ALL=LC_CTYPE=C.UTF-8`, `TERM=dumb`이고 SYMPY_SITE는 보존 패키지 경로를 가리킨다. locale.setlocale(..., None)의 실제 결과는 RustPython `C`, CPython `C/C.UTF-8/C/C/C/C`다. locale -a의 전체 가능 목록은 logs/env-locales.stdout에 보존했다. 본 슬롯의 판정은 locale 서식에 의존하지 않는다. 색상 traceback은 `PYTHON_COLORS=1 FORCE_COLOR=1`을 추가했다.

각 프로세스는 controller.py에서 새 process group으로 실행하며 30–90초 timeout을 둔다. 정상 종료를 먼저 기다리고 남은 process group을 정리한다. temp/history는 새 agent-b/environment 아래로 분리했고 -B를 적용했다. 실행 ID는 재사용을 거부한다. 명령·환경·시간·입력/실행 파일 전후 해시·stdout/stderr·종료·timeout·판정 근거는 records/<ID>.json에 있다. 기존 source/tests/assertion/skip marker, build/cache와 외부 서비스를 변경하지 않았다.
