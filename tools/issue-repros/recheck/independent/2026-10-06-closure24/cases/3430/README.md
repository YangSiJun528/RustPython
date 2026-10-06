**#3430 — 유효한 XML의 ElementTree 파싱**

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

[원문](https://github.com/RustPython/RustPython/issues/3430)은 2026-10-05T16:08:43.767572+00:00 UTC 조회에서 **open**였다. 본문과 댓글 1개를 모두 읽었다. 비교한 초안은 report commit `ad600eb347fd7de31a453dd56cd377d6ae948c10`의 report.md 및 이 이슈 README다.

원문은 import xml.etree.ElementTree as etree 후 etree.XML("<root></root>")가 None encoding 때문에 TypeError를 내는 문제다. Linux 경로가 나오지만 별도 의존성 버전은 없다. 댓글은 당시 expat 인수 처리가 미완성이었다고 설명한다.

초안 검증 범위: 원래 빈 root와 children/text/attributes/namespaces/UTF-8 표본이 성공한다는 주장이다. 잘못된 닫는 태그를 받아들이는 차이는 초안에도 제한으로 적혀 있다.

모든 새 interpreter 실행의 cwd는 `<workspace>`이고 slot A만 사용했다. OS는 macOS 26.5.2 (25F84), 아키텍처는 ARM64이다. RustPython 실경로는 `<survey>/.build/slot-a/verification/rustpython`, SHA-256은 `a40f4d564f9c53ffcc4ec27c1a61ae3261b68cf3286f511a2ad39fb7f60c9b99`이다. 배너는 Python 3.14.0.alpha / RustPython 0.6.1 / f39b054b9 / rustc 1.99.0이다. CPython은 `<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14`, 3.14.6 ARM64, SHA-256 `58eea46bd68c84e30980ca1133d1b0efb139c878a4934a519dba0846b74069ef`이다. RustPython이 실제 읽은 collections/ElementTree/dis/modulefinder/locale/sysconfig 및 test 파일은 `<workspace>/Lib` 아래이며 [실제 경로와 hash](../../agent-a/environment/identity.json)에 기록했다.

현재 HEAD 및 추적 소스는 목표 `f39b054b9c8cbbf884f53123eef028131789990c`이고 tracked diff는 없다. 바이너리 연결은 HEAD만으로 판단하지 않았다. 실행 배너, Cargo build-script 출력, [기존 build-variants-a.json](../../agent-a/environment/build-variants-a.json)의 `optimized_sqlite` actual_sha·동일 바이너리 SHA, 성공한 verification-profile/default+sqlite 빌드 로그가 함께 일치한다. 재빌드하지 않았으므로 과거 모든 build input의 순수성을 독립적으로 재현·증명한 것은 아니다. 동적 링크는 macOS 시스템 라이브러리로 확인했다.

재현용 공통 shell 설정은 다음과 같다. 아래 Python 코드 블록을 표시한 입력 파일명으로 저장한 다음 실행한다.

~~~sh
SRC='<workspace>'
A='<closure24-audit>/agent-a'
RP='<survey>/.build/slot-a/verification/rustpython'
CP='<home>/.local/share/uv/python/cpython-3.14.6-macos-aarch64-none/bin/python3.14'
export SRC A RP CP
unset PYTHONPATH PYTHONHOME PYTHONWARNINGS PYTHONSTARTUP PYTHONSAFEPATH RUSTPYTHONPATH
unset LC_COLLATE LC_CTYPE LC_MESSAGES LC_MONETARY LC_NUMERIC LC_TIME
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$A/tmp"
export LANG=C LC_ALL=C NO_COLOR=1 TERM=dumb
cd "$SRC"
~~~

아래 코드는 저장한 실제 새 입력이다. 명령의 `RP`, `CP`, `A`, `SRC`는 각각 위 RustPython 실행 경로, CPython 실행 경로, `<closure24-audit>/agent-a`, `<workspace>`의 약어다. 실행은 `-B`와 PYTHONDONTWRITEBYTECODE=1을 적용했고 TMPDIR은 `$A/tmp`로 격리했다. locale·path 환경 및 제거된 변수의 효과는 각 [실행 기록](../../agent-a/executions.jsonl)의 argv/cwd/relevant_env와 stdout/stderr 파일로 확인할 수 있다. 각 실행은 20~60초 timeout과 process-group cleanup을 두었고 이번 재현에 timeout은 없었다.

실행 입력 [3430-original.py](../../agent-a/inputs/3430-original.py.txt), SHA-256 `19c65c7c2b2824ce96f3001be6ef0fcc6f372b09860c57e1a7144e88b7b17870`:

```python
import xml.etree.ElementTree as etree

etree.XML("<root></root>")
```

실행 입력 [3430-parsing-valid.py](../../agent-a/inputs/3430-parsing-valid.py.txt), SHA-256 `971759222f6783e42bd359361ec53d3e8169fab1af33cbe2927c1cdbd8d4a101`:

```python
import xml.etree.ElementTree as etree
import pyexpat

for xml in [
    "<root></root>",
    '<root k="v"><child>text</child></root>',
    '<root xmlns="urn:r"><child a="b">한글🚀</child></root>',
    b'<?xml version="1.0" encoding="UTF-8"?><root>caf\xc3\xa9</root>',
]:
    r = etree.XML(xml)
    print([(e.tag, e.text, sorted(e.attrib.items())) for e in r.iter()])
p = pyexpat.ParserCreate(None, "}")
events = []
p.StartElementHandler = lambda n, a: events.append((n, sorted(a.items())))
p.Parse("<root><child/></root>", True)
print("expat events", events)
assert len(events) == 2
try:
    r = etree.XML("<a></b>")
    print("malformed accepted", r.tag)
except etree.ParseError as e:
    print("malformed rejected", type(e).__name__)
```

실제 실행 명령(공통 cwd는 위 SRC, 환경은 실행 기록 참조):

```sh
# 3430-original-rp
"$RP" -B "$A/inputs/3430-original.py"
# 3430-original-cp
"$CP" -B "$A/inputs/3430-original.py"
# 3430-parsing-valid-rp
"$RP" -B "$A/inputs/3430-parsing-valid.py"
# 3430-parsing-valid-cp
"$CP" -B "$A/inputs/3430-parsing-valid.py"
```

관찰과 판정 근거: 원래 XML 호출은 양쪽 exit 0이다. 빈 root, child의 text, k=v attribute, urn:r namespace, 한글·이모지 및 UTF-8 bytes의 café가 같은 트리 관찰값을 냈다. 직접 pyexpat.ParserCreate(None, '}') 생성 후 실제 Parse를 끝내 start 이벤트 root/child 두 개를 확인했다. 별도 '<a></b>'는 RustPython에서 tag a로 허용되지만 CPython은 ParseError를 냈다. 원래 유효한 XML TypeError가 재발한 것은 아니다. 보강 probe 초안 3430-parsing.py는 생성기의 bytes escape 실수로 두 인터프리터에서 SyntaxError였고 판정에서 제외했다. 그 파일·로그는 보존하고 새 3430-parsing-valid.py로 바로잡았다.

원문·본문·실행 입력 대조: 기존 과거 입력은 원문 결과를 변수에 담아 type/tag/text/len을 출력한다. 새 원문은 원래 호출을 그대로 실행했다. 초안의 빈 줄·따옴표 정리는 동작을 바꾸지 않는다.

과거 310578c422c9b3d76eb8c739136b972d78e37180의 원래 XML 호출은 expat.ParserCreate에서 TypeError: Expected type 'str', not 'NoneType'으로 exit 1이었다.

과거 증거는 `310578c422c9b3d76eb8c739136b972d78e37180`의 기록을 읽어 대조했다. 기록된 exit는 `1`이다. 저장된 historical stdout/stderr의 export hash가 metadata와 일치함을 [별도 audit](../../agent-a/old-history-audit.json)에서 확인했다. 이 과거 바이너리는 이번에 재실행하지 않았다. 경로를 치환한 옛 로그의 hash 일치는 로그 보존 확인이며 과거 빌드의 모든 입력을 새로 인증하는 것은 아니다.

관련 변경: f91ffe34d45ec744cd0d6e00703ed3eb19db0c22 (#6582)는 ParserCreate encoding/namespace_separator를 Option<PyStrRef>로 바꿨다. 358f6a875afa154f9eb04411c0bc8288b2f1082a (#8741)는 native ElementTree parser와 pyexpat 연결을 추가했다. 원문과 연결되는 실제 diff를 읽고 모두 target 조상인지 확인한 기록은 해당 `*-change-*` 및 `*-ancestor-*` execution에 있다. 변경 전 부모와 수정 commit을 각각 실행하지 않았으므로 최초 수정 commit으로 단정하지 않는다.

한계: malformed XML 검증은 해결되지 않았다. 명시적인 비-None encoding 전반과 XML 완전 호환성을 주장할 수 없다. 초안의 명시적 현재 동작 주장은 새 입력으로 모두 확인했다. 과거 revision 재실행과 최초 해결 경계는 확인하지 않았다.

보존: 기존 소스·테스트·assertion·skip marker는 수정하지 않았다. [추적 파일 비교](../../agent-a/environment/tracked-after.json)와 [재사용 파일 비교](../../agent-a/environment/reused-after.json)는 변경 0건이다. 초기 새 source-collector의 sandbox 네트워크 실패 stdout/stderr는 성공 retry가 덮어썼고 실패 metadata만 남았다. 이는 이번 출력 디렉터리의 초기 수집 로그에 국한된다. 재현·identity execution 로그는 고유 ID로 유지했고 입력/바이너리 전후 hash가 같다. 전체 저장소 테스트·clippy·build는 코드 변경 없는 읽기/재현 검증 범위에 따라 실행하지 않았다.

권장 종료 요청 문구: 원래 유효한 XML 및 검사한 유효 XML 표본은 파싱된다. 잘못된 닫는 태그 허용 문제는 별도로 남아 있으므로 XML 전체 호환성을 뜻하지 않는다.

기술 판정: **해결 확인**

초안 처분: **유지** — 위 원문과 명시된 표본 범위를 유지한다. 이슈는 열려 있으므로 종료 요청은 여전히 의미가 있으며 실제 제출은 하지 않았다.
