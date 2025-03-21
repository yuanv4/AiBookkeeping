import React, { useState, useEffect } from 'react';
import { Upload, message, Table, Card, Row, Col, Statistic, Alert } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

// 添加调试日志工具函数
const debug = (label, data) => {
  console.log(`[${new Date().toISOString()}] [DEBUG] ${label}:`, data);
};

// 添加数据预处理函数
const safeFormatAmount = (amount) => {
  debug('格式化金额', { input: amount, type: typeof amount });
  
  // 已经是格式化好的字符串
  if (typeof amount === 'string' && amount.includes('¥')) {
    return amount;
  }
  
  // 处理数字或数字字符串
  let numAmount = 0;
  try {
    if (typeof amount === 'string') {
      // 移除任何非数字字符（保留小数点和负号）
      const cleanedAmount = amount.replace(/[^0-9.-]/g, '');
      numAmount = parseFloat(cleanedAmount);
    } else if (typeof amount === 'number') {
      numAmount = amount;
    }
    
    // 检查是否为有效数字
    if (isNaN(numAmount)) {
      return '¥0.00';
    }
    
    // 格式化为货币
    return '¥' + numAmount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
  } catch (error) {
    debug('金额格式化失败', { amount, error: error.toString() });
    return '¥0.00';
  }
};

const FileUpload = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [invalidRecords, setInvalidRecords] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0
  });

  // 添加生命周期日志
  useEffect(() => {
    debug('组件已挂载', 'FileUpload 组件初始化完成');
    return () => {
      debug('组件将卸载', 'FileUpload 组件清理');
    };
  }, []);

  // 监控 transactions 变化
  useEffect(() => {
    if (transactions.length > 0) {
      debug('交易数据已更新', {
        count: transactions.length,
        firstTransaction: transactions[0],
        lastTransaction: transactions[transactions.length - 1]
      });
    }
  }, [transactions]);

  const columns = [
    {
      title: '交易日期',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      sorter: (a, b) => new Date(a.transaction_date) - new Date(b.transaction_date)
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (text, record) => {
        debug('渲染金额', {
          amount: text,
          type: typeof text,
          record: record
        });
        return (
          <span style={{ color: record.is_income ? '#52c41a' : '#f5222d' }}>
            {text}
          </span>
        );
      }
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category'
    },
    {
      title: '摘要',
      dataIndex: 'memo',
      key: 'memo'
    },
    {
      title: '交易对手',
      dataIndex: 'counterparty',
      key: 'counterparty'
    }
  ];

  const handleTableChange = (newPagination) => {
    debug('分页变化', newPagination);
    setPagination(newPagination);
    // 这里可以添加获取新页数据的逻辑
  };

  const uploadProps = {
    name: 'file',
    action: '/api/upload',
    accept: '.xlsx,.csv',
    showUploadList: false,
    beforeUpload: (file) => {
      debug('准备上传文件', {
        name: file.name,
        type: file.type,
        size: file.size
      });
      const isExcelOrCSV = file.type === 'application/vnd.ms-excel' || 
                          file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                          file.type === 'text/csv';
      if (!isExcelOrCSV) {
        message.error('只支持 Excel 或 CSV 文件！');
        return false;
      }
      return true;
    },
    onChange(info) {
      debug('上传状态变化', {
        status: info.file.status,
        name: info.file.name
      });

      if (info.file.status === 'uploading') {
        setLoading(true);
      }
      if (info.file.status === 'done') {
        setLoading(false);
        const response = info.file.response;
        debug('上传完成，收到响应', response);
        
        try {
          if (response.success) {
            debug('响应成功，处理数据', {
              dataCount: response.data.length,
              stats: response.stats,
              warnings: response.warnings?.length || 0,
              invalidRecords: response.invalidRecords?.length || 0
            });
            
            // 安全处理数据
            let safeData = [];
            if (response.data && Array.isArray(response.data)) {
              safeData = response.data.map(transaction => {
                // 创建安全的交易记录
                return {
                  ...transaction,
                  // 确保金额是安全的格式化字符串
                  amount: safeFormatAmount(transaction.amount)
                };
              });
            }
            
            // 检查数据类型
            if (safeData.length > 0) {
              const firstTransaction = safeData[0];
              debug('处理后的第一条交易数据', {
                transaction: firstTransaction,
                amountType: typeof firstTransaction.amount
              });
            }
            
            // 使用安全处理后的数据
            setTransactions(safeData);
            
            // 安全处理统计数据
            const safeStats = response.stats ? {
              ...response.stats,
              totalIncome: typeof response.stats.totalIncome === 'string' 
                ? response.stats.totalIncome 
                : safeFormatAmount(response.stats.totalIncome),
              totalExpense: typeof response.stats.totalExpense === 'string'
                ? response.stats.totalExpense
                : safeFormatAmount(response.stats.totalExpense)
            } : null;
            
            setStats(safeStats);
            setWarnings(response.warnings || []);
            setInvalidRecords(response.invalidRecords || []);
            setPagination({
              ...pagination,
              total: response.meta.total
            });
            message.success('文件上传成功！');
          } else {
            debug('响应表示失败', response.error);
            message.error(response.error.message || '文件处理失败');
          }
        } catch (error) {
          debug('处理响应时出错', {
            error: error.toString(),
            stack: error.stack,
            response: response
          });
          message.error(`处理数据时出错: ${error.message}`);
        }
      }
      if (info.file.status === 'error') {
        debug('上传失败', info.file.error);
        setLoading(false);
        message.error(`文件上传失败: ${info.file.error?.message || '未知错误'}`);
      }
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="文件上传" style={{ marginBottom: '24px' }}>
        <Upload {...uploadProps}>
          <button className="ant-btn ant-btn-primary">
            <UploadOutlined /> 选择文件
          </button>
        </Upload>
      </Card>

      {stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总收入"
                value={stats.totalIncome}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="总支出"
                value={stats.totalExpense}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="交易笔数"
                value={pagination.total}
              />
            </Card>
          </Col>
        </Row>
      )}

      {warnings.length > 0 && (
        <Alert
          message="数据警告"
          description={`发现 ${warnings.length} 条数据存在警告信息`}
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {invalidRecords.length > 0 && (
        <Alert
          message="数据错误"
          description={`发现 ${invalidRecords.length} 条无效数据`}
          type="error"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      <Table
        columns={columns}
        dataSource={transactions}
        rowKey={(record, index) => index}
        loading={loading}
        pagination={pagination}
        onChange={handleTableChange}
        scroll={{ x: true }}
      />
    </div>
  );
};

// 添加全局错误处理
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    debug('组件错误', { error: error.toString(), errorInfo });
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '24px' }}>
          <Alert
            message="组件错误"
            description={`发生了一个错误: ${this.state.error?.toString()}`}
            type="error"
            showIcon
          />
          <pre style={{ marginTop: '16px', backgroundColor: '#f5f5f5', padding: '16px' }}>
            {this.state.errorInfo?.componentStack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

// 导出时包装错误边界
export default function FileUploadWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <FileUpload />
    </ErrorBoundary>
  );
} 