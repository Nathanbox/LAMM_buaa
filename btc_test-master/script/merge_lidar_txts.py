#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_lidar_txts.py

将指定文件夹内的所有 .txt 文件按文件名（时间戳）从小到大排序，并将每个源文件的内容作为一行写入目标文件。
目标文件保存在源文件夹的父目录，文件名为：<源文件夹名>.txt

用法:
    python3 merge_lidar_txts.py /path/to/mainold_1s_lidar

如果不提供路径，默认使用当前工作目录下的 `mainold_1s_lidar`。

注意：如果源文件中含有多行，脚本会将换行替换为空格，保证每个源文件对应目标文件的一行。
"""

import argparse
import os
import sys
import re
import shutil


def sort_key(fname):
    """尝试从文件名中提取整数时间戳用于排序；若提取失败，退回为文件名字符串排序。
    为避免不同类型导致的比较错误，返回统一类型：
    - 若能解析为数字，返回 (0, number)
    - 否则返回 (1, lowercased-string)
    """
    base = os.path.splitext(fname)[0]
    # 直接整个 base 是数字
    if re.fullmatch(r"\d+", base):
        return (0, int(base))
    # 提取末尾的数字序列
    m = re.search(r"(\d+)(?!.*\d)", base)
    if m:
        try:
            return (0, int(m.group(1)))
        except Exception:
            pass
    # 最后使用小写的字母序作为后备
    return (1, base.lower())


def merge(folder):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        print(f"错误：{folder} 不是一个存在的目录", file=sys.stderr)
        sys.exit(2)

    files = [f for f in os.listdir(folder) if f.lower().endswith('.txt')]
    if not files:
        print(f"目录 {folder} 中没有找到 .txt 文件，退出。")
        return

    files.sort(key=sort_key)

    parent = os.path.abspath(os.path.join(folder, os.pardir))
    outname = os.path.basename(os.path.normpath(folder)) + '.txt'
    outpath = os.path.join(parent, outname)

    # 写入时以 utf-8 保存，源文件读取使用 replace 错误处理以防编码问题
    with open(outpath, 'w', encoding='utf-8') as out:
        for fname in files:
            path = os.path.join(folder, fname)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception as e:
                print(f"读取文件 {path} 时出错：{e}", file=sys.stderr)
                content = ''
            # 将内部行换行合并为单行，去除首尾空白
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            content = ' '.join(line.strip() for line in content.split('\n') if line.strip() != '')
            out.write(content + '\n')

    print(f"合并完成，输出文件：{outpath}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=('处理指定父文件夹内的所有子文件夹：对每个子文件夹中所有 .txt 文件按文件名时间戳排序，'
                     '将每个源文件内容合并为一行并输出为一个 <子文件夹名>.txt 到父文件夹（与子文件夹平行），'
                     '然后删除子文件夹内的单个 .txt 文件。')
    )
    parser.add_argument('folder', nargs='?', default='.',
                        help='包含若干子文件夹的父目录路径，默认当前目录')
    args = parser.parse_args()
    parent = args.folder
    parent = os.path.abspath(parent)
    if not os.path.isdir(parent):
        print(f"错误：{parent} 不是一个目录", file=sys.stderr)
        sys.exit(2)



    # 遍历父目录下的每个子文件夹并处理
    # 先收集父目录下的子目录（排除隐藏目录和 __pycache__），并按文件名时间戳排序
    raw_subdirs = [d for d in os.listdir(parent) if os.path.isdir(os.path.join(parent, d))]
    subdirs = [d for d in raw_subdirs if not (d.startswith('.') or d == '__pycache__')]
    if not subdirs:
        print(f"在 {parent} 下未找到可处理的子文件夹。")
        sys.exit(0)
    # 按原始文件夹名的时间戳排序，以保证重命名顺序可预测
    subdirs.sort(key=sort_key)

    # 将子文件夹先重命名为临时名以避免命名冲突，然后再批量改为 0,1,2,...
    temp_pairs = []
    # 记录原始名字 -> 数字名 的映射，便于打印
    rename_map = []
    try:
        for idx, name in enumerate(subdirs):
            src = os.path.join(parent, name)
            temp = os.path.join(parent, f'.tmpdir_rename_{idx}')
            if os.path.exists(temp):
                # 覆盖已有的临时名（极少发生）
                if os.path.isdir(temp):
                    shutil.rmtree(temp)
                else:
                    os.remove(temp)
            os.rename(src, temp)
            temp_pairs.append((temp, os.path.join(parent, str(idx))))
            rename_map.append((name, str(idx)))
        # 再把临时名改为最终的数字名
        for temp, final in temp_pairs:
            if os.path.exists(final):
                # 若目标名已存在，先删除以便覆盖
                if os.path.isdir(final):
                    shutil.rmtree(final)
                else:
                    os.remove(final)
            os.rename(temp, final)
        # 打印映射信息
        if rename_map:
            print("子文件夹重命名映射：")
            for orig, new in rename_map:
                print(f"  {orig} -> {new}")
    except Exception as e:
        print(f"在重命名子文件夹为临时名或数字名时出错：{e}", file=sys.stderr)
        # 尝试回滚：将已重命名的临时文件恢复为原名（但不保证完全恢复）
        for temp, final in temp_pairs:
            try:
                if os.path.exists(final) and not os.path.exists(temp):
                    # final 已经存在，尝试把它改回 temp 再恢复原名
                    os.rename(final, temp)
            except Exception:
                pass
        print("中止处理。请检查目录并重试。")
        sys.exit(1)

    any_processed = False
    # 按数字顺序处理重命名后的子文件夹
    for idx in range(len(subdirs)):
        name = str(idx)
        sub = os.path.join(parent, name)
        print(f"处理子文件夹: {sub}")
        # 处理子文件夹中的 txt 并把合并文件输出到 parent
        files = [f for f in os.listdir(sub) if f.lower().endswith('.txt') and os.path.isfile(os.path.join(sub, f))]
        if not files:
            print(f"  跳过（没有找到 .txt 文件）：{sub}")
            continue
        files.sort(key=sort_key)
        outname = os.path.basename(os.path.normpath(sub)) + '.txt'
        outpath = os.path.join(parent, outname)
        try:
            with open(outpath, 'w', encoding='utf-8') as out:
                for fname in files:
                    path = os.path.join(sub, fname)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"  读取文件 {path} 时出错：{e}", file=sys.stderr)
                        content = ''
                    content = content.replace('\r\n', '\n').replace('\r', '\n')
                    content = ' '.join(line.strip() for line in content.split('\n') if line.strip() != '')
                    out.write(content + '\n')
            # 合并成功后：首先按时间戳将子文件夹内的 .pcd 文件重命名为 1.pcd、2.pcd、...（安全重命名以避免冲突）
            pcd_files = [p for p in os.listdir(sub) if p.lower().endswith('.pcd') and os.path.isfile(os.path.join(sub, p))]
            renamed_pcd = 0
            if pcd_files:
                pcd_files.sort(key=sort_key)
                temp_pairs = []
                try:
                    # 第一步：将原文件移动为临时隐藏名，避免与目标名冲突
                    for pidx, pname in enumerate(pcd_files, start=1):
                        src = os.path.join(sub, pname)
                        temp = os.path.join(sub, f'.tmp_rename_{pidx}.pcd')
                        # 如果 temp 已存在，先删除（很少发生）
                        if os.path.exists(temp):
                            os.remove(temp)
                        os.rename(src, temp)
                        temp_pairs.append((temp, os.path.join(sub, f'{pidx}.pcd')))

                    # 第二步：把临时名按序移动到最终名（覆盖同名目标）
                    for temp, final in temp_pairs:
                        if os.path.exists(final):
                            try:
                                os.remove(final)
                            except Exception:
                                pass
                        os.rename(temp, final)
                        renamed_pcd += 1
                    print(f"  重命名 {renamed_pcd} 个 .pcd 文件为 1..{renamed_pcd}.pcd")
                except Exception as e:
                    # 若出现异常，尝试回滚临时文件（将尚未移动的临时文件还原为原名无法完全恢复）
                    print(f"  在重命名 .pcd 时发生错误：{e}", file=sys.stderr)
                    # 尝试把仍在 temp_pairs 的临时文件恢复为原始名（如果可能）
                    for temp, final in temp_pairs:
                        if os.path.exists(temp) and not os.path.exists(final):
                            try:
                                os.rename(temp, final)
                            except Exception:
                                pass

            # 然后删除子文件夹中的原始 txt 文件
            deleted = 0
            for fname in files:
                try:
                    os.remove(os.path.join(sub, fname))
                    deleted += 1
                except Exception as e:
                    print(f"  无法删除 {os.path.join(sub, fname)}: {e}", file=sys.stderr)
            print(f"  合并完成 -> {outpath} （删除了 {deleted} 个源 txt 文件）")
            any_processed = True
        except Exception as e:
            print(f"  写入输出文件 {outpath} 时出错：{e}", file=sys.stderr)

    if not any_processed:
        print(f"在 {parent} 下未处理到任何子文件夹或没有可合并的 txt 文件。")


        # 检查 parent 下是否存在 truth/ 或 pose_correct/ 文件夹
    truth_dir = os.path.join(parent, 'truth')
    pose_dir = os.path.join(parent, 'pose_correct')
    truth_exists = os.path.isdir(truth_dir)
    pose_exists = os.path.isdir(pose_dir)
    if truth_exists or pose_exists:
        exist_list = []
        if truth_exists:
            exist_list.append('truth')
        if pose_exists:
            exist_list.append('pose_correct')
        print(f"发现以下目录已存在于 {parent}：{', '.join(exist_list)}。")
        print("请手动清空上述目录后再运行脚本（脚本不会自动删除它们）。")
    else:
        # 两个目录都不存在，创建它们
        try:
            os.makedirs(truth_dir, exist_ok=True)
            os.makedirs(pose_dir, exist_ok=True)
            print(f"已创建目录: {truth_dir} 和 {pose_dir}")
        except Exception as e:
            print(f"创建 truth/ 或 pose_correct/ 目录时出错：{e}", file=sys.stderr)
            sys.exit(1)


# ========== 后处理：将每个合并后的 <子文件夹名>.txt 的第一列时间戳从 ns 转为 s，保留 5 位小数 ==========
# 处理逻辑：只处理那些其文件名（去掉 .txt 后）在 parent 目录下作为子文件夹存在的 txt 文件，保证只改合并文件。
try:
    converted_count = 0
    for fname in os.listdir(parent):
        if not fname.lower().endswith('.txt'):
            continue
        base = os.path.splitext(fname)[0]
        # 仅处理那些与子文件夹同名的合并文件
        if not os.path.isdir(os.path.join(parent, base)):
            continue

        path = os.path.join(parent, fname)
        tmp_path = path + '.tmp'
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as r, \
                    open(tmp_path, 'w', encoding='utf-8') as w:
                for line in r:
                    if not line.strip():
                        w.write('\n')
                        continue
                    parts = line.rstrip('\n').split(None, 1)
                    ts = parts[0]
                    rest = parts[1] if len(parts) > 1 else ''
                    ts_out = ts
                    # 尝试把 ts 视为纳秒数（int），转为秒并保留 5 位小数；失败则尝试 float
                    try:
                        ns_val = int(ts)
                        s_val = ns_val / 1e9
                        ts_out = f"{s_val:.5f}"
                    except Exception:
                        try:
                            fval = float(ts)
                            s_val = fval / 1e9
                            ts_out = f"{s_val:.5f}"
                        except Exception:
                            # 无法解析，保持原样
                            ts_out = ts

                    # 对剩余字段逐个尝试解析为浮点数，成功则格式化为 8 位小数，失败则保留原样
                    if rest:
                        parts_rest = rest.split()
                        formatted = []
                        for tok in parts_rest:
                            try:
                                v = float(tok)
                                formatted.append(f"{v:.8f}")
                            except Exception:
                                formatted.append(tok)
                        w.write(f"{ts_out} {' '.join(formatted)}\n")
                    else:
                        w.write(f"{ts_out}\n")

            # 原子替换
            os.replace(tmp_path, path)
            converted_count += 1
        except Exception as e:
            print(f"处理文件 {path} 时出错：{e}", file=sys.stderr)
            # 清理临时文件（若存在）
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    print(f"时间戳后处理完成，共转换 {converted_count} 个合并文件（ns -> s，保留5位小数）。")
except Exception as e:
    print(f"执行时间戳后处理时发生错误：{e}", file=sys.stderr)
