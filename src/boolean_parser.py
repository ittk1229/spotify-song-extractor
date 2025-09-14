import re
from abc import ABC, abstractmethod
from typing import List


class BooleanExpression(ABC):
    """ブール式の抽象基底クラス"""

    @abstractmethod
    def evaluate(self, text: str) -> bool:
        """テキストに対してブール式を評価する"""
        pass


class Keyword(BooleanExpression):
    """単一キーワードの検索"""

    def __init__(self, keyword: str):
        self.keyword = keyword.strip()

    def evaluate(self, text: str) -> bool:
        return self.keyword.lower() in text.lower()

    def __repr__(self) -> str:
        return f"Keyword('{self.keyword}')"


class AndExpression(BooleanExpression):
    """AND演算を表現するクラス"""

    def __init__(self, left: BooleanExpression, right: BooleanExpression):
        self.left = left
        self.right = right

    def evaluate(self, text: str) -> bool:
        return self.left.evaluate(text) and self.right.evaluate(text)

    def __repr__(self) -> str:
        return f"({self.left} AND {self.right})"


class OrExpression(BooleanExpression):
    """OR演算を表現するクラス"""

    def __init__(self, left: BooleanExpression, right: BooleanExpression):
        self.left = left
        self.right = right

    def evaluate(self, text: str) -> bool:
        return self.left.evaluate(text) or self.right.evaluate(text)

    def __repr__(self) -> str:
        return f"({self.left} OR {self.right})"


class NotExpression(BooleanExpression):
    """NOT演算を表現するクラス"""

    def __init__(self, operand: BooleanExpression):
        self.operand = operand

    def evaluate(self, text: str) -> bool:
        return not self.operand.evaluate(text)

    def __repr__(self) -> str:
        return f"NOT {self.operand}"


class BooleanParser:
    """ブール式文字列をパースしてBooleanExpressionオブジェクトを生成するクラス"""

    def __init__(self):
        self.tokens = []
        self.position = 0

    def parse(self, expression: str) -> BooleanExpression:
        """ブール式文字列をパースする"""
        # トークン化
        self.tokens = self._tokenize(expression)
        self.position = 0

        # 構文解析
        if not self.tokens:
            raise ValueError("空の検索式です")

        result = self._parse_or()

        if self.position < len(self.tokens):
            raise ValueError(f"予期しないトークン: {self.tokens[self.position]}")

        return result

    def _tokenize(self, expression: str) -> List[str]:
        """文字列をトークンに分割する"""
        # 正規表現でトークンを抽出
        # キーワード、演算子、括弧を識別
        token_pattern = r"(\(|\)|AND|OR|NOT|[^\s()]+)"
        tokens = re.findall(token_pattern, expression, re.IGNORECASE)

        # 大小文字を正規化（演算子のみ）
        normalized_tokens = []
        for token in tokens:
            upper_token = token.upper()
            if upper_token in ("AND", "OR", "NOT", "(", ")"):
                normalized_tokens.append(upper_token)
            else:
                normalized_tokens.append(token)

        return normalized_tokens

    def _current_token(self) -> str:
        """現在のトークンを取得"""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def _consume_token(self) -> str:
        """現在のトークンを消費して次に進む"""
        if self.position < len(self.tokens):
            token = self.tokens[self.position]
            self.position += 1
            return token
        return None

    def _parse_or(self) -> BooleanExpression:
        """OR演算子をパースする（最低優先度）"""
        left = self._parse_and()

        while self._current_token() == "OR":
            self._consume_token()  # OR を消費
            right = self._parse_and()
            left = OrExpression(left, right)

        return left

    def _parse_and(self) -> BooleanExpression:
        """AND演算子をパースする（中間優先度）"""
        left = self._parse_not()

        while self._current_token() == "AND":
            self._consume_token()  # AND を消費
            right = self._parse_not()
            left = AndExpression(left, right)

        return left

    def _parse_not(self) -> BooleanExpression:
        """NOT演算子をパースする（高優先度）"""
        if self._current_token() == "NOT":
            self._consume_token()  # NOT を消費
            operand = self._parse_primary()
            return NotExpression(operand)

        return self._parse_primary()

    def _parse_primary(self) -> BooleanExpression:
        """基本要素（キーワードや括弧）をパースする"""
        token = self._current_token()

        if token is None:
            raise ValueError("予期しない式の終了")

        if token == "(":
            self._consume_token()  # ( を消費
            expr = self._parse_or()
            if self._current_token() != ")":
                raise ValueError("対応する ')' がありません")
            self._consume_token()  # ) を消費
            return expr

        if token in ("AND", "OR", "NOT", ")"):
            raise ValueError(f"予期しないトークン: {token}")

        # キーワードとして処理
        keyword = self._consume_token()
        return Keyword(keyword)


def parse_boolean_expression(expression: str) -> BooleanExpression:
    """ブール式文字列をパースしてBooleanExpressionオブジェクトを返す

    簡単なファクトリー関数として提供
    """
    parser = BooleanParser()
    return parser.parse(expression)


def is_boolean_expression(expression: str) -> bool:
    """文字列がブール式かどうかを判定する

    AND, OR, NOT, 括弧のいずれかが含まれている場合はブール式とみなす
    """
    upper_expr = expression.upper()
    # 括弧があるかチェック
    if "(" in upper_expr or ")" in upper_expr:
        return True
    
    # 演算子をワード境界を考慮してチェック
    import re
    operators = ["AND", "OR", "NOT"]
    for op in operators:
        # ワード境界を使用して演算子を検出
        if re.search(r'\b' + op + r'\b', upper_expr):
            return True
    
    return False
