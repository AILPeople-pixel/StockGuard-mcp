import yfinance as yf
from mcp.server.fastmcp import FastMCP
import random

# 1. MCP 서버 초기화
mcp = FastMCP("KakaoStockGuardian")

@mcp.tool()
def analyze_stock(ticker: str) -> str:
    """
    특정 주식 종목의 최신 재무 데이터, 주가, 뉴스를 분석하여 '지킴이 리포트'를 생성합니다.
    
    [중요: 한국어 및 국내 주식 검색 지원]
    사용자가 '삼성전자', '애플', '에코프로' 등 한국어 기업명이나 약칭을 입력하면, 
    반드시 당신(LLM)이 야후 파이낸스 기준 티커(Ticker)로 변환하여 이 도구의 ticker로 전달하세요.
    - 한국 코스피 주식: 종목코드 6자리 + '.KS' (예: 삼성전자 -> 005930.KS, SK하이닉스 -> 000660.KS)
    - 한국 코스닥 주식: 종목코드 6자리 + '.KQ' (예: 에코프로 -> 086520.KQ)
    - 미국 주식: 알파벳 티커 (예: 애플 -> AAPL, 테슬라 -> TSLA)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 기업 정보 추출
        company_name = info.get('longName', ticker)
        current_price = info.get('currentPrice', '데이터 없음')
        currency = info.get('currency', 'USD')
        
        # 재무 건전성 지표 추출
        debt_to_equity = info.get('debtToEquity', None) # 부채비율
        quick_ratio = info.get('quickRatio', None)       # 당좌비율 (단기 상환 능력)
        
        # 1. 뉴스 가져오기 로직
        news_list = stock.news
        latest_news = "최근 관련 뉴스가 없습니다."
        if news_list and len(news_list) > 0:
            # 가장 첫 번째(최신) 뉴스의 제목과 링크 가져오기
            news_title = news_list[0].get('title', '제목 없음')
            news_link = news_list[0].get('link', '#')
            latest_news = f"[{news_title}]({news_link})"

        # 2. 1~10점 점수 산출 로직
        score = 5.0  # 기본 점수
        
        if debt_to_equity is not None:
            if debt_to_equity < 50:
                score += 2.5 # 부채가 아주 적으면 가산점
            elif debt_to_equity < 100:
                score += 1.0
            elif debt_to_equity > 200:
                score -= 2.0 # 부채가 너무 많으면 감점
            elif debt_to_equity > 150:
                score -= 1.0
                
        if quick_ratio is not None:
            if quick_ratio >= 1.5:
                score += 2.0 # 단기 상환 능력이 좋으면 가산점
            elif quick_ratio >= 1.0:
                score += 1.0
            elif quick_ratio < 0.5:
                score -= 2.0 # 당장 갚을 돈이 없으면 심각한 감점
            elif quick_ratio < 1.0:
                score -= 1.0
                
        # 점수가 1.0~10.0 사이를 벗어나지 않게 조정
        score = max(1.0, min(10.0, score))

        # 3. 상황별 명언 로직
        if score >= 8.0:
            quotes = [
                "10년 보유할 주식이 아니면 단 10분도 보유하지 마라. - 워런 버핏\n(지킴이: 이 종목은 푹 묵혀둬도 좋을 만큼 뼈대가 튼튼하네요!)",
                "탁월한 기업을 적당한 가격에 사는 것이 낫다. - 찰리 멍거\n(지킴이: 재무 상태가 탁월합니다. 가격만 맞으면 훌륭한 선택입니다.)"
            ]
        elif score <= 4.0:
            quotes = [
                "부채가 많은 기업은 맑은 날에는 빠르게 달리지만, 비가 오면 진흙탕에 빠집니다. - 피터 린치\n(지킴이: 부채 리스크가 보입니다. 맑은 날인지 비 오는 날인지 확인부터 하세요!)",
                "떨어지는 칼날을 잡지 마라. - 월가 격언\n(지킴이: 섣부른 물타기보다는 재무 개선 여부를 먼저 지켜보시길 권합니다.)"
            ]
        else:
            quotes = [
                "주식 시장은 조급한 사람의 돈을 인내심 있는 사람에게 이동시키는 도구다. - 워런 버핏\n(지킴이: 무난한 상태입니다. 조급해하지 말고 차분히 타이밍을 노려보세요.)",
                "리스크는 자신이 무엇을 하는지 모르는 데서 온다. - 워런 버핏\n(지킴이: 장단점이 혼재되어 있습니다. 기업의 사업 모델을 한 번 더 공부해 보세요.)"
            ]
        
        selected_quote = random.choice(quotes)

        # 리포트 조립
        report = f"📊 [{company_name} ({ticker}) 주식 지킴이 리포트]\n"
        report += f"💵 현재 주가: {current_price} {currency}\n"
        report += f"📰 최근 핫이슈: {latest_news}\n\n"
        
        report += "🔍 [재무 건전성 진단]\n"
        if debt_to_equity is not None:
            report += f"- 부채비율(Debt to Equity): {debt_to_equity:.2f}% " + ("(⚠️높음)" if debt_to_equity > 150 else "(✅양호)") + "\n"
        if quick_ratio is not None:
            report += f"- 당좌비율(Quick Ratio): {quick_ratio:.2f} " + ("(⚠️현금부족)" if quick_ratio < 1.0 else "(✅양호)") + "\n"
            
        report += f"\n🎯 [지킴이 뼈때리는 한줄평]\n"
        report += f"⭐ 재무 안전성 점수: {score:.1f} / 10.0 점\n\n"
        report += f"💡 {selected_quote}"
            
        return report

    except Exception as e:
        return f"주식 데이터를 분석하는 도중 오류가 발생했습니다: {str(e)}\n티커 변환이 잘못되었거나 야후 파이낸스에 데이터가 없는 종목일 수 있습니다."

if __name__ == "__main__":
    import os
    # Render에서 제공하는 포트 번호를 자동으로 잡도록 설정
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", port=port)
