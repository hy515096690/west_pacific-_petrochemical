# PyCharm 中消除 `from app.xxx` 报错

项目根目录是 **west_pacific _petrochemical**，而 `app` 包在 **backend/app** 下。若在 PyCharm 里直接打开上层目录，解释器默认不会把 `backend` 加入模块搜索路径，所以 `from app.xxx import ...` 会报「未解析的引用」。

## 做法一：把 backend 标成「源代码根」（推荐）

1. 在项目树里**右键 `backend` 文件夹**。
2. 选 **Mark Directory as** → **Sources Root**。
3. `backend` 会变成蓝色，PyCharm 会把 `backend` 加入 PYTHONPATH，`app` 会解析到 `backend/app`，红色报错应消失。

若仍报错，可 **File → Invalidate Caches → Invalidate and Restart** 再试。

## 做法二：用 .idea 配置（已为项目配置好）

若仓库里已有 `.idea` 且 `west_pacific _petrochemical.iml` 中把 `backend` 设成了 Source Root，打开项目后应自动生效。若没有，按做法一操作一次即可。

## 运行 / 调试时的工作目录

运行 `backend/main.py` 或 `uvicorn main:app` 时，**工作目录必须是 `backend`**，这样：

- `config.yaml` 能被找到（在 `backend/` 下）；
- 模块 `app` 能正确加载（若用「运行 main.py」且未把 `backend` 标为 Sources Root，需在运行配置里把 **Working directory** 设为 `backend`）。

在 PyCharm 里：

1. **Run → Edit Configurations**。
2. 选中运行 `main.py` 的配置（或新建一个，Script path 选 `backend/main.py`）。
3. **Working directory** 设为：`D:\PYTHON_PROJECT\west_pacific _petrochemical\backend`（或你的实际 `backend` 绝对路径）。
4. 保存后运行。

这样既消除编辑器里的 `app` 报错，又保证运行时不报「找不到 config / 找不到 app」。
