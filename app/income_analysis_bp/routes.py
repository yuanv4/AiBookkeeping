from flask import render_template, current_app, request
from . import income_analysis_bp

@income_analysis_bp.route('/')
def income_analysis():
    """收入分析页面"""
    try:
        db_manager = current_app.db_manager
        
        # 获取账户余额
        balance_summary = db_manager.get_balance_summary()
        
        # 获取收入与支出平衡分析数据
        income_expense_balance = db_manager.get_income_expense_balance()
        
        # 获取收入稳定性分析数据
        income_stability = db_manager.get_income_stability()
        
        # 获取收入多样性评估数据
        income_diversity = db_manager.get_income_diversity()
        
        # 获取现金流健康度数据
        cash_flow_health = db_manager.get_cash_flow_health()
        
        # 获取收入增长评估数据
        income_growth = db_manager.get_income_growth()
        
        # 获取财务韧性指标数据
        financial_resilience = db_manager.get_financial_resilience()
        
        # 组装数据
        data = {
            'income_expense_balance': income_expense_balance,
            'income_stability': income_stability,
            'income_diversity': income_diversity,
            'cash_flow_health': cash_flow_health,
            'income_growth': income_growth,
            'financial_resilience': financial_resilience
        }
        
        current_app.logger.info("收入分析页面数据已加载")
        
        return render_template('income_analysis.html', data=data)
        
    except Exception as e:
        current_app.logger.error(f"收入分析页面加载出错: {e}", exc_info=True)
        raise 