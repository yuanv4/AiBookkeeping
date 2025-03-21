const request = require('supertest');
const path = require('path');
const fs = require('fs');
const app = require('../../server');

describe('文件上传功能测试', () => {
  const testFilePath = path.join(__dirname, '../../../20220219130307.xlsx');
  
  beforeAll(() => {
    // 确保上传目录存在
    const uploadDir = path.join(__dirname, '../../../uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
  });

  afterAll(() => {
    // 清理测试过程中产生的文件
    const uploadDir = path.join(__dirname, '../../../uploads');
    if (fs.existsSync(uploadDir)) {
      const files = fs.readdirSync(uploadDir);
      files.forEach(file => {
        fs.unlinkSync(path.join(uploadDir, file));
      });
    }
  });

  test('上传Excel文件 - 成功场景', async () => {
    const response = await request(app)
      .post('/api/upload/excel')
      .attach('file', testFilePath)
      .set('Authorization', 'Bearer test-token'); // 模拟认证token

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('message', '文件解析成功');
    expect(response.body).toHaveProperty('data');
    expect(Array.isArray(response.body.data)).toBe(true);
  });

  test('上传非Excel文件 - 失败场景', async () => {
    // 创建一个临时的非Excel文件
    const tempFilePath = path.join(__dirname, 'temp.txt');
    fs.writeFileSync(tempFilePath, 'This is not an Excel file');

    const response = await request(app)
      .post('/api/upload/excel')
      .attach('file', tempFilePath)
      .set('Authorization', 'Bearer test-token');

    expect(response.status).toBe(400);
    expect(response.body).toHaveProperty('error');

    // 清理临时文件
    fs.unlinkSync(tempFilePath);
  });

  test('未提供文件 - 失败场景', async () => {
    const response = await request(app)
      .post('/api/upload/excel')
      .set('Authorization', 'Bearer test-token');

    expect(response.status).toBe(400);
    expect(response.body).toHaveProperty('error', '请选择要上传的文件');
  });

  test('未认证 - 失败场景', async () => {
    const response = await request(app)
      .post('/api/upload/excel')
      .attach('file', testFilePath);

    expect(response.status).toBe(401);
  });
}); 