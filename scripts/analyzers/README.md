# 交易分析模块

此模块提供账务交易数据的分析功能，包括摘要统计、时间维度分析、类别分析、商户分析和异常交易分析等。

## 模块结构

- `transaction_analyzer.py` - 交易分析器门面类，提供向后兼容的API
- `modules/` - 模块化分析器组件
  - `data_extractor.py` - 数据提取器，负责从数据库获取数据
  - `base_analyzer.py` - 分析器基类，定义通用接口和方法
  - `time_analyzer.py` - 时间维度分析器，负责日/周/月/年的统计分析
  - `category_analyzer.py` - 类别分析器，负责交易类型、支出分布、收入来源分析
  - `merchant_analyzer.py` - 商户分析器，负责商户相关分析
  - `anomaly_analyzer.py` - 异常分析器，负责核心交易和异常交易分析
  - `summary_analyzer.py` - 摘要分析器，负责提供交易摘要统计
  - `analyzer_factory.py` - 分析器工厂，负责创建和管理各种分析器

## 使用方法

### 使用门面类 (推荐)

门面类 `TransactionAnalyzer` 提供了向后兼容的API，可以直接使用。

```python
from scripts.db.db_manager import DBManager
from scripts.analyzers import TransactionAnalyzer

# 创建数据库管理器
db_manager = DBManager()

# 创建交易分析器
analyzer = TransactionAnalyzer(db_manager)

# 分析交易数据
results = analyzer.analyze_transaction_data_direct(
    start_date='2023-01-01', 
    end_date='2023-12-31'
)
```

### 直接使用分析器工厂

如果需要更灵活的使用方式，可以直接使用分析器工厂。

```python
from scripts.db.db_manager import DBManager
from scripts.analyzers.modules import AnalyzerFactory

# 创建数据库管理器
db_manager = DBManager()

# 创建分析器工厂
factory = AnalyzerFactory(db_manager)

# 获取特定分析器
time_analyzer = factory.get_analyzer('time')
category_analyzer = factory.get_analyzer('category')

# 执行分析
time_results = time_analyzer.analyze(
    start_date='2023-01-01', 
    end_date='2023-12-31'
)

# 或者一次执行所有分析
all_results = factory.analyze_all(
    start_date='2023-01-01', 
    end_date='2023-12-31'
)
```

### 创建自定义分析器

可以继承 `BaseAnalyzer` 创建自定义分析器。

```python
from scripts.analyzers.modules import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, start_date=None, end_date=None, **kwargs):
        # 获取数据
        df = self.get_data(start_date, end_date, **kwargs)
        
        # 执行自定义分析
        # ...
        
        # 返回结果
        return results
``` 