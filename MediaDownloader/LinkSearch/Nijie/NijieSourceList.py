# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from MediaDownloader.LinkSearch.URL import URL


@dataclass(frozen=True)
class NijieSourceList(Iterable):
    """nijie作品への直リンクリスト
    """
    _list: list[URL]

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid NijieSourceList.")
        if self._list:
            if not all([isinstance(r, URL) for r in self._list]):
                raise ValueError("include not URL element, invalid NijieSourceList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def __getitem__(self, i):
        return self._list.__getitem__(i)

    @classmethod
    def create(cls, nijie_url_list: list[URL] | list[str]) -> "NijieSourceList":
        if not isinstance(nijie_url_list, list):
            raise TypeError("Args is not list.")
        if not nijie_url_list:
            return cls([])
        if isinstance(nijie_url_list[0], URL):
            return cls(nijie_url_list)
        if isinstance(nijie_url_list[0], str):
            return cls([URL(r) for r in nijie_url_list])
        raise ValueError("Create NijieSourceList failed.")


if __name__ == "__main__":
    url_base = "https://nijie.info/view_popup.php?id={}"
    urls = [URL(url_base.format(i)) for i in range(10)]
    nijie_url_list = NijieSourceList.create(urls)
    print(nijie_url_list)
