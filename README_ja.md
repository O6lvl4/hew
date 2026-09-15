# hew

コードを、モデルが読むべき形で読むためのコマンドです。コーディングエージェントが 1 セッションに
何百回も実行する `cat` / `grep` / `sed -n` / `awk '/^fn x/,/^}/'` のパイプラインの置き換えとして、
毎回「頼まれたものだけ」を、行番号とサイズ付きで、コードの構造を踏まえて返します。

[English](README.md)

```
hew src/lower.rs --symbol lower_match              関数を 1 つ、名前で
hew src/lower.rs --grep "Expr::Match" --around 4   マッチ行と前後。どの関数の中かを添えて
hew src/lower.rs --lines 120-160                   行範囲。番号付き
hew outline src/lower.rs                           ファイルの目次
hew grep "unwrap()" src                            同じ行を畳み、囲むシンボルを示す grep
hew tree src --depth 2                             ディレクトリ。vcs / build / 依存は除外
```

## なぜ作ったか

4,000 行のファイルを読んで関数 1 つについて答えるエージェントは、そのファイル全体を以後の
全ターンで払い続けます。エージェントもそれを知っていて、シェルのパイプラインで範囲を絞ります。
ただしそのやり方は壊れやすい。`awk` の範囲指定はネストした波括弧で崩れ、`sed -n` は先に行番号を
探す必要があり、`grep -n` の結果はマッチが *どこの* ものかを教えてくれない。`hew` はその絞り込みを
1 つのバイナリで、正しく、1 回で行います。

- **構造を知っている。** `--symbol` で関数・型・クラス・impl のメソッド・テストを名前で切り出せます。
  Almide・Rust・Go・Python・JavaScript・TypeScript(JSX と `.tsx` も)はバイナリにリンクした
  [gramide](https://github.com/O6lvl4/gramide) の文法でパースします。編集途中の Python・JavaScript・
  TypeScript は回復した宣言から読みます。他の言語は
  `HEW_OUTLINE_BIN` で目次プログラムを差し込めます。
- **番号とサイズが付く。** 全行に行番号が付くので、次の呼び出しは `--lines A-B` で済みます。
  長い行は切り詰め、飛ばした箇所には飛ばした行数を示します。ヘッダにはファイル全体の大きさ、
  フッタには見せた量が出ます。
- **grep が場所を教える。** マッチはファイルごとにまとめ、同一行は畳んで（`×3`）、それぞれに囲んでいる
  シンボル名を付けます。ファイルごとと全体の上限で出力量は抑えられます。
- **何も隠さない。** `hew` は頼まれたものだけを返します。要約も予算もありません。何が必要かは
  モデルが決めます。

## モデルに届くもの

```
$ hew src/cmds/git/git.rs --symbol compact_diff
# src/cmds/git/git.rs  (4720 lines, 168 KB)
       ⋮  (647 lines)
     ── fn compact_diff ──
 648│ pub fn compact_diff(input: &str, opts: &DiffOpts) -> String {
 649│     let mut out = String::new();
 …
 821│ }
       ⋮  (3899 lines)
# shown: 174 lines, 6 KB
```

```
$ hew grep "fn run_" src/cmds/git
# 14 matches in 3 files
src/cmds/git/git.rs  (9)
  112│ pub fn run_diff(args: &[String]) -> Result<()>    ‹run_diff›
  230│ pub fn run_log(args: &[String]) -> Result<()>     ‹run_log›
  …
src/cmds/git/stash.rs  (2)
   40│ pub fn run_stash(args: &[String]) -> Result<()>   ‹run_stash›
```

```
$ hew src/lower.rs --grep "Expr::Match" --around 2
# src/lower.rs  (1210 lines, 41 KB)
       ⋮  (310 lines)
     ── in fn lower_expr ──
 311│         Expr::If { .. } => self.lower_if(e),
 312│         Expr::Match { scrutinee, arms } => self.lower_match(scrutinee, arms),
 313│         Expr::Block(b) => self.lower_block(b),
       ⋮  (402 lines)
     ── in fn lower_match ──
 716│     // Expr::Match with a single arm is a let
 …
# shown: 12 lines, 640 B
```

## インストール

```bash
almide install github.com/O6lvl4/hew      # ネイティブバイナリが 1 つ → ~/.local/bin/hew
```

バイナリ 1 つ、ランタイムなし、他のツールも不要です。パーサはその中にあり、`hew --version` が
リンクしたエンジンと文法の版を表示します。任意で `HEW_OUTLINE_BIN=<プログラム>` に目次プログラムを
指定できます（パスを引数に受け取り、`{"lang","total_lines","symbols":[{"kind","name","start","end"}]}`
を出力するもの）。指定すると、そのプログラムが知っている言語すべてで、`--symbol`、`outline`、grep の
ラベルにその結果が使われます。この契約で話せる tree-sitter 系のツールなら何でも差し込めます。

## エージェントに教える

`CLAUDE.md`（または使っているエージェントの同等ファイル）に追記します:

```
コードは cat / sed -n / awk ではなく `hew` で読むこと:
- `hew <file> --symbol NAME`            関数や型を 1 つ
- `hew <file> --grep RE [--around N]`   マッチ行と前後
- `hew <file> --lines A-B`              行範囲（出力は番号付きなので戻ってこられる）
- `hew outline <file|dir>`              読む前に、何が入っているか
- `hew grep RE [path]`                  囲んでいるシンボルを示す検索
```

## コマンド

```
hew <file> [--lines A-B] [--symbol NAME] [--grep RE] [--around N] [--head N] [--tail N] [--clip N]
hew outline <file|dir> [--max N]
hew read-json <file> [--max-chars N]
hew grep <RE> [path...] [--per-file N] [--max-files N] [--clip N]
hew tree <dir> [--depth N]
```

既定値は `--around` 3、`--clip` 200 文字、`--per-file` 20 件、`--max-files` 50 ファイル。
正規表現は Rust 構文ですが、`\b` と非貪欲量指定子は使えません（Almide の regex の制約）。
`grep` と `tree` は `.git`、`target`、`node_modules`、`dist`、`build`、`vendor`、仮想環境、
2 MB 超のファイルを飛ばします。

## アーキテクチャ

![hew architecture](docs/architecture.svg)

エージェントは Bash 経由で `hew` を呼びます。main が引数を解釈してコマンドを選び、
3 つのモジュールを組み合わせて答えを作ります。

- **view** — 表示する行範囲（ウィンドウ）を受け取り、番号付きの行、切り詰め、省略マーカー、
  ヘッダとフッタを組み立てる。
- **outline** — ファイルの目次。Almide・Rust・Go・Python・JavaScript(JSX 込み)・TypeScript(`.tsx` 込み)
  は **parsers** にある gramide の文法でパースする（まず厳密に、失敗したらパッケージが提供する回復文書で）。
  それ以外（契約を破ったプロバイダ）は言語ごとの宣言ルール表で宣言行を見つけ、
  波括弧の対応（Python はインデント）で範囲を決める。状態を持つ字句マスクがコメントとリテラルを
  先に隠す。それでもヒューリスティックはヒューリスティックで、複数行ヘッダや正規表現リテラル、
  テンプレート補間までは完全な文法ではない。
  `find(name)` で名前から、`enclosing(line)` で行番号から、シンボルを引く。
- **search** — ディレクトリを歩き（vcs / build / 依存 / バイナリは除外）、マッチをファイルごとに
  まとめ、同一行を畳み、上限をかけ、outline で囲んでいるシンボルを付ける。

文法も含めてすべて内蔵です。`HEW_OUTLINE_BIN` で外部の目次プログラムを指定した場合は、その JSON の
結果が内蔵ルールの代わりに使われます。

[Almide](https://github.com/almide/almide) 製。MIT / Apache-2.0 のデュアルライセンス。

## パーサに裏打ちされた読み取り

## ast-grep の outline との比較

`ast-grep outline`（0.45）は、コーディングエージェントが今日呼べるもう一つの構造を知る
目次で、tree-sitter の文法の上に載っている。この機械で、毎回新しいプロセスを起動し、
5 回の最小値を取った計測（[証拠](docs/evidence/ast-grep-outline.json)）:

| | ファイル | hew | ast-grep |
|---|---:|---:|---:|
| Node `lib/`（JavaScript） | 427 | 0.055 秒 | 0.053 秒 |
| TypeScript 5.9 `src/` | 701 | 0.136 秒 | 0.169 秒 |

TypeScript の数字は 1 ファイルで決まる。`checker.ts` は 3.1 MB でパースに約 0.10 秒かかり、
それを持つアームより先に終われるアームはない。ファイルは大きい順に、その時点で最もバイト数の
少ないアームへ配り、答えは 1 回の書き出しで出す。リストを等バイトの範囲に切っていた頃は
そのファイルと隣の 2.5 MB が同じスライスに入り、49,000 行を 1 行ずつ出力する時間が
パースと同じだけかかっていた。

3 つ目のメンバーのヘッダが壊れたクラス（`broken( {`）では、hew は回復パースから無事な
2 つのメソッドとクラスの後の関数を `gramide-recovered` のラベル付きで列挙し、ast-grep は
`nothing found` と答える。hew に無いのは ast-grep の言語数で、tree-sitter の数百に対して
文法は 6 つ。残りは `HEW_OUTLINE_BIN` の契約で差し込む。

hew は [gramide](https://github.com/O6lvl4/gramide)（エンジン）と 6 つの言語パッケージ
（[Almide](https://github.com/O6lvl4/gramide-almide)・[Go](https://github.com/O6lvl4/gramide-go)・
[Rust](https://github.com/O6lvl4/gramide-rust)・[Python 3.14](https://github.com/O6lvl4/gramide-python)・
[JavaScript](https://github.com/O6lvl4/gramide-javascript)・[TypeScript 5.9](https://github.com/O6lvl4/gramide-typescript)）
を普通の Almide 依存としてリンクし、`almide.lock` で版を固定しています。`gramide` コマンドと同じ
合成をプロセス内で呼ぶので、ディレクトリのアウトラインはファイルごとのプロセス起動ではなく
ファイルごとのパース 1 回で済み、`PATH` に何も要りません。ディレクトリのアウトラインは、リンクした
パッケージが `symbols` に答える拡張子をすべて読みます（`.pyi` も）。文法は Rust の属性や複数行ヘッダ、
Python のデコレータを含む宣言範囲を返します。Python の入れ子クラス・関数は `Outer.Inner.method` や
`Outer.method.helper` のような修飾パスを持つので、`--symbol` で同名の宣言を正確に選べます。
明示した `HEW_OUTLINE_BIN` が最優先です。パースに失敗したら、パッケージが提供する場合は明示的な
回復宣言の契約を使い、それも無理なら内蔵ヒューリスティックに戻ります。アウトラインのヘッダと
選択したシンボルのラベルには `gramide`、`gramide-recovered`、`provider`、`heuristic` のどれで読んだかが
出ます。フォールバックはパーサと同等ではありません。

どの経路から来た文書も同じように検証します。言語、行数、実ファイル内に収まる整った範囲、そして
厳密な文法経路ではスキーマ版 1 と完全なパース。リンクしたエンジンからでも外部プロバイダからでも
同じです。tree-sitter のインストールは不要です。

`hew read-json FILE --max-chars 24000` は正確な `content`、要求した `path`、`total_chars`、
`complete` をバージョン付き JSON で返します。改行と長い行をそのまま保ち、表示用ラベルは付きません。
上限は byte ではなく Unicode 文字数で数えます。`complete` が false なら内容は先頭部分だけで、
ファイル全体の置き換えには使えません。対応する上限は 1〜1,000,000 文字です。

書きかけの Python については、厳密なパースに失敗したあと hew が回復文書を読みます。回復ポリシー、
診断、順序付きのエラー範囲、宣言範囲を検証し、エラーと重なる宣言は拒否します。無傷の兄弟メソッドは
修飾名で選べたままで、エラーを含む外側のクラスや関数は省かれます。出力には `gramide-recovered` と
表示されます。これでファイルが構文的に正しくなるわけではありません。パッケージが範囲を確定できない
損傷では、ラベル付きのヒューリスティックに戻ります。
