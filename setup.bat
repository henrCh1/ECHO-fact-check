@echo off
chcp 65001 >nul

echo =========================================
echo 事实核查系统 - 快速设置
echo =========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ 检测到Python
python --version
echo.

REM 创建虚拟环境
echo 📦 创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖包...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 创建必要的目录
echo 📁 创建数据目录...
if not exist data\playbook\history mkdir data\playbook\history
if not exist data\cases mkdir data\cases
if not exist data\feedback mkdir data\feedback
if not exist logs mkdir logs

REM 创建.env文件
if not exist .env (
    echo 📝 创建.env配置文件...
    (
        echo # Google Gemini API密钥（必需）
        echo GOOGLE_API_KEY=your_google_api_key_here
        echo.
        echo # 模型选择（可选）
        echo GEMINI_MODEL=gemini-2.0-flash-exp
        echo.
        echo # 搜索API（可选）
        echo SERPAPI_KEY=your_serpapi_key_here
    ) > .env
    echo ⚠️  请编辑 .env 文件，填入你的API密钥
) else (
    echo ℹ️  .env文件已存在，跳过创建
)

echo.
echo =========================================
echo ✨ 设置完成！
echo =========================================
echo.
echo 下一步:
echo 1. 编辑 .env 文件，填入你的 GOOGLE_API_KEY
echo 2. 运行演示: python demo.py
echo 3. 运行完整程序: python main.py
echo.
echo 激活虚拟环境: venv\Scripts\activate.bat
echo =========================================
echo.
pause
