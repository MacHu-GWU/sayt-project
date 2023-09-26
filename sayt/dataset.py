# -*- coding: utf-8 -*-

"""
This module implements the abstraction of the dataset settings, and convert the
settings to ``whoosh.fields.Schema`` Class.

**Overview**

**使用场景**

从任何地方获取许多条结构化的数据, 每一条数据都是一个字典, 例如我们的数据集是图书数据::

    {
        "isbn": "978-0-201-03801-1",
        "book_name": "The Art of Computer Programming",
        "author": "Donald Knuth",
        "date": "1968-07-01",
    }

然后我们需要对这些数据进行全文搜索. 首先, 我们要定义这批数据要如何被索引 (或者说如何被搜索到).
例如希望对 book_name 能进行 ngram 搜索, 对与 Author 则是进行 phrase 搜索. 而一条数据的唯一
id 则是 isbn.


"""

import typing as T
import shutil
import os
import hashlib
import dataclasses
from collections import OrderedDict

from pathlib import Path

import whoosh.fields
import whoosh.qparser
import whoosh.query
import whoosh.sorting
from whoosh.index import open_dir, create_in, FileIndex, exists_in
from diskcache import Cache

from .exc import MalformedDatasetSettingError
from .compat import cached_property


@dataclasses.dataclass
class BaseField:
    name: str = dataclasses.field()

    def _is_sortable(self) -> bool:
        try:
            return self.sortable
        except AttributeError:
            return False

    def _is_ascending(self) -> bool:
        try:
            return self.ascending
        except AttributeError:
            return False


@dataclasses.dataclass
class StoredField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.STORED
    """

    pass


@dataclasses.dataclass
class IdField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.ID
    """

    stored: bool = dataclasses.field(default=False)
    unique: bool = dataclasses.field(default=False)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)
    analyzer: T.Optional[str] = dataclasses.field(default=None)


@dataclasses.dataclass
class IdListField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.IDLIST
    """

    stored: bool = dataclasses.field(default=False)
    unique: bool = dataclasses.field(default=False)
    expression: T.Optional[str] = dataclasses.field(default=None)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)


@dataclasses.dataclass
class KeywordField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.KEYWORD
    """

    stored: bool = dataclasses.field(default=False)
    lowercase: bool = dataclasses.field(default=False)
    commas: bool = dataclasses.field(default=False)
    scorable: bool = dataclasses.field(default=False)
    unique: bool = dataclasses.field(default=False)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)
    vector: T.Optional = dataclasses.field(default=None)
    analyzer: T.Optional = dataclasses.field(default=None)


@dataclasses.dataclass
class TextField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.TEXT
    """

    stored: bool = dataclasses.field(default=False)
    analyzer: T.Optional = dataclasses.field(default=None)
    phrase: bool = dataclasses.field(default=True)
    chars: bool = dataclasses.field(default=False)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)
    multitoken_query: str = dataclasses.field(default="default")
    spelling: bool = dataclasses.field(default=False)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)
    lang: T.Optional = dataclasses.field(default=None)
    vector: T.Optional = dataclasses.field(default=None)
    spelling_prefix: str = dataclasses.field(default="spell_")


@dataclasses.dataclass
class NumericField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.NUMERIC
    """

    stored: bool = dataclasses.field(default=False)
    numtype: T.Union[T.Type[int], T.Type[float]] = dataclasses.field(default=int)
    bits: int = dataclasses.field(default=32)
    unique: bool = dataclasses.field(default=False)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)
    decimal_places: int = dataclasses.field(default=0)
    shift_step: int = dataclasses.field(default=4)
    signed: bool = dataclasses.field(default=True)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)
    default: T.Optional[T.Union[int, float]] = dataclasses.field(default=None)


@dataclasses.dataclass
class DatetimeField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.DATETIME
    """

    stored: bool = dataclasses.field(default=False)
    unique: bool = dataclasses.field(default=False)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)


@dataclasses.dataclass
class BooleanField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.BOOLEAN
    """

    stored: bool = dataclasses.field(default=False)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)


@dataclasses.dataclass
class NgramField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.NGRAM
    """

    stored: bool = dataclasses.field(default=False)
    minsize: int = dataclasses.field(default=2)
    maxsize: int = dataclasses.field(default=4)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)
    queryor: bool = dataclasses.field(default=False)
    phrase: bool = dataclasses.field(default=False)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)


@dataclasses.dataclass
class NgramWordsField(BaseField):
    """
    Ref: https://whoosh.readthedocs.io/en/latest/api/fields.html#whoosh.fields.NGRAMWORDS
    """

    stored: bool = dataclasses.field(default=False)
    minsize: int = dataclasses.field(default=2)
    maxsize: int = dataclasses.field(default=4)
    field_boost: T.Union[int, float] = dataclasses.field(default=1.0)
    queryor: bool = dataclasses.field(default=False)
    phrase: bool = dataclasses.field(default=False)
    tokenizer: T.Optional = dataclasses.field(default=None)
    at: T.Optional[str] = dataclasses.field(default=None)
    sortable: bool = dataclasses.field(default=False)
    ascending: bool = dataclasses.field(default=True)


_whoosh_field_mapper = {
    StoredField: whoosh.fields.STORED,
    IdField: whoosh.fields.ID,
    IdListField: whoosh.fields.IDLIST,
    KeywordField: whoosh.fields.KEYWORD,
    TextField: whoosh.fields.TEXT,
    NumericField: whoosh.fields.NUMERIC,
    DatetimeField: whoosh.fields.DATETIME,
    BooleanField: whoosh.fields.BOOLEAN,
    NgramField: whoosh.fields.NGRAM,
    NgramWordsField: whoosh.fields.NGRAMWORDS,
}

T_Field = T.Union[
    StoredField,
    IdField,
    IdListField,
    KeywordField,
    TextField,
    NumericField,
    DatetimeField,
    BooleanField,
    NgramField,
    NgramWordsField,
]


def _to_whoosh_field(field: BaseField) -> whoosh.fields.SpellField:
    kwargs = dataclasses.asdict(field)
    kwargs.pop("name")
    if "ascending" in kwargs:
        kwargs.pop("ascending")
    return _whoosh_field_mapper[field.__class__](**kwargs)


@dataclasses.dataclass
class DataSet:
    """
    Defines how you want to index your dataset.

    :param dir_index: 索引所在的文件夹. 如果不存在, 会自动创建.
    :param index_name: 索引的名字. 一个索引是类似于数据库中的数据表的概念. 在同一个索引文件夹
        下不同的索引会被分散到不同的文件中, 属于同一个索引的文件会有相同的前缀. 这个最终传给
        whoosh 的索引名是 ``index_name`` 的 MD5 哈希, 这样可以避免索引名之间共享前缀导致
        磁盘寻址搜索性能下降.
    :param fields: 定义了这个数据集将会如何被索引.
    :param cache: diskcache 缓存对象.
    :param cache_key: 该 dataset 被缓存时所用的 key.
    :param cache_tag: 该 dataset 被缓存时所用的 tag, 这个 tag 可以被用作清除缓存的时候的过滤条件.
    :param cache_expire: cache 的缓存失效实践
    :param skip_validation: 是否跳过对 Dataset 初始化的 validation 检查. 默认是不跳过,
        也就是进行检查.
    """

    dir_index: Path = dataclasses.field()
    index_name: str = dataclasses.field()
    fields: T.List[T_Field] = dataclasses.field()

    cache: Cache = dataclasses.field()
    cache_key: str = dataclasses.field()
    cache_tag: T.Optional[str] = dataclasses.field(default=None)
    cache_expire: T.Optional[int] = dataclasses.field(default=None)

    skip_validation: bool = dataclasses.field(default=False)

    # --------------------------------------------------------------------------
    # Schema 相关
    # --------------------------------------------------------------------------
    __1_SCHEMA = None

    def _check_fields_name(self):  # pragma: no cover
        if len(set(self._field_names)) != len(self.fields):
            msg = f"you have duplicate field names in your fields: {self._field_names}"
            raise MalformedDatasetSettingError(msg)

    def _validate_attributes(self):
        self._check_fields_name()

    def __post_init__(self):
        # do some validation
        if self.skip_validation is False:
            self._validate_attributes()

    @cached_property
    def _field_names(self) -> T.List[str]:
        """
        all field name list.
        """
        return [field.name for field in self.fields]

    @cached_property
    def _fields_mapper(self) -> T.Dict[str, T_Field]:
        """
        field name to field object mapper.
        """
        return {field.name: field for field in self.fields}

    @cached_property
    def _stored_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, StoredField)]

    @cached_property
    def _id_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, IdField)]

    @cached_property
    def _idlist_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, IdListField)]

    @cached_property
    def _keyword_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, KeywordField)]

    @cached_property
    def _text_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, TextField)]

    @cached_property
    def _numeric_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, NumericField)]

    @cached_property
    def _datetime_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, DatetimeField)]

    @cached_property
    def _boolean_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, BooleanField)]

    @cached_property
    def _ngram_fields(self) -> T.List[str]:  # pragma: no cover
        return [field.name for field in self.fields if isinstance(field, NgramField)]

    @cached_property
    def _ngramwords_fields(self) -> T.List[str]:  # pragma: no cover
        return [
            field.name for field in self.fields if isinstance(field, NgramWordsField)
        ]

    @cached_property
    def _searchable_fields(self) -> T.List[str]:
        return [
            field.name
            for field in self.fields
            if isinstance(field, StoredField) is False
        ]

    @cached_property
    def _sortable_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field._is_sortable()]

    def _create_whoosh_schema(self) -> whoosh.fields.Schema:
        """
        Dynamically create whoosh.fields.SchemaClass schema object.
        It defines how you index your dataset.
        """
        schema_classname = "WhooshSchema"
        schema_classname = str(schema_classname)
        attrs = OrderedDict()
        for field in self.fields:
            attrs[field.name] = _to_whoosh_field(field)
        SchemaClass = type(schema_classname, (whoosh.fields.SchemaClass,), attrs)
        schema = SchemaClass()
        return schema

    @cached_property
    def schema(self) -> whoosh.fields.Schema:
        """
        Access the whoosh schema based on the setting.
        """
        return self._create_whoosh_schema()

    # --------------------------------------------------------------------------
    # Index
    # --------------------------------------------------------------------------
    __2_INDEX = None

    @property
    def normalized_index_name(self) -> str:
        m = hashlib.md5()
        m.update(self.index_name.encode("utf-8"))
        return m.hexdigest()

    def _get_index(self) -> FileIndex:
        """
        Get the whoosh index object. If the index does not exist, create one.
        if the index exists, open it.
        """
        if exists_in(str(self.dir_index), indexname=self.normalized_index_name):
            idx = open_dir(str(self.dir_index), indexname=self.normalized_index_name)
        else:
            self.dir_index.mkdir(parents=True, exist_ok=True)
            idx = create_in(
                dirname=str(self.dir_index),
                schema=self.schema,
                indexname=self.normalized_index_name,
            )
        return idx

    def remove_index(self):  # pragma: no cover
        """
        Remove the whoosh index for this dataset.
        """
        if exists_in(str(self.dir_index), indexname=self.normalized_index_name):
            idx = create_in(
                dirname=str(self.dir_index),
                schema=self.schema,
                indexname=self.normalized_index_name,
            )
            idx.close()

    def remove_all_index(self):  # pragma: no cover
        """
        Remove all whoosh index in the index directory.
        """
        if self.dir_index.exists():
            shutil.rmtree(self.dir_index, ignore_errors=True)

    def build_index(
        self,
        data: T.List[T.Dict[str, T.Any]],
        memory_limit: int = 512,
        multi_thread: bool = True,
        rebuild: bool = True,
    ):
        """
        Build whoosh index for this dataset.

        :param data:
        :param memory_limit: maximum memory you can use for indexing, default is 512MB,
            you can use a larger number if you have more memory.
        :param multi_thread: use multi-threading to build index, default is False.
        :param rebuild: if True, remove the existing index and rebuild it.
        """
        if rebuild:
            self.remove_index()
            self.remove_cache()

        idx = self._get_index()
        if multi_thread:  # pragma: no cover
            cpu_count = os.cpu_count()
            writer = idx.writer(
                limitmb=memory_limit, procs=cpu_count, multisegment=True
            )
        else:
            writer = idx.writer(limitmb=memory_limit)

        for row in data:
            doc = {field_name: row.get(field_name) for field_name in self._field_names}
            writer.add_document(**doc)

        writer.commit()

    # --------------------------------------------------------------------------
    # Cache
    # --------------------------------------------------------------------------
    __3_CACHE = None

    # --------------------------------------------------------------------------
    # Search
    # --------------------------------------------------------------------------
    def remove_cache(self):  # pragma: no cover
        """
        Remove the cache for this dataset.
        """
        if Path(self.cache.directory).exists():
            self.cache.evict(tag=self.cache_tag)

    def remove_all_cache(self):  # pragma: no cover
        """
        Remove all cache in the cache directory.
        """
        if Path(self.cache.directory).exists():
            self.cache.clear()

    def _parse_query(self, query_str: str) -> whoosh.query.Query:
        """
        Use multi field parser to convert query string into a whoosh query object.
        """
        parser = whoosh.qparser.MultifieldParser(
            self._searchable_fields,
            schema=self.schema,
        )
        parser.add_plugins(
            [
                whoosh.qparser.FuzzyTermPlugin(),
                whoosh.qparser.GtLtPlugin(),
            ]
        )
        q = parser.parse(query_str)
        return q

    def search(
        self,
        query: T.Union[str, whoosh.query.Query],
        limit=20,
    ) -> T.List[dict]:
        """
        Use full-text search for result.

        :param query: 如果是一个字符串, 则使用 ``MultifieldParser`` 解析. 如果是一个
            ``Query`` 对象, 则直接使用.
        :param limit: 返回结果的最大数量.
        """
        key = (self.cache_key, str(query), limit)
        if key in self.cache:
            return self.cache.get(key)

        if isinstance(query, str):
            q = self._parse_query(query)
        else:  # pragma: no cover
            q = query

        search_kwargs = dict(
            q=q,
            limit=limit,
        )
        if len(self._sortable_fields):
            multi_facet = whoosh.sorting.MultiFacet()
            for field_name in self._sortable_fields:
                field = self._fields_mapper[field_name]
                multi_facet.add_field(field_name, reverse=not field._is_ascending())
            search_kwargs["sortedby"] = multi_facet

        idx = self._get_index()
        with idx.searcher() as searcher:
            doc_list = [hit.fields() for hit in searcher.search(**search_kwargs)]

        self.cache.set(key, doc_list, expire=self.cache_expire)
        return doc_list
