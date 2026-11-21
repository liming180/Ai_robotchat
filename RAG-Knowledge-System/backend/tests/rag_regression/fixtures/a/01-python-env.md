# Python 虚拟环境

本项目测试环境固定使用 Python 3.12.4，虚拟环境目录名为 `.venv`。Windows 下激活命令是 `.venv\Scripts\Activate.ps1`，激活后先执行 `python -m pip install -r requirements.txt`。若系统策略阻止激活，可以直接调用 `.venv\Scripts\python.exe`，不要为了激活脚本放宽整台机器的执行策略。每次换依赖分支后先核对解释器路径，再运行测试，避免把包装进全局环境。
