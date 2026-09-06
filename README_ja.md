# peek

コードを、モデルが読むべき形で読むためのコマンドです。コーディングエージェントが 1 セッションに
何百回も実行する `cat` / `grep` / `sed -n` / `awk '/^fn x/,/^}/'` のパイプラインの置き換えとして、
毎回「頼まれたものだけ」を、行番号とサイズ付きで、コードの構造を踏まえて返します。

[English](README.md)

```
peek src/lower.rs --symbol lower_match              関数を 1 つ、名前で
peek src/lower.rs --grep "Expr::Match" --around 4   マッチ行と前後。どの関数の中かを添えて
peek src/lower.rs --lines 120-160                   行範囲。番号付き
peek outline src/lower.rs                           ファイルの目次
peek grep "unwrap()" src                            同じ行を畳み、囲むシンボルを示す grep
peek tree src --depth 2                             ディレクトリ。vcs / build / 依存は除外
```

## なぜ作ったか

4,000 行のファイルを読んで関数 1 つについて答えるエージェントは、そのファイル全体を以後の
全ターンで払い続けます。エージェントもそれを知っていて、シェルのパイプラインで範囲を絞ります。
ただしそのやり方は壊れやすい。`awk` の範囲指定はネストした波括弧で崩れ、`sed -n` は先に行番号を
探す必要があり、`grep -n` の結果はマッチが *どこの* ものかを教えてくれない。`peek` はその絞り込みを
1 つのバイナリで、正しく、1 回で行います。

- **構造を知っている。** `--symbol` で関数・型・クラス・impl のメソッド・テストを名前で切り出せます。
  Almide、Rust、Go、TypeScript/JavaScript、Python は内蔵パーサで扱い、外部依存はありません。
  tree-sitter の精度が欲しければ `PEEK_OUTLINE_BIN` で外部の目次プログラムを差し込めます。
- **番号とサイズが付く。** 全行に行番号が付くので、次の呼び出しは `--lines A-B` で済みます。
  長い行は切り詰め、飛ばした箇所には飛ばした行数を示します。ヘッダにはファイル全体の大きさ、
  フッタには見せた量が出ます。
- **grep が場所を教える。** マッチはファイルごとにまとめ、同一行は畳んで（`×3`）、それぞれに囲んでいる
  シンボル名を付けます。ファイルごとと全体の上限で出力量は抑えられます。
- **何も隠さない。** `peek` は頼まれたものだけを返します。要約も予算もありません。何が必要かは
  モデルが決めます。

## モデルに届くもの

```
$ peek src/cmds/git/git.rs --symbol compact_diff
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
$ peek grep "fn run_" src/cmds/git
# 14 matches in 3 files
src/cmds/git/git.rs  (9)
  112│ pub fn run_diff(args: &[String]) -> Result<()>    ‹run_diff›
  230│ pub fn run_log(args: &[String]) -> Result<()>     ‹run_log›
  …
src/cmds/git/stash.rs  (2)
   40│ pub fn run_stash(args: &[String]) -> Result<()>   ‹run_stash›
```

```
$ peek src/lower.rs --grep "Expr::Match" --around 2
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
almide install github.com/O6lvl4/peek      # ネイティブバイナリが 1 つ → ~/.local/bin/peek
```

バイナリ 1 つ、ランタイムなし、他のツールも不要です。任意で `PEEK_OUTLINE_BIN=<プログラム>` に
目次プログラムを指定できます（パスを引数に受け取り、
`{"lang","total_lines","symbols":[{"kind","name","start","end"}]}` を出力するもの）。指定すると、
そのプログラムが知っている言語すべてで、`--symbol`、`outline`、grep のラベルにその結果が使われます。
たとえば [`ctxgate-outline`](https://github.com/O6lvl4/ctxgate/tree/main/tools/ctxgate-outline)
（tree-sitter: 専用ルール付きの 16 言語と、初回使用時にダウンロードされる 371 言語）:

```bash
export PEEK_OUTLINE_BIN=ctxgate-outline
```

## エージェントに教える

`CLAUDE.md`（または使っているエージェントの同等ファイル）に追記します:

```
コードは cat / sed -n / awk ではなく `peek` で読むこと:
- `peek <file> --symbol NAME`            関数や型を 1 つ
- `peek <file> --grep RE [--around N]`   マッチ行と前後
- `peek <file> --lines A-B`              行範囲（出力は番号付きなので戻ってこられる）
- `peek outline <file|dir>`              読む前に、何が入っているか
- `peek grep RE [path]`                  囲んでいるシンボルを示す検索
```

## コマンド

```
peek <file> [--lines A-B] [--symbol NAME] [--grep RE] [--around N] [--head N] [--tail N] [--clip N]
peek outline <file|dir> [--max N]
peek grep <RE> [path...] [--per-file N] [--max-files N] [--clip N]
peek tree <dir> [--depth N]
```

既定値は `--around` 3、`--clip` 200 文字、`--per-file` 20 件、`--max-files` 50 ファイル。
正規表現は Rust 構文ですが、`\b` と非貪欲量指定子は使えません（Almide の regex の制約）。
`grep` と `tree` は `.git`、`target`、`node_modules`、`dist`、`build`、`vendor`、仮想環境、
2 MB 超のファイルを飛ばします。

## アーキテクチャ

![peek architecture](docs/architecture.svg)

エージェントは Bash 経由で `peek` を呼びます。main が引数を解釈してコマンドを選び、
3 つのモジュールを組み合わせて答えを作ります。

- **view** — 表示する行範囲（ウィンドウ）を受け取り、番号付きの行、切り詰め、省略マーカー、
  ヘッダとフッタを組み立てる。
- **outline** — ファイルの目次。Almide は専用パーサ、Rust / Go / TS・JS / Python は言語ごとの
  宣言ルール表で宣言行を見つけ、波括弧の対応（Python はインデント）で範囲を決める。
  `find(name)` で名前から、`enclosing(line)` で行番号から、シンボルを引く。
- **search** — ディレクトリを歩き（vcs / build / 依存 / バイナリは除外）、マッチをファイルごとに
  まとめ、同一行を畳み、上限をかけ、outline で囲んでいるシンボルを付ける。

すべて内蔵です。`PEEK_OUTLINE_BIN` で外部の目次プログラムを指定した場合は、その JSON の結果が
内蔵ルールの代わりに使われます。

## ctxgate との関係

[ctxgate](https://github.com/O6lvl4/ctxgate) はツール呼び出しの *出力* 側で働きます。返ってきた
ものを vault に保存し、必要なら絞る。それを計測して分かったのは、モデルが頼んでいない要約は
ターンを増やしがちで、いちばん良いセッションはエージェントが自分で読む範囲を絞っていた
セッションだった、ということでした。`peek` はその絞り込みを、きちんとやるための道具です。
両方使ってください。ctxgate は安全網、`peek` は入口です。

[Almide](https://github.com/almide/almide) 製。MIT / Apache-2.0 のデュアルライセンス。
