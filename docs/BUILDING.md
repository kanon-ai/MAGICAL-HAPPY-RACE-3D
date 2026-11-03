# Source and reconstruction / ソースとROM再現

## 最終デモ / Final demo

`demo-source/src/` は現在のC・アセンブリ・生成済みヘッダー、`demo-source/tools/` は開発で使用した生成・ビルド・パッチ処理のソース資料です。開発ツールは過去の中間生成物やローカル構成に依存し、**この公開一式だけで最新版をソースから一括コンパイルできる環境には整理できていません**。

The current C/assembly/generated headers are in `demo-source/src/`; development generation/build/patch sources are in `demo-source/tools/`. These tools depend on intermediate artifacts and local configurations. **This snapshot is not a self-contained, one-command source build of the final demo.**

検証済みの最新版ROMは、保存した旧版ROMとハッシュ検証付き差分からバイト単位で再現できます。これはソースコンパイルではありません。

The tested final ROMs can be reconstructed byte-for-byte from the preserved prior ROMs and checked deltas. This is binary reconstruction, not source compilation:

```powershell
python tools/reconstruct_demo.py
```

Outputs: `outputs/final-demo/`. Distributed ROMs are not overwritten. Code is MIT; embedded artwork, music, generated game data and ROM/delta data retain the asset terms.

## 旧公開版のソースビルド / Historical source build

以下は旧v0.1.1向けの手順です。ルートの `src/`、従来の `assets/`、`tools/build.py` は旧版保存用で、最新版にはなりません。旧ROMは `rom/legacy/` に保持しています。

The root `src/`, historical assets and `tools/build.py` belong to v0.1.1, not the final demo. Prior ROMs are preserved in `rom/legacy/`.

# ビルド / Building

## 日本語

Python 3、SDCC、Pasmoが必要です。対応ツールをPATHに置くか、SDCC/PASMO環境変数で実行ファイルを指定します。ビルドにはBIOSもエミュレーターも不要です。

```powershell
$env:SDCC = "C:/tools/sdcc/bin/sdcc.exe"
$env:PASMO = "C:/tools/pasmo/pasmo.exe"
python tools/build.py --pack-only
```

出力は `outputs/MAGICAL_HAPPY_RALLY_3D.rom`。`rom/` の配布済みROMは上書きしません。ランチャーの `--rom outputs/MAGICAL_HAPPY_RALLY_3D.rom` で生成版を指定できます。

この公開版はC/アセンブリのソースと、再ビルドに必要な生成済み画像・コースデータを含みます。原画や試行中の素材生成・撮影ツール一式は含みません。生成済み素材は別ライセンスです。異なるコンパイラー版では配置・コードサイズが変わり、ビルド時の領域検査に失敗する場合があります。

## English

Install Python 3, SDCC and Pasmo. Put them on PATH or set SDCC and PASMO to the executable paths, then run `python tools/build.py --pack-only` (the PowerShell example above applies). No BIOS or emulator is needed to build.

Output: `outputs/MAGICAL_HAPPY_RALLY_3D.rom`; the distributed ROM in `rom/` is preserved. Pass `--rom outputs/MAGICAL_HAPPY_RALLY_3D.rom` to the launcher to run your build.

This release includes C/assembly sources and the pre-generated graphics/course data required to rebuild. Original artwork and the experimental asset-generation/capture tool collection are not included. Generated assets retain their separate terms. Compiler versions can change code size/layout and trigger the build's memory-range checks.

検証ツール / Verified compiler: SDCC 4.6.0 #16555 (MINGW64).
Verified ROM SHA-256: `3ef176403cb7ad752196dca81f877b99ffddaefd508315676bddcd159c345ea6`.


## 外付け版のビルド / Build the external edition

```powershell
python tools/build.py --pack-only --external-88h
```

出力 / Output: `outputs/external-88h/MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H.rom`.

`src/io_ports.h` でVDPとGeo3DのI/Oポートだけを選択します。ゲーム内容・素材・音楽は共通です。ビルド先を分離し、内蔵版を上書きしません。

`src/io_ports.h` selects the VDP and Geo3D I/O ports. Gameplay, assets and music are shared. The separate output directory preserves the internal edition.
