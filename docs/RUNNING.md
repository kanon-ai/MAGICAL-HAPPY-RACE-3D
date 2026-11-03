# 実行方法 / Running the demo

## 日本語

### 必要な環境

- Geo3D V2・V9968（256色EPAL・256KiB VRAM）に対応したopenMSX。
- `Panasonic_FS-A1ST_V9968` の機種定義と `geo3d` 拡張定義。
- MSX turbo RのR800、256KiB以上のRAM、MSX-MUSIC/OPLL。
- ご自身が適法に入手したBIOS／システムROM。openMSXの通常の `systemroms` 探索先に配置してください。
- 同梱ランチャーを使用する場合はPython 3（追加Pythonパッケージ不要）。

このリポジトリは必要なエミュレーターやBIOSを自動取得しません。対応エミュレーターの開発元は [Geo3D openMSX](https://github.com/alexmoncks/openMSX)、関連資料は [Geo3D](https://github.com/alexmoncks/V9968_Cartridge/tree/main/geo3d) と [V9968](https://github.com/hra1129/V9968_Cartridge) を参照してください。開発中の拡張のため、任意の版での互換性は保証しません。必要な機種・拡張が含まれない版では、対応する定義を別途用意する必要があります。

### Windows：ランチャーで起動

ZIP展開先でPowerShellを開きます。

```powershell
python tools/play.py --openmsx "C:/path/to/compatible-openmsx/openmsx.exe"
```

毎回パスを指定しない場合は、同じPowerShellで次のように設定できます。

```powershell
$env:OPENMSX = "C:/path/to/compatible-openmsx/openmsx.exe"
.\PLAY.cmd
```

`C:/path/to/...` は実在する対応版openMSXの場所に置き換えてください。ランチャーは初期速度100%、通常時間進行、音声ONで起動します。ファームウェアを書き込む処理はありません。

### openMSXを直接起動（Python不要）

展開先をカレントディレクトリにして実行します。

```powershell
& "C:/path/to/compatible-openmsx/openmsx.exe" -machine Panasonic_FS-A1ST_V9968 -ext geo3d -cart rom/MAGICAL_HAPPY_RACE_3D_INTERNAL_98H.rom -romtype ASCII16 -script tools/play.tcl
```

タイトルでSpace、メニューでは1/2/3でBGM、5/6/7/8で車体色を選択。Spaceで開始。加速はSpace/↑、操舵は←/→、ブレーキはX/↓、視点切替はCです。初期視点は運転席です。Escでポーズ／復帰、ポーズ中Xでメニューに戻ります。

### 起動しないとき

- `Unknown machine` / `Unknown extension`：通常版ではなく、必要な機種・Geo3D V2定義がある対応版か確認してください。
- `Missing ROM`：エミュレーターが要求するBIOSを適法に入手して配置してください。本ゲームROMとBIOSは別物です。
- 画面が乱れる／真っ黒：Geo3D V2、V9968の内蔵98h I/O、R800機種設定を確認してください。内蔵版を外付け88h構成で使用しないでください。
- 動作が重い：実験段階であり、場面ごとにfpsが変わります。ゲームが未調整である点はREADMEを参照してください。

実機のフラッシュ手順は提供していません。このROMでの実機・カートリッジ互換性は未検証です。

## English

### Requirements

Use an openMSX build supporting **Geo3D V2 and V9968 (256-color EPAL, 256KiB VRAM)**, with the `Panasonic_FS-A1ST_V9968` machine and `geo3d` extension definitions. It must provide R800, at least 256KiB RAM and MSX-MUSIC/OPLL. Supply legally obtained turbo R BIOS/system ROMs in openMSX's normal `systemroms` search locations. The optional launcher needs Python 3, with no extra Python packages.

No emulator or BIOS is downloaded automatically. See [Geo3D openMSX](https://github.com/alexmoncks/openMSX), [Geo3D documentation](https://github.com/alexmoncks/V9968_Cartridge/tree/main/geo3d) and [V9968](https://github.com/hra1129/V9968_Cartridge). This is a developing extension: arbitrary builds are not guaranteed compatible. If the required machine/extension definitions are absent, obtain compatible definitions separately.

### Start on Windows

Open PowerShell in the extracted directory and run:

```powershell
python tools/play.py --openmsx "C:/path/to/compatible-openmsx/openmsx.exe"
```

Or set `$env:OPENMSX` to that executable path and run `.\PLAY.cmd`. Replace the example path with your actual installation. The launcher uses normal 100% emulation speed and enables sound; it does not flash firmware.

Without Python, run openMSX directly from the extracted directory:

```powershell
& "C:/path/to/compatible-openmsx/openmsx.exe" -machine Panasonic_FS-A1ST_V9968 -ext geo3d -cart rom/MAGICAL_HAPPY_RACE_3D_INTERNAL_98H.rom -romtype ASCII16 -script tools/play.tcl
```

Press Space to start. Space/Up accelerates, Left/Right steers, X/Down brakes and C switches camera. The default is cockpit view. Esc pauses/resumes; X while paused returns to the menu.

### Troubleshooting

Unknown machine/extension means your emulator lacks the required definitions. Missing ROM errors refer to legally obtained system BIOS files, not necessarily the game ROM. A corrupt or blank screen may indicate the wrong Geo3D version, V9968 I/O configuration or CPU/machine. Use the matching internal 98h or external 88h ROM. Frame rate varies by scene; see the prototype limitations in README.

No hardware flashing instructions are provided. This release's physical hardware and cartridge compatibility are unverified.


## 外付けV9968版（88h） / External V9968 edition (88h)

内蔵98h版と外付け88h版を別のROMで提供します。外付け版は `rom/MAGICAL_HAPPY_RACE_3D_EXTERNAL_88H.rom` です。**V9968は88h〜8Ch、Geo3D V2は8Dh/8Fh**を使用します。実機では外付けV9968側の映像出力を使用する構成です。ただし、この公開ROMの実機・FPGA・BlueMSX+での動作は未検証です。

対応版openMSXで `Panasonic_FS-A1ST`、`HRA_V9968`、`geo3d88` を使用します。通常のMSX本体側VDPと外付けV9968が共存します。`geo3d88` は外付けVDP（V9968）に接続する設定が必要です。

```powershell
python tools/play.py --external-88h --openmsx "C:/path/to/compatible-openmsx/openmsx.exe"
```

`OPENMSX` を設定済みなら `PLAY_EXTERNAL_88H.cmd` でも起動できます。ランチャーは外付け側の映像を選択します。

Pythonを使わない場合 / Without Python:

```powershell
& "C:/path/to/compatible-openmsx/openmsx.exe" -machine Panasonic_FS-A1ST -ext HRA_V9968 -ext geo3d88 -cart rom/MAGICAL_HAPPY_RACE_3D_EXTERNAL_88H.rom -romtype ASCII16 -script tools/play-external.tcl
```

If the screen shows the host MSX instead of the game, select **V9968** as openMSX's video source. The provided external launcher does this automatically. Required machine and extension definitions must be supplied by your compatible emulator installation.

The external ROM uses V9968 ports **88h–8Ch** and Geo3D V2 ports **8Dh/8Fh**; the original ROM uses the internal 98h connection. Keep the ROM and emulator/board I/O configuration matched. The external version is for the cartridge VDP output, not the host's internal VDP output. Physical hardware, FPGA and BlueMSX+ remain unverified for this ROM.
