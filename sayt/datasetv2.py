# -*- coding: utf-8 -*-

"""
The core feature of Sayt.
"""

import typing as T
import time
import shutil
import os
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
from .tracker import Tracker, TrackerIsLockedError


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


class _Nothing:
    pass


NOTHING = _Nothing()


T_DOCUMENT = T.Dict[str, T.Any]


class T_Hit(T.TypedDict):
    """
    Represent a hit in the search result.
    """

    _id: int
    _score: int
    _source: T_DOCUMENT


class T_Result(T.TypedDict):
    """
    Return type of the :meth:`DataSet.search` method when ``simple_response = False``.

    Reference:

    - https://www.elastic.co/guide/en/elasticsearch/reference/current/search-your-data.html
    """

    index: str
    took: int
    size: int
    fresh: bool
    cache: bool
    hits: T.List[T_Hit]


T_DOWNLOADER = T.Callable[..., T.Iterable[T_DOCUMENT]]


@dataclasses.dataclass
class DataSet:
    """
    Defines how you want to index your dataset.

    You should run :meth:`DataSet.build_index` to create the index for your
    dataset, then you can start using :meth:`DataSet.search` to search your
    data.

    If it is time-consuming to load your dataset, for example, you have to
    download it from internet, you can consider :class:`RefreshableDataSet` to
    cache your index and dataset and refresh them when need needed.

    :param dir_index: 索引所在的文件夹. 如果不存在, 会自动创建.
    :param index_name: 索引的名字. 一个索引是类似于数据库中的数据表的概念. 在同一个索引文件夹
        下不同的索引会被分散到不同的文件中, 属于同一个索引的文件会有相同的前缀.
    :param fields: 定义了这个数据集将会如何被索引.
    :param cache: diskcache 缓存对象.
    :param cache_key: 该 dataset 被缓存时所用的 key.
    :param cache_tag: 该 dataset 被缓存时所用的 tag, 这个 tag 可以被用作清除缓存的时候的过滤条件.
    :param cache_expire: cache 的缓存失效时间
    :param skip_validation: 是否跳过对 Dataset 初始化的 validation 检查. 默认是不跳过,
        也就是进行检查.
    """

    dir_index: Path = dataclasses.field(default=NOTHING)
    index_name: str = dataclasses.field(default=NOTHING)
    fields: T.List[T_Field] = dataclasses.field(default_factory=list)

    dir_cache: T.Optional[Path] = dataclasses.field(default=None)
    cache: Cache = dataclasses.field(default=None)
    cache_key: str = dataclasses.field(default=NOTHING)
    cache_tag: T.Optional[str] = dataclasses.field(default=None)
    cache_expire: T.Optional[int] = dataclasses.field(default=None)

    downloader: T_DOWNLOADER = dataclasses.field(default=lambda: [])

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

    def _init_attrs(self):
        self.dir_index = Path(self.dir_index)
        if self.dir_cache is not None:  # pragma: no cover
            self.dir_cache = Path(self.dir_cache)
        if self.cache is None:  # pragma: no cover
            self.cache = Cache(str(self.dir_cache))
        else:
            self.dir_cache = Path(self.cache.directory)

        for k, v in dataclasses.asdict(self).items():
            if isinstance(v, _Nothing):  # pragma: no cover
                raise ValueError(
                    f"arg {k!r} is required for "
                    f"{self.__class__.__module__}.{self.__class__.__qualname__}"
                )

    def __post_init__(self):
        self._init_attrs()
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

    def _get_index(self) -> FileIndex:
        """
        Get the whoosh index object. If the index does not exist, create one.
        if the index exists, open it.
        """
        if exists_in(str(self.dir_index), indexname=self.index_name):
            idx = open_dir(str(self.dir_index), indexname=self.index_name)
        else:
            self.dir_index.mkdir(parents=True, exist_ok=True)
            idx = create_in(
                dirname=str(self.dir_index),
                schema=self.schema,
                indexname=self.index_name,
            )
        return idx

    def remove_index(self):  # pragma: no cover
        """
        Remove the whoosh index for this dataset.
        """
        if exists_in(str(self.dir_index), indexname=self.index_name):
            idx = create_in(
                dirname=str(self.dir_index),
                schema=self.schema,
                indexname=self.index_name,
            )
            idx.close()

    def remove_all_index(self):  # pragma: no cover
        """
        Remove all whoosh index in the index directory.
        """
        if self.dir_index.exists():
            shutil.rmtree(self.dir_index, ignore_errors=True)

    @property
    def _path_tracker(self):
        return self.dir_index / f"{self.index_name}.tracker.json"

    def is_indexing(self) -> bool:  # pragma: no cover
        """
        Return a boolean value to indicate that if this dataset is indexing.

        If True, we should not allow other thread working on the same dataset
        to index.
        """
        return Tracker.new(self._path_tracker).is_locked()

    def _build_index(
        self,
        data: T.List[T.Dict[str, T.Any]],
        memory_limit: int = 512,
        multi_thread: bool = True,
        rebuild: bool = True,
    ):
        """
        Build whoosh index for this dataset and update the cache to indicate
        that it is succeeded.

        :param data: list of dictionary documents data.
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
        else:  # pragma: no cover
            writer = idx.writer(limitmb=memory_limit)

        for row in data:
            doc = {field_name: row.get(field_name) for field_name in self._field_names}
            writer.add_document(**doc)
        writer.commit()
        self.cache.set(
            self.cache_key,
            self.index_name,
            expire=self.cache_expire,
            tag=self.cache_tag,
        )

    def build_index(
        self,
        data: T.List[T.Dict[str, T.Any]],
        memory_limit: int = 512,
        multi_thread: bool = True,
        rebuild: bool = True,
        raise_lock_error: bool = False,
    ) -> bool:
        """
        A wrapper of the :meth:`DataSet._build_index`. Also prevent from
        concurrent indexing.

        :param data: list of dictionary documents data.
        :param memory_limit: maximum memory you can use for indexing, default is 512MB,
            you can use a larger number if you have more memory.
        :param multi_thread: use multi-threading to build index, default is False.
        :param rebuild: if True, remove the existing index and rebuild it.
        :param raise_lock_error: if True, it will raise an error when attempts to
            index a dataset that there's another thread is indexing. if False,
            then it silently pass without doing anying.

        :return: a boolean value to indicate whether building index happened.
        """
        try:
            with Tracker.lock(self._path_tracker, expire=300):
                self._build_index(
                    data=data,
                    memory_limit=memory_limit,
                    multi_thread=multi_thread,
                    rebuild=rebuild,
                )
            return True
        except TrackerIsLockedError as e:  # pragma: no cover
            if raise_lock_error:
                raise e
            else:
                return False
        except Exception as e:  # pragma: no cover
            raise e

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

    def _search(
        self,
        fresh: bool,
        query_cache_key: tuple,
        query: T.Union[str, whoosh.query.Query],
        limit: int = 20,
        simple_response: bool = True,
    ) -> T.Union[T.List[dict], T_Result]:
        # preprocess query and search arguments
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

        # run search
        idx = self._get_index()
        with idx.searcher() as searcher:
            if simple_response:
                res = searcher.search(**search_kwargs)
                doc_list = [hit.fields() for hit in res]
                result = doc_list
            else:
                st = time.process_time()
                res = searcher.search(**search_kwargs)
                hits = list()
                for hit in res:
                    hits.append(
                        {
                            "_id": hit.docnum,
                            "_score": hit.score,
                            "_source": hit.fields(),
                        }
                    )
                et = time.process_time()
                result = {
                    "index": self.index_name,
                    "took": int((et - st) // 0.001),
                    "size": len(hits),
                    "fresh": fresh,
                    "cache": False,
                    "hits": hits,
                }

        # set cache
        self.cache.set(
            query_cache_key,
            result,
            expire=self.cache_expire,
            tag=self.cache_tag,
        )
        return result

    def search(
        self,
        query: T.Union[str, whoosh.query.Query],
        limit: int = 20,
        simple_response: bool = True,
        refresh_data: bool = False,
    ) -> T.Union[T.List[dict], T_Result]:
        """
        Run full-text search. For details about the query language, check this
        `link <https://whoosh.readthedocs.io/en/latest/querylang.html>`_.

        From 0.3.1, you can set ``simple_response`` to ``False`` to get the
        elasticsearch-HTTP-response styled result. For example::

            {
                'index': '3dd28d068ad007367ac7816d7752d382',
                'took': 5,
                'size': 4, # milliseconds
                'cache': False,
                'hits': [
                    {
                        '_id': 470,
                        '_score': -2147485651,
                        '_source': {
                            'id': 'c7242d2f47cb4aa2a1eebd75c7e81bbf',
                            'title': 'More parent message heavy police development how simply.',
                            'author': 'Margaret Ellis',
                            'year': 2003
                        }
                    },
                    {
                        '_id': 456,
                        '_score': -2147485642,
                        '_source': {
                            'id': 'ff91fd8545c64af59637caa043435f50',
                            'author': 'Laura Walters',
                            'title': 'Discover police discussion kitchen.',
                            'year': 1994
                        }
                    },
                    ...
                ]
            }

        :param query: 如果是一个字符串, 则使用 ``MultifieldParser`` 解析. 如果是一个
            ``Query`` 对象, 则直接使用.
        :param limit: 返回结果的最大数量.
        :param simple_response: 如果为 ``True``, 则返回 list of dict 对象, 否则返回
            类似于 ElasticSearch 的 HTTP response 的那种 :class:`Result` 对象.
        :param refresh_data: if True, then will force to download the data
            and refresh the index and cache.
        """
        # check cache
        if (refresh_data is True) or self.cache_key not in self.cache:
            fresh = True
            docs = self.downloader()
            self.build_index(data=docs, rebuild=True)
        else:
            fresh = False

        query_cache_key = (self.cache_key, str(query), limit, simple_response)
        if query_cache_key in self.cache:
            result = self.cache.get(query_cache_key)
            if simple_response is False:
                result["fresh"] = False
                result["cache"] = True
            return result

        return self._search(
            fresh=fresh,
            query_cache_key=query_cache_key,
            query=query,
            limit=limit,
            simple_response=simple_response,
        )
