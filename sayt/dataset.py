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

from .exc import MalformedFieldSettingError, MalformedDatasetSettingError
from .utils import is_no_overlap
from .compat import cached_property


@dataclasses.dataclass
class Field:
    """
    Defines how do you want to store / index this field for full text search:

    :param name: the name of the field
    :param type_is_store: if True, the value is only stored but not indexed for
        search. Usually it can be used to dynamically construct value for argument
        (the action when you press enter), or for auto complete (the action
        when you press tab)
    :param type_is_ngram: if True, the value is index using ngram. It matches
        any character shorter than N characters.
        https://whoosh.readthedocs.io/en/latest/ngrams.html.
    :param type_is_phrase: if True, the value is indexed using phrase. Only
        case-insensitive phrase will be matched. See
        https://whoosh.readthedocs.io/en/latest/schema.html#built-in-field-types
    :param type_is_keyword: if True, the value is indexed using keyword. The
        keyword has to be exactly matched. See
        https://whoosh.readthedocs.io/en/latest/schema.html#built-in-field-types
    :param type_is_numeric: if True, the value is indexed using number. The
        number field is not used for searching, it is only used for sorting. See
        https://whoosh.readthedocs.io/en/latest/schema.html#built-in-field-types
    :param ngram_minsize: minimal number of character to match, default is 2.
    :param ngram_maxsize: maximum number of character to match, default is 10.
    :param keyword_lowercase: for keyword type field, is the match case-sensitive?
        default True (not sensitive).
    :param keyword_commas: is the delimiter of keyword is comma or space?
    :param weight: the weight of the field for sorting in the search result.
        default is 1.0.
    :param is_sortable: is the field will be used for sorting? If True, the field
        has to be stored.
    :param is_sort_ascending: is the field will be used for sort ascending?
    """

    name: str = dataclasses.field()
    type_is_store: bool = dataclasses.field(default=False)
    type_is_id: bool = dataclasses.field(default=False)
    type_is_ngram: bool = dataclasses.field(default=False)
    type_is_phrase: bool = dataclasses.field(default=False)
    type_is_keyword: bool = dataclasses.field(default=False)
    type_is_numeric: bool = dataclasses.field(default=False)
    ngram_minsize: int = dataclasses.field(default=2)
    ngram_maxsize: int = dataclasses.field(default=10)
    keyword_lowercase: bool = dataclasses.field(default=True)
    keyword_commas: bool = dataclasses.field(default=True)
    weight: float = dataclasses.field(default=1.0)
    is_sortable: bool = dataclasses.field(default=False)
    is_sort_ascending: bool = dataclasses.field(default=True)

    def __post_init__(self):
        # do some validation
        flag = sum(
            [
                self.type_is_id,
                self.type_is_ngram,
                self.type_is_phrase,
                self.type_is_keyword,
                self.type_is_numeric,
            ]
        )
        if flag <= 1:
            pass
        else:
            msg = (
                f"you have to specify one and only one index type for field {self.name!r}, "
                f"valid types are: store, id, ngram, phrase, keyword, numeric."
            )
            raise MalformedFieldSettingError(msg)

        if self.is_sortable is True and self.type_is_store is False:
            msg = f"you have to use store field for sorting by {self.name!r}!"
            raise MalformedFieldSettingError(msg)


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
    fields: T.List[Field] = dataclasses.field()

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

    def _check_id_fields(self):  # pragma: no cover
        if len(self._id_fields) > 1:
            msg = "you can have at most one id field!"
            raise MalformedDatasetSettingError(msg)

    def _check_fields_index_type(self):  # pragma: no cover
        if not is_no_overlap(
            [
                self._id_fields,
                self._ngram_fields,
                self._phrase_fields,
                self._keyword_fields,
            ]
        ):
            msg = (
                "`ngram_fields`, `phrase_fields` and `keyword_fields` "
                "should not have any overlaps!"
            )
            raise MalformedDatasetSettingError(msg)

    def _validate_attributes(self):
        self._check_fields_name()
        self._check_fields_index_type()

    def __post_init__(self):
        # do some validation
        if self.skip_validation is False:
            self._validate_attributes()

    @cached_property
    def _fields_mapper(self) -> T.Dict[str, Field]:
        """
        从 field name 到 field 对象的映射
        """
        return {field.name: field for field in self.fields}

    @cached_property
    def _store_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.type_is_store]

    @cached_property
    def _id_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.type_is_id]

    @cached_property
    def _ngram_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.type_is_ngram]

    @cached_property
    def _phrase_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.type_is_phrase]

    @cached_property
    def _keyword_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.type_is_keyword]

    @cached_property
    def _numeric_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.type_is_numeric]

    @cached_property
    def _searchable_fields(self) -> T.List[str]:
        return (
            self._id_fields
            + self._ngram_fields
            + self._phrase_fields
            + self._keyword_fields
            + self._numeric_fields
        )

    @cached_property
    def _sortable_fields(self) -> T.List[str]:
        return [field.name for field in self.fields if field.is_sortable]

    @cached_property
    def _field_names(self) -> T.List[str]:
        return [field.name for field in self.fields]

    def _create_whoosh_schema(self) -> whoosh.fields.Schema:
        """
        Dynamically create whoosh.fields.SchemaClass schema object.
        It defines how you index your dataset.
        """
        schema_classname = "WhooshSchema"
        schema_classname = str(schema_classname)
        attrs = OrderedDict()
        for field in self.fields:
            if field.type_is_id:
                whoosh_field = whoosh.fields.ID(
                    stored=field.type_is_id,
                    unique=True,
                    field_boost=field.weight,
                    sortable=field.is_sortable,
                )
            elif field.type_is_ngram:
                whoosh_field = whoosh.fields.NGRAM(
                    stored=field.type_is_store,
                    minsize=field.ngram_minsize,
                    maxsize=field.ngram_maxsize,
                    field_boost=field.weight,
                    sortable=field.is_sortable,
                )
            elif field.type_is_phrase:
                whoosh_field = whoosh.fields.TEXT(
                    stored=field.type_is_store,
                    field_boost=field.weight,
                    sortable=field.is_sortable,
                )
            elif field.type_is_keyword:  # pragma: no cover
                whoosh_field = whoosh.fields.KEYWORD(
                    stored=field.type_is_store,
                    lowercase=field.keyword_lowercase,
                    commas=field.keyword_commas,
                    field_boost=field.weight,
                    sortable=field.is_sortable,
                )
            elif field.type_is_numeric:
                whoosh_field = whoosh.fields.NUMERIC(
                    stored=field.type_is_store,
                    field_boost=field.weight,
                    sortable=field.is_sortable,
                )
            elif field.type_is_store:  # pragma: no cover
                whoosh_field = whoosh.fields.STORED()
            else:  # pragma: no cover
                raise NotImplementedError
            attrs[field.name] = whoosh_field
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
        self.cache.evict(tag=self.cache_tag)

    def remove_all_cache(self):  # pragma: no cover
        """
        Remove all cache in the cache directory.
        """
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
                multi_facet.add_field(field_name, reverse=not field.is_sort_ascending)
            search_kwargs["sortedby"] = multi_facet

        idx = self._get_index()
        with idx.searcher() as searcher:
            doc_list = [hit.fields() for hit in searcher.search(**search_kwargs)]

        self.cache.set(key, doc_list, expire=self.cache_expire)
        return doc_list
