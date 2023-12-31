What is SAYT
==============================================================================
SAYT (Search as you Type) 是一个为了解决对任意自定义数据集进行全文搜索的工具. 它构建于纯 Python 实现的搜索引擎 whoosh 和纯 Python 实现的缓存引擎 diskcache 之上, 希望能为开发者提供一个简单易用的全文搜索工具.

SAYT 的目标是解决当数据集的变化频率不高 (低于 1 分钟), 数据量不大 (不超过 1M), 每次数据集更新都是全量更新的场景下的全文搜索问题. 例如当你获得了 1000 个 PDF 文件名信息, 你希望对它们进行全文搜索, 但你不想花很长时间去定义如何创建和更新 index, 如何定义 query language, 如何缓存搜索结果等等. SAYT 就是为这种小而高频的需求而设计的.

很多大型企业内的搜索类项目的数据是不断增加和更新的. 同一条 Document 可能会被反复修改. 因为这种 Use case 会有很多个性化的需求, 你的 Schema 可能会变化, 可能会需要数据管道来进行数据更新, 结构化查询也是根据业务高度自定义的, 查询引擎和数据存储的部署的方式也很多, 很难说用一套框架来解决所有问题. 所以 SAYT 并不考虑这种 Use case.

SAYT 的主要应用场景是一写, 多读的场景, 又或者读写的频率都很高, 不够数据量不大 (小于 1K 条), 所以 index 的快到可以忽略不计的情况.
