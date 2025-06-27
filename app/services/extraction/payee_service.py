"""PayeeService for extracting and normalizing merchant names from transaction descriptions.

此服务负责从原始的银行交易描述中识别并提取规范化的商家名称。
"""

import re
from typing import Optional, Dict, List


class PayeeService:
    """商家名称解析服务"""
    
    def __init__(self):
        """初始化商家名称解析服务，设置规则库"""
        self._merchant_rules = self._build_merchant_rules()
    
    def _build_merchant_rules(self) -> List[Dict[str, str]]:
        """构建商家识别规则库
        
        Returns:
            List[Dict]: 包含匹配模式和标准商家名称的规则列表
        """
        rules = [
            # 美团相关
            {'pattern': r'美团|MEITUAN|三快在线|北京三快', 'merchant': '美团'},
            
            # 支付宝相关
            {'pattern': r'支付宝|ALIPAY|蚂蚁金服', 'merchant': '支付宝'},
            
            # 微信支付相关
            {'pattern': r'微信支付|WECHAT|腾讯|财付通', 'merchant': '微信支付'},
            
            # 淘宝天猫相关
            {'pattern': r'淘宝|TAOBAO|天猫|TMALL|阿里巴巴', 'merchant': '淘宝/天猫'},
            
            # 京东相关
            {'pattern': r'京东|JD\.COM|京东商城', 'merchant': '京东'},
            
            # 滴滴相关
            {'pattern': r'滴滴|DIDI|小桔科技', 'merchant': '滴滴出行'},
            
            # 星巴克相关
            {'pattern': r'星巴克|STARBUCKS', 'merchant': '星巴克'},
            
            # Apple相关
            {'pattern': r'APPLE|苹果|APP STORE|ITUNES', 'merchant': 'Apple'},
            
            # 中国移动相关
            {'pattern': r'中国移动|CHINA MOBILE|移动通信', 'merchant': '中国移动'},
            
            # 中国联通相关
            {'pattern': r'中国联通|CHINA UNICOM|联通', 'merchant': '中国联通'},
            
            # 中国电信相关
            {'pattern': r'中国电信|CHINA TELECOM|电信', 'merchant': '中国电信'},
            
            # 国家电网相关
            {'pattern': r'国家电网|电力公司|供电局', 'merchant': '国家电网'},
            
            # 水费相关
            {'pattern': r'自来水|水务|供水', 'merchant': '自来水公司'},
            
            # 燃气费相关
            {'pattern': r'燃气|天然气|煤气', 'merchant': '燃气公司'},
            
            # 房租相关（通用模式）
            {'pattern': r'房租|租金|物业费', 'merchant': '房租/物业'},
            
            # 银行相关
            {'pattern': r'工商银行|ICBC', 'merchant': '工商银行'},
            {'pattern': r'建设银行|CCB', 'merchant': '建设银行'},
            {'pattern': r'农业银行|ABC', 'merchant': '农业银行'},
            {'pattern': r'中国银行|BOC', 'merchant': '中国银行'},
            {'pattern': r'招商银行|CMB', 'merchant': '招商银行'},
            
            # 网约车相关
            {'pattern': r'曹操出行|神州专车|首汽约车', 'merchant': '网约车'},
            
            # 外卖相关
            {'pattern': r'饿了么|ELEME', 'merchant': '饿了么'},
            
            # 电商平台
            {'pattern': r'拼多多|PDD', 'merchant': '拼多多'},
            {'pattern': r'唯品会|VIPSHOP', 'merchant': '唯品会'},
            
            # 视频娱乐
            {'pattern': r'爱奇艺|IQIYI', 'merchant': '爱奇艺'},
            {'pattern': r'腾讯视频|优酷|YOUKU', 'merchant': '视频平台'},
            {'pattern': r'网易云音乐|QQ音乐', 'merchant': '音乐平台'},
            
            # 生活服务
            {'pattern': r'58同城|赶集网', 'merchant': '生活服务'},
            {'pattern': r'大众点评|DIANPING', 'merchant': '大众点评'},
        ]
        
        return rules
    
    def extract_merchant_name(self, description: str, counterparty: str = None) -> Optional[str]:
        """从交易描述和交易对方信息中提取商家名称
        
        Args:
            description: 交易描述
            counterparty: 交易对方信息（可选）
            
        Returns:
            Optional[str]: 识别出的标准商家名称，如果无法识别则返回None
        """
        if not description:
            return None
        
        # 合并描述和交易对方信息进行匹配
        text_to_match = description
        if counterparty:
            text_to_match = f"{description} {counterparty}"
        
        # 清理文本，移除特殊字符但保留中英文
        text_to_match = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text_to_match)
        
        # 遍历规则库进行匹配
        for rule in self._merchant_rules:
            pattern = rule['pattern']
            merchant = rule['merchant']
            
            # 使用正则表达式进行匹配（忽略大小写）
            if re.search(pattern, text_to_match, re.IGNORECASE):
                return merchant
        
        # 如果没有匹配到规则，尝试提取可能的商家名称
        # 这里可以添加更复杂的启发式规则
        return self._extract_heuristic_merchant(text_to_match)
    
    def _extract_heuristic_merchant(self, text: str) -> Optional[str]:
        """使用启发式规则提取商家名称
        
        Args:
            text: 待分析的文本
            
        Returns:
            Optional[str]: 提取的商家名称，如果无法提取则返回None
        """
        # 移除常见的无用词汇
        text = re.sub(r'(有限公司|股份有限公司|科技|网络|信息|服务|管理|投资)', '', text)
        
        # 尝试提取中文公司名称（包含"公司"、"集团"等关键词）
        company_pattern = r'[\u4e00-\u9fff]{2,10}(公司|集团|企业|商城|商店|超市|餐厅|酒店)'
        company_match = re.search(company_pattern, text)
        if company_match:
            return company_match.group(0)
        
        # 尝试提取英文品牌名称（大写字母开头的连续单词）
        brand_pattern = r'\b[A-Z][a-zA-Z]{2,15}(?:\s+[A-Z][a-zA-Z]{2,15}){0,2}\b'
        brand_match = re.search(brand_pattern, text)
        if brand_match:
            brand_name = brand_match.group(0).strip()
            # 过滤掉常见的非商家词汇
            if brand_name not in ['PAY', 'PAYMENT', 'BANK', 'CARD', 'TRANSFER']:
                return brand_name
        
        return None
    
    def add_merchant_rule(self, pattern: str, merchant_name: str):
        """动态添加商家识别规则
        
        Args:
            pattern: 正则表达式模式
            merchant_name: 标准商家名称
        """
        self._merchant_rules.append({
            'pattern': pattern,
            'merchant': merchant_name
        })
    
    def get_merchant_rules_count(self) -> int:
        """获取当前规则库中的规则数量
        
        Returns:
            int: 规则数量
        """
        return len(self._merchant_rules)


# 创建全局实例
payee_service = PayeeService() 