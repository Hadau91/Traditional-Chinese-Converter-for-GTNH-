import os
import sys
import shutil
import zipfile
from opencc import OpenCC
import re
import tempfile
from datetime import datetime

# 初始化 OpenCC（簡體 → 繁體）
cc = OpenCC('s2t')

# 讀取字典
def load_dict(path):
    replace_dict = {}
    if not os.path.exists(path):
        return replace_dict

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                k, v = line.split('=', 1)
                replace_dict[k.strip()] = v.strip()
    return replace_dict


# 套用字典
def apply_dict(text, replace_dict):
    for k, v in replace_dict.items():
        text = text.replace(k, v)
    return text


# 轉換檔案
def convert_file(src, dst, replace_dict):
    try:
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    # 簡→繁
    content = cc.convert(content)

    # 字典修正
    content = apply_dict(content, replace_dict)

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✔ 轉換: {src}")


# =========================
# 第一階段：config
# =========================
def stage1(base_path, replace_dict):
    config_path = os.path.join(base_path, ".minecraft", "config")

    for root, dirs, files in os.walk(config_path):
        for file in files:
            if "zh_CN" in file:
                src = os.path.join(root, file)
                dst = os.path.join(root, file.replace("zh_CN", "zh_TW"))

                convert_file(src, dst, replace_dict)


# =========================
# 第二階段：GregTech
# =========================
def stage2(base_path, replace_dict):
    mc_path = os.path.join(base_path, ".minecraft")

    src = os.path.join(mc_path, "GregTech_zh_CN.lang")
    dst = os.path.join(mc_path, "GregTech_zh_TW.lang")

    if os.path.exists(src):
        convert_file(src, dst, replace_dict)


# =========================
# 第三階段：mods jar
# =========================
def stage3(base_path, replace_dict):
    mods_path = os.path.join(base_path, ".minecraft", "mods")

    for file in os.listdir(mods_path):
        if file.endswith(".jar"):
            jar_path = os.path.join(mods_path, file)

            temp_dir = jar_path + "_temp"

            try:
                # 解壓
                with zipfile.ZipFile(jar_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                modified = False

                # 搜尋 zh_CN.lang
                for root, dirs, files in os.walk(temp_dir):
                    for f in files:
                        if f == "zh_CN.lang":
                            src = os.path.join(root, f)
                            dst = os.path.join(root, "zh_TW.lang")

                            convert_file(src, dst, replace_dict)
                            modified = True

                # 重新壓縮
                if modified:
                    new_jar = jar_path + ".new"

                    with zipfile.ZipFile(new_jar, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(temp_dir):
                            for f in files:
                                full_path = os.path.join(root, f)
                                rel_path = os.path.relpath(full_path, temp_dir)
                                zipf.write(full_path, rel_path)

                    # 覆蓋原檔
                    os.remove(jar_path)
                    os.rename(new_jar, jar_path)

                    print(f"✔ 更新 JAR: {file}")

            except Exception as e:
                print(f"✘ 錯誤: {file} -> {e}")

            finally:
                # 清理
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)


# =========================
# 第四階段：GuideNH 遊戲內百科
# =========================

def convert_text_content(content, replace_dict):
    """簡體轉繁體並套用自訂字典"""
    content = cc.convert(content)
    content = apply_dict(content, replace_dict)
    return content


def convert_text_file(src, dst, replace_dict):
    """讀取文字檔，自動判斷常見編碼並保留 UTF-8 BOM"""
    try:
        with open(src, "rb") as f:
            raw = f.read()

        # 判斷編碼
        if raw.startswith(b"\xef\xbb\xbf"):
            encoding = "utf-8-sig"
        else:
            encoding = None

        if encoding:
            content = raw.decode(encoding)
        else:
            try:
                content = raw.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                content = raw.decode("gb18030")
                encoding = "gb18030"

        content = convert_text_content(content, replace_dict)

        with open(dst, "w", encoding=encoding, newline="") as f:
            f.write(content)

        return True

    except (UnicodeDecodeError, OSError, LookupError) as e:
        print(f"  [跳過] 無法轉換文字檔：{src} ({e})")
        return False


def rename_zh_cn(name):
    """不區分大小寫，將檔名中的 zh_cn 替換成 zh_tw"""
    return re.sub(
        r"zh_cn",
        "zh_tw",
        name,
        flags=re.IGNORECASE
    )


def stage3_guidenh(base_path, replace_dict):
    print("\n=== 第三階段：GuideNH 遊戲內百科 ===")

    guide_path = os.path.join(
        base_path,
        ".minecraft",
        "config",
        "guidenh",
        "DefaultGuide.zip"
    )

    if not os.path.isfile(guide_path):
        print(f"[略過] 找不到百科檔案：{guide_path}")
        return

    print(f"百科檔案：{guide_path}")

    # 建立備份
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = guide_path + f".{timestamp}.bak"

    try:
        shutil.copy2(guide_path, backup_path)
        print(f"[備份] {backup_path}")
    except OSError as e:
        print(f"[錯誤] 無法建立備份：{e}")
        return

    converted_files = 0
    copied_dirs = 0
    converted_md = 0

    # 使用暫存資料夾，避免直接修改原始 ZIP
    with tempfile.TemporaryDirectory(
        prefix="GTNH_Guide_",
        dir=os.path.dirname(guide_path)
    ) as temp_dir:

        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir)

        try:
            # 1. 解壓縮 ZIP
            print("\n[1/4] 解壓縮百科檔案...")

            with zipfile.ZipFile(guide_path, "r") as zip_ref:
                for info in zip_ref.infolist():
                    # 防止 ZIP 路徑穿越
                    target = os.path.abspath(
                        os.path.join(extract_dir, info.filename)
                    )

                    if os.path.commonpath(
                        [os.path.abspath(extract_dir), target]
                    ) != os.path.abspath(extract_dir):
                        raise ValueError(
                            f"ZIP 包含不安全路徑：{info.filename}"
                        )

                    zip_ref.extract(info, extract_dir)

            print("[完成] 解壓縮成功")

            # 2. 搜尋所有檔名含 zh_cn 的檔案
            print("\n[2/4] 搜尋 zh_cn 檔案...")

            for root, dirs, files in os.walk(extract_dir):
                for filename in files:

                    if "zh_cn" not in filename.lower():
                        continue

                    src = os.path.join(root, filename)
                    new_filename = rename_zh_cn(filename)
                    dst = os.path.join(root, new_filename)

                    if convert_text_file(src, dst, replace_dict):
                        converted_files += 1
                        print(f"  [轉換] {filename} -> {new_filename}")

            # 3. 複製所有 _zh_cn 資料夾至 _zh_tw
            print("\n[3/4] 搜尋並複製 _zh_cn 資料夾...")

            zh_cn_dirs = []

            # 先搜尋原始資料夾，避免搜尋到新建立的 _zh_tw
            for root, dirs, files in os.walk(extract_dir):
                for dirname in dirs:
                    if dirname.lower() == "_zh_cn":
                        zh_cn_dirs.append(
                            os.path.join(root, dirname)
                        )

            for src_dir in zh_cn_dirs:

                parent_dir = os.path.dirname(src_dir)
                dst_dir = os.path.join(parent_dir, "_zh_tw")

                # 若原本已有 _zh_tw，先移除舊版本
                if os.path.exists(dst_dir):
                    shutil.rmtree(dst_dir)

                # 完整複製資料夾及所有子目錄、檔案
                shutil.copytree(src_dir, dst_dir)

                copied_dirs += 1
                print(f"  [複製] {src_dir}")
                print(f"      -> {dst_dir}")

                # 只轉換新資料夾中的 Markdown 檔案
                for root, dirs, files in os.walk(dst_dir):
                    for filename in files:

                        if filename.lower().endswith(".md"):
                            md_path = os.path.join(root, filename)

                            if convert_text_file(
                                md_path,
                                md_path,
                                replace_dict
                            ):
                                converted_md += 1

                print(f"  [完成] Markdown 檔案轉換")

            
            # 4. 重新壓縮 ZIP
            print("\n[4/4] 重新壓縮百科檔案...")

            new_zip = os.path.join(temp_dir, "DefaultGuide_new.zip")

            with zipfile.ZipFile(guide_path, "r") as original_zip:

                # 記錄原始 ZIP 已有的檔案
                original_entries = {
                    info.filename for info in original_zip.infolist()
                }

                with zipfile.ZipFile(
                    new_zip, "w", zipfile.ZIP_DEFLATED
                ) as new_zip_file:

                    # 保留所有原始檔案
                    for info in original_zip.infolist():
                        file_path = os.path.join(
                            extract_dir, info.filename
                        )

                        if info.is_dir():
                            new_zip_file.writestr(info, b"")
                        else:
                            with open(file_path, "rb") as f:
                                new_zip_file.writestr(info, f.read())

                    # 加入所有新產生的檔案及資料夾
                    for root, dirs, files in os.walk(extract_dir):

                        for dirname in dirs:
                            full_path = os.path.join(root, dirname)
                            relative_path = os.path.relpath(
                                full_path, extract_dir
                            ).replace(os.sep, "/")

                            entry_name = relative_path.rstrip("/") + "/"

                            if entry_name not in original_entries:
                                new_zip_file.writestr(entry_name, b"")

                        for filename in files:
                            full_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(
                                full_path, extract_dir
                            ).replace(os.sep, "/")

                            if relative_path not in original_entries:
                                new_zip_file.write(
                                    full_path,
                                    relative_path,
                                    compress_type=zipfile.ZIP_DEFLATED
                                )

            # 成功產生新 ZIP 後才取代原檔
            os.replace(new_zip, guide_path)

            print("\n[完成] GuideNH 百科轉換成功！")


        except Exception as e:
            print(f"\n[錯誤] GuideNH 轉換失敗：{e}")
            print(f"原始備份位置：{backup_path}")
            return

    print("\n========== GuideNH 轉換統計 ==========")
    print(f"zh_CN 檔案轉換數量：{converted_files}")
    print(f"_zh_cn 資料夾複製數量：{copied_dirs}")
    print(f"Markdown 轉換數量：{converted_md}")
    print(f"備份位置：{backup_path}")
    print("======================================")



# =========================
# 主程式
# =========================
def main():
    if len(sys.argv) < 2:
        print("請提供路徑")
        return

    base_path = sys.argv[1]

    dict_path = os.path.join(os.path.dirname(__file__), "dictionary.txt")
    replace_dict = load_dict(dict_path)

    print("=== 第一階段: config ===")
    stage1(base_path, replace_dict)

    print("=== 第二階段: GregTech ===")
    stage2(base_path, replace_dict)

    print("=== 第三階段: GuideNH ===")
    stage3_guidenh(base_path, replace_dict)


if __name__ == "__main__":
    main()
