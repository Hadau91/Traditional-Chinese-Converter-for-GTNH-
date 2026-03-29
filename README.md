# Traditional-Chinese-Converter-for-GTNH-
簡繁中文轉換器，自動轉換 GTNH 內所有含 zh_CN 的語言檔

支援自訂字典(dictionary.txt)進行慣用語翻譯修正

使用說明:
1. 在電腦上安裝Python，可以是3.10~3.12的版本。
2. 打開 cmd 或 PowerShell 輸入執行：pip install opencc-python-reimplemented。
3. 將zip檔內所有檔案解壓縮到同一個資料夾內。
4. 點擊啟動run.bat，輸入你想轉換的GTNH資料夾位置，例如：D:\.Minecraft\PrismLauncher\instances\GT_New_Horizons_2.8.4_Java_17-25。
5. 等待程式跑完(約20~30分鐘...)，開啟遊戲並將語言切換到繁體中文，退出遊戲再重進即可完成轉換。

⚠️ 注意：會覆蓋 mods 的.jar檔案，建議先備份！如果有翻譯用詞想優化，也可以直接改字典檔，但是工具要重跑才能更新。
