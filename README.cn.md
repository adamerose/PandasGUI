# PandasGUI
---
一个用于分析Pandas DataFrames的GUI

## Demo
---
<video src="https://www.youtube.com/watch?v=NKXdolMxW2Y" width="100%" controls="controls"></video>

## 安装
---
从PyPi安装最新发布版本：
```
pip install pandasgui
```
直接从Github安装获取最新的未发布更改：
```
pip install git+https://github.com/adamerose/pandasgui.git
```

## 使用
---
创建并查看一个简单的DataFrame
```
import pandas as pd
from pandasgui import show
df = pd.DataFrame(([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
show(df)
```
如果您将代码作为脚本而不是在IPython或Jupyter中运行，则需要这样做：
```
# This will pause the script until you close the GUI
show(df, settings={'block': True})
```
PandasGUI随附了示例数据集，这些数据集将在首次使用时下载。您还可以导入all_datasets，它是所有样本数据集的字典。
```
from pandasgui import show
from pandasgui.datasets import pokemon, titanic, all_datasets
show(pokemon, titanic)
show(**all_datasets)
```

## 特征
---
* 查看DataFrames和Series(支持多种Index方式)
* 交互式绘图
* 过滤
* 统计摘要
* 数据编辑和复制/粘贴
* 拖放导入CSV文件
* 搜索工具栏

## 更多信息
---
__欢迎提出问题，反馈和要求。__
该项目的版本仍为0.x.y，并且可能会有重大更改。
最新更改将在<code>development</code>分支上，并且偶尔会与发行版合并为<code>master</code>版本，并带有指示版本号的标签，然后发布到PyPi。

如果喜欢本仓库，记得点个<g-emoji class="g-emoji" alias="star" fallback-src="https://github.githubassets.com/images/icons/emoji/unicode/2b50.png">⭐</g-emoji>！
