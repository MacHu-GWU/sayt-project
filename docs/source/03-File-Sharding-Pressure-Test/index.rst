File Sharding Pressure Test
==============================================================================
由于我们所有的 dataset index 都放在一个目录下, 最终可能会生成非常多文件. 于是我们想知道在单个文件夹内文件数量很多的情况, 是否会影响到我们的性能.

根据下面的测试结果, 结论是在 10w 个文件的情况下, 对于已知文件路径的寻址速度几乎没有什么影响.

.. literalinclude:: ./file_sharding_pressure_test.py
   :language: python
   :linenos:
