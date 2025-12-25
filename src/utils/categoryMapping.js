/**
 * 交易分类映射转换工具
 * 统一业务层对象映射和 IndexedDB 数组行格式之间的转换
 */

/**
 * 将对象映射转换为数组行(用于存储到 IndexedDB)
 * ⚠️ 这是唯一的转换入口,所有代码必须使用此函数
 * @param {Object} mapping - { txId1: { category, ... }, txId2: { ... } }
 * @returns {Array} - [{ transactionId: txId1, category, ... }, ...]
 */
export function mappingToRows(mapping) {
  return Object.entries(mapping).map(([transactionId, data]) => ({
    transactionId,
    ...data
  }))
}

/**
 * 将数组行转换为对象映射(用于业务层使用)
 * ⚠️ 这是唯一的转换入口,所有代码必须使用此函数
 * @param {Array} rows - [{ transactionId: txId1, category, ... }, ...]
 * @returns {Object} - { txId1: { category, ... }, txId2: { ... } }
 */
export function rowsToMapping(rows) {
  const mapping = {}
  rows.forEach(row => {
    const { transactionId, ...data } = row
    mapping[transactionId] = data
  })
  return mapping
}
