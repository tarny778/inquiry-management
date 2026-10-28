"""文字列入力の空白正規化ユーティリティ。"""


def blank_string_to_none(value):
    """空文字列・空白だけの文字列をNoneに変換する。

    空白以外を含む文字列は変更しない。特にパスワードの前後の空白は保持する。
    """
    if isinstance(value, str) and not value.strip():
        return None
    return value
