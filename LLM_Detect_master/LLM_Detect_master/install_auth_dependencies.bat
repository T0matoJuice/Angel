@echo off
echo ========================================
echo 安装用户认证功能依赖包
echo ========================================
echo.

cd LLM_Detection_System

echo 正在安装 Flask-Login...
pip install flask-login>=0.6.0

echo.
echo 正在安装 Flask-SQLAlchemy...
pip install flask-sqlalchemy>=3.0.0

echo.
echo ========================================
echo 依赖包安装完成！
echo ========================================
echo.
echo 现在可以运行以下命令启动系统：
echo python LLM_Detection_System/app.py
echo.
pause

