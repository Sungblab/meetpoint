"""서로 연결된 사람의 전자 명함을 휴대폰 연락처 파일(vCard 3.0)로 만든다."""

from urllib.parse import quote


def _esc(value: str) -> str:
    # RFC 6350 3.4: 역슬래시, 쉼표, 세미콜론, 줄바꿈을 이스케이프한다.
    return (
        value.replace("\\", "\\\\")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\r\n", "\\n")
        .replace("\r", "\\n")  # 홀로 쓴 CR도 줄바꿈으로 읽는 연락처 앱이 있어 칸을 새로 끼워 넣지 못하게 한다
        .replace("\n", "\\n")
    )


def build_vcard(*, name: str, company: str, job_title: str, headline: str, phone: str, email: str, other: str,
                note: str) -> str:
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"N:;{_esc(name)};;;", f"FN:{_esc(name)}"]
    if company:
        lines.append(f"ORG:{_esc(company)}")
    # 직함을 안 적은 사람은 한 줄 소개를 직함 칸에 둔다.
    if job_title or headline:
        lines.append(f"TITLE:{_esc(job_title or headline)}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{_esc(phone)}")
    if email:
        lines.append(f"EMAIL;TYPE=INTERNET:{_esc(email)}")
    memo = note + (f"\n기타 연락처: {other}" if other else "")
    lines.append(f"NOTE:{_esc(memo)}")
    lines.append("END:VCARD")
    return "\r\n".join(lines) + "\r\n"


def vcard_disposition(name: str) -> str:
    # inline이어야 iOS Safari가 파일 앱 대신 연락처 추가 화면을 연다. 안드로이드·데스크톱은 그대로 내려받는다.
    # 한글 이름은 filename*로, 오래된 브라우저에는 ASCII 이름을 준다.
    return f"inline; filename=\"contact.vcf\"; filename*=UTF-8''{quote(name + '.vcf')}"
