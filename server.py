import yfinance as yf
from mcp.server.fastmcp import FastMCP
import random
import os

# 1. MCP 서버 초기화
mcp = FastMCP("StockGuard")

@mcp.tool(
    description="Analyzes financial data and stock news for a given ticker, providing a premium report via StockGuard(카카오주식지킴이).",
    annotations={
        "title": "Get Stock Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": True,
        "idempotentHint": True
    }
)
def get_stock(symbol: str) -> str:
    """
    주식 종목의 재무 데이터와 뉴스를 분석하여 '지킴이 리포트'를 생성합니다.
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        company_name = info.get('longName', symbol)
        current_price = info.get('currentPrice', '데이터 없음')
        currency = info.get('currency', 'USD')
        
        debt_to_equity = info.get('debtToEquity', None)
        quick_ratio = info.get('quickRatio', None)
        
        # 뉴스 가져오기
        news_list = stock.news
        latest_news = news_list[0].get('title', '관련 뉴스 없음') if news_list else "최신 뉴스가 없습니다."

        # 점수 산출
        score = 5.0
        if debt_to_equity:
            if debt_to_equity < 50: score += 2.5
            elif debt_to_equity > 200: score -= 2.0
        if quick_ratio:
            if quick_ratio >= 1.5: score += 2.0
            elif quick_ratio < 0.5: score -= 2.0
        score = max(1.0, min(10.0, score))

        # [강화] 세밀해진 등급 로직
        if score >= 8.0:
            quotes = [
                "10년 보유할 주식이 아니면 단 10분도 보유하지 마라. - 워런 버핏\n(지킴이: 이 종목은 뼈대가 매우 튼튼합니다. 장기 투자로 최고예요!)",
                "탁월한 기업을 적당한 가격에 사는 것이 낫다. - 찰리 멍거\n(지킴이: 재무 상태가 우량합니다. 흔들리지 말고 보유하세요!)",
                "최고의 투자는 자신에게 하는 투자입니다. - 워런 버핏\n(지킴이: 훌륭한 종목을 고르셨네요. 안목이 탁월하십니다.)"
            ]
            eval_text = "매우 건전함 (Strong Buy & Hold)"
        
        elif score >= 5.0:
            quotes = [
                "주식 시장은 인내심 있는 사람을 위한 곳입니다. - 워런 버핏\n(지킴이: 무난한 상태입니다. 적립식 투자를 추천해요.)",
                "가격은 당신이 지불하는 것이고, 가치는 당신이 얻는 것이다. - 워런 버핏\n(지킴이: 현재는 안정적입니다. 성장 동력을 계속 주시하세요!)",
                "시장이 비이성적일 때가 기회다. - 벤자민 그레이엄\n(지킴이: 평범한 우등생입니다. 시장 흔들릴 때가 매수 타이밍입니다.)"
            ]
            eval_text = "안정적 / 관망 (Stable & Neutral)"
            
        elif score >= 4.0:
            quotes = [
                "모든 것이 계획대로 되지 않을 때가 가장 위험합니다. - 월가 격언\n(지킴이: 약간 불안합니다. 분할 매도나 현금 비중 조절을 고려하세요.)",
                "리스크는 자신이 무엇을 하는지 모르는 데서 온다. - 워런 버핏\n(지킴이: 재무 지표가 조금 아쉽네요. 기업 내용을 더 자세히 공부해야 합니다.)"
            ]
            eval_text = "주의 필요 (Caution)"
            
        else: # 4.0 미만 (최악의 구간)
            quotes = [
                "부채가 많은 기업은 비가 오면 진흙탕에 빠집니다. - 피터 린치\n(지킴이: 부채 리스크가 심각합니다. 절대적인 주의가 필요해요!)",
                "떨어지는 칼날을 잡지 마라. - 월가 격언\n(지킴이: 재무적 경고등이 강하게 켜졌습니다. 당장 손 떼세요!)",
                "손실을 보지 않는 것이 투자의 첫 번째 규칙이다. - 워런 버핏\n(지킴이: 제발.. 소중한 돈을 지키세요. 이 종목은 피하는 게 상책입니다!)"
            ]
            eval_text = "매우 위험 (Watch Out & Avoid)"

        selected_quote = random.choice(quotes)

        report = (
            f"📊 [{company_name} ({symbol}) 지킴이 리포트]\n\n"
            f"💵 현재가: {current_price} {currency}\n"
            f"📰 최신 이슈: {latest_news}\n\n"
            f"🔍 [재무 건전성 진단]\n"
            f"- 부채비율: {debt_to_equity:.2f}%" if debt_to_equity else "- 부채비율: 데이터없음"
            f"\n- 당좌비율: {quick_ratio:.2f}" if quick_ratio else "\n- 당좌비율: 데이터없음"
            f"\n\n🎯 [지킴이 최종 평가: {eval_text}]\n"
            f"⭐ 점수: {score:.1f} / 10.0 점\n\n"
            f"💡 {selected_quote}"
        )
        return report

    except Exception as e:
        return f"분석 중 오류 발생: {str(e)}\n(지킴이: 종목 코드를 다시 한번 확인해 주세요!)"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    mcp.run(transport="sse")
