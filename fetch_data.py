"""뉴스 Top5 + 나라장터 퇴직연금 사업자 선정 공고를 모아 data.json으로 저장 (표준 라이브러리만 사용)"""
import difflib, json, os, re, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
# 조달청 나라장터 입찰공고정보서비스(용역, 공고명 검색). 인증키 발급 후 이 주소가 맞는지 먼저 확인할 것
BID_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def norm(t):
    return re.sub(r"[^0-9a-z가-힣]", "", t.lower())

def news(q="퇴직연금", days=3, dedupe=True):
    """최근 days일 기사를 모두 가져와 같은 내용(제목이 거의 같은 기사)은 하나만 남기고 최신순 정렬"""
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + f" when:{days}d", "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
    items, seen = [], []
    for it in ET.fromstring(get(url)).iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        k = norm(title)
        if not k or (dedupe and any(difflib.SequenceMatcher(None, k, o).ratio() >= 0.8 for o in seen)):
            continue
        seen.append(k)
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
        except Exception:
            dt = None
        items.append((dt or NOW, {"title": title, "source": src,
                                  "date": dt.strftime("%m.%d %H:%M") if dt else "", "url": it.findtext("link")}))
    items.sort(key=lambda x: x[0], reverse=True)
    return [i[1] for i in items]

# 희망퇴직 현황에서 구분할 주요 기업 (이름: 제목에서 찾을 말). 위에서부터 먼저 맞는 기업으로 분류하니 긴 이름을 앞에 둘 것
COMPANIES = {
    "KB국민은행": ["국민은행", "KB국민"], "신한은행": ["신한은행"], "하나은행": ["하나은행"], "우리은행": ["우리은행"],
    "NH농협은행": ["농협은행"], "IBK기업은행": ["기업은행"], "SC제일은행": ["SC제일", "제일은행"], "한국씨티은행": ["씨티은행"],
    "iM뱅크": ["iM뱅크", "대구은행"], "BNK부산은행": ["부산은행"], "BNK경남은행": ["경남은행"],
    "삼성생명": ["삼성생명"], "한화생명": ["한화생명"], "교보생명": ["교보생명"], "삼성화재": ["삼성화재"],
    "현대해상": ["현대해상"], "DB손해보험": ["DB손보", "DB손해보험"], "KB손해보험": ["KB손보", "KB손해보험"],
    "신한카드": ["신한카드"], "삼성카드": ["삼성카드"], "롯데카드": ["롯데카드"], "현대카드": ["현대카드"],
    "KB증권": ["KB증권"], "NH투자증권": ["NH투자증권"], "한국투자증권": ["한국투자증권"],
    "미래에셋증권": ["미래에셋증권"], "삼성증권": ["삼성증권"],
    "삼성전자": ["삼성전자"], "LG전자": ["LG전자"], "LG디스플레이": ["LG디스플레이"], "SK하이닉스": ["SK하이닉스"],
    "포스코": ["포스코"], "두산": ["두산"], "롯데": ["롯데"], "한화": ["한화"],
}

def company_of(title):
    for name, kws in COMPANIES.items():
        if any(k in title for k in kws):
            return name
    return "기타 기업"

def retire(days=14):
    """희망퇴직 기사를 기업별로 묶어 기업당 최신 기사 1건 + 관련 기사 목록으로 정리"""
    arts = [a for a in news("희망퇴직 OR 명예퇴직", days, dedupe=False)
            if re.search("희망퇴직|명예퇴직|특별퇴직", a["title"])]
    groups = {}
    for a in arts:
        groups.setdefault(company_of(a["title"]), []).append(a)
    out = []
    for name, lst in groups.items():
        uniq = []
        for a in lst:  # 같은 기업 안에서만 비슷한 제목 제거 (기업이 다르면 제목이 비슷해도 별개)
            if not any(difflib.SequenceMatcher(None, norm(a["title"]), norm(u["title"])).ratio() >= 0.8 for u in uniq):
                uniq.append(a)
        m = re.search(r"(\d[\d,]*)\s*명", uniq[0]["title"])
        out.append({"company": name, "count": len(uniq), "people": m.group(1) + "명" if m else "",
                    "latest": uniq[0], "articles": uniq[1:6]})
    out.sort(key=lambda g: (g["company"].startswith("기타"), -g["count"]))
    return out

def bids(key, kw="퇴직연금", days=30):
    q = {"serviceKey": urllib.parse.unquote(key), "numOfRows": 100, "pageNo": 1, "inqryDiv": 1,
         "type": "json", "bidNtceNm": kw,
         "inqryBgnDt": (NOW - timedelta(days=days)).strftime("%Y%m%d0000"),
         "inqryEndDt": NOW.strftime("%Y%m%d2359")}
    body = json.loads(get(BID_URL + "?" + urllib.parse.urlencode(q)))["response"]["body"]
    items = body.get("items") or []
    if isinstance(items, dict):
        items = items.get("item", [])
    if isinstance(items, dict):
        items = [items]
    out = [{"title": i.get("bidNtceNm", ""), "org": i.get("ntceInsttNm") or i.get("dminsttNm", ""),
            "posted": i.get("bidNtceDt", ""), "close": i.get("bidClseDt", ""),
            "url": i.get("bidNtceDtlUrl", "")} for i in items if kw in i.get("bidNtceNm", "")]
    return sorted(out, key=lambda x: x["posted"], reverse=True)

def main():
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        old = {}
    stamp = NOW.strftime("%Y-%m-%d %H:%M")
    data = {"news": old.get("news", []), "bids": old.get("bids", []), "notes": [],
            "sample": old.get("sample", False),
            "retire": old.get("retire", []), "retire_updated": old.get("retire_updated", ""),
            "news_updated": old.get("news_updated", ""), "bids_updated": old.get("bids_updated", "")}
    try:
        data["news"] = news(); data["news_updated"] = stamp; data["sample"] = False
    except Exception as e:
        print("news 실패:", e, file=sys.stderr); data["notes"].append("기사 갱신에 실패해 이전 내용을 보여줍니다.")
    try:
        data["retire"] = retire(); data["retire_updated"] = stamp; data["sample"] = False
    except Exception as e:
        print("retire 실패:", e, file=sys.stderr); data["notes"].append("희망퇴직 현황 갱신에 실패해 이전 내용을 보여줍니다.")
    key = os.environ.get("DATA_GO_KR_KEY", "")
    if key:
        try:
            data["bids"] = bids(key); data["bids_updated"] = stamp; data["sample"] = False
        except Exception as e:
            print("bids 실패:", e, file=sys.stderr); data["notes"].append("공고 갱신에 실패해 이전 내용을 보여줍니다.")
    else:
        data["notes"].append("나라장터 인증키가 설정되지 않아 공고를 불러오지 못했습니다.")
    data["updated"] = stamp
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
