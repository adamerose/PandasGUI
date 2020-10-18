# PandasGUI
---
一个用于分析Pandas DataFrames的GUI

<video src="https://camo.githubusercontent.com/9ec086a965ac8ff4d26c8faaa4e07b3bf268bc35/68747470733a2f2f696d6775722e636f6d2f4c4541516661312e676966" width="100%" controls="controls"></video>

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
如果您将代码作为脚本而不是在IPython中运行，你将需要组织执行直到关闭GUI
```
show(df, settings={'block': True})
```
PandasGUI随附了示例数据集，这些数据集将在首次使用时下载。您还可以导入<code>all_datasets</code>，它是所有样本数据集的字典。
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

## 屏幕截图
DataFrame查看器

![img1](https://camo.githubusercontent.com/db36ef320d5fbca5b288fa48d4b43e32722fd538/68747470733a2f2f696d6775722e636f6d2f68556e754269592e706e67)

过滤器

![img2](https://camo.githubusercontent.com/0a9160a4226a3cb3cf33a923829968db69d5f01c/68747470733a2f2f696d6775722e636f6d2f596e305a7161362e706e67)

统计分析

![img3](https://camo.githubusercontent.com/fae8d69919b8328fab9232cd098af14beee7bcac/68747470733a2f2f696d6775722e636f6d2f6d4b4361614e4d2e706e67)

仪表盘

![img4](https://camo.githubusercontent.com/057632710a82a423fd1c3fae53d55663bcfbf1aa/68747470733a2f2f696d6775722e636f6d2f7a5a4965417a6a2e706e67)

多Index支持

![img5](https://camo.githubusercontent.com/92eac862348ac82e5e492df831c345b06e9cd7fc/68747470733a2f2f696d6775722e636f6d2f32727a394f7a432e706e67)