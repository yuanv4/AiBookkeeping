const { BertTokenizer } = require('@nlpjs/bert-tokenizer');
const { CRF } = require('crfsuite');
const winston = require('winston');

// 获取日志记录器实例
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: '../logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: '../logs/combined.log' })
  ]
});

class TransactionClassifier {
  constructor() {
    this.tokenizer = new BertTokenizer();
    this.crf = new CRF();
    this.categories = [
      '餐饮', '交通', '购物', '娱乐', '居住',
      '医疗', '教育', '通讯', '投资', '其他'
    ];
  }

  // 提取特征
  extractFeatures(transaction) {
    const { amount, memo, transaction_date } = transaction;
    const features = [];

    // 文本特征
    const tokens = this.tokenizer.tokenize(memo);
    features.push(...tokens);

    // 金额区间特征
    const amountRange = this.getAmountRange(amount);
    features.push(`amount_range_${amountRange}`);

    // 时间特征
    const date = new Date(transaction_date);
    features.push(`hour_${date.getHours()}`);
    features.push(`weekday_${date.getDay()}`);

    return features;
  }

  // 获取金额区间
  getAmountRange(amount) {
    if (amount <= 50) return '0-50';
    if (amount <= 200) return '51-200';
    if (amount <= 1000) return '201-1000';
    if (amount <= 5000) return '1001-5000';
    return '5000+';
  }

  // 预测交易类别
  async predict(transaction) {
    try {
      const features = this.extractFeatures(transaction);
      const prediction = await this.crf.predict(features);
      
      // 获取预测概率最高的类别
      const category = this.categories[prediction.indexOf(Math.max(...prediction))];
      
      return {
        category,
        confidence: Math.max(...prediction)
      };
    } catch (error) {
      logger.error('交易分类预测失败:', error);
      return {
        category: '其他',
        confidence: 0
      };
    }
  }

  // 训练模型
  async train(transactions) {
    try {
      const trainingData = transactions.map(transaction => ({
        features: this.extractFeatures(transaction),
        label: transaction.category
      }));

      await this.crf.train(trainingData);
      logger.info('模型训练完成');
      return true;
    } catch (error) {
      logger.error('模型训练失败:', error);
      return false;
    }
  }
}

module.exports = new TransactionClassifier();