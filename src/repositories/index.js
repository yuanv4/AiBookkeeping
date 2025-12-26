/**
 * Repository 统一导出
 * 使用 HTTP 后端 API 作为数据源
 */

// 从 HTTP repositories 导出所有模块
export * from './http/index.js'

// 默认导出 HTTP repositories
import * as httpRepos from './http/index.js'

export const transactionsRepo = httpRepos.transactionsRepo
export const categoriesRepo = httpRepos.categoriesRepo
export const transactionCategoriesRepo = httpRepos.transactionCategoriesRepo
export const correctionsRepo = httpRepos.correctionsRepo
export const configRepo = httpRepos.configRepo

// 导出模式判断函数(保持向后兼容)
export const isRemoteMode = () => true
export const isLocalMode = () => false

// 在控制台输出当前模式
console.log('☁️ Repository 模式: Remote (HTTP API)')
