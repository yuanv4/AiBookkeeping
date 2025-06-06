import os
from dotenv import load_dotenv
from app import create_app

# 加载 .env 文件
print("正在加载 .env 文件...")
loaded_dotenv = load_dotenv(override=True)
print(f".env 文件加载状态: {'成功' if loaded_dotenv else '未找到或加载失败'}")

# 显示当前环境配置
flask_config = os.getenv('FLASK_CONFIG', 'development')
log_level = os.getenv('LOG_LEVEL', 'INFO')
print(f"当前环境配置: {flask_config}")
print(f"日志级别: {log_level}")

# 创建应用实例（使用环境变量中的配置）
app = create_app()

if __name__ == '__main__':
    # Debug 状态现在由配置对象控制 (app.config['DEBUG'])
    # host 和 port 可以硬编码或从配置/环境变量读取
    # app.run 的 debug 参数若设置，会覆盖配置中的 DEBUG 值
    # 通常在开发时，依赖配置中的 DEBUG=True，或通过环境变量 FLASK_DEBUG=1
    app.run(host='0.0.0.0', port=5000)