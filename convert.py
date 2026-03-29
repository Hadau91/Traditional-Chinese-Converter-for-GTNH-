import os
import sys
import shutil
import zipfile
from opencc import OpenCC

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

    print("=== 第三階段: mods ===")
    stage3(base_path, replace_dict)


if __name__ == "__main__":
    main()