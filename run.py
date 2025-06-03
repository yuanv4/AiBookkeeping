import os
from dotenv import load_dotenv # 导入 python-dotenv 库中的 load_dotenv 函数
from app import create_app

print(f"试图加载 .env 文件...")
loaded_dotenv = load_dotenv(override=True) # 确保.env文件中的设置覆盖系统环境变量
print(f".env 文件加载是否成功: {loaded_dotenv}") # True 表示找到了.env文件并加载

# 打印环境变量，看它们在 load_dotenv() 之后的值
flask_config_env = os.getenv('FLASK_CONFIG')
secret_key_env = os.getenv('SECRET_KEY')

print(f"运行前 - FLASK_CONFIG 环境变量: '{flask_config_env}' (类型: {type(flask_config_env)})")
print(f"运行前 - SECRET_KEY 环境变量: '{secret_key_env}' (类型: {type(secret_key_env)})")

# 强制使用 development 配置，不管环境变量如何设置
config_to_use = 'development'
print(f"将使用的配置名称: '{config_to_use}'")

app = create_app(config_to_use)

if __name__ == '__main__':
    # Debug 状态现在由配置对象控制 (app.config['DEBUG'])
    # host 和 port 可以硬编码或从配置/环境变量读取
    # app.run 的 debug 参数若设置，会覆盖配置中的 DEBUG 值
    # 通常在开发时，依赖配置中的 DEBUG=True，或通过环境变量 FLASK_DEBUG=1
    app.run(host='0.0.0.0', port=5000) 