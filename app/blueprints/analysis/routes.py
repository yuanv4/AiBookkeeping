from flask import render_template, current_app
from . import analysis_bp

@analysis_bp.route('/income-expense')
def income_expense():
    """收支分析页面 - 显示收入与支出的对比分析"""
    try:
        # 从 financial_service 获取收支分析数据
        analysis_data = current_app.financial_service.get_income_expense_analysis()
        
        template_data = {
            'monthly_income_expense': analysis_data.get('monthly_income_expense', []),
            'total_income': analysis_data.get('total_income', 0.0),
            'total_expense': analysis_data.get('total_expense', 0.0),
            'net_income': analysis_data.get('net_income', 0.0)
        }
        
        return render_template('analysis_income_expense.html',
                             page_title='收支分析',
                             template_data=template_data)
                             
    except Exception as e:
        current_app.logger.error(f"加载收支分析页面失败: {str(e)}")
        template_data = {
            'monthly_income_expense': [],
            'total_income': 0.0,
            'total_expense': 0.0,
            'net_income': 0.0
        }
        return render_template('analysis_income_expense.html',
                             page_title='收支分析',
                             template_data=template_data)

@analysis_bp.route('/category-insights')
def category_insights():
    """分类洞察页面 - 显示消费分类分析"""
    try:
        # 从 financial_service 获取分类分析数据
        analysis_data = current_app.financial_service.get_category_analysis()
        
        template_data = {
            'category_breakdown': analysis_data.get('category_breakdown', []),
            'top_categories': analysis_data.get('top_categories', []),
            'total_expense': analysis_data.get('total_expense', 0.0),
            'category_count': analysis_data.get('category_count', 0)
        }
        
        return render_template('analysis_category.html',
                             page_title='分类洞察',
                             template_data=template_data)
                             
    except Exception as e:
        current_app.logger.error(f"加载分类洞察页面失败: {str(e)}")
        template_data = {
            'category_breakdown': [],
            'top_categories': [],
            'total_expense': 0.0,
            'category_count': 0
        }
        return render_template('analysis_category.html',
                             page_title='分类洞察',
                             template_data=template_data) 